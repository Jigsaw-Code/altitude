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

"""Define class for importing Signals using ThreatExchange's API."""

import datetime
import functools
import logging
from typing import Any, Iterable

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

from importers import importer
from models.case import Review
from models.job import Job
from models.signal import Content, ContentFeatures, Signal, Source, Sources

# Fields in the ThreatExchange API response.
_RESPONSE_DATA = "data"
_RESPONSE_PAGING = "paging"
_RESPONSE_CURSORS = "cursors"
_RESPONSE_AFTER = "after"
_RESPONSE_NEXT = "next"

# Fields in the returned data.
_ID = "id"
_INDICATOR = "indicator"
_TYPE = "type"
_SHOULD_DELETE = "should_delete"
_ADDED_ON = "added_on"
_LAST_UPDATED = "last_updated"
_CREATION_TIME = "creation_time"
_DESCRIPTORS = "descriptors"
_DATA = "data"
_CONFIDENCE = "confidence"
_DESCRIPTION = "description"
_OWNER = "owner"
_NAME = "name"
_REVIEW_STATUS = "review_status"
_TAGS = "tags"

REQUEST_TIMEOUT_SEC = 30

SignalData = dict[str, Any]

GIFCT_DECISION_MAP = {
    Review.Decision.APPROVE: "NON_MALICIOUS",
    Review.Decision.BLOCK: "HELPFUL",
}


def _get_sources(signal: SignalData, source_name: Source.Name) -> list[Source]:
    def get_report_date(
        *, signal: SignalData, source_data: dict[str, Any]
    ) -> datetime.datetime | None:
        """Get the most appropriate available report date.

        Use the source's creation date, the source's last update date, the
        signal's creation time, or the signal's last update time in that order.
        """
        if _ADDED_ON in source_data:
            # TODO use fromisoformat() here and below once the Python
            # version is >= 3.11.
            # https://docs.python.org/3.11/library/datetime.html#datetime.datetime.fromisoformat
            return datetime.datetime.strptime(
                source_data[_ADDED_ON], "%Y-%m-%dT%H:%M:%S%z"
            )
        if _LAST_UPDATED in source_data:
            return datetime.datetime.strptime(
                source_data[_LAST_UPDATED], "%Y-%m-%dT%H:%M:%S%z"
            )
        if _CREATION_TIME in signal:
            return datetime.datetime.fromtimestamp(signal[_CREATION_TIME])
        if _LAST_UPDATED in signal:
            return datetime.datetime.fromtimestamp(signal[_LAST_UPDATED])

        return None

    sources = []
    for source_data in signal.get(_DESCRIPTORS, {}).get(_DATA, [{}]):
        sources.append(
            Source(
                name=source_name,
                author=_get_source_author(signal, source_data),
                source_signal_id=source_data.get(_ID, signal.get(_ID, None)),
                report_date=get_report_date(signal=signal, source_data=source_data),
            )
        )
    return sources


def _get_confidence(signal: SignalData) -> float | None:
    data = signal.get(_DESCRIPTORS, {}).get(_DATA, [{}])
    confidence = 0
    for data_by_source in data:
        confidence = max(confidence, data_by_source.get(_CONFIDENCE, 0))

    if confidence:
        confidence_score = confidence / 100
        return confidence_score

    return None


def _get_source_author(signal: SignalData, source_data: dict[str, Any]) -> str | None:
    name = source_data.get(_OWNER, {}).get(_NAME, None)
    if name:
        return name

    for tag in signal.get(_TAGS, []):
        if tag.lower().startswith("source:"):
            return tag.lower().replace("source:", "")

    return None


def _get_content_features(signal: SignalData) -> ContentFeatures:
    content_features = ContentFeatures()
    review_status = (
        signal.get(_DESCRIPTORS, {}).get(_DATA, [{}])[0].get(_REVIEW_STATUS, None)
    )
    if review_status:
        content_features.tags.append(review_status)

    data_description = (
        signal.get(_DESCRIPTORS, {}).get(_DATA, [{}])[0].get(_DESCRIPTION, None)
    )
    if data_description:
        content_features.tags.append(data_description)

    confidence = _get_confidence(signal)
    if confidence:
        content_features.confidence = confidence

    for tag in signal.get(_TAGS, []):
        if tag.lower().startswith("group:"):
            content_features.associated_terrorist_organizations.append(tag)
        content_features.tags.append(tag)
    return content_features


