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
"""Test that the ThreatExchange API Signal Importer behaves as expected."""

import copy
import datetime
import http
import json
import time
from typing import Any, Dict, List
from unittest import mock

import requests
from absl.testing import parameterized

from importers import importer, threat_exchange
from models.case import Review
from models.job import Job
from models.signal import Content, ContentFeatures, Signal, Source, Sources
from testing import test_case
from testing.test_entities import (
    TEST_CASE_RESOLVED_APPROVAL,
    TEST_CASE_RESOLVED_BLOCKED,
    TEST_SIGNAL,
)

# session.get() has self as it's first argument. This is to make the asserts
# clearer so we are testing what is actually used.
_SESSION_SELF_OBJECT = mock.ANY


def _make_response(
    content: Dict[str, Any], status: int = http.HTTPStatus.OK
) -> requests.Response:
    response = requests.Response()
    response.status_code = status
    if not "paging" in content:
        content["paging"] = {"cursors": {"before": "123", "after": "456"}, "next": ""}
    # pylint: disable=protected-access
    response._content = json.dumps(content).encode("utf-8")
    return response


class ThreatExchangeImporterLibTest(parameterized.TestCase, test_case.TestCase):
    def setUp(self):
        super().setUp()

        self.mock_get = self.enter_context(
            mock.patch.object(requests.Session, "get", autospec=True)
        )
        self.mock_get.return_value = _make_response({})

        self.mock_post = self.enter_context(
            mock.patch.object(requests.Session, "post", autospec=True)
        )
        self.mock_post.return_value = _make_response({})

    def test_pre_check_fails_on_bad_credentials(self):
        self.mock_get.return_value = _make_response({}, http.HTTPStatus.BAD_REQUEST)
        threat_exchange_importer = threat_exchange.ThreatExchangeImporter(
            access_token="abc", privacy_group_id="123"
        )

        with self.assertRaises(importer.PreCheckError):
            threat_exchange_importer.pre_check()

        self.mock_get.assert_called_with(
            _SESSION_SELF_OBJECT,
            "https://graph.facebook.com/v16.0/123/threat_updates?"
            "access_token=abc&since=0&limit=1",
            timeout=mock.ANY,
        )

    @parameterized.named_parameters(
        (
            "sparse_response",
            {
                "data": [
                    {"id": "1", "indicator": "image_hash_123", "type": "HASH_PDQ"}
                ],
            },
            Signal(
                id=mock.ANY,
                content=[
                    Content(
                        value="image_hash_123",
                        content_type=Content.ContentType.HASH_PDQ,
                    )
                ],
                sources=Sources(
                    sources=[
                        Source(
                            name=Source.Name.GIFCT,
                            source_signal_id="1",
                        )
                    ]
                ),
                user_content_to_past_review={},
                content_features=ContentFeatures(
                    associated_terrorist_organizations=[],
                    is_illegal_in_countries=[],
                    tags=[],
                ),
            ),
        ),
        (
            "full_response",
            {
                "data": [
                    {
                        "id": "123",
                        "indicator": "content123",
                        "type": "HASH_MD5",
                        "creation_time": 1599040926,
                        "last_updated": 1607921860,
                        "should_delete": False,
                        "tags": [
                            "tag1",
                            "media_priority_foo",
                            "media_priority_baz",
                        ],
                        "status": "MALICIOUS",
                        "applications_with_opinions": ["456"],
                        "descriptors": {
                            "data": [
                                {
                                    "added_on": "2020-09-02T10:02:06+0000",
                                    "confidence": 50,
                                    "description": "Shared by Company 1",
                                    "id": "123",
                                    "indicator": {
                                        "id": "123",
                                        "indicator": "content123",
                                        "type": "HASH_MD5",
                                    },
                                    "last_updated": "2020-09-02T10:02:07+0000",
                                    "owner": {
                                        "id": "456",
                                        "email": "company1@gmail.com",
                                        "name": "Company 1",
                                    },
                                    "privacy_type": "HAS_PRIVACY_GROUP",
                                    "raw_indicator": "content123",
                                    "review_status": "REVIEWED_MANUALLY",
                                    "severity": "WARNING",
                                    "share_level": "AMBER",
                                    "status": "MALICIOUS",
                                    "type": "HASH_MD5",
                                }
                            ]
                        },
                    }
                ],
            },
            Signal(
                id=mock.ANY,
                content=[
                    Content(
                        value="content123",
                        content_type=Content.ContentType.HASH_MD5,
                    )
                ],
                sources=Sources(
                    sources=[
                        Source(
                            name=Source.Name.GIFCT,
                            author="Company 1",
                            source_signal_id="123",
                            report_date=datetime.datetime(
                                2020, 9, 2, 10, 2, 6, tzinfo=datetime.timezone.utc
                            ),
                        )
                    ]
                ),
                content_features=ContentFeatures(
                    associated_terrorist_organizations=[],
                    is_illegal_in_countries=[],
                    confidence=0.5,
                    tags=[
                        "REVIEWED_MANUALLY",
                        "Shared by Company 1",
                        "tag1",
                        "media_priority_foo",
                        "media_priority_baz",
                    ],
                ),
            ),
        ),
        (
            "two_sources",
            {
                "data": [
                    {
                        "id": "123",
                        "indicator": "content123",
                        "type": "HASH_MD5",
                        "creation_time": 1599040926,
                        "last_updated": 1607921860,
                        "should_delete": False,
                        "tags": [
                            "tag1",
                            "unknown_tag",
                        ],
                        "status": "MALICIOUS",
                        "applications_with_opinions": ["456"],
                        "descriptors": {
                            "data": [
                                {
                                    "added_on": "2022-11-14T01:30:32+0000",
                                    "confidence": 75,
                                    "description": "Company 1 Daily Hash Upload",
                                    "id": "123",
                                    "indicator": {
                                        "id": "123",
                                        "indicator": "content123",
                                        "type": "HASH_MD5",
                                    },
                                    "last_updated": "2022-11-14T01:30:35+0000",
                                    "owner": {
                                        "id": "456",
                                        "name": "Company 1 Media Hash Sharing",
                                    },
                                    "privacy_type": "HAS_PRIVACY_GROUP",
                                    "raw_indicator": "content123",
                                    "review_status": "REVIEWED_MANUALLY",
                                    "severity": "WARNING",
                                    "share_level": "AMBER",
                                    "status": "MALICIOUS",
                                    "type": "HASH_MD5",
                                },
                                {
                                    "added_on": "2018-12-14T16:36:09+0000",
                                    "confidence": 100,
                                    "id": "123",
                                    "indicator": {
                                        "id": "123",
                                        "indicator": "content123",
                                        "type": "HASH_MD5",
                                    },
                                    "last_updated": "2021-08-13T00:07:54+0000",
                                    "owner": {
                                        "id": "789",
                                        "email": "company2@gmail.com",
                                        "name": "Company 2 Hash Sharing",
                                    },
                                    "privacy_type": "HAS_PRIVACY_GROUP",
                                    "raw_indicator": "content123",
                                    "review_status": "REVIEWED_AUTOMATICALLY",
                                    "severity": "INFO",
                                    "share_level": "AMBER",
                                    "status": "MALICIOUS",
                                    "type": "HASH_MD5",
                                },
                            ]
                        },
                    }
                ],
            },
            Signal(
                id=mock.ANY,
                content=[
                    Content(
                        value="content123",
                        content_type=Content.ContentType.HASH_MD5,
                    )
                ],
                sources=Sources(
                    sources=[
                        Source(
                            name=Source.Name.GIFCT,
                            author="Company 1 Media Hash Sharing",
                            source_signal_id="123",
                            report_date=datetime.datetime(
                                2022, 11, 14, 1, 30, 32, tzinfo=datetime.timezone.utc
                            ),
                        ),
                        Source(
                            name=Source.Name.GIFCT,
                            author="Company 2 Hash Sharing",
                            source_signal_id="123",
                            report_date=datetime.datetime(
                                2018, 12, 14, 16, 36, 9, tzinfo=datetime.timezone.utc
                            ),
                        ),
                    ]
                ),
                content_features=ContentFeatures(
                    associated_terrorist_organizations=[],
                    is_illegal_in_countries=[],
                    confidence=1.0,
                    tags=[
                        "REVIEWED_MANUALLY",
                        "Company 1 Daily Hash Upload",
                        "tag1",
                        "unknown_tag",
                    ],
                ),
            ),
        ),
    )
    def test_get_data_converts_to_signals(self, response, expected_signal):
        self.mock_get.return_value = _make_response(response)

        threat_exchange_importer = threat_exchange.ThreatExchangeImporter(
            access_token="abc", privacy_group_id="123"
        )

        new_ids = list(sum(threat_exchange_importer.run(20), ()))
        self.assertLen(new_ids, 1)
        self.assertEqual(
            expected_signal,
            Signal.objects.get(id=new_ids[0]),
        )

    def test_get_data_handles_redactions(self):
        Signal(
            sources=Sources(sources=[Source(name=Source.Name.GIFCT)]),
            content=[
                Content(
                    value="image_hash_123",
                    content_type=Content.ContentType.HASH_PDQ,
                )
            ],
        ).save()
        self.mock_get.return_value = _make_response(
            {
                "data": [
                    {
                        "id": "1",
                        "indicator": "image_hash_123",
                        "type": "HASH_PDQ",
                        "should_delete": True,
                    }
                ],
            }
        )

        threat_exchange_importer = threat_exchange.ThreatExchangeImporter(
            privacy_group_id="group", access_token="token"
        )

        new_ids = list(sum(threat_exchange_importer.run(20), ()))
        self.assertEmpty(new_ids)
        signal = Signal.objects.get()
        self.assertTrue(signal.sources.sources[0].is_redacted)
        self.assertEqual("[REDACTED]", signal.content[0].value)

    @mock.patch.object(time, "time", return_value=3600)
    def test_get_data_calls_threatexchange_api_with_credentials(self, _):
        threat_exchange_importer = threat_exchange.ThreatExchangeImporter(
            privacy_group_id="group", access_token="token"
        )

        list(threat_exchange_importer.run(20))

        self.mock_get.assert_called_with(
            _SESSION_SELF_OBJECT,
            "https://graph.facebook.com/v16.0/group/threat_updates?"
            "access_token=token&fields=id,indicator,type,creation_time,"
            "last_updated,should_delete,tags,status,"
            "applications_with_opinions,descriptors",
            timeout=mock.ANY,
        )

    @mock.patch.object(time, "time", return_value=3600)
    def test_get_data_pagination(self, _):
        self.mock_get.side_effect = [
            # The first response is for the pre-check call.
            _make_response({}),
            _make_response(
                {
                    "data": [
                        {"id": "1", "indicator": "image_hash_1", "type": "HASH_PDQ"}
                    ],
                    "paging": {
                        "cursors": {"before": "123", "after": "456"},
                        "next": "next1",
                    },
                }
            ),
            _make_response(
                {
                    "data": [
                        {"id": "2", "indicator": "image_hash_2", "type": "HASH_PDQ"}
                    ],
                    "paging": {
                        "cursors": {"before": "123", "after": "456"},
                        "next": "next2",
                    },
                }
            ),
            _make_response(
                {
                    "data": [
                        {"id": "3", "indicator": "image_hash_3", "type": "HASH_PDQ"}
                    ],
                    "paging": {
                        "cursors": {"before": "123", "after": "456"},
                        "next": "",
                    },
                }
            ),
        ]

        threat_exchange_importer = threat_exchange.ThreatExchangeImporter(
            privacy_group_id="group", access_token="token"
        )

        new_ids = list(sum(threat_exchange_importer.run(20), ()))

        self.assertLen(new_ids, 3)
        # Check that the Signals have been added to the DB.
        for i in range(1, 4):
            signal = Signal.objects.get(content__value=f"image_hash_{i}")
            values = [content.value for content in signal.content]
            self.assertIn(f"image_hash_{i}", values)

        self.mock_get.assert_has_calls(
            [
                mock.call(
                    _SESSION_SELF_OBJECT,
                    "https://graph.facebook.com/v16.0/group/threat_updates?"
                    "access_token=token&fields=id,indicator,type,creation_time,"
                    "last_updated,should_delete,tags,status,"
                    "applications_with_opinions,descriptors",
                    timeout=mock.ANY,
                ),
                mock.call(_SESSION_SELF_OBJECT, "next1", timeout=mock.ANY),
                mock.call(_SESSION_SELF_OBJECT, "next2", timeout=mock.ANY),
            ]
        )

    @parameterized.named_parameters(
        (
            "no_previous_job",
            [],
            "https://graph.facebook.com/v16.0/group/threat_updates?"
            "access_token=token&fields=id,indicator,type,creation_time,"
            "last_updated,should_delete,tags,status,"
            "applications_with_opinions,descriptors",
        ),
        (
            "filters_out_other_jobs",
            [
                Job(
                    status=Job.JobStatus.SUCCESS,
                    type=Job.JobType.SIGNAL_IMPORT,
                    source=Job.JobSource.THREAT_EXCHANGE_API,
                    start_time=datetime.datetime(2020, 12, 25),
                    import_size=1,
                    continuation_token="abc",
                    last_successful_continuation_token="abc",
                ),
                Job(
                    status=Job.JobStatus.SUCCESS,
                    type=Job.JobType.SIGNAL_IMPORT,
                    source=Job.JobSource.TCAP_CSV,
                    start_time=datetime.datetime(2020, 12, 25),
                    import_size=1,
                    continuation_token="def",
                    last_successful_continuation_token="def",
                ),
                Job(
                    status=Job.JobStatus.FAILURE,
                    type=Job.JobType.SIGNAL_IMPORT,
                    source=Job.JobSource.THREAT_EXCHANGE_API,
                    start_time=datetime.datetime(2020, 12, 25),
                    import_size=1,
                    continuation_token="ghi",
                ),
            ],
            "https://graph.facebook.com/v16.0/group/threat_updates?"
            "access_token=token&fields=id,indicator,type,creation_time,"
            "last_updated,should_delete,tags,status,applications_with_opinions"
            ",descriptors&after=abc",
        ),
        (
            "uses_latest_job",
            [
                Job(
                    status=Job.JobStatus.SUCCESS,
                    type=Job.JobType.SIGNAL_IMPORT,
                    source=Job.JobSource.THREAT_EXCHANGE_API,
                    start_time=datetime.datetime(2020, 12, 25),
                    import_size=1,
                    continuation_token="abc",
                ),
                Job(
                    status=Job.JobStatus.SUCCESS,
                    type=Job.JobType.SIGNAL_IMPORT,
                    source=Job.JobSource.THREAT_EXCHANGE_API,
                    start_time=datetime.datetime(2020, 12, 26),
                    import_size=1,
                    continuation_token="def",
                ),
                Job(
                    status=Job.JobStatus.FAILURE,
                    type=Job.JobType.SIGNAL_IMPORT,
                    source=Job.JobSource.THREAT_EXCHANGE_API,
                    start_time=datetime.datetime(2020, 12, 28),
                    import_size=1,
                    last_successful_continuation_token="ghi",
                    continuation_token="jkl",
                ),
            ],
            "https://graph.facebook.com/v16.0/group/threat_updates?"
            "access_token=token&fields=id,indicator,type,creation_time,"
            "last_updated,should_delete,tags,status,applications_with_opinions"
            ",descriptors&after=ghi",
        ),
    )
    @mock.patch.object(time, "time", return_value=3600)
    def test_get_first_request(self, prev_jobs: List[Job], expected_call: str, _):
        for job in prev_jobs:
            job.save()

        threat_exchange_importer = threat_exchange.ThreatExchangeImporter(
            privacy_group_id="group", access_token="token"
        )
        list(threat_exchange_importer.run(20))

        self.mock_get.assert_called_with(
            _SESSION_SELF_OBJECT, expected_call, timeout=mock.ANY
        )

    def test_job_continuation_token_updates(self):
        continuation_token = "token"
        self.mock_get.return_value = _make_response(
            {
                "data": [
                    {"id": "1", "indicator": "image_hash_123", "type": "HASH_PDQ"}
                ],
                "paging": {"cursors": {"before": "123", "after": continuation_token}},
            }
        )

        threat_exchange_importer = threat_exchange.ThreatExchangeImporter(
            privacy_group_id="group", access_token="token"
        )

        new_ids = list(sum(threat_exchange_importer.run(20), ()))
        self.assertLen(new_ids, 1)
        self.assertEqual(continuation_token, Job.objects.get().continuation_token)

    def test_send_decisions(self):
        self.mock_get.return_value = _make_response(
            {
                "data": [
                    {
                        "added_on": "2022-04-26T05:57:38+0000",
                        "confidence": 100,
                        "id": "descriptor_id_1",
                    }
                ]
            }
        )
        signal = copy.deepcopy(TEST_SIGNAL).save()
        signal.sources.sources[1].source_signal_id = "id1"
        signal.content = [
            Content(value="foo.com", content_type=Content.ContentType.URL)
        ]
        signal.save()
        copy.deepcopy(TEST_CASE_RESOLVED_APPROVAL).save()
        copy.deepcopy(TEST_CASE_RESOLVED_BLOCKED).save()

        threat_exchange_importer = threat_exchange.ThreatExchangeImporter(
            privacy_group_id="group", access_token="token"
        )
        threat_exchange_importer.send_diagnostics(
            datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(hours=1),
            datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(hours=1),
        )

        self.mock_get.assert_has_calls(
            [
                mock.call(
                    _SESSION_SELF_OBJECT,
                    "https://graph.facebook.com/v4.0/id1/descriptors/?access_token=token",
                    timeout=mock.ANY,
                ),
            ]
        )

        self.mock_post.assert_has_calls(
            [
                mock.call(
                    _SESSION_SELF_OBJECT,
                    "https://graph.facebook.com/v4.0/descriptor_id_1?access_token=token&"
                    "reactions=NON_MALICIOUS,SAW_THIS_TOO",
                    timeout=mock.ANY,
                ),
                mock.call(
                    _SESSION_SELF_OBJECT,
                    "https://graph.facebook.com/v4.0/descriptor_id_1?access_token=token&"
                    "reactions=HELPFUL,SAW_THIS_TOO",
                    timeout=mock.ANY,
                ),
            ]
        )
