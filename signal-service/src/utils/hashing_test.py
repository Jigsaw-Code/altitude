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

"""Tests for hashing utilities."""

import http
import json
from typing import Any, Dict
from unittest import mock

import requests

from testing import test_case
from utils import hashing


def _make_response(
    content: Dict[str, Any], status: int = http.HTTPStatus.OK
) -> requests.Response:
    response = requests.Response()
    response.status_code = status
    # pylint: disable=protected-access
    response._content = json.dumps(content).encode("utf-8")
    return response


class HahsingUtilsTest(test_case.TestCase):
    "Tests for hashing utility functions."

    def setUp(self):
        super().setUp()
        requests_get_patch = mock.patch.object(requests, "get", autospec=True)
        self.mock_get = requests_get_patch.start()

    def test_generate_pdq_hash_from_url_returns_digest_for_image(self):
        img_file_path = self.root_path.joinpath("testing/testdata/logo.png")
        with open(img_file_path, "rb") as img_file:
            test_image_bytes = img_file.read()
        self.mock_get.return_value.content = test_image_bytes

        pdq_digest = hashing.generate_pdq_hash_from_url("https://abc.xyz")

        self.assertEqual(
            pdq_digest,
            "9c66cd9c49893672e671c3339a72ecf94d8c384eb06cc7924d32f07196db0d8e",
        )

    def test_generate_pdq_hash_from_url_bad_request(self):
        self.mock_get.return_value = _make_response({}, http.HTTPStatus.NOT_FOUND)

        pdq_digest = hashing.generate_pdq_hash_from_url("https://abc.xyz")

        self.assertIsNone(pdq_digest)

    def test_generate_pdq_hash_from_url_not_image(self):
        self.mock_get.return_value.content = b"123"

        pdq_digest = hashing.generate_pdq_hash_from_url("https://abc.xyz")

        self.assertIsNone(pdq_digest)

    def test_generate_pdq_hash_from_url_bad_url(self):
        self.mock_get.side_effect = requests.exceptions.InvalidSchema

        pdq_digest = hashing.generate_pdq_hash_from_url("https://abc.xyz")

        self.assertIsNone(pdq_digest)
