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

"""Utilities for image hashing."""

import logging

import requests
from threatexchange.signal_type.pdq import PdqSignal

from utils.image import is_image


def generate_pdq_hash_from_url(url: str) -> str | None:
    """Sends a request to the URL and hashes the image.

    Args:
        url: The url (possibly) containing the image
    Returns:
        The pdq digest of the url image content as a string
        or None if content was not hashable
    """
    try:
        response = requests.get(url, timeout=5)
    except requests.RequestException:
        logging.error("%s not reachable", url)
        return None
    if not response:
        logging.info("%s not responsive", url)
        return None
    data = response.content

    if not is_image(data):
        logging.info("%s does not link to an image", url)
        return None

    pdq_digest = PdqSignal.hash_from_bytes(data)

    if not pdq_digest:
        logging.info("%s has non hashable", url)
        return None

    return pdq_digest
