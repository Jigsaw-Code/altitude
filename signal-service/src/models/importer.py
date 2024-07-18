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

"""Importer-related models."""

import enum

from mongoengine import Document, EmbeddedDocument, fields

import config
from importers import importer, tcap_api, threat_exchange


class Error(Exception):
    """Base class for exceptions in this module."""


class ImporterLoadError(Error):
    """Raised when an importer cannot be loaded."""


class Credential(EmbeddedDocument):
    """Represents a credential combination."""

    identifier = fields.StringField(required=True)
    token = fields.StringField(required=True)


class ImporterConfig(Document):
    """Corresponds to the representation of an ImporterConfig in the DB."""

    @enum.unique
    class Type(enum.Enum):
        UNKNOWN = "UNKNOWN"
        TCAP_API = "TCAP_API"
        THREAT_EXCHANGE_API = "THREAT_EXCHANGE_API"

    @enum.unique
    class State(enum.Enum):
        UNKNOWN = "UNKNOWN"
        ACTIVE = "ACTIVE"
        INACTIVE = "INACTIVE"

    type = fields.EnumField(Type, default=Type.UNKNOWN, required=True, primary_key=True)
    state = fields.EnumField(State, default=State.UNKNOWN, required=True)
    # Whether decisions are regularly sent back to the Importer.
    diagnostics_state = fields.EnumField(State, default=State.UNKNOWN, required=True)
    credential = fields.EmbeddedDocumentField(Credential, required=True)

    @property
    def enabled(self):
        return self.state == ImporterConfig.State.ACTIVE

    def to_importer(self) -> importer.Importer:
        """Converts the importer configuration to an importer that can be run."""
        if not self.enabled:
            raise ImporterLoadError("Importer not enabled.")

        if self.type == ImporterConfig.Type.TCAP_API:
            if config.DEVELOPMENT_APP_VERSION:
                tcap_server = tcap_api.Server.STAGING
            else:
                tcap_server = tcap_api.Server.PROD
            return tcap_api.TcapApiImporter(
                username=self.credential.identifier,
                password=self.credential.token,
                server=tcap_server,
            )

        if self.type == ImporterConfig.Type.THREAT_EXCHANGE_API:
            return threat_exchange.ThreatExchangeImporter(
                privacy_group_id=self.credential.identifier,
                access_token=self.credential.token,
            )

        raise NotImplementedError(f"Importer of type {self.type} not configured.")
