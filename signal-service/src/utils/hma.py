# Copyright 2024 Google LLC
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

"""A client module to interact with the Hasher Matcher Actioner (HMA) API.

HMA is a REST API which we run in its own container. This is just a convenience module
to centralize interaction with that API.

See https://github.com/facebook/ThreatExchange/tree/main/hasher-matcher-actioner for
details on the HMA system.
"""

from __future__ import annotations

import enum
import logging
from dataclasses import dataclass

import requests

_HMA_HOST = "http://hma:5000"
_DEFAULT_REQUEST_TIMEOUT_SEC = 5


@enum.unique
class ContentType(str, enum.Enum):
    """Enum of content type values allowed by the HMA API."""

    IMAGE = "photo"
    VIDEO = "video"


@dataclass
class Hash:
    """Data class to hold hashes."""

    pdq: str
    video_md5: str

    @classmethod
    def deserialize(cls, data: any) -> Hash:
        return cls(**data)


def hash_from_bytes(
    data: bytes, content_type: ContentType = ContentType.IMAGE
) -> Hash | None:
    """Generates a hash from bytes based on the content type."""
    response = requests.post(
        f"{_HMA_HOST}/h/hash",
        files={content_type.value: data},
        timeout=_DEFAULT_REQUEST_TIMEOUT_SEC,
    )

    if not response.ok:
        logging.warn("Unable to hash provided bytes")
        return None

    return Hash.deserialize(response.json())


def hash_from_url(url: str) -> Hash | None:
    """Generates a hash from a URL."""
    response = requests.get(
        f"{_HMA_HOST}/h/hash?url={url}",
        timeout=_DEFAULT_REQUEST_TIMEOUT_SEC,
    )

    if not response.ok:
        logging.warn("Unable to hash %s", url)
        return None

    return Hash.deserialize(response.json())
