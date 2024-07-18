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
# pylint: disable=missing-docstring
"""Test that the Translation functions behave as expected."""

from unittest import mock

from absl.testing import absltest
from google.api_core.exceptions import GoogleAPIError

from analyzers import translation
from testing import test_case


class TranslationTest(test_case.TestCase):
    def setUp(self):
        super().setUp()
        translation.TRANSLATION_TARGET_LANGUAGE_CODE = "en"

    @mock.patch("google.cloud.translate_v2.Client", spec=True)
    def test_translation_output_parsing(self, mock_translation):
        mock_translation.return_value.translate.return_value = {
            "translatedText": "Hello",
            "detectedSourceLanguage": "ja",
            "input": "こんにちは",
        }
        translation_test = translation.Translate()
        self.assertEqual(
            ("Hello", "ja"),
            translation_test.analyze("こんにちは"),
        )

    @mock.patch("google.cloud.translate_v2.Client", spec=True)
    def test_translation_returns_none_for_same_language(self, mock_translation):
        mock_translation.return_value.translate.return_value = {
            "translatedText": "Hello",
            "detectedSourceLanguage": "en",
            "input": "Hello",
        }
        translation_test = translation.Translate()
        self.assertIsNone(translation_test.analyze("Hello"))

    @mock.patch("google.cloud.translate_v2.Client", spec=True)
    def test_translation_raises_error_from_incorrect_input(self, mock_translation):
        translation.TRANSLATION_TARGET_LANGUAGE_CODE = "x"
        mock_translation.return_value.translate.side_effect = GoogleAPIError
        translation_test = translation.Translate()
        with self.assertRaises(translation.TranslationAPIError):
            translation_test.analyze("こんにちは")


if __name__ == "__main__":
    absltest.main()
