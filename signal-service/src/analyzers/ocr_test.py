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
"""Test that the OCR functions behave as expected."""

from unittest import mock

from absl.testing import absltest
from google.cloud.vision_v1.types.image_annotator import EntityAnnotation

from analyzers import ocr
from testing import test_case


class OCRTest(test_case.TestCase):
    def setUp(self):
        super().setUp()
        self.vision_ocr_mock = self.enter_context(
            mock.patch("google.cloud.vision.ImageAnnotatorClient", spec=True)
        )
        self.pytesseract_ocr_mock = self.enter_context(
            mock.patch("pytesseract.image_to_string", return_value="JIGSAW")
        )
        ocr.ENABLE_VISION_OCR_API = True

    def test_vision_ocr_analyze(self):
        entity_annotation = [
            EntityAnnotation(description="JIGSAW"),
            EntityAnnotation(description="NOTJIGSAW"),
        ]
        self.vision_ocr_mock.return_value.text_detection.return_value.error.message = (
            False
        )
        self.vision_ocr_mock.return_value.text_detection.return_value.text_annotations = (
            entity_annotation
        )
        vision_ocr_test = ocr.OCR()
        self.assertEqual("JIGSAW", vision_ocr_test.analyze(b""))

    def test_pytesseract_ocr_analyze(self):
        ocr.ENABLE_VISION_OCR_API = False
        img_file_path = self.root_path.joinpath("testing/testdata/jigsaw.png")
        with open(img_file_path, "rb") as img_file:
            test_image_bytes = img_file.read()
        pytesseract_ocr_test = ocr.OCR()
        self.assertEqual("JIGSAW", pytesseract_ocr_test.analyze(test_image_bytes))


if __name__ == "__main__":
    absltest.main()
