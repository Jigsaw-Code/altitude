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
"""Tests for the importer data models."""

from absl.testing import absltest, parameterized

from importers import tcap_api, threat_exchange
from models.importer import Credential, ImporterConfig
from testing import test_case


class ImporterConfigTest(parameterized.TestCase, test_case.TestCase):
    @parameterized.parameters(
        (ImporterConfig.Type.TCAP_API, tcap_api.TcapApiImporter),
        (
            ImporterConfig.Type.THREAT_EXCHANGE_API,
            threat_exchange.ThreatExchangeImporter,
        ),
    )
    def test_to_importer(self, importer_type, importer_cls):
        config = ImporterConfig(
            state=ImporterConfig.State.ACTIVE,
            type=importer_type,
            credential=Credential(identifier="username", token="password"),
        )

        importer = config.to_importer()

        self.assertIsInstance(importer, importer_cls)


if __name__ == "__main__":
    absltest.main()
