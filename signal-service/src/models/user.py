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

"""User-related models."""

from __future__ import annotations

import datetime

from mongoengine import Document, EmbeddedDocument, fields

from mongodb.fields import ExpireDateTimeField, ListField


class QueueConfig(EmbeddedDocument):
    """Represents a priority queue configuration in the DB."""

    weight_illegal = fields.FloatField(min_value=0.0, max_value=1.0)
    weight_violent = fields.FloatField(min_value=0.0, max_value=1.0)
    weight_popular = fields.FloatField(min_value=0.0, max_value=1.0)
    weight_trust = fields.FloatField(min_value=0.0, max_value=1.0)


class ReviewHistory(EmbeddedDocument):
    """Represents the history of a User's reviews in the DB."""

    # TODO: Replace these with `count()` queries once we have actual review
    # history data.
    count_disputed_all_time = fields.IntField(default=0, min_value=0)
    count_removed_all_time = fields.IntField(default=0, min_value=0)
    count_alerts_all_time = fields.IntField(default=0, min_value=0)
    recent_removal_dates = ListField(
        ExpireDateTimeField(expiration=datetime.timedelta(days=30)),
        null=False,
        filter_predicate=None.__ne__,
    )
    recent_alert_dates = ListField(
        ExpireDateTimeField(expiration=datetime.timedelta(days=30)),
        null=False,
        filter_predicate=None.__ne__,
    )


class User(Document):
    """Corresponds to the representation of a User in the DB."""

    user_id = fields.StringField(primary_key=True)
    settings_config = fields.DictField()
    queue_config = fields.EmbeddedDocumentField(QueueConfig)
    review_history = fields.EmbeddedDocumentField(ReviewHistory)
    cases = fields.ListField(fields.ObjectIdField())
