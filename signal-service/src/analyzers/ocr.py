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

"""Analyzer to provide Optical Character Recognition (OCR) functionality.

If the `ENABLE_VISION_OCR_API` environment variable is set, we use the Cloud Vision API
(see https://cloud.google.com/vision/docs/ocr).
Otherwise, we use the local Tesseract-OCR Engine
(see https://pypi.org/project/pytesseract/).
"""

import os
from io import BytesIO

import pytesseract
from google.cloud import vision
from PIL import Image

from analyzers import analyzer

# Whether to enable the Vision OCR API. If enabled, it will send target data to
# the OCR API and extract text found within. If disabled, it will use the Tesseract
# OCR engine to extract text.
ENABLE_VISION_OCR_API = os.environ.get("ENABLE_VISION_OCR_API", "").lower() == "true"


class Error(analyzer.Error):
    """Base class for exceptions in this module."""


class VisionOCRAPIError(Error):
    """Error message for Vision OCR API response."""


class OCR(analyzer.Analyzer):
    """Class for utilizing the OCR API in Cloud Vision or the Pytesseract Engine."""

    def analyze(self, data: bytes) -> str:
        """Detects text in the file.

        Args:
            data: The content bytes that will be processed either
            using Cloud Vision API or Pytesseract Engine.
        Returns:
            A string containing the full text extracted from the image if
            any was found.
        Raises:
            VisionOCRAPIError: An error ocurred with the response from Vision OCR.
        """
        if not ENABLE_VISION_OCR_API:
            return pytesseract.image_to_string(Image.open(BytesIO(data)))

        client = vision.ImageAnnotatorClient(credentials=self.credentials)

        image = vision.Image(content=data)

        response = client.text_detection(image=image)  # pylint:disable=no-member
        texts = response.text_annotations

        if response.error.message:
            raise VisionOCRAPIError(
                f"{response.error.message}\nFor more info on error messages, check: "
                "https://cloud.google.com/apis/design/errors"
            )
        if texts:
            return texts[0].description
        return ""
