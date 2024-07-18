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
"""Tests for JSON utilities."""

import datetime
import enum
import json

from absl.testing import absltest

from utils.json import JSONEncoder


class JSONEncoderTest(absltest.TestCase):
    def test_encode_primitive(self):
        self.assertEqual('"hello world"', json.dumps("hello world", cls=JSONEncoder))

    def test_encode_object(self):
        self.assertEqual(
            '{"foo": "bar", "baz": 123}',
            json.dumps({"foo": "bar", "baz": 123}, cls=JSONEncoder),
        )

    def test_encode_datetime(self):
        date = datetime.datetime(1955, 11, 5, 6, 15, tzinfo=datetime.timezone.utc)

        self.assertEqual(
            '"1955-11-05T06:15:00+00:00"', json.dumps(date, cls=JSONEncoder)
        )

    def test_encode_enum(self):
        class MyEnum(enum.Enum):
            FOO = "BAR"

        self.assertEqual('"BAR"', json.dumps(MyEnum.FOO, cls=JSONEncoder))

    def test_encode_bytes(self):
        self.assertEqual('"foo"', json.dumps(b"foo", cls=JSONEncoder))


if __name__ == "__main__":
    absltest.main()
