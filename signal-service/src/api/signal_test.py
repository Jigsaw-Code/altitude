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
"""Tests for the Signal API."""

import copy
import datetime
import http
from unittest import mock

from absl.testing import absltest, parameterized
from bson.objectid import ObjectId

from api.signal import bp as signal_bp
from models.signal import (
    Content,
    ContentFeatures,
    ContentStatus,
    Signal,
    Source,
    Sources,
)
from testing.test_case import ApiTestCase

_TEST_SIGNAL = Signal(
    content=[Content(value="https://www.google.com/", content_type="URL")],
    sources=Sources(
        sources=[
            Source(
                name=Source.Name.TCAP,
                report_date=datetime.datetime(
                    2000, 12, 25, tzinfo=datetime.timezone.utc
                ),
            )
        ]
    ),
    user_content_to_past_review={
        "123": ["PENDING"],
        "456": ["PENDING"],
    },
    content_features=ContentFeatures(
        trust=0.9,
        contains_pii=ContentFeatures.Confidence.NO,
        is_violent_or_graphic=ContentFeatures.Confidence.YES,
    ),
    content_status=ContentStatus(
        last_checked_date=datetime.datetime(2000, 12, 26, tzinfo=datetime.timezone.utc),
        most_recent_status=ContentStatus.Status.ACTIVE,
        verifier=ContentStatus.Verifier.UNKNOWN,
    ),
)

_TEST_SIGNAL_SPARSE_DATA = Signal(
    content=[Content(value="https://abc.xyz/", content_type=Content.ContentType.URL)],
    sources=Sources(sources=[Source(name=Source.Name.TCAP, report_date=None)]),
)


class SignalAPITest(parameterized.TestCase, ApiTestCase):
    blueprint = signal_bp

    def test_create_new_signal(self):
        response = self.post(
            "/signals/",
            json={
                "content": {"value": "foobar", "type": "HASH_PDQ"},
                "source": {
                    "name": "USER_REPORT",
                    "author": "Jigsaw Test",
                    "create_time": "2023-11-09T22:02:47",
                },
            },
            expected_status=http.HTTPStatus.CREATED,
        )

        self.assertEqual(1, Signal.objects.count())
        signal = Signal.objects.get(id=ObjectId(response.json["id"]))
        self.assertEqual("foobar", signal.content[0].value)
        self.assertEqual(Content.ContentType.HASH_PDQ, signal.content[0].content_type)
        self.assertEqual("USER_REPORT", signal.sources.sources[0].name)
        self.assertEqual("Jigsaw Test", signal.sources.sources[0].author)
        self.assertEqual(
            datetime.datetime(2023, 11, 9, 22, 2, 47, tzinfo=datetime.timezone.utc),
            signal.sources.sources[0].report_date,
        )

    def test_get_signal_invalid_signal_id_raises(self):
        self.get(
            "/signals/foobar",
            expected_status=http.HTTPStatus.NOT_FOUND,
            expected_message="Signal foobar not found.",
        )

    def test_get_signal_nonexistent_case_id_raises(self):
        missing_id = str(ObjectId())
        self.get(
            f"/signals/{missing_id}",
            expected_status=http.HTTPStatus.NOT_FOUND,
            expected_message=f"Signal {missing_id} not found.",
        )

    @parameterized.named_parameters(
        (
            "for_full_signal",
            _TEST_SIGNAL,
            {
                "id": mock.ANY,
                "create_time": "2000-12-25T00:00:00+00:00",
                "content": [
                    {
                        "value": "https://www.google.com/",
                        "content_type": "URL",
                    }
                ],
                "sources": [
                    {
                        "name": "TCAP",
                        "create_time": "2000-12-25T00:00:00+00:00",
                    }
                ],
                "content_features": {
                    "associated_entities": [],
                    "contains_pii": "NO",
                    "is_violent_or_graphic": "YES",
                    "is_illegal_in_countries": [],
                    "tags": [],
                },
                "status": {
                    "last_checked_time": "2000-12-26T00:00:00+00:00",
                    "most_recent_status": "ACTIVE",
                },
            },
        ),
        (
            "for_sparse_signal",
            _TEST_SIGNAL_SPARSE_DATA,
            {
                "id": mock.ANY,
                "create_time": None,
                "content": [
                    {
                        "value": "https://abc.xyz/",
                        "content_type": "URL",
                    }
                ],
                "sources": [{"name": "TCAP"}],
            },
        ),
    )
    def test_get_signal_returns_matching_data(self, signal, expected_response):
        signal = copy.deepcopy(signal)
        signal.save()

        observed_response = self.get(f"/signals/{signal.id}")

        self.assertEqual(expected_response, observed_response.json)
        self.assertEqual(str(signal.id), observed_response.json["id"])

    def test_list_signals_no_signals_returns_empty_list(self):
        response = self.get("/signals/")

        self.assertEmpty(response.json)

    def test_list_signals_returns_matching_data(self):
        signal = copy.deepcopy(_TEST_SIGNAL)
        signal.save()

        response = self.get("/signals/")
        self.assertEqual(
            [
                {
                    "id": str(signal.id),
                    "create_time": "2000-12-25T00:00:00+00:00",
                    "content": [
                        {
                            "value": "https://www.google.com/",
                            "content_type": "URL",
                        }
                    ],
                    "sources": [
                        {
                            "name": "TCAP",
                            "create_time": "2000-12-25T00:00:00+00:00",
                        }
                    ],
                    "content_features": {
                        "associated_entities": [],
                        "contains_pii": "NO",
                        "is_violent_or_graphic": "YES",
                        "is_illegal_in_countries": [],
                        "tags": [],
                    },
                    "status": {
                        "last_checked_time": "2000-12-26T00:00:00+00:00",
                        "most_recent_status": "ACTIVE",
                    },
                }
            ],
            response.json,
        )


if __name__ == "__main__":
    absltest.main()
