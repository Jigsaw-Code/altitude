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

"""Signal-related models."""

from __future__ import annotations

import enum

import pytz
from mongoengine import Document, EmbeddedDocument, fields, queryset_manager


class Source(EmbeddedDocument):
    """Represents the source of a Signal in the DB."""

    @enum.unique
    class Name(str, enum.Enum):
        UNKNOWN = "UNKNOWN"
        TCAP = "TCAP"
        GIFCT = "GIFCT"
        USER_REPORT = "USER_REPORT"
        SAFE_SEARCH = "SAFE_SEARCH"
        PERSPECTIVE = "PERSPECTIVE"

    name = fields.EnumField(Name, default=Name.UNKNOWN)
    # The original author that created the signal. For example, a username or email for
    # a user report, or the original owner of a signal for GIFCT.
    author = fields.StringField()
    deprecated_description = fields.StringField(db_field="description")
    report_date = fields.DateTimeField()
    source_signal_id = fields.StringField()
    is_redacted = fields.BooleanField(default=False)


class Sources(EmbeddedDocument):
    """Represents a collection of sources and their metadata."""

    sources = fields.EmbeddedDocumentListField(Source, required=True)


class ContentStatus(EmbeddedDocument):
    """Describes the status of content."""

    @enum.unique
    class Status(str, enum.Enum):
        UNKNOWN = "UNKNOWN"
        ACTIVE = "ACTIVE"
        REMOVED_BY_USER = "REMOVED_BY_USER"
        REMOVED_BY_MODERATOR = "REMOVED_BY_MODERATOR"
        UNAVAILABLE = "UNAVAILABLE"

    # TODO: we should rely on an in-house verification system only,
    # and once that's in place this should be removed.
    @enum.unique
    class Verifier(str, enum.Enum):
        UNKNOWN = "UNKNOWN"
        TCAP = "TCAP"
        INTERNAL = "INTERNAL"

    # TODO - create a sub-class for DateTimeField that requires
    # timezone to be set.
    last_checked_date = fields.DateTimeField()
    most_recent_status = fields.EnumField(Status, default=Status.UNKNOWN)
    verifier = fields.EnumField(Verifier, default=Status.UNKNOWN)

    def __lt__(self, other: ContentStatus) -> bool:
        if not other.last_checked_date:
            return False
        if not self.last_checked_date:
            return True

        # Default to UTC timezone if no timezone is given.
        other_date = other.last_checked_date
        if other_date.tzinfo is None or other_date.tzinfo.utcoffset(other_date) is None:
            other_date = other_date.replace(tzinfo=pytz.utc)
        self_date = self.last_checked_date
        if self_date.tzinfo is None or self_date.tzinfo.utcoffset(self_date) is None:
            self_date = self_date.replace(tzinfo=pytz.utc)

        return self_date < other_date


class ContentFeatures(EmbeddedDocument):
    """Describes the features of Content in the DB."""

    class Confidence(str, enum.Enum):
        YES = "YES"
        NO = "NO"
        UNSURE = "UNSURE"

    description = fields.StringField()
    deprecated_platform_content_to_popularity = fields.MapField(
        fields.IntField(), db_field="platform_content_to_popularity"
    )
    # TODO: Refactor these fields to be specific to a given source.
    trust = fields.FloatField(default=-1)
    confidence = fields.FloatField(default=-1)
    associated_terrorist_organizations = fields.ListField(
        fields.StringField(), default=[]
    )
    contains_pii = fields.EnumField(Confidence)
    is_violent_or_graphic = fields.EnumField(Confidence)
    is_illegal_in_countries = fields.ListField(fields.StringField())
    tags = fields.ListField(fields.StringField(), default=[])


# TODO: consider renaming this field.
class Content(EmbeddedDocument):
    """Describes the Signal's contents."""

    # We don't inherit from `str` here, due to https://github.com/google/pytype/issues/654.
    class ContentType(enum.Enum):
        URL = "URL"
        HASH_PDQ = "HASH_PDQ"
        HASH_MD5 = "HASH_MD5"
        API = "API"
        UNKNOWN = "UNKNOWN"

    value = fields.StringField()
    content_type = fields.EnumField(
        ContentType, default=ContentType.UNKNOWN, required=True
    )


class Signal(Document):
    """Corresponds to the representation of a Signal in the DB."""

    _REDACTED = "[REDACTED]"

    content = fields.EmbeddedDocumentListField(Content, required=True)
    sources = fields.EmbeddedDocumentField(Sources, required=True)
    user_content_to_past_review = fields.MapField(
        fields.ListField(fields.StringField())
    )
    content_features = fields.EmbeddedDocumentField(ContentFeatures)
    content_status = fields.EmbeddedDocumentField(ContentStatus)

    meta = {"indexes": ["content.value", "content.content_type"]}

    @queryset_manager
    def pdq(doc_cls, queryset):  # pylint: disable=no-self-argument
        return queryset.filter(content__content_type=Content.ContentType.HASH_PDQ)

    @property
    def is_redacted(self):
        return all(source.is_redacted for source in self.sources.sources)

    @property
    def is_url_only(self) -> bool:
        return (
            len(self.content) == 1
            and self.content[0].content_type == Content.ContentType.URL
        )

    def redact(self, source_name: Source.Name) -> Signal:
        """Redacts a given source of this signal.

        This sets the source into a `redacted` state. If all sources are redacted, the
        content of the signal also gets redacted as a final redaction.

        Args:
            source_name: The name of the source to redact.

        Raises:
            ValueError: If the provided name of the source to redact is not found on the
                signal.
        """
        for source in self.sources.sources:
            if source.name == source_name:
                source.is_redacted = True
                break
        else:
            raise ValueError(f"No source found with name {source_name}.")
        # Remove the content if all the sources have now been redacted.
        if self.is_redacted:
            self.content = [Content(value=Signal._REDACTED)]
        return self

    def __eq__(self, other) -> bool:
        """Compare equality of Signals ignoring ID field."""
        if not isinstance(other, self.__class__):
            return False

        ignore_keys = {"id"}
        self_data = {k: v for (k, v) in self._data.items() if k not in ignore_keys}
        other_data = {k: v for k, v in other._data.items() if k not in ignore_keys}
        return self_data == other_data

    def merge(self, other: Signal) -> None:
        """Merges two Signals, defaulting to self."""

        def should_update_content_status() -> bool:
            # The new content_status must be descriptive.
            if (
                not other.content_status
                or other.content_status.most_recent_status
                == ContentStatus.Status.UNKNOWN
            ):
                return False
            # Update if there is no existing status.
            if not self.content_status:
                return True
            # Use the most recent status.
            return other.content_status > self.content_status

        # pylint: disable=invalid-name,attribute-defined-outside-init
        self.id = self.id if self.id else other.id

        # Append new sources and update existing sources.
        existing_names = {s.name for s in self.sources.sources}
        for source in other.sources.sources:
            if source.name in existing_names:
                existing = next(
                    filter(
                        lambda e_source, name=source.name: e_source.name == name,
                        self.sources.sources,
                    )
                )
                # pylint: disable=protected-access
                for attribute_name, attribute in source._data.items():
                    if attribute_name not in existing:
                        existing[attribute_name] = attribute
            else:
                self.sources.sources.append(source)

        if should_update_content_status():
            self.content_status = other.content_status

        if other.content_features:
            # pylint: disable=protected-access
            for name, value in other.content_features._data.items():
                if (
                    name not in self.content_features._data
                    or not self.content_features._data[name]
                ):
                    self.content_features[name] = value
