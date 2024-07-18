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
"""Tests for the ReviewStats API."""

import copy

from absl.testing import absltest, parameterized

from api import review_stats
from testing.test_case import ApiTestCase
from testing.test_entities import (
    TEST_CASE_ACTIVE,
    TEST_CASE_RESOLVED_APPROVAL,
    TEST_CASE_RESOLVED_BLOCKED,
)


class ReviewStatsAPITest(parameterized.TestCase, ApiTestCase):
    blueprint = review_stats.bp

    def test_get_review_stats(self):
        copy.deepcopy(TEST_CASE_ACTIVE).save()
        copy.deepcopy(TEST_CASE_RESOLVED_APPROVAL).save()
        copy.deepcopy(TEST_CASE_RESOLVED_BLOCKED).save()

        observed_response = self.get("/cases/review_stats/")

        self.assertEqual(
            observed_response.json,
            {
                "count_approved": 1,
                "count_removed": 1,
                "count_active": 1,
            },
        )


if __name__ == "__main__":
    absltest.main()
