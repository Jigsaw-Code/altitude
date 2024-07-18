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
from __future__ import annotations

import http
import os
import pathlib
import traceback
import unittest
from typing import Callable, Iterator
from unittest import mock

import flask
import mongomock
from absl import flags
from absl.testing import absltest
from flask_celeryext import create_celery_app
from google.auth.credentials import Credentials

import api
from api.validation import Schema, Validator
from mongodb import connection
from taskqueue import tasks

flags.FLAGS.mark_as_parsed()


class TestCase(absltest.TestCase):
    """Convenience class to help with testing with some common setup"""

    def setUp(self):
        """Sets up the test harness."""
        self.addCleanup(mock.patch.stopall)
        super().setUp()

        if not hasattr(self, "app"):
            self.app = flask.Flask(__name__)
        self.app.config.update(
            {
                "CELERY_TASK_ALWAYS_EAGER": True,
                "CELERY_RESULT_BACKEND": "cache",
                "CELERY_CACHE_BACKEND": "memory",
                "CELERY_EAGER_PROPAGATES": True,
            }
        )
        create_celery_app(self.app)

        # The root path is the root of the Python project (i.e. the `src/` directory).
        # This can be helpful when referencing file paths by specifing them relative to
        # the root versus relative to the calling module, which would require updates
        # whenever the calling module moves.
        self.root_path = pathlib.Path(__file__).parent.parent

        # MongoDB uses credentials loaded from Docker secrets files. The filenames for
        # those secrets are set in the environment. Here, we need to configure these so
        # that the MongoClient under test is instantiated with the same host as the
        # MongoMock patch.
        username_file = self.create_tempfile(content="test-user")
        password_file = self.create_tempfile(content="password123")
        env_patcher = mock.patch.dict(
            os.environ,
            {
                "MONGO_USERNAME_FILE": username_file.full_path,  # pylint: disable=no-member
                "MONGO_PASSWORD_FILE": password_file.full_path,  # pylint: disable=no-member
                "MONGO_SERVER": "mongodb",
                "MONGO_DATABASE": "altitude",
            },
        )
        env_patcher.start()
        self.connection_ctx = connection.connect(
            "mongoenginetest",
            host=f"mongodb://{connection.HOST}",
            uuidRepresentation="standard",
            tz_aware=connection.TZ_AWARE,
            username="test-user",
            password="password123",
            mongo_client_class=mongomock.MongoClient,
        )
        self.mock_connection = self.connection_ctx.__enter__()

        # Some tasks write logs to files. These filepaths need to exist in tests.
        tasks.LOG_FILEPATH = self.create_tempdir().full_path

        # Mock out all Google Auth credential calls.
        fake_creds = (
            mock.create_autospec(Credentials, universe_domain="googleapis.com"),
            "project",
        )
        mock.patch("google.auth.default", return_value=fake_creds).start()

    def tearDown(self):
        super().tearDown()
        self.connection_ctx.__exit__(None, None, None)


class ApiTestCase(TestCase):
    """Convenience class to help with API testing.

    Example usage:
        class MyAPITest(ApiTestCase):

            blueprint = my_api.bp

            def test_not_found(self):
                self.get(
                    "/foobar",
                    expected_status=http.HTTPStatus.NOT_FOUND,
                    expected_message="foobar not found.",
                )
    """

    blueprint: Callable | None = None

    @classmethod
    def setUpClass(cls):
        if cls == ApiTestCase:
            raise unittest.SkipTest("Skip `ApiTestCase` base class tests.")

        assert cls.blueprint is not None, (
            "No `blueprint` property found on test case " + cls.__name__
        )
        cls.app = api.Api(__name__, blueprints={cls.blueprint}, static_folder=None)

    def _send(self, method, url, expected_status=200, expected_message=None, json=None):
        if method in ("POST", "PATCH") and json is None:
            json = {}
        with self.app.test_client() as client:
            try:
                response = getattr(client, method.lower())(url, json=json)
            except Exception as e:
                self.assertEqual(expected_status, 500, f"{e}\n{traceback.format_exc()}")
                raise

        has_error = response.json and "error" in response.json
        if has_error:
            error_msg = response.json["error"]["message"]
        else:
            error_msg = http.HTTPStatus(response.status_code).description
        self.assertEqual(
            expected_status,
            response.status_code,
            msg=error_msg,
        )
        if has_error:
            if expected_message:
                self.assertEqual(expected_message, error_msg)
        else:
            self.assertIsNone(expected_message, "Exception was expected")
        return response

    def get(self, url, *args, **kwargs):
        return self._send("GET", url, *args, **kwargs)

    def post(self, url, *args, **kwargs):
        return self._send("POST", url, *args, **kwargs)

    def patch(self, url, *args, **kwargs):
        return self._send("PATCH", url, *args, **kwargs)

    def delete(self, url, *args, **kwargs):
        return self._send("DELETE", url, *args, **kwargs)

    def _get_validators(self) -> Iterator[tuple[str, set[Validator]]]:
        for name, function in self.app.view_functions.items():
            yield name, getattr(function, "_validators", set())

    def _get_schemas(self) -> Iterator[tuple[str, Schema]]:
        for name, validators in self._get_validators():
            for validator in validators:
                for schema in validator._schemas:  # pylint: disable=protected-access
                    yield name, schema

    def assert_schema_valid(self, schema: Schema, msg):
        self.assertIsNotNone(schema, msg)
        self.assertNotEmpty(schema, msg)
        Validator.JSON_SCHEMA_VALIDATOR_CLS.check_schema(schema)

    def test_all_http_methods_have_validator_decorators(self):
        """Tests that all HTTP methods are protected with a validator decorator."""
        for name, validators in self._get_validators():
            self.assertNotEmpty(
                validators,
                f"HTTP method `{name}` requires a validator. Make sure to decorate "
                "the method with an instance of `validation.Validator`.",
            )
            self.assertLen(
                validators, 1, f"HTTP method `{name}` has more than one validator."
            )

    def test_all_validator_decorators_have_valid_schemas(self):
        """Tests that all method validators have been configured with valid schemas."""
        for name, schema in self._get_schemas():
            self.assert_schema_valid(
                schema,
                f"`{name}` decorated `Validator` must provide non-empty schemas",
            )
            self.assertIsNotNone(
                schema.get("title"),
                f"`{name}` decorated `Validator` must set `title` property on all "
                "schemas",
            )

    def test_all_objects_in_schemas_prohibit_additional_properties(self):
        """Tests that all validator schema prohibit arbitrary additional properties."""

        def _validate(schema):
            """Recursively validates a JSON schema by checking `additionalProperties`.

            Raises:
                ValueError: If an object type is found and it is missing the
                    `additionalProperties` property or it is not set to `False`.
            """
            if not schema or not isinstance(schema, dict):
                return
            if schema.get("type") == "object":
                if schema.get("additionalProperties") is not False:
                    raise ValueError
                for item in schema.get("properties", {}).items():
                    _validate(item)
            elif schema.get("type") == "array":
                _validate(schema.get("items"))
            elif "anyOf" in schema:
                for item in schema.get("anyOf"):
                    _validate(item)
            elif "oneOf" in schema:
                for item in schema.get("oneOf"):
                    _validate(item)

        for name, schema in self._get_schemas():
            try:
                _validate(schema)
            except ValueError:
                schema_title = schema.get("title")
                self.fail(
                    f'`{name}` schema "{schema_title}" uses `object` that does not '
                    "prohibit additional properties. Please add "
                    '`"additionalProperties": False` to all schema `object` types.'
                )
