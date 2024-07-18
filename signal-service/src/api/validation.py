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

"""Validation related functionality for the API."""
from __future__ import annotations

import base64
import binascii
import functools
import http
import logging
from typing import Any, Callable, Iterator

import flask
import jsonschema

from api.api_error import ApiError

Schema = dict[str, Any]


def _validator_decorator(decorator):
    """A decorator for our validation decorator.

    This allows us to easily test the use of the validator and the validation schemas.
    It does this by recording the validation decorator on the method it's validating.
    """

    @functools.wraps(decorator)
    def wrapper(self: Validator, wrapped: Callable):
        validators = getattr(wrapped, "_validators", [])
        validators.append(self)
        wrapped._validators = validators  # pylint: disable=protected-access
        return decorator(self, wrapped)

    return wrapper


def _validate_content_encoding(unused_validator, encoding, instance, unused_schema):
    if encoding == "base64":
        try:
            base64.b64decode(instance, validate=True)
        except binascii.Error:
            yield jsonschema.ValidationError(
                f"'{instance}' is not a valid base64-encoded string"
            )


class Validator:
    """A decorator that wraps requests to validate API inputs and outputs.

    Example usage:

        @app.get('/my-route/')
        @Validator(
            input_schema={
                "title": "My API input schema",
                "type": "object",
                "properties": {
                    "foo": {"type": "number"},
                },
                "additionalProperties": False,
            },
            output_schema={
                "title": "My API output schema",
                "type": "object",
                "properties": {
                    "bar": {"type": "string"},
                },
                "additionalProperties": False,
            },
        )
        def get():
            ...
    """

    JSON_SCHEMA_VALIDATOR_CLS = jsonschema.validators.extend(
        jsonschema.validators.Draft202012Validator,
        {"contentEncoding": _validate_content_encoding},
        format_checker=jsonschema.FormatChecker(),
    )

    def __init__(self, input_schema: Schema, output_schema: Schema):
        """Initializer.

        Args:
            input_schema: The JSON schema used to validate the request input.
            output_schema: The JSON schema used to validate the response output.
        """
        self._input_schema = input_schema
        self._input_validator = self.JSON_SCHEMA_VALIDATOR_CLS(self._input_schema)
        self._output_schema = output_schema
        self._output_validator = self.JSON_SCHEMA_VALIDATOR_CLS(self._output_schema)

    @property
    def _schemas(self) -> Iterator[Schema]:
        """Convenience method to return all the schemas configured on this validator.

        This allows us to easily test the validation schemas.
        """
        yield self._input_schema
        yield self._output_schema

    @_validator_decorator
    def __call__(self, wrapped):
        """Decorate the method or function."""

        @functools.wraps(wrapped)
        def wrapper(*args, **kwargs):
            self._validate_request(flask.request)
            response = flask.current_app.make_response(wrapped(*args, **kwargs))
            self._validate_response(response)
            return response

        return wrapper

    def _validate_request(self, request: flask.Request):
        try:
            self._input_validator.validate(request.get_json(silent=True))
        except jsonschema.ValidationError as e:
            logging.error(e)
            raise ApiError(http.HTTPStatus.BAD_REQUEST, e.message) from e

    def _validate_response(self, response: flask.Response):
        try:
            self._output_validator.validate(response.get_json(silent=True))
        except jsonschema.ValidationError as e:
            logging.exception(e)
            raise ApiError(http.HTTPStatus.INTERNAL_SERVER_ERROR) from e
