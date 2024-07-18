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
"""Test that the signal prioritization algorithm computes as expected."""

from models.signal import Content, ContentFeatures, Signal, Source, Sources
from prioritization import case_priority
from testing import test_case


class CasePriorityTest(test_case.TestCase):
    def test_calculate_confidence_based_on_signal_confidence_tag(self):
        signal = Signal(
            content=[Content(value="foo1", content_type=Content.ContentType.URL)],
            sources=Sources(sources=[Source()]),
            content_features=ContentFeatures(confidence=0.7),
        )
        signal.save()
        self.assertEqual(case_priority.calculate_confidence(signal_ids=[signal.id]), 2)

    def test_calculate_severity(self):
        signal = Signal(
            content=[Content(value="foo1", content_type=Content.ContentType.URL)],
            sources=Sources(sources=[Source()]),
            content_features=ContentFeatures(
                associated_terrorist_organizations=[
                    "Hello World Organization",
                    "Goodbye World Association",
                ],
                contains_pii=ContentFeatures.Confidence.YES,
            ),
        )
        signal.save()
        self.assertEqual(case_priority.calculate_severity(signal_ids=[signal.id]), 3)

    def test_calculate_confidence_no_fields_set(self):
        signal = Signal(
            content=[Content(value="foo1", content_type=Content.ContentType.URL)],
            sources=Sources(sources=[Source()]),
        )
        signal.save()
        self.assertEqual(case_priority.calculate_confidence(signal_ids=[signal.id]), 0)

    def test_calculate_severity_no_fields_set(self):
        signal = Signal(
            content=[Content(value="foo1", content_type=Content.ContentType.URL)],
            sources=Sources(sources=[Source()]),
        )
        signal.save()
        self.assertEqual(case_priority.calculate_severity(signal_ids=[signal.id]), 0)
