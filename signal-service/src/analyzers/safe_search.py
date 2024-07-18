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

"""Analyzer to provide Safe Search Detection API functionality.

The Safe Search API detects explicit content within
an image,labels them into categories,and returns the
likelihood of each category.
See https://cloud.google.com/vision/docs/detecting-safe-search
"""

import json

from google.cloud import vision

from analyzers import analyzer


class Error(Exception):
    """Base class for exceptions in this module."""


class SafeSearchAPIError(Error):
    """Error message for Safe Search API response."""


class SafeSearch(analyzer.Analyzer):
    """Class for ulitizing the Safe Search Detection API."""

    def analyze(self, data: bytes) -> dict[str, int]:
        """Detects unsafe features in the content.

        Args:
            data: The content bytes that will be processed through Safe Search.
        Returns:
            A dictionary containing the likelihood scores.
        Raises:
            SafeSearchAPIError: An error ocurred with the response from Safe Search.
        """
        client = vision.ImageAnnotatorClient(credentials=self.credentials)

        image = vision.Image(content=data)

        # pylint: disable-next=no-member
        response = client.safe_search_detection(image=image)
        safe = response.safe_search_annotation

        if response.error.message:
            raise SafeSearchAPIError(
                f"{response.error.message}\nFor more info on error messages, check: "
                "https://cloud.google.com/apis/design/errors"
            )
        return json.loads(type(safe).to_json(safe))
