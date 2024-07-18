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

""" Tests for perspective module function. """

from unittest import mock

import googleapiclient

from analyzers import analyzer, perspective
from testing import test_case

MOCK_BUILD_RESPONSE = {
    "attributeScores": {
        "INSULT": {
            "spanScores": [
                {"begin": 0, "end": 9, "score": {"value": 0.1, "type": "PROBABILITY"}}
            ],
            "summaryScore": {"value": 0.1, "type": "PROBABILITY"},
        },
        "LIKELY_TO_REJECT": {
            "spanScores": [
                {"begin": 0, "end": 9, "score": {"value": 0.1, "type": "PROBABILITY"}}
            ],
            "summaryScore": {"value": 0.2, "type": "PROBABILITY"},
        },
        "SEVERE_TOXICITY": {
            "spanScores": [
                {"begin": 0, "end": 9, "score": {"value": 0.1, "type": "PROBABILITY"}}
            ],
            "summaryScore": {"value": 0.3, "type": "PROBABILITY"},
        },
        "IDENTITY_ATTACK": {
            "spanScores": [
                {"begin": 0, "end": 9, "score": {"value": 0.1, "type": "PROBABILITY"}}
            ],
            "summaryScore": {"value": 0.4, "type": "PROBABILITY"},
        },
        "TOXICITY": {
            "spanScores": [
                {"begin": 0, "end": 9, "score": {"value": 0.1, "type": "PROBABILITY"}}
            ],
            "summaryScore": {"value": 0.6, "type": "PROBABILITY"},
        },
        "THREAT": {
            "spanScores": [
                {"begin": 0, "end": 9, "score": {"value": 0.1, "type": "PROBABILITY"}}
            ],
            "summaryScore": {"value": 0.7, "type": "PROBABILITY"},
        },
        "PROFANITY": {
            "spanScores": [
                {"begin": 0, "end": 9, "score": {"value": 0.1, "type": "PROBABILITY"}}
            ],
            "summaryScore": {"value": 0.8, "type": "PROBABILITY"},
        },
    },
    "languages": ["en"],
    "detectedLanguages": ["en"],
}


class PerspectiveTest(test_case.TestCase):
    """Perspective API Test Class."""

    @mock.patch.object(googleapiclient.discovery, "build", autospec=True)
    def test_analyze_with_success_response_returns_scores(self, mock_build):
        """Tests analyze function with a successful Perspective success response."""
        # pylint: disable-next=protected-access, no-member
        mock_analyze = mock_build.return_value.comments.return_value.analyze
        mock_analyze.return_value.execute.return_value = MOCK_BUILD_RESPONSE

        scores = perspective.Perspective().analyze("Test Message")

        self.assertEqual(
            {
                "IDENTITY_ATTACK": 0.4,
                "INSULT": 0.1,
                "PROFANITY": 0.8,
                "SEVERE_TOXICITY": 0.3,
                "THREAT": 0.7,
                "TOXICITY": 0.6,
            },
            scores,
        )

    @mock.patch.object(googleapiclient.discovery, "build", autospec=True)
    def test_analyze_with_error_response_raises_error(self, mock_build):
        """Tests analyze function with a Perspective error response."""
        api_key_file = self.create_tempfile(content="APIKEY")
        # pylint: disable-next=protected-access,no-member
        analyzer._API_KEY_PATH = api_key_file.full_path
        mock_http_response = mock.Mock(status=400, reason="custom message")
        mock_analyze = mock_build.return_value.comments.return_value.analyze
        mock_analyze.return_value.execute.side_effect = (
            googleapiclient.errors.HttpError(
                resp=mock_http_response, content=b"Some test content"
            )
        )

        with self.assertRaisesWithLiteralMatch(
            perspective.PerspectiveAPIError,
            "Unable to get Perspective API scores: custom message",
        ):
            perspective.Perspective().analyze("Test Message")
