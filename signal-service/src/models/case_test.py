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
"""Tests for the signal data models."""

import copy
from unittest import mock

from absl.testing import absltest, parameterized
from bson.objectid import ObjectId

from models.case import Case, Review
from models.signal import Content, ContentFeatures, Signal, Source, Sources
from models.target import FeatureSet, Target
from prioritization import case_priority
from testing import test_case
from testing.test_entities import TEST_CASE_RESOLVED_APPROVAL


class CaseTest(parameterized.TestCase, test_case.TestCase):
    @mock.patch.object(case_priority, "calculate_confidence", return_value=3)
    @mock.patch.object(case_priority, "calculate_severity", return_value=3)
    def test_priority_with_values_set(self, *_):
        signal = Signal(
            content=[Content(value="foo1", content_type=Content.ContentType.URL)],
            sources=Sources(sources=[Source()]),
            content_features=ContentFeatures(confidence=0.7),
        )
        signal.save()
        target = Target(feature_set=FeatureSet())
        target.save()
        case = Case(signal_ids=[signal.id], target_id=target.id)
        case.save()
        self.assertEqual(6, case.priority)
        self.assertEqual(case_priority.Level.HIGH, case.priority_level)
        self.assertEqual(3, case.confidence)
        self.assertEqual(3, case.severity)

    @mock.patch.object(case_priority, "calculate_confidence", return_value=None)
    @mock.patch.object(case_priority, "calculate_severity", return_value=None)
    def test_priority_without_values(self, *_):
        signal = Signal(
            content=[Content(value="foo1", content_type=Content.ContentType.URL)],
            sources=Sources(sources=[Source()]),
        )
        signal.save()
        target = Target(feature_set=FeatureSet())
        target.save()
        case = Case(signal_ids=[signal.id], target_id=target.id)
        self.assertIsNone(case.priority_level)

    @mock.patch.object(case_priority, "calculate_confidence")
    def test_priority_changes_on_save(self, mock_calculate_confidence):
        mock_calculate_confidence.side_effect = [2, 3]
        signal = Signal(
            content=[Content(value="foo1", content_type=Content.ContentType.URL)],
            sources=Sources(sources=[Source()]),
            content_features=ContentFeatures(trust=0.6),
        )
        signal.save()
        case = Case(signal_ids=[signal.id])
        self.assertEqual(2, case.priority)

        signal.sources = Sources(sources=[Source(), Source()])
        signal.save()
        del case.__dict__["confidence"]  # Delete the cached property.

        self.assertEqual(3, case.priority)

    def test_get_latest_review_no_review(self):
        self.assertIsNone(Case().latest_review)

    def test_get_latest_review(self):
        review_1 = Review(
            id=ObjectId("bbbbbbbbbbbbbbbbbbbbbbbb"), decision=Review.Decision.APPROVE
        )
        review_2 = Review(
            id=ObjectId("aaaaaaaaaaaaaaaaaaaaaaaa"), decision=Review.Decision.BLOCK
        )
        case = Case(review_history=[review_1, review_2])
        self.assertEqual(case.latest_review, review_2)

    def test_save_with_published_review_changes_state(self):
        case = copy.deepcopy(TEST_CASE_RESOLVED_APPROVAL).save()

        self.assertEqual(case.state, Case.State.RESOLVED)

    def test_save_with_unknown_review_does_not_change_state(self):
        case = copy.deepcopy(TEST_CASE_RESOLVED_APPROVAL)
        case.review_history[0].state = Review.State.UNKNOWN
        case.save()

        self.assertEqual(case.state, Case.State.ACTIVE)


if __name__ == "__main__":
    absltest.main()
