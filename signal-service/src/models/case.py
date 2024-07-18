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

"""Case-related model."""

import datetime
import enum
from functools import cached_property

from bson.objectid import ObjectId
from mongoengine import Document, EmbeddedDocument, fields

from prioritization import case_priority


class Review(EmbeddedDocument):
    """Represents the decision made on a case in the DB."""

    @enum.unique
    class State(enum.Enum):
        UNKNOWN = "UNKNOWN"
        # State for a review that is not yet published.
        DRAFT = "DRAFT"
        # Default state for a review that has been published.
        PUBLISHED = "PUBLISHED"

    @enum.unique
    class Decision(enum.Enum):
        # The decision options available to the moderator. Subject to change.
        BLOCK = "BLOCK"
        APPROVE = "APPROVE"

    @enum.unique
    class DeliveryStatus(enum.Enum):
        PENDING = "PENDING"
        ACCEPTED = "ACCEPTED"
        FAILED = "FAILED"

    # The unique identifier for this review. This is needed because `Review` is an
    # embedded document on `Case`, which do not get IDs by default.
    id = fields.ObjectIdField(db_field="_id", required=True, default=ObjectId)

    # The timestamp of when this review was created.
    create_time = fields.DateTimeField(default=datetime.datetime.utcnow, required=True)

    # The timestamp of when this review was last updated.
    update_time = fields.DateTimeField(default=datetime.datetime.utcnow, required=True)

    # The current state of the review.
    state = fields.EnumField(State, default=State.UNKNOWN)

    # The decision made in this review.
    decision = fields.EnumField(Decision)

    # The user that completed this review.
    user = fields.StringField()

    # Whether or not the platform has been sent the decision.
    delivery_status = fields.EnumField(
        DeliveryStatus, db_field="status", default=DeliveryStatus.PENDING
    )

    def clean(self):
        """Cleans the document before validation."""
        self.update_time = datetime.datetime.utcnow()


class Case(Document):
    """Represents a match between some flagged signal and platform content.

    Platform content is modeled as a Target entity in our system. Note that there are
    cases that represent a "match without target", namely signals that point at a a
    URL. This URL may not be represented by the platform as a Target, but we still want
    to enqueue those for review. In all other cases, there should be a `target_id` to
    point to the relevant Target entity that this match is for.
    """

    @enum.unique
    class State(str, enum.Enum):
        ACTIVE = "ACTIVE"
        RESOLVED = "RESOLVED"

    # A list of source signal entities of the case. These signals were used to
    # flag this target entity to create this case.
    signal_ids = fields.ListField(fields.ObjectIdField(), required=True)

    # The target entity of the case. This is not currently set to `required` because
    # some cases represent a "match without target", which is a signal that matches
    # by default because it represents a URL. For signals with URLs, we do not currently
    # (need to) compare its value to a target entity in order to create a case.
    target_id = fields.ObjectIdField()

    # The timestamp of when this case was created.
    create_time = fields.DateTimeField(default=datetime.datetime.utcnow, required=True)

    # The current state of the case.
    state = fields.EnumField(State, default=State.ACTIVE)

    # The history of reviews made on this case, in chronological order.
    review_history = fields.EmbeddedDocumentListField(Review)

    # The notes a user may set on a case.
    notes = fields.StringField()

    @property
    def latest_review(self) -> Review | None:
        if not self.review_history:
            return None
        return self.review_history[-1]

    # NOTE: You should only need to reference the cached variants when doing a DB query.
    # If you want to read the value for an instance, use the non-cached variabts (e.g.
    # `self.confidence` instead of `self.cached_confidence`).
    cached_confidence = fields.FloatField(db_field="confidence")
    cached_severity = fields.FloatField(db_field="severity")
    cached_priority = fields.IntField(db_field="priority")

    @cached_property
    def confidence(self) -> int | None:
        return (
            case_priority.calculate_confidence(self.signal_ids)
            if self.signal_ids
            else None
        )

    @property
    def confidence_level(self) -> case_priority.Level | None:
        """The confidence level of the case."""
        if not self.confidence:
            return None
        return case_priority.get_confidence_level(int(self.confidence))

    @cached_property
    def severity(self) -> int | None:
        return (
            case_priority.calculate_severity(self.signal_ids)
            if self.signal_ids
            else None
        )

    @property
    def severity_level(self) -> case_priority.Level | None:
        """The severity level of the case."""
        if not self.severity:
            return None
        return case_priority.get_severity_level(int(self.severity))

    @property
    def priority(self) -> int | None:
        confidence = self.confidence
        severity = self.severity

        # We are unable to calculate a priority score for this
        # case. We return `-1` for these cases to differentiate
        # them from the real priority score of `0`. Giving these
        # cases a distinct numerical score will allow them to
        # be ordered alongside and compared to cases for which
        # we do have a real priority score. This is used in places
        # like the the API which returns a list of Cases in order
        # of priority.
        if not any((confidence, severity)):
            return -1

        return int(confidence or 0) + int(severity or 0)

    @property
    def priority_level(self) -> case_priority.Level | None:
        """The priority level of the case."""
        if self.priority == -1:
            return None
        return case_priority.get_priority_level(int(self.priority))

    meta = {
        "indexes": ["-cached_priority"],
        "ordering": ["-cached_priority"],
    }

    def clean(self):
        """Cleans the document before validation."""
        # Update the state of the Case based on the latest Review state.
        if self.latest_review and self.latest_review.state in {
            Review.State.DRAFT,
            Review.State.PUBLISHED,
        }:
            self.state = Case.State.RESOLVED
        else:
            self.state = Case.State.ACTIVE

        self.cached_confidence = self.confidence
        self.cached_severity = self.severity
        self.cached_priority = self.priority
