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
"""Test that the Safe Search functionality behaves as expected."""

from unittest import mock

from absl.testing import absltest
from google.cloud.vision_v1.types.image_annotator import SafeSearchAnnotation

from analyzers import safe_search
from testing import test_case


class SafeSearchTest(test_case.TestCase):
    @mock.patch("google.cloud.vision.ImageAnnotatorClient", spec=True)
    def test_returns_safe_search_scores_dictionary(self, mock_safe_search):
        fake_response = SafeSearchAnnotation(
            adult=2, spoof=1, medical=2, violence=2, racy=2
        )
        mock_safe_search.return_value.safe_search_detection.return_value.error.message = (
            False
        )
        mock_safe_search.return_value.safe_search_detection.return_value.safe_search_annotation = (
            fake_response
        )
        safe_search_test = safe_search.SafeSearch()
        self.assertEqual(
            {"adult": 2, "spoof": 1, "medical": 2, "violence": 2, "racy": 2},
            safe_search_test.analyze(b""),
        )


if __name__ == "__main__":
    absltest.main()
