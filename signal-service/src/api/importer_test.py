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
"""Tests for the Importer API."""

import http
from datetime import datetime
from typing import Iterable
from unittest import mock

from absl.testing import absltest, parameterized

from api.importer import bp as importer_bp
from importers import importer
from models.case import Review
from models.importer import Credential, ImporterConfig
from models.job import Job
from testing.test_case import ApiTestCase


class TestImporter(importer.Importer):
    def __init__(self):
        super().__init__(Job.JobSource.UNKNOWN)

    def pre_check(self):
        pass

    def _get_data(self):
        return []

    def _send_decisions(self, decisions: Iterable[tuple[str, Review.Decision]]) -> None:
        pass


class TestImporterFailPrecheck(importer.Importer):
    def __init__(self):
        super().__init__(Job.JobSource.UNKNOWN)

    def pre_check(self):
        raise importer.PreCheckError("Bad credentials")

    def _get_data(self):
        return []

    def _send_decisions(self, decisions: Iterable[tuple[str, Review.Decision]]) -> None:
        pass


class ImporterAPITest(parameterized.TestCase, ApiTestCase):
    blueprint = importer_bp

    def test_get_importer_invalid_importer_type_raises(self):
        self.get(
            "/importers/foobar",
            expected_status=http.HTTPStatus.NOT_FOUND,
            expected_message="Importer FOOBAR not found.",
        )

    def test_get_importer_returns_data(self):
        ImporterConfig(
            type=ImporterConfig.Type.TCAP_API,
            credential=Credential(identifier="foo", token="bar"),
        ).save()
        Job(
            source=Job.JobSource.TCAP_API,
            start_time=datetime(2024, 6, 12),
            import_size=12,
        ).save()
        Job(
            source=Job.JobSource.THREAT_EXCHANGE_API,
            start_time=datetime(2025, 6, 12),
            import_size=9,
        ).save()
        Job(
            source=Job.JobSource.TCAP_API,
            start_time=datetime(2022, 1, 1),
            import_size=4,
        ).save()

        observed_response = self.get("/importers/tcap_api")

        self.assertEqual(
            {
                "type": "TCAP_API",
                "state": "UNKNOWN",
                "diagnostics_state": "UNKNOWN",
                "credential": {
                    "identifier": "foo",
                    "token": "bar",
                },
                "last_run_time": "2024-06-12T00:00:00+00:00",
                "total_import_count": 16,
            },
            observed_response.json,
        )

    def test_create_new_importer(self):
        with mock.patch.object(
            ImporterConfig, "to_importer", new=lambda x: TestImporter()
        ):
            self.post(
                "/importers/",
                json={
                    "type": "TCAP_API",
                    "state": "ACTIVE",
                    "diagnostics_state": "INACTIVE",
                    "credential": {
                        "identifier": "foo",
                        "token": "bar",
                    },
                },
                expected_status=http.HTTPStatus.CREATED,
            )

        self.assertEqual(1, ImporterConfig.objects.count())
        importer_config = ImporterConfig.objects.get(type=ImporterConfig.Type.TCAP_API)
        self.assertEqual(ImporterConfig.State.ACTIVE, importer_config.state)
        self.assertEqual(
            ImporterConfig.State.INACTIVE, importer_config.diagnostics_state
        )
        self.assertEqual("foo", importer_config.credential.identifier)
        self.assertEqual("bar", importer_config.credential.token)

    def test_create_new_importer_fails_if_credentials_are_incorrect(self):
        with mock.patch.object(
            ImporterConfig, "to_importer", new=lambda x: TestImporterFailPrecheck()
        ):
            self.post(
                "/importers/",
                json={
                    "type": "TCAP_API",
                    "state": "INACTIVE",
                    "diagnostics_state": "INACTIVE",
                    "credential": {
                        "identifier": "foo",
                        "token": "bar",
                    },
                },
                expected_status=http.HTTPStatus.BAD_REQUEST,
            )

        self.assertEqual(0, ImporterConfig.objects.count())

    def test_create_new_importer_overrides_existing_type(self):
        ImporterConfig(
            type=ImporterConfig.Type.TCAP_API,
            credential=Credential(identifier="foo", token="bar"),
        ).save()

        with mock.patch.object(
            ImporterConfig, "to_importer", new=lambda x: TestImporter()
        ):
            self.post(
                "/importers/",
                json={
                    "type": "TCAP_API",
                    "credential": {
                        "identifier": "updated_foo",
                        "token": "updated_bar",
                    },
                },
                expected_status=http.HTTPStatus.CREATED,
            )

        self.assertEqual(1, ImporterConfig.objects.count())
        importer_config = ImporterConfig.objects.get(type=ImporterConfig.Type.TCAP_API)
        self.assertEqual("updated_foo", importer_config.credential.identifier)
        self.assertEqual("updated_bar", importer_config.credential.token)

    def test_delete_importer(self):
        ImporterConfig(
            type=ImporterConfig.Type.TCAP_API,
            credential=Credential(identifier="foo", token="bar"),
        ).save()

        response = self.delete(
            "/importers/tcap_api",
            expected_status=http.HTTPStatus.NO_CONTENT,
        )

        self.assertEqual(response.json, None)
        with self.assertRaises(ImporterConfig.DoesNotExist):
            ImporterConfig.objects.get(type=ImporterConfig.Type.TCAP_API)


if __name__ == "__main__":
    absltest.main()
