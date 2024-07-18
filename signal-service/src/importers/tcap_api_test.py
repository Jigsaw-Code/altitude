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

# pylint: disable=missing-docstring
"""Test that the TCAP API Signal Importer behaves as expected."""

import copy
import datetime
import http
import json
from typing import Any, Dict
from unittest import mock

import requests_mock
import retry
from absl.testing import parameterized

from importers import importer, tcap_api
from models.job import Job
from models.signal import (
    Content,
    ContentFeatures,
    ContentStatus,
    Signal,
    Source,
    Sources,
)
from testing import test_case
from testing.test_entities import (
    TEST_CASE_RESOLVED_APPROVAL,
    TEST_CASE_RESOLVED_BLOCKED,
    TEST_SIGNAL,
)

_MOCK_TOKEN = "token123"
_MOCK_RESULT = {
    "id": 123,
    "tech_platform": {
        "id": 24,
        "name": "JigsawTestPlatform",
        "description": "",
    },
    "terrorist_group": {
        "id": 5,
        "name": "Bad Guys",
        "description": "",
    },
    "domain": "jigsaw.com",
    "url": "jigsaw.com/Gunpowder_Plot",
    "created_by": {"username": "abc123"},
    "created_on": "2023-03-10T11:40:57.267447",
    "url_status": "UNK",
    "status_tested_on": "2023-03-10T11:40:57.267521",
    "pii_flag": True,
    "extreme_content_flag": False,
}


class TcapApiImporterLibTest(parameterized.TestCase, test_case.TestCase):
    def setUp(self):
        super().setUp()

        self.mock_requests = self.enter_context(requests_mock.Mocker())
        self.mock_requests.post(
            "https://staging.terrorismanalytics.org/token-auth/tcap/",
            json={"token": _MOCK_TOKEN},
        )
        self.enter_context(mock.patch.object(retry.api.time, "sleep"))

    def test_pre_check_fails_on_bad_credentials(self):
        self.mock_requests.post(
            "https://staging.terrorismanalytics.org/token-auth/tcap/", json={}
        )

        with self.assertRaises(importer.PreCheckError):
            tcap_api.TcapApiImporter(username="user1", password="pass1").pre_check()

    def test_get_data_converts_to_signals(self):
        self.mock_requests.get(
            "https://staging.terrorismanalytics.org/integrations/api/jigsaw/urls/",
            json={"results": [_MOCK_RESULT]},
        )

        new_ids = list(
            sum(
                tcap_api.TcapApiImporter(username="user1", password="pass1").run(20), ()
            )
        )

        self.assertLen(new_ids, 1)
        expected = Signal(
            id=new_ids[0],
            content=[
                Content(
                    value="jigsaw.com/Gunpowder_Plot",
                    content_type=Content.ContentType.URL,
                )
            ],
            sources=Sources(
                sources=[
                    Source(
                        name=Source.Name.TCAP,
                        source_signal_id="123",
                        report_date=mock.ANY,
                    )
                ]
            ),
            content_features=ContentFeatures(
                associated_terrorist_organizations=["Bad Guys"],
                contains_pii=ContentFeatures.Confidence.YES,
                is_violent_or_graphic=ContentFeatures.Confidence.NO,
            ),
            content_status=ContentStatus(
                last_checked_date=mock.ANY,
                most_recent_status=ContentStatus.Status.UNKNOWN,
                verifier=ContentStatus.Verifier.TCAP,
            ),
        )
        self.assertEqual(
            expected,
            Signal.objects.get(id=new_ids[0]),
        )

    def test_get_data_calls_token_auth_with_credentials(self):
        adapter = self.mock_requests.post(
            "https://staging.terrorismanalytics.org/token-auth/tcap/",
            json={"token": _MOCK_TOKEN},
        )
        self.mock_requests.get(
            "https://staging.terrorismanalytics.org/integrations/api/jigsaw/urls/",
            json={},
        )

        list(tcap_api.TcapApiImporter(username="user1", password="pass1").run(20))

        assert adapter.called
        self.assertEqual(
            {"username": "user1", "password": "pass1"}, adapter.last_request.json()
        )

    def test_get_data_handles_bad_token_return(self):
        self.mock_requests.post(
            "https://staging.terrorismanalytics.org/token-auth/tcap/", status_code=405
        )
        tcap_api_importer = tcap_api.TcapApiImporter(username="user1", password="pass1")

        with self.assertRaises(importer.PreCheckError):
            list(tcap_api_importer.run(20))

    def test_get_data_calls_get_with_token(self):
        adapter = self.mock_requests.get(
            "https://staging.terrorismanalytics.org/integrations/api/jigsaw/urls/",
            json={},
        )

        list(tcap_api.TcapApiImporter(username="user1", password="pass1").run(20))

        assert adapter.called
        self.assertEqual(
            "Bearer token123", adapter.last_request.headers.get("Authorization")
        )

    def test_uses_job_continuation_token(self):
        adapter = self.mock_requests.get(
            "https://staging.terrorismanalytics.org/integrations/api/jigsaw/urls/",
            json={},
        )
        previous_job = Job(
            status=Job.JobStatus.FAILURE,
            type=Job.JobType.SIGNAL_IMPORT,
            source=Job.JobSource.TCAP_API,
            start_time=datetime.datetime(2020, 12, 28),
            import_size=1,
            last_successful_continuation_token=(
                "https://staging.terrorismanalytics.org/integrations/api/jigsaw/urls/?page=3"
            ),
            continuation_token=(
                "https://staging.terrorismanalytics.org/integrations/api/jigsaw/urls/?page=4"
            ),
        )
        previous_job.save()

        list(tcap_api.TcapApiImporter(username="user1", password="pass1").run(20))

        assert adapter.called
        self.assertEqual({"page": ["3"]}, adapter.last_request.qs)

    def test_api_calls_retry(self):
        adapter = self.mock_requests.get(
            "https://staging.terrorismanalytics.org/integrations/api/jigsaw/urls/",
            status_code=403,
        )
        tcap_api_importer = tcap_api.TcapApiImporter(username="user1", password="pass1")

        list(tcap_api_importer.run(20))

        self.assertEqual(5, adapter.call_count)

    def test_updates_continuation_token(self):
        response_next = (
            "https://staging.terrorismanalytics.org/"
            "integrations/api/jigsaw/urls/?page=3"
        )
        self.mock_requests.get(
            "https://staging.terrorismanalytics.org/integrations/api/jigsaw/urls/",
            [
                {"json": {"results": [_MOCK_RESULT], "next": response_next}},
                {"json": {}},
            ],
        )

        list(tcap_api.TcapApiImporter(username="user1", password="pass1").run(20))

        self.assertEqual(response_next, Job.objects.get().continuation_token)

    def test_send_diagnostics(self):
        adapter = self.mock_requests.post(
            "https://staging.terrorismanalytics.org/integrations/api/jigsaw/decisions/",
            json={},
        )
        signal = copy.deepcopy(TEST_SIGNAL)
        signal.content = [
            Content(value="foo.com", content_type=Content.ContentType.URL)
        ]
        signal.save()
        copy.deepcopy(TEST_CASE_RESOLVED_APPROVAL).save()
        copy.deepcopy(TEST_CASE_RESOLVED_BLOCKED).save()

        tcap_api.TcapApiImporter(username="user1", password="pass1").send_diagnostics(
            datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(hours=1),
            datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(hours=1),
        )

        assert adapter.called
        self.assertEqual(
            [
                {"url": "foo.com", "decision": "APPROVE"},
                {"url": "foo.com", "decision": "REMOVE"},
            ],
            adapter.last_request.json(),
        )
