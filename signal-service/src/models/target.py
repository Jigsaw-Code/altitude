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

"""Target-related models."""

import datetime

from mongoengine import Document, EmbeddedDocument, fields

from models.features.engagement import Engagement
from models.features.image import Image
from models.features.text import Text
from models.features.user import User


class FeatureSet(EmbeddedDocument):
    """The collection of features that make up Target entity."""

    # Features related to target creator.
    creator = fields.EmbeddedDocumentField(User)

    # Features related to target engagement. e.g. views, shares, comments.
    engagement_metrics = fields.EmbeddedDocumentField(Engagement)

    # Features related to image processing.
    image = fields.EmbeddedDocumentField(Image)

    # Features related to text processing.
    text = fields.EmbeddedDocumentField(Text)


class Target(Document):
    """Corresponds to the representation of a Target in the DB.

    A target is the entity that content moderation workflows are targeting. It is
    represented as a collection of Features. Some of those Features are provided by the
    client when they are created, while others could be fetched or calculated at later
    stages by the system.
    """

    # The time this target was created in the system.
    create_time = fields.DateTimeField(default=datetime.datetime.utcnow)

    # An opaque string provided in the target creation API that will be stored as-is,
    # passed through without modification and returned with results in callbacks. A
    # common use case would be to hold information related to the request from the
    # client, including identifiers and other request params.
    # Do not try to parse this string. It could be encoded or encrypted.
    client_context = fields.StringField()

    # The collection of features that make up the entity.
    feature_set = fields.EmbeddedDocumentField(FeatureSet, required=True)
