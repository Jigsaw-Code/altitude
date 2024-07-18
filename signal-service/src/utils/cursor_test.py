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

"""Tests for cursor encoding/decoding utilities"""

from testing import test_case
from utils import cursor


class CursorUtilsTest(test_case.TestCase):
    """Tests for cursor encoding utility functions."""

    def test_encode(self):
        next_cursor_token = {
            "token_id": "hello_world",
            "token_priority": 4,
        }
        self.assertEqual(
            "eyJ0b2tlbl9pZCI6ICJoZWxsb193b3JsZCIsICJ0b2tlbl9wcmlvcml0eSI6IDR9",
            cursor.encode_cursor(next_cursor_token),
        )

    def test_encode_and_decode(self):
        next_cursor_token = {
            "token_id": "hello_world",
            "token_priority": 4,
        }
        encoded_cursor = cursor.encode_cursor(next_cursor_token)
        self.assertEqual(cursor.decode_cursor(encoded_cursor), next_cursor_token)
