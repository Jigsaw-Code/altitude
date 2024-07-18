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
"""Tests for the Review API."""

import copy
import datetime
import http
import json
from typing import Any, Dict
from unittest import mock

import requests
from absl.testing import absltest

from api import review as review_api
from models.case import Case, Review
from models.target import FeatureSet, Target
from testing.test_case import ApiTestCase
from testing.test_entities import TEST_CASE


def _make_response(
    content: Dict[str, Any], status: int = http.HTTPStatus.OK
) -> requests.Response:
    response = requests.Response()
    response.status_code = status
    # pylint: disable=protected-access
    response._content = json.dumps(content).encode("utf-8")
    return response


class ReviewAPITest(ApiTestCase):
    blueprint = review_api.bp

    def setUp(self):
        super().setUp()
        # Mock out the client delivery endpoint request we make.
        requests_post_patch = mock.patch.object(requests, "post", autospec=True)
        mock_post = requests_post_patch.start()
        mock_post.return_value = _make_response({})

    @mock.patch("models.case.datetime", wraps=datetime)
    def test_create_review_for_valid_case(self, mock_datetime):
        mock_datetime.datetime.utcnow.return_value = datetime.datetime(
            2001, 5, 10, tzinfo=datetime.timezone.utc
        )
        Review.create_time.default = mock_datetime.datetime.utcnow
        case = copy.deepcopy(TEST_CASE)
        case.save()
        Target(id=case.target_id, feature_set=FeatureSet()).save()

        response = self.post(
            f"/cases/{case.id}/reviews/",
            json={"decision": "BLOCK"},
            expected_status=http.HTTPStatus.CREATED,
        )

        self.assertEqual(
            {
                "id": mock.ANY,
                "create_time": "2001-05-10T00:00:00+00:00",
                "decision": "BLOCK",
            },
            response.json,
        )
        review_id = response.json["id"]
        observed_delivery_status = (
            Case.objects.get(id=case.id)
            .review_history.get(id=review_id)
            .delivery_status
        )
        self.assertEqual(observed_delivery_status, Review.DeliveryStatus.ACCEPTED)

    def test_create_review_for_unknown_case_fails(self):
        self.post(
            "/cases/foobar/reviews/",
            json={"decision": "BLOCK"},
            expected_status=http.HTTPStatus.NOT_FOUND,
            expected_message="Case foobar not found.",
        )

    def test_delete_draft_review_succeeds(self):
        case = copy.deepcopy(TEST_CASE)
        review = Review(state=Review.State.DRAFT)
        case.review_history = [review]
        case.save()

        self.delete(
            f"/cases/{case.id}/reviews/{review.id}",
            expected_status=http.HTTPStatus.NO_CONTENT,
        )

        case.reload()
        self.assertEmpty(case.review_history)

    def test_delete_published_draft_fails(self):
        case = copy.deepcopy(TEST_CASE)
        review = Review(state=Review.State.PUBLISHED)
        case.review_history = [review]
        case.save()

        self.delete(
            f"/cases/{case.id}/reviews/{review.id}",
            expected_status=http.HTTPStatus.METHOD_NOT_ALLOWED,
            expected_message=f"Review {review.id} on case {case.id} cannot be deleted.",
        )

        case.reload()
        self.assertNotEmpty(case.review_history)

    def test_delete_review_for_unknown_case_fails(self):
        self.delete(
            "/cases/foobar/reviews/123",
            expected_status=http.HTTPStatus.NOT_FOUND,
            expected_message="Case foobar not found.",
        )

    def test_delete_review_for_unknown_review_on_case_fails(self):
        case = copy.deepcopy(TEST_CASE)
        case.save()
        Target(id=case.target_id, feature_set=FeatureSet()).save()

        self.delete(
            f"cases/{case.id}/reviews/foobar",
            expected_status=http.HTTPStatus.NOT_FOUND,
            expected_message=f"Review foobar not found on case {case.id}.",
        )

    def test_delete_review_for_unknown_review_fails(self):
        self.delete(
            "/reviews/foobar",
            expected_status=http.HTTPStatus.NOT_FOUND,
            expected_message="Review foobar not found.",
        )


if __name__ == "__main__":
    absltest.main()
