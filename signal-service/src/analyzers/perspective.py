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

"""Analyzer to provide Perspective API functionality.

The Perspective API uses machine learning models to identify abusive text.
See more at https://perspectiveapi.com/.
"""

from googleapiclient import discovery, errors

from analyzers import analyzer

_DISCOVERY_URL = (
    "https://commentanalyzer.googleapis.com/$discovery/rest?version=v1alpha1"
)

# These are the default attributes requested because they support the most languages
ATTRIBUTES = [
    "IDENTITY_ATTACK",
    "INSULT",
    "PROFANITY",
    "SEVERE_TOXICITY",
    "THREAT",
    "TOXICITY",
]


class Error(Exception):
    """Base class for exceptions in this module."""


class PerspectiveAPIError(Error):
    """Raised when the Perspective API responds with an error."""


class Perspective(analyzer.Analyzer):
    """Class for utilizing the Perspective API."""

    def analyze(self, data: str) -> dict[str, float]:
        """Gets corresponding scores for certain attributes from Perspective API.

        Args:
          data: String data to be analyzed.

        Returns:
          scores: A dictionary with attribute key and score value.

        Raises:
            PerspectiveAPIError: The Perspective API returned an error response.
        """
        client = discovery.build(
            "commentanalyzer",
            "v1alpha1",
            credentials=self.credentials,
            discoveryServiceUrl=_DISCOVERY_URL,
            static_discovery=False,
        )
        analyze_request = {
            "comment": {"text": data},
            "requestedAttributes": {attribute: {} for attribute in ATTRIBUTES},
        }
        try:
            # pylint: disable-next=no-member
            response = client.comments().analyze(body=analyze_request).execute()
        except errors.HttpError as e:
            raise PerspectiveAPIError(
                f"Unable to get Perspective API scores: {e.reason}"
            ) from e

        # Extracts only the scores from response.
        scores = {
            attribute: response["attributeScores"][attribute]["summaryScore"]["value"]
            for attribute in ATTRIBUTES
        }
        return scores
