# Copyright 2023 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""Define class for importing Signals from TCAP APIs into the DB."""
import datetime
import enum
import functools
import logging
from typing import Any, Dict, Iterable, Iterator
from urllib.parse import urljoin

import requests
from retry import retry

from importers import importer
from models.case import Review
from models.job import Job
from models.signal import (
    Content,
    ContentFeatures,
    ContentStatus,
    Signal,
    Source,
    Sources,
)
from utils.iterators import grouper

# Fields from the TCAP API responses
_AUTH_TOKEN = "token"
_RESULTS = "results"
_NEXT = "next"

# Fields in the returned signals.
_ID = "id"
_URL = "url"
_PII_FLAG = "pii_flag"
_EXTREME_CONTENT_FLAG = "extreme_content_flag"
_TERRORIST_GROUP = "terrorist_group"
_NAME = "name"
_STATUS_TESTED_ON = "status_tested_on"
_CREATED_ON = "created_on"
_URL_STATUS = "url_status"
_DESCRIPTION = "description"

_RETRY_CONFIG = {"tries": 5, "delay": 1, "backoff": 2}

REQUEST_TIMEOUT_SEC = 30

_GROUP_SIZE = 10


@enum.unique
class Server(enum.Enum):
    STAGING = "https://staging.terrorismanalytics.org/"
    PROD = "https://beta.terrorismanalytics.org/"


TCAP_DECISION_MAP = {
    Review.Decision.APPROVE: "APPROVE",
    Review.Decision.BLOCK: "REMOVE",
}


class TcapApiImporter(importer.Importer):
    """Importer compatible with Tech Against Terrorism's TCAP API."""

    SIGNAL_SOURCE = Source.Name.TCAP

    def __init__(
        self,
        username: str,
        password: str,
        server: Server = Server.STAGING,
    ):
        super().__init__(Job.JobSource.TCAP_API)
        self._username = username
        self._password = password
        self._server = server

    @functools.cached_property
    def _auth_token(self) -> str | None:
        try:
            response = _send_request(
                urljoin(self._server.value, "token-auth/tcap/"),
                method="POST",
                json={"username": self._username, "password": self._password},
            )
        except importer.Error:
            logging.warning("Failed to get auth token from TCAP.")
            return
        return response.get(_AUTH_TOKEN)

    def _bool_to_confidence(
        self, val: bool | None
    ) -> ContentFeatures.Confidence | None:
        if val is None:
            return None
        return ContentFeatures.Confidence.YES if val else ContentFeatures.Confidence.NO

    def _convert_tcap_status(self, conf: str | None) -> ContentStatus.Status | None:
        if not conf:
            return None
        if conf == "ACT":
            return ContentStatus.Status.ACTIVE
        if conf == "INA":
            return ContentStatus.Status.UNAVAILABLE
        return ContentStatus.Status.UNKNOWN

    def _get_terrorist_organization(
        self, terrorist_org: Dict[str, str] | None
    ) -> str | None:
        if not terrorist_org:
            return None

        description = terrorist_org.get(_DESCRIPTION, None)
        name = terrorist_org.get(_NAME, None)

        if name:
            description_suffix = f": {description}" if description else ""
            return name + description_suffix

        return None

    def _convert_to_datetime(self, iso_time: str | None) -> datetime.datetime | None:
        if not iso_time:
            return None

        return datetime.datetime.fromisoformat(iso_time)

    def _convert_to_signals(
        self, signals: Iterable[Dict[Any, Any]]
    ) -> Iterable[tuple[Signal, importer.Action]]:
        for signal in signals:
            source = Source(
                name=self.SIGNAL_SOURCE,
                source_signal_id=str(signal.get(_ID, None)),
                report_date=self._convert_to_datetime(signal.get(_CREATED_ON, None)),
            )
            terrorist_organizations = []
            terrorist_organization = self._get_terrorist_organization(
                signal.get(_TERRORIST_GROUP, None)
            )
            if terrorist_organization:
                terrorist_organizations = [terrorist_organization]
            content_status = ContentStatus(
                verifier=ContentStatus.Verifier.TCAP,
                last_checked_date=self._convert_to_datetime(
                    signal.get(_STATUS_TESTED_ON, signal.get(_CREATED_ON, None))
                ),
                most_recent_status=self._convert_tcap_status(
                    signal.get(_URL_STATUS, None)
                ),
            )
            new_signal = Signal(
                content_features=ContentFeatures(
                    associated_terrorist_organizations=terrorist_organizations,
                    contains_pii=self._bool_to_confidence(signal.get(_PII_FLAG, None)),
                    is_violent_or_graphic=self._bool_to_confidence(
                        signal.get(_EXTREME_CONTENT_FLAG, None)
                    ),
                ),
                content=[
                    Content(
                        value=signal.get(_URL, None),
                        content_type=Content.ContentType.URL,
                    )
                ],
                content_status=content_status,
                sources=Sources(sources=[source]),
            )
            yield (new_signal, importer.Action.UPDATE_OR_INSERT)

    def _get_first_request_url(self) -> str:
        """Get the first request from after the last successful call."""
        job = self._get_last_job()
        next_url = (
            job.last_successful_continuation_token
            if job and job.last_successful_continuation_token
            else None
        )
        return next_url or urljoin(self._server.value, "integrations/api/jigsaw/urls/")

    def pre_check(self) -> None:
        """Checks whether the importer is configured correctly."""
        if not self._auth_token:
            raise importer.PreCheckError("Failed to get authorization token.")

    def _get_data(
        self,
    ) -> Iterable[tuple[Signal, importer.Action]]:
        next_request_url = self._get_first_request_url()

        while next_request_url:
            token = self._auth_token
            if not token:
                logging.error("Failed to get authorization token. Aborting.")
                return
            try:
                response = _send_request(
                    next_request_url,
                    headers={"Authorization": f"Bearer {token}"},
                )
            except importer.Error:
                logging.warning("Failed to get data from TCAP.")
                return

            response_data = response.get(_RESULTS)
            if not response_data:
                return
            yield from self._convert_to_signals(response_data)

            next_request_url = response.get(_NEXT)
            self._job.last_successful_continuation_token = self._job.continuation_token
            self._job.continuation_token = next_request_url

    def _send_decisions(
        self, decisions: Iterable[tuple[Signal, Review.Decision]]
    ) -> None:
        """Send the given decisions to the platform."""
        for decision_group in grouper(iter(decisions), _GROUP_SIZE):
            data = []
            for signal, decision in decision_group:
                content = signal.content.filter(content_type=Content.ContentType.URL)[0]
                data.append(
                    {
                        "url": content.value,
                        "decision": TCAP_DECISION_MAP.get(decision),
                    }
                )
            token = self._auth_token
            if not token:
                logging.error("Failed to get authorization token. Aborting.")
                return

            try:
                _send_request(
                    urljoin(self._server.value, "integrations/api/jigsaw/decisions/"),
                    method="POST",
                    json=data,
                    headers={"Authorization": f"Bearer {token}"},
                )
            except importer.Error:
                logging.warning("Failed to send decisions to TCAP.")


# The TCAP API seems to allow very few QPS for both API endpoints. We pause and
# retry these calls.
@retry((importer.SourceResponseError), **_RETRY_CONFIG)
def _send_request(url: str, method: str = "GET", **kwargs) -> Dict[str, any]:
    response = requests.request(
        method=method, url=url, timeout=REQUEST_TIMEOUT_SEC, **kwargs
    )
    if not response.ok:
        raise importer.SourceResponseError(
            f"Bad response from TCAP API: {response.text}"
        )
    return response.json()
