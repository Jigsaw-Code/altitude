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

"""Tests for image utilities."""

from testing import test_case
from utils import image


class ImageUtilsTest(test_case.TestCase):
    "Tests for image utility functions."

    def test_is_image_true(self):
        img_file_path = self.root_path.joinpath("testing/testdata/logo.png")
        with open(img_file_path, "rb") as img_file:
            test_image_bytes = img_file.read()
        result = image.is_image(test_image_bytes)
        self.assertTrue(result)

    def test_is_image_false(self):
        result = image.is_image(b"123")
        self.assertFalse(result)
