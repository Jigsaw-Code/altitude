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

"""A feature for text data."""

from mongoengine import EmbeddedDocument, fields


class Text(EmbeddedDocument):
    """Features related to text processing."""

    title = fields.StringField()
    description = fields.StringField()

    # The raw text data.
    data = fields.StringField()
    # The translation for the text data if the language differs from the preferred language.
    translated_data = fields.StringField()
    # The language detected by the API for the raw text data.
    detected_language_code = fields.StringField()

    # Scores of text data from Perspective API.
    # See more info at https://perspectiveapi.com/.
    perspective_scores = fields.DictField()
