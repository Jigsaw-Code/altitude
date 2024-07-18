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
"""Tests for the API valdation decorator."""

import base64

import flask
from absl.testing import absltest

from api import api_error, validation
from testing import test_case

VALIDATOR = validation.Validator(
    input_schema={
        "type": "object",
        "properties": {"foo": {"type": "string"}},
        "required": ["foo"],
    },
    output_schema={
        "type": "object",
        "properties": {"bar": {"type": "number"}},
        "required": ["bar"],
    },
)


class ValidatorTest(test_case.TestCase):
    def test_validator_succeeds_with_good_input_and_output(self):
        @VALIDATOR
        def my_func():  # pylint: disable=unused-argument,disallowed-name
            return {"bar": 123}

        with flask.Flask(__name__).test_request_context("/", json={"foo": "a string"}):
            my_func()

    def test_validator_raises_on_bad_input(self):
        @VALIDATOR
        def my_func():  # pylint: disable=unused-argument,disallowed-name
            return {"bar": 123}

        with (
            flask.Flask(__name__).test_request_context("/", json={"foo": 456}),
            self.assertRaisesWithLiteralMatch(
                api_error.ApiError, "456 is not of type 'string'"
            ),
        ):
            my_func()

    def test_validator_raises_on_bad_output(self):
        @VALIDATOR
        def my_func():  # pylint: disable=unused-argument,disallowed-name
            return {"bar": "not-a-number"}

        with (
            flask.Flask(__name__).test_request_context("/", json={"foo": "a string"}),
            self.assertRaisesWithLiteralMatch(
                api_error.ApiError, "Server got itself in trouble"
            ),
        ):
            my_func()

    def test_base64_validator_validates_base64_string(self):
        @validation.Validator(
            input_schema={
                "type": "object",
                "properties": {"foo": {"type": "string", "contentEncoding": "base64"}},
            },
            output_schema={},
        )
        def my_func():  # pylint: disable=unused-argument,disallowed-name
            return {}

        base64_input = base64.b64encode(b"a string").decode(errors="ignore")
        with flask.Flask(__name__).test_request_context(
            "/", json={"foo": base64_input}
        ):
            my_func()

    def test_base64_validator_raises_on_invalid_base64_string(self):
        @validation.Validator(
            input_schema={
                "type": "object",
                "properties": {"foo": {"type": "string", "contentEncoding": "base64"}},
            },
            output_schema={},
        )
        def my_func():  # pylint: disable=unused-argument,disallowed-name
            return {}

        with (
            flask.Flask(__name__).test_request_context(
                "/", json={"foo": "not-base64-encoded"}
            ),
            self.assertRaisesWithLiteralMatch(
                api_error.ApiError,
                "'not-base64-encoded' is not a valid base64-encoded string",
            ),
        ):
            my_func()


if __name__ == "__main__":
    absltest.main()
