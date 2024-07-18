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

"""Analyzer for Cloud Translation API functionality.

The Cloud Translation Basic API uses a Google pre-trained
model to translate text.
See https://cloud.google.com/translate/docs/overview
"""

import os

from google.api_core.exceptions import GoogleAPIError
from google.cloud import translate_v2

from analyzers import analyzer

TRANSLATION_TARGET_LANGUAGE_CODE = os.environ.get(
    "TRANSLATION_TARGET_LANGUAGE_CODE", "en"
)


class Error(analyzer.Error):
    """Base class for exceptions in this module."""


class TranslationAPIError(Error):
    """Error message for the Translation API response."""


class Translate(analyzer.Analyzer):
    """Class for utilizing the basic Cloud Translation API."""

    def analyze(self, data: str) -> tuple[str, str] | None:
        """Translates text into the target language.
        Args:
            data: The string that will be translated.
        Returns:
            A tuple where the 0th position is the translated text from 'data' and the 1st position
            is the detected language code of 'data', if the target language is different from
            the detected language. If the target language is the same as the detected
            language, it returns None.
        Raises:
            TranslationAPIError: An error ocurred with the response from Translation.
        """
        translate_client = translate_v2.Client(credentials=self.credentials)
        try:
            result = translate_client.translate(
                data, target_language=TRANSLATION_TARGET_LANGUAGE_CODE
            )
        except GoogleAPIError as exc:
            raise TranslationAPIError(
                "An error ocurred while requesting translation."
                " Check the language code or the string data that was inputted."
            ) from exc

        if result["detectedSourceLanguage"] == TRANSLATION_TARGET_LANGUAGE_CODE:
            return None

        return (result["translatedText"], result["detectedSourceLanguage"])