class ThreatExchangeImporter(importer.Importer):
    """Importer compatible with ThreatExchange's API."""

    SIGNAL_SOURCE = Source.Name.GIFCT

    def __init__(
        self,
        privacy_group_id: str,
        access_token: str,
    ):
        super().__init__(Job.JobSource.THREAT_EXCHANGE_API)
        self._privacy_group_id = privacy_group_id
        self._access_token = access_token

    def _convert_to_signals(
        self, signals: list[SignalData]
    ) -> Iterable[tuple[Signal, importer.Action]]:
        for signal in signals:
            # TODO - add support for more hash types.
            if signal.get(_TYPE, None) not in {x.value for x in Content.ContentType}:
                continue

            action = (
                importer.Action.DELETE
                if signal.get(_SHOULD_DELETE, False)
                else importer.Action.UPDATE_OR_INSERT
            )
            new_signal = Signal(
                content=[
                    Content(
                        value=signal.get(_INDICATOR, None),
                        content_type=Content.ContentType[signal.get(_TYPE, None)],
                    )
                ],
                sources=Sources(sources=_get_sources(signal, self.SIGNAL_SOURCE)),
                content_features=_get_content_features(signal),
            )
            yield (new_signal, action)

    def _get_first_request_url(self) -> str:
        """Get the threat_updates request from after the last successful call."""
        job = self._get_last_job()
        after = job.last_successful_continuation_token if job else None

        threat_updates_url = (
            "https://graph.facebook.com/v16.0/"
            f"{self._privacy_group_id}/threat_updates?"
            f"access_token={self._access_token}&"
            "fields=id,indicator,type,creation_time,last_updated,should_delete"
            ",tags,status,applications_with_opinions,descriptors"
            f"{'&after=' + after if after else ''}"
        )
        return threat_updates_url

    def pre_check(self) -> None:
        """Checks whether the importer is configured correctly."""
        response = self._session.get(
            "https://graph.facebook.com/v16.0/"
            f"{self._privacy_group_id}/threat_updates?"
            f"access_token={self._access_token}&since=0&limit=1",
            timeout=REQUEST_TIMEOUT_SEC,
        )
        if not response.ok:
            message = (
                response.json().get("error", {}).get("message", "Invalid access token")
            )
            raise importer.PreCheckError(message)

    @functools.cached_property
    def _session(self):
        # Use session to avoid overloading the API and to handle random
        # failures.
        session = requests.Session()
        retry = Retry(connect=3, backoff_factor=0.5)
        adapter = HTTPAdapter(max_retries=retry)
        session.mount("https://", adapter)
        return session

    def _get_data(
        self,
    ) -> Iterable[tuple[Signal, importer.Action]]:
        next_request_url = self._get_first_request_url()
        while next_request_url:
            response = self._session.get(
                next_request_url, timeout=REQUEST_TIMEOUT_SEC
            ).json()
            response_data = response.get(_RESPONSE_DATA)

            if not response_data:
                return
            yield from self._convert_to_signals(response_data)

            self._job.last_successful_continuation_token = self._job.continuation_token
            self._job.continuation_token = (
                response.get(_RESPONSE_PAGING)
                .get(_RESPONSE_CURSORS)
                .get(_RESPONSE_AFTER)
            )
            next_request_url = response.get(_RESPONSE_PAGING).get(_RESPONSE_NEXT)

    def _send_decisions(self, decisions: Iterable[tuple[str, Review.Decision]]) -> None:
        """Send the given decisions to the platform."""
        for signal, decision in decisions:
            source = signal.sources.sources.filter(name=self.SIGNAL_SOURCE)[0]
            indicator_id = source.source_signal_id
            descriptor_response = self._session.get(
                f"https://graph.facebook.com/v4.0/{indicator_id}/descriptors/?"
                f"access_token={self._access_token}",
                timeout=REQUEST_TIMEOUT_SEC,
            )
            if not descriptor_response.ok:
                logging.error(
                    "Error getting the descriptor ID from GIFCT: %s",
                    descriptor_response.json().get("error", {}),
                )

            descriptor_id = descriptor_response.json().get(_RESPONSE_DATA)[0][_ID]
            reaction = GIFCT_DECISION_MAP.get(decision)
            response = self._session.post(
                f"https://graph.facebook.com/v4.0/{descriptor_id}?"
                f"access_token={self._access_token}&"
                f"reactions={reaction},SAW_THIS_TOO",
                timeout=REQUEST_TIMEOUT_SEC,
            )
            if not response.ok:
                logging.error(
                    "Error sending reactions to GIFCT: %s",
                    response.json().get("error", {}),
                )
