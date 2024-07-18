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

"""Utilities for image processing."""

from io import BytesIO

from PIL import Image, UnidentifiedImageError


def is_image(data: bytes) -> bool:
    """Check if content is an image by attempting to open with the pillow library.

    Args:
        data: The byte content to be checked.
    Returns:
        Boolean representing if bytes data represents an image.
    """
    try:
        Image.open(BytesIO(data))
    except UnidentifiedImageError:
        return False
    return True
