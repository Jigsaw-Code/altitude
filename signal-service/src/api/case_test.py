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

"""Tests for the Case API."""
# pylint: disable=missing-docstring

import copy
import datetime
import http
from typing import List
from unittest import mock

from absl.testing import absltest, parameterized
from bson.objectid import ObjectId

from api.case import bp as case_bp
from models.case import Case
from models.signal import Content, Signal, Source, Sources
from models.target import FeatureSet, Target
from prioritization import case_priority
from testing.test_case import ApiTestCase
from testing.test_entities import TEST_CASE, TEST_CASE_SPARSE_DATA
from utils import cursor


class CaseAPITest(parameterized.TestCase, ApiTestCase):
    """Tests Case API endpoints."""

    blueprint = case_bp

    def setUp(self):
        super().setUp()
        self.calculate_confidence_mock = self.enter_context(
            mock.patch.object(case_priority, "calculate_confidence", return_value=None)
        )
        self.calculate_severity_mock = self.enter_context(
            mock.patch.object(case_priority, "calculate_severity", return_value=None)
        )

    def test_create_case(self):
        signal = Signal(
            content=[Content(value="foo1", content_type=Content.ContentType.URL)],
            sources=Sources(sources=[Source()]),
        )
        signal.save()
        target = Target(feature_set=FeatureSet())
        target.save()

        response = self.post(
            "/cases/",
            json={"signal_ids": [str(signal.id)], "target_id": str(target.id)},
            expected_status=http.HTTPStatus.CREATED,
        )

        case = Case.objects.get(id=response.json["id"])
        self.assertEqual([signal.id], case.signal_ids)
        self.assertEqual(target.id, case.target_id)

    def test_create_case_without_target(self):
        signal = Signal(
            content=[Content(value="foo1", content_type=Content.ContentType.URL)],
            sources=Sources(sources=[Source()]),
        )
        signal.save()

        response = self.post(
            "/cases/",
            json={"signal_ids": [str(signal.id)]},
            expected_status=http.HTTPStatus.CREATED,
        )

        case = Case.objects.get(id=response.json["id"])
        self.assertIsNone(case.target_id)

    def test_create_case_with_nonexistent_signal_raises(self):
        signal = Signal(
            content=[Content(value="foo1", content_type=Content.ContentType.URL)],
            sources=Sources(sources=[Source()]),
        )
        signal.save()

        missing_id = str(ObjectId())
        self.post(
            "/cases/",
            json={"signal_ids": [str(signal.id), missing_id]},
            expected_status=http.HTTPStatus.NOT_FOUND,
            expected_message=f"Signals ['{missing_id}'] not found.",
        )

    def test_create_case_with_nonexistent_target_raises(self):
        signal = Signal(
            content=[Content(value="foo1", content_type=Content.ContentType.URL)],
            sources=Sources(sources=[Source()]),
        )
        signal.save()

        missing_id = str(ObjectId())
        self.post(
            "/cases/",
            json={"signal_ids": [str(signal.id)], "target_id": missing_id},
            expected_status=http.HTTPStatus.NOT_FOUND,
            expected_message=f"Target {missing_id} not found.",
        )

    def test_get_case_invalid_case_id_raises(self):
        self.get(
            "/cases/foobar",
            expected_status=http.HTTPStatus.NOT_FOUND,
            expected_message="Case foobar not found.",
        )

    def test_get_case_nonexistent_case_id_raises(self):
        missing_id = str(ObjectId())
        self.get(
            f"/cases/{missing_id}",
            expected_status=http.HTTPStatus.NOT_FOUND,
            expected_message=f"Case {missing_id} not found.",
        )

    @parameterized.named_parameters(
        (
            "for_full_case",
            TEST_CASE,
            {
                "id": mock.ANY,
                "signal_ids": ["bbbbbbbbbbbbbbbbbbbbbbbb"],
                "target_id": "cccccccccccccccccccccccc",
                "create_time": "2000-12-25T00:00:00+00:00",
                "state": "RESOLVED",
                "priority": -1,
                "priority_level": None,
                "confidence": None,
                "severity": None,
                "review_history": [
                    {
                        "id": mock.ANY,
                        "create_time": "2000-12-26T00:00:00+00:00",
                        "decision": "APPROVE",
                        "user": "user1",
                    }
                ],
                "notes": "Hello World",
            },
        ),
        (
            "for_sparse_signal",
            TEST_CASE_SPARSE_DATA,
            {
                "id": mock.ANY,
                "signal_ids": ["bbbbbbbbbbbbbbbbbbbbbbbb"],
                "create_time": "2000-12-25T00:00:00+00:00",
                "state": "ACTIVE",
                "priority": -1,
                "priority_level": None,
                "confidence": None,
                "severity": None,
                "notes": None,
            },
        ),
    )
    def test_get_case_returns_matching_data(self, case, expected_response):
        """Tests if /cases/<case_id> successfully returns matching case."""
        case = copy.deepcopy(case)
        case.save()

        observed_response = self.get(f"/cases/{case.id}")

        self.assertEqual(expected_response, observed_response.json)
        self.assertEqual(str(case.id), observed_response.json["id"])

    def test_list_cases_no_cases_returns_empty_list(self):
        response = self.get("/cases/")

        self.assertEmpty(response.json["data"])

    def test_list_cases_returns_matching_data(self):
        case = copy.deepcopy(TEST_CASE)
        case.save()

        response = self.get("/cases/")
        self.assertEqual(
            [
                {
                    "id": mock.ANY,
                    "signal_ids": ["bbbbbbbbbbbbbbbbbbbbbbbb"],
                    "target_id": "cccccccccccccccccccccccc",
                    "create_time": "2000-12-25T00:00:00+00:00",
                    "state": "RESOLVED",
                    "priority": -1,
                    "priority_level": None,
                    "confidence": None,
                    "severity": None,
                    "review_history": [
                        {
                            "id": mock.ANY,
                            "create_time": "2000-12-26T00:00:00+00:00",
                            "decision": "APPROVE",
                            "user": "user1",
                        }
                    ],
                    "notes": "Hello World",
                },
            ],
            response.json["data"],
        )

    @parameterized.named_parameters(
        ("gets_active_cases", "active", TEST_CASE, []),
        (
            "gets_resolved_case",
            "resolved",
            TEST_CASE,
            [
                {
                    "id": mock.ANY,
                    "signal_ids": ["bbbbbbbbbbbbbbbbbbbbbbbb"],
                    "target_id": "cccccccccccccccccccccccc",
                    "create_time": "2000-12-25T00:00:00+00:00",
                    "state": "RESOLVED",
                    "priority": -1,
                    "priority_level": None,
                    "confidence": None,
                    "severity": None,
                    "review_history": [
                        {
                            "id": mock.ANY,
                            "create_time": "2000-12-26T00:00:00+00:00",
                            "decision": "APPROVE",
                            "user": "user1",
                        }
                    ],
                    "notes": "Hello World",
                },
            ],
        ),
    )
    def test_get_cases_filters_by_state(
        self, state: str, case: Case, expected_response: List[Case]
    ):
        """Tests if /cases/ successfully filters by state."""
        case = copy.deepcopy(case)
        case.save()

        observed_response = self.get(f"/cases/?state={state}")

        self.assertEqual(expected_response, observed_response.json["data"])

    def test_get_cases_filters_by_signal_ids(self):
        """Tests if /cases/ successfully filters by signal ids."""
        case_one = copy.deepcopy(TEST_CASE)
        case_one.save()
        signal_id_one = case_one.signal_ids[0]
        case_two = copy.deepcopy(TEST_CASE_SPARSE_DATA)
        case_two.save()
        signal_id_two = case_two.signal_ids[0]
        case_three = Case(
            signal_ids=[signal_id_one, signal_id_two],
            create_time=datetime.datetime(2000, 12, 25, tzinfo=datetime.timezone.utc),
            state=Case.State.ACTIVE,
        )
        case_three.save()
        case_four = Case(
            signal_ids=[ObjectId("dddddddddddddddddddddddd")],
            create_time=datetime.datetime(2000, 12, 25, tzinfo=datetime.timezone.utc),
            state=Case.State.ACTIVE,
        )
        case_four.save()

        observed_response = self.get(
            f"/cases/?signal_id={signal_id_one}&signal_id={signal_id_two}&page_size={10}"
        )
        observed_response_cases = observed_response.json["data"]
        self.assertLen(observed_response_cases, 3)
        self.assertEqual(str(case_one.id), observed_response_cases[0]["id"])
        self.assertEqual(str(case_two.id), observed_response_cases[1]["id"])
        self.assertEqual(str(case_three.id), observed_response_cases[2]["id"])

    def test_update_case_invalid_case_id_raises(self):
        self.patch(
            "/cases/foobar",
            expected_status=http.HTTPStatus.NOT_FOUND,
            expected_message="Case foobar not found.",
        )

    def test_update_case_nonexistent_case_id_raises(self):
        missing_id = str(ObjectId())
        self.patch(
            f"/cases/{missing_id}",
            expected_status=http.HTTPStatus.NOT_FOUND,
            expected_message=f"Case {missing_id} not found.",
        )

    def test_update_case_invalid_fields_raises(self):
        case = copy.deepcopy(TEST_CASE)
        case.save()
        self.patch(
            f"/cases/{case.id}",
            json={
                "create_time": "2011-06-12T00:00:00+00:00",
            },
            expected_status=http.HTTPStatus.BAD_REQUEST,
        )

    def test_update_case(self):
        """Tests if case note is successfully updated."""
        case = copy.deepcopy(TEST_CASE)
        case.save()
        response = self.patch(
            f"/cases/{case.id}",
            json={
                "notes": "Goodbye World",
            },
            expected_status=http.HTTPStatus.OK,
        )
        self.assertEqual("Goodbye World", response.json["notes"])

    def test_update_case_to_none(self):
        """Tests if case note is successfully updated."""
        case = copy.deepcopy(TEST_CASE)
        case.save()
        response = self.patch(
            f"/cases/{case.id}",
            json={
                "notes": None,
            },
            expected_status=http.HTTPStatus.OK,
        )
        self.assertIsNone(response.json["notes"])

    def test_get_cases_multiple_cursor_tokens_raises(self):
        """Tests if /cases/ raises an error if multiple cursors are provided."""

        case_two_id = ObjectId("aaaaaaaaaaaaaaaaaaaaaaab")
        raw_cursor = {"token_id": str(case_two_id), "priority": 2}
        encoded_cursor = cursor.encode_cursor(raw_cursor)
        self.get(
            f"/cases/?next_cursor_token={encoded_cursor}&"
            f"previous_cursor_token={encoded_cursor}&page_size=2",
            expected_status=http.HTTPStatus.BAD_REQUEST,
            expected_message="Only one cursor token should be provided.",
        )

    def test_get_cases_wrong_cursor_token_format_raises(self):
        """Tests if /cases/ validates the cursor format."""

        case_two_id = f"{ObjectId('aaaaaaaaaaaaaaaaaaaaaaab')}"
        self.get(
            f"/cases/?next_cursor_token={case_two_id}&page_size={2}",
            expected_status=http.HTTPStatus.BAD_REQUEST,
            expected_message="Invalid cursor format: 'utf-8' codec can't "
            "decode byte 0xa6 in position 1: invalid start byte",
        )

    def test_get_cases_paginated_next(self):
        """Tests if /cases/ successfully handles cursor based pagination."""

        def priority_side_effect(case):
            priority_values = {
                ObjectId("aaaaaaaaaaaaaaaaaaaaaaaa"): 3,
                ObjectId("aaaaaaaaaaaaaaaaaaaaaaab"): 2,
                ObjectId("aaaaaaaaaaaaaaaaaaaaaaac"): 4,
                ObjectId("aaaaaaaaaaaaaaaaaaaaaaad"): 5,
                ObjectId("aaaaaaaaaaaaaaaaaaaaaaae"): 2,
            }
            return priority_values.get(case.id)

        with mock.patch.object(Case, "priority", property(priority_side_effect)):
            case_one = copy.deepcopy(TEST_CASE_SPARSE_DATA)
            case_one.id = ObjectId("aaaaaaaaaaaaaaaaaaaaaaaa")
            case_one.save()

            case_two = copy.deepcopy(TEST_CASE_SPARSE_DATA)
            case_two.id = ObjectId("aaaaaaaaaaaaaaaaaaaaaaab")
            case_two.save()

            case_three = copy.deepcopy(TEST_CASE_SPARSE_DATA)
            case_three.id = ObjectId("aaaaaaaaaaaaaaaaaaaaaaac")
            case_three.save()

            case_four = copy.deepcopy(TEST_CASE_SPARSE_DATA)
            case_four.id = ObjectId("aaaaaaaaaaaaaaaaaaaaaaad")
            case_four.save()

            case_five = copy.deepcopy(TEST_CASE_SPARSE_DATA)
            case_five.id = ObjectId("aaaaaaaaaaaaaaaaaaaaaaae")
            case_five.save()

            raw_cursor = {
                "token_id": str(case_four.id),
                "token_priority": case_four.priority,
            }
            encoded_cursor = cursor.encode_cursor(raw_cursor)
            request_str = f"/cases/?next_cursor_token={encoded_cursor}&page_size={4}"
            observed_response = self.get(
                request_str,
            )
        cases = observed_response.json["data"]
        self.assertLen(cases, 4)
        self.assertEqual(str(case_three.id), cases[0]["id"])
        self.assertEqual(str(case_one.id), cases[1]["id"])
        self.assertEqual(str(case_two.id), cases[2]["id"])
        self.assertEqual(str(case_five.id), cases[3]["id"])
        self.assertNotIn("next_cursor_token", observed_response.json)
        previous_cursor = {"token_id": str(case_three.id), "token_priority": 4}
        self.assertEqual(
            previous_cursor,
            cursor.decode_cursor(observed_response.json["previous_cursor_token"]),
        )

    def test_get_cases_paginated_previous(self):
        """Tests if /cases/ successfully handles navigating to previous page."""

        def priority_side_effect(case):
            priority_values = {
                ObjectId("aaaaaaaaaaaaaaaaaaaaaaaf"): 6,
                ObjectId("aaaaaaaaaaaaaaaaaaaaaaae"): 5,
                ObjectId("aaaaaaaaaaaaaaaaaaaaaaad"): 4,
                ObjectId("aaaaaaaaaaaaaaaaaaaaaaac"): 3,
                ObjectId("aaaaaaaaaaaaaaaaaaaaaaab"): 2,
                ObjectId("aaaaaaaaaaaaaaaaaaaaaaaa"): 1,
            }
            return priority_values.get(case.id)

        with mock.patch.object(Case, "priority", property(priority_side_effect)):
            case_six = copy.deepcopy(TEST_CASE_SPARSE_DATA)
            case_six.id = ObjectId("aaaaaaaaaaaaaaaaaaaaaaaf")
            case_six.save()

            case_five = copy.deepcopy(TEST_CASE_SPARSE_DATA)
            case_five.id = ObjectId("aaaaaaaaaaaaaaaaaaaaaaae")
            case_five.save()

            case_four = copy.deepcopy(TEST_CASE_SPARSE_DATA)
            case_four.id = ObjectId("aaaaaaaaaaaaaaaaaaaaaaad")
            case_four.save()

            case_three = copy.deepcopy(TEST_CASE_SPARSE_DATA)
            case_three.id = ObjectId("aaaaaaaaaaaaaaaaaaaaaaac")
            case_three.save()

            case_two = copy.deepcopy(TEST_CASE_SPARSE_DATA)
            case_two.id = ObjectId("aaaaaaaaaaaaaaaaaaaaaaab")
            case_two.save()

            case_one = copy.deepcopy(TEST_CASE_SPARSE_DATA)
            case_one.id = ObjectId("aaaaaaaaaaaaaaaaaaaaaaaa")
            case_one.save()

            raw_cursor = {
                "token_id": str(case_two.id),
                "token_priority": case_two.priority,
            }
            encoded_cursor = cursor.encode_cursor(raw_cursor)
            observed_response = self.get(
                f"/cases/?previous_cursor_token={encoded_cursor}&page_size={2}"
            )
        cases = observed_response.json["data"]
        self.assertLen(cases, 2)
        self.assertEqual(str(case_four.id), cases[0]["id"])
        self.assertEqual(str(case_three.id), cases[1]["id"])
        next_cursor = {"token_id": str(case_three.id), "token_priority": 3}
        self.assertEqual(
            next_cursor,
            cursor.decode_cursor(observed_response.json["next_cursor_token"]),
        )
        previous_cursor = {"token_id": str(case_four.id), "token_priority": 4}
        self.assertEqual(
            previous_cursor,
            cursor.decode_cursor(observed_response.json["previous_cursor_token"]),
        )

    def test_get_cases_paginated_less_than_limit(self):
        """Tests if /cases/ pagination handles uneven number of cases."""

        def priority_side_effect(case):
            priority_values = {
                ObjectId("aaaaaaaaaaaaaaaaaaaaaaac"): 3,
                ObjectId("aaaaaaaaaaaaaaaaaaaaaaab"): 2,
                ObjectId("aaaaaaaaaaaaaaaaaaaaaaaa"): 1,
            }
            return priority_values.get(case.id)

        with mock.patch.object(Case, "priority", property(priority_side_effect)):
            case_three = copy.deepcopy(TEST_CASE_SPARSE_DATA)
            case_three.id = ObjectId("aaaaaaaaaaaaaaaaaaaaaaac")
            case_three.save()

            case_two = copy.deepcopy(TEST_CASE_SPARSE_DATA)
            case_two.id = ObjectId("aaaaaaaaaaaaaaaaaaaaaaab")
            case_two.save()

            case_one = copy.deepcopy(TEST_CASE_SPARSE_DATA)
            case_one.id = ObjectId("aaaaaaaaaaaaaaaaaaaaaaaa")
            case_one.save()

            raw_cursor = {
                "token_id": str(case_two.id),
                "token_priority": case_two.priority,
            }
            encoded_cursor = cursor.encode_cursor(raw_cursor)
            observed_response = self.get(
                f"/cases/?next_cursor_token={encoded_cursor}&page_size={2}"
            )
        cases = observed_response.json["data"]
        self.assertLen(cases, 1)
        self.assertEqual(str(case_one.id), cases[0]["id"])
        self.assertNotIn("next_cursor_token", observed_response.json)
        previous_cursor = {"token_id": str(case_one.id), "token_priority": 1}
        self.assertEqual(
            previous_cursor,
            cursor.decode_cursor(observed_response.json["previous_cursor_token"]),
        )

    def test_get_cases_paginated_no_priority(self):
        """Tests if /cases/ pagination handles uneven number of cases."""

        case_one = copy.deepcopy(TEST_CASE_SPARSE_DATA)
        case_one.id = ObjectId("aaaaaaaaaaaaaaaaaaaaaaaa")
        case_one.save()

        case_two = copy.deepcopy(TEST_CASE_SPARSE_DATA)
        case_two = copy.deepcopy(TEST_CASE_SPARSE_DATA)
        case_two.id = ObjectId("aaaaaaaaaaaaaaaaaaaaaaab")
        case_two.save()

        case_three = copy.deepcopy(TEST_CASE_SPARSE_DATA)
        case_three.id = ObjectId("aaaaaaaaaaaaaaaaaaaaaaac")
        case_three.save()

        raw_cursor = {"token_id": str(case_one.id), "token_priority": case_one.priority}
        encoded_cursor = cursor.encode_cursor(raw_cursor)
        observed_response = self.get(
            f"/cases/?next_cursor_token={encoded_cursor}&page_size={1}"
        )
        cases = observed_response.json["data"]
        self.assertLen(cases, 1)
        self.assertEqual(str(case_two.id), cases[0]["id"])
        next_and_prev_cursor = {"token_id": str(case_two.id), "token_priority": -1}
        self.assertEqual(
            next_and_prev_cursor,
            cursor.decode_cursor(observed_response.json["next_cursor_token"]),
        )
        self.assertEqual(
            next_and_prev_cursor,
            cursor.decode_cursor(observed_response.json["previous_cursor_token"]),
        )

    def test_get_cases_paginated_first(self):
        """Tests if /cases/ successfully handles cursor based pagination."""

        def priority_side_effect(case):
            priority_values = {
                ObjectId("aaaaaaaaaaaaaaaaaaaaaaaa"): 3,
                ObjectId("aaaaaaaaaaaaaaaaaaaaaaab"): 2,
                ObjectId("aaaaaaaaaaaaaaaaaaaaaaac"): 4,
                ObjectId("aaaaaaaaaaaaaaaaaaaaaaad"): 5,
                ObjectId("aaaaaaaaaaaaaaaaaaaaaaae"): 2,
            }
            return priority_values.get(case.id)

        with mock.patch.object(Case, "priority", property(priority_side_effect)):
            case_one = copy.deepcopy(TEST_CASE_SPARSE_DATA)
            case_one.id = ObjectId("aaaaaaaaaaaaaaaaaaaaaaaa")
            case_one.save()

            case_two = copy.deepcopy(TEST_CASE_SPARSE_DATA)
            case_two.id = ObjectId("aaaaaaaaaaaaaaaaaaaaaaab")
            case_two.save()

            case_three = copy.deepcopy(TEST_CASE_SPARSE_DATA)
            case_three.id = ObjectId("aaaaaaaaaaaaaaaaaaaaaaac")
            case_three.save()

            case_four = copy.deepcopy(TEST_CASE_SPARSE_DATA)
            case_four.id = ObjectId("aaaaaaaaaaaaaaaaaaaaaaad")
            case_four.save()

            case_five = copy.deepcopy(TEST_CASE_SPARSE_DATA)
            case_five.id = ObjectId("aaaaaaaaaaaaaaaaaaaaaaae")
            case_five.save()

            observed_response = self.get(f"/cases/?page_size={4}")
        cases = observed_response.json["data"]
        self.assertLen(cases, 4)
        self.assertEqual(str(case_four.id), cases[0]["id"])
        self.assertEqual(str(case_three.id), cases[1]["id"])
        self.assertEqual(str(case_one.id), cases[2]["id"])
        self.assertEqual(str(case_two.id), cases[3]["id"])
        next_cursor = {"token_id": str(case_two.id), "token_priority": 2}

        self.assertEqual(
            next_cursor,
            cursor.decode_cursor(observed_response.json["next_cursor_token"]),
        )
        self.assertNotIn("previous_cursor_token", observed_response.json)


if __name__ == "__main__":
    absltest.main()
