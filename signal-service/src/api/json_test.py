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
"""Tests for the JSONEncoder."""

import datetime
import enum

from absl.testing import absltest

import api
from api.json import JSONProvider


class JSONProviderTest(absltest.TestCase):
    def setUp(self):
        super().setUp()
        application = api.Api("Test", static_folder=None)
        self.json_provider = JSONProvider(app=application)

    def test_encode_primitive(self):
        self.assertEqual('"hello world"', self.json_provider.dumps("hello world"))

    def test_encode_object(self):
        self.assertEqual(
            '{"foo": "bar", "baz": 123}',
            self.json_provider.dumps({"foo": "bar", "baz": 123}),
        )

    def test_encode_datetime(self):
        date = datetime.datetime(1955, 11, 5, 6, 15, tzinfo=datetime.timezone.utc)

        self.assertEqual('"1955-11-05T06:15:00+00:00"', self.json_provider.dumps(date))

    def test_encode_enum(self):
        class MyEnum(enum.Enum):
            FOO = "BAR"

        self.assertEqual('"BAR"', self.json_provider.dumps(MyEnum.FOO))

    def test_encode_bytes(self):
        self.assertEqual('"foo"', self.json_provider.dumps(b"foo"))


if __name__ == "__main__":
    absltest.main()
