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

"""TestCase subclasses that provide useful common testing functionality."""

from unittest import mock

from absl.testing import absltest


class TestCase(absltest.TestCase):
    def setUp(self):
        """Sets up the test harness."""
        self.addCleanup(mock.patch.stopall)
        super().setUp()
