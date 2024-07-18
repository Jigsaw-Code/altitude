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

"""A feature for image data."""

import enum

from mongoengine import EmbeddedDocument, fields

from models.features.text import Text


@enum.unique
class Likelihood(enum.IntEnum):
    """Representation of an image's likelihood for certain
    categories based on Safe Search API results.
    See https://cloud.google.com/vision/docs/reference/rpc/google.cloud.vision.v1#google.cloud.vision.v1.SafeSearchAnnotation #pylint: disable=line-too-long
    """

    UNKNOWN = 0
    VERY_UNLIKELY = 1
    UNLIKELY = 2
    POSSIBLE = 3
    LIKELY = 4
    VERY_LIKELY = 5


class Image(EmbeddedDocument):
    """Corresponds to the representation of an Image feature in a Target in the DB.

    An image contains data provided by the user which is processed by the system
    in order to determine if a Case needs to be created.
    """

    title = fields.StringField()
    description = fields.StringField()

    # The image data in bytes.
    data = fields.BinaryField()

    # Text extracted from image through OCR processing and perspective api scores.
    ocr_text = fields.EmbeddedDocumentField(Text)

    # PDQ hash digest extracted from the image bytes.
    pdq_digest = fields.StringField()

    # Safe Search Data Result Properties.
    # pylint: disable-next=line-too-long
    # See https://cloud.google.com/vision/docs/reference/rpc/google.cloud.vision.v1#google.cloud.vision.v1.SafeSearchAnnotation
    adult_likelihood = fields.EnumField(Likelihood, default=Likelihood.UNKNOWN)
    spoof_likelihood = fields.EnumField(Likelihood, default=Likelihood.UNKNOWN)
    medical_likelihood = fields.EnumField(Likelihood, default=Likelihood.UNKNOWN)
    violence_likelihood = fields.EnumField(Likelihood, default=Likelihood.UNKNOWN)
    racy_likelihood = fields.EnumField(Likelihood, default=Likelihood.UNKNOWN)
