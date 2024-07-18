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

"""Tests for iterators utilities."""

from absl.testing import absltest

from utils.iterators import grouper


class IteratorsTest(absltest.TestCase):
    "Tests for iterator utility functions."

    def test_grouper_divides_data_into_chunks(self):
        grouper_iter = grouper(iter(range(26)), 3)

        chunks = list(grouper_iter)

        self.assertLen(chunks, 9)
        self.assertEqual(chunks[0], (0, 1, 2))
        self.assertEqual(chunks[1], (3, 4, 5))

    def test_grouper_divides_data_into_chunks_of_at_most_n(self):
        grouper_iter = grouper(iter(range(26)), 7)

        chunks = list(grouper_iter)

        for chunk in chunks:
            self.assertLessEqual(len(chunk), 7)

    def test_grouper_does_not_fill_last_chunk(self):
        grouper_iter = grouper(iter(range(26)), 10)

        *_, last_chunk = grouper_iter

        self.assertLen(last_chunk, 6)
