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
"""Tests for the Target API."""

import base64
import datetime
import http
from unittest import mock

from absl.testing import absltest
from bson import ObjectId

from analyzers import ocr, perspective, safe_search, translation
from api.target import bp as target_bp
from models import features
from models.target import FeatureSet, Target
from taskqueue import tasks
from testing.test_case import ApiTestCase


# pylint: disable-next=too-many-instance-attributes
class TargetAPITest(ApiTestCase):
    blueprint = target_bp

    def setUp(self):
        super().setUp()

        tasks.ENABLE_PERSPECTIVE_API = True
        tasks.ENABLE_SAFE_SEARCH_API = True
        tasks.ENABLE_TRANSLATION_API = True
        ocr.ENABLE_VISION_OCR_API = True

        self.ocr_mock = self.enter_context(
            mock.patch.object(
                ocr.OCR,
                "analyze",
                return_value="",
            )
        )

        self.translation_mock = self.enter_context(
            mock.patch.object(
                translation.Translate,
                "analyze",
                return_value=None,
            )
        )

        self.perspective_mock = self.enter_context(
            mock.patch.object(perspective.Perspective, "analyze", return_value={})
        )

        self.safe_search_mock = self.enter_context(
            mock.patch.object(
                safe_search.SafeSearch,
                "analyze",
                return_value={
                    "adult": 3,
                    "spoof": 3,
                    "medical": 3,
                    "violence": 3,
                    "racy": 3,
                },
            )
        )
        # Mocking is to avoid error with synchronous subtasks
        # https://github.com/celery/celery/issues/4661
        self.task_join_mock = self.enter_context(
            mock.patch("celery.app.task.denied_join_result")
        )
        self.task_join_mock.__enter__.return_value = None

        self.test_text_b64 = base64.b64encode(b"Test message")
        img_file_path = self.root_path.joinpath("testing/testdata/logo.png")
        with open(img_file_path, "rb") as img_file:
            self.test_image_b64 = base64.b64encode(img_file.read())

        img_with_text_path = self.root_path.joinpath("testing/testdata/jigsaw.png")
        with open(img_with_text_path, "rb") as img_text_file:
            self.test_text_image_b64 = base64.b64encode(img_text_file.read())

    def test_create_invalid_img_target(self):
        client_context = "abc"

        self.post(
            "/targets/",
            json={
                "client_context": client_context,
                "content_type": "IMAGE",
                "content_bytes": self.test_text_b64,
            },
            expected_status=http.HTTPStatus.BAD_REQUEST,
            expected_message="Unable to process image data",
        )

    @mock.patch.object(
        translation.Translate, "analyze", return_value=("Translation complete.", "ja")
    )
    def test_create_text_target(self, _):
        client_context = "abc"

        response = self.post(
            "/targets/",
            json={
                "title": "Title",
                "description": "description",
                "views": 5,
                "creator": {"ip_address": "1.2.3.4"},
                "client_context": client_context,
                "content_type": "TEXT",
                "content_bytes": self.test_text_b64,
            },
            expected_status=http.HTTPStatus.CREATED,
        )

        self.assertEqual(1, Target.objects.count())
        target = Target.objects.get(id=response.json["id"])
        self.assertEqual(client_context, target.client_context)
        self.assertEqual("Test message", target.feature_set.text.data)
        self.assertEqual(
            "Translation complete.", target.feature_set.text.translated_data
        )
        self.assertEqual("ja", target.feature_set.text.detected_language_code)

    def test_create_text_target_with_sparse_data(self):
        client_context = "abc"

        response = self.post(
            "/targets/",
            json={
                "creator": {},
                "client_context": client_context,
                "content_type": "TEXT",
                "content_bytes": self.test_text_b64,
            },
            expected_status=http.HTTPStatus.CREATED,
        )

        self.assertEqual(1, Target.objects.count())
        target = Target.objects.get(id=response.json["id"])
        self.assertEqual(client_context, target.client_context)
        self.assertIsNone(target.feature_set.text.title)
        self.assertIsNone(target.feature_set.text.description)
        self.assertIsNone(target.feature_set.creator)
        self.assertIsNone(target.feature_set.text.translated_data)
        self.assertIsNone(target.feature_set.text.detected_language_code)

    def test_create_img_target(self):
        client_context = "abc"

        response = self.post(
            "/targets/",
            json={
                "title": "Title",
                "description": "description",
                "views": 5,
                "creator": {"ip_address": "1.2.3.4"},
                "client_context": client_context,
                "content_type": "IMAGE",
                "content_bytes": self.test_image_b64,
            },
            expected_status=http.HTTPStatus.CREATED,
        )

        self.assertEqual(1, Target.objects.count())
        target = Target.objects.get(id=response.json["id"])
        self.assertEqual(client_context, target.client_context)

    def test_create_target_hashes_image(self):
        self.post(
            "/targets/",
            json={
                "content_type": "IMAGE",
                "content_bytes": self.test_image_b64,
            },
            expected_status=http.HTTPStatus.CREATED,
        )

        target = Target.objects.get()
        self.assertEqual(
            "9c66cd9c49893672e671c3339a72ecf94d8c384eb06cc7924d32f07196db0d8e",
            target.feature_set.image.pdq_digest,
        )

    def test_get_target_invalid_target_id_raises(self):
        self.get(
            "/targets/foobar",
            expected_status=http.HTTPStatus.NOT_FOUND,
            expected_message="Target foobar not found.",
        )

    def test_get_target_nonexistent_target_id_raises(self):
        missing_id = str(ObjectId())
        self.get(
            f"/targets/{missing_id}",
            expected_status=http.HTTPStatus.NOT_FOUND,
            expected_message=f"Target {missing_id} not found.",
        )

    def test_get_target_by_identifier(self):
        client_context = "abc"
        target = Target(
            create_time=datetime.datetime(2011, 6, 12, tzinfo=datetime.timezone.utc),
            client_context=client_context,
            feature_set=FeatureSet(
                creator=features.user.User(ip_address="1.2.3.4"),
                engagement_metrics=features.engagement.Engagement(views=5),
                image=features.image.Image(
                    title="Title", description="description", data=b"imagebytes"
                ),
            ),
        )
        target.save()

        response = self.get(f"/targets/{target.id}")

        self.assertEqual(
            {
                "id": str(target.id),
                "create_time": "2011-06-12T00:00:00+00:00",
                "client_context": client_context,
                "title": "Title",
                "description": "description",
                "creator": {"ip_address": "1.2.3.4"},
                "content_bytes": mock.ANY,
                "views": 5,
                "safe_search_scores": {
                    "adult": "UNKNOWN",
                    "spoof": "UNKNOWN",
                    "medical": "UNKNOWN",
                    "violence": "UNKNOWN",
                    "racy": "UNKNOWN",
                },
            },
            response.json,
        )

    def test_get_target_sparse_data(self):
        client_context = "abc"
        target = Target(
            create_time=datetime.datetime(2011, 6, 12, tzinfo=datetime.timezone.utc),
            client_context=client_context,
            feature_set=FeatureSet(
                creator=features.user.User(),
                engagement_metrics=features.engagement.Engagement(views=5),
                image=features.image.Image(data=b"imagebytes"),
            ),
        )
        target.save()

        response = self.get(f"/targets/{target.id}")

        self.assertEqual(
            {
                "id": str(target.id),
                "create_time": "2011-06-12T00:00:00+00:00",
                "client_context": client_context,
                "content_bytes": mock.ANY,
                "views": 5,
                "safe_search_scores": {
                    "adult": "UNKNOWN",
                    "spoof": "UNKNOWN",
                    "medical": "UNKNOWN",
                    "violence": "UNKNOWN",
                    "racy": "UNKNOWN",
                },
            },
            response.json,
        )

    def test_update_target_invalid_target_id_raises(self):
        self.patch(
            "/targets/foobar",
            expected_status=http.HTTPStatus.NOT_FOUND,
            expected_message="Target foobar not found.",
        )

    def test_update_target_nonexistent_target_id_raises(self):
        missing_id = str(ObjectId())
        self.patch(
            f"/targets/{missing_id}",
            expected_status=http.HTTPStatus.NOT_FOUND,
            expected_message=f"Target {missing_id} not found.",
        )

    def test_update_target_invalid_fields_raises(self):
        client_context = "abc"
        target = Target(
            create_time=datetime.datetime(2011, 6, 12, tzinfo=datetime.timezone.utc),
            client_context=client_context,
            feature_set=FeatureSet(image=features.image.Image(data=b"imagebytes")),
        )
        target.save()

        self.patch(
            f"/targets/{target.id}",
            json={
                "create_time": "2011-06-12T00:00:00+00:00",
            },
            expected_status=http.HTTPStatus.BAD_REQUEST,
        )

    def test_update_target(self):
        client_context = "abc"
        target = Target(
            create_time=datetime.datetime(2011, 6, 12, tzinfo=datetime.timezone.utc),
            client_context=client_context,
            feature_set=FeatureSet(
                creator=features.user.User(ip_address="1.2.3.4"),
                engagement_metrics=features.engagement.Engagement(views=5),
                image=features.image.Image(
                    title="Title",
                    description="description",
                    data=b"imagebytes",
                ),
            ),
        )
        target.save()

        response = self.patch(
            f"/targets/{target.id}",
            json={
                "title": "Title 2.0",
                "description": "Description 2.0",
                "creator": {"ip_address": "1.2.3.5"},
                "views": 10,
                "client_context": client_context,
            },
            expected_status=http.HTTPStatus.OK,
        )

        self.assertEqual(
            {
                "id": str(target.id),
                "create_time": "2011-06-12T00:00:00+00:00",
                "client_context": client_context,
                "title": "Title 2.0",
                "description": "Description 2.0",
                "creator": {"ip_address": "1.2.3.5"},
                "content_bytes": mock.ANY,
                "views": 10,
                "safe_search_scores": {
                    "adult": "UNKNOWN",
                    "spoof": "UNKNOWN",
                    "medical": "UNKNOWN",
                    "violence": "UNKNOWN",
                    "racy": "UNKNOWN",
                },
            },
            response.json,
        )

        self.assertEqual(1, Target.objects.count())
        target = Target.objects.get(id=target.id)
        self.assertEqual("Title 2.0", target.feature_set.image.title)
        self.assertEqual("Description 2.0", target.feature_set.image.description)
        self.assertEqual("1.2.3.5", target.feature_set.creator.ip_address)
        self.assertEqual(10, target.feature_set.engagement_metrics.views)

    @mock.patch.object(
        ocr.OCR,
        "analyze",
        return_value="The API was called properly.",
    )
    @mock.patch.object(
        translation.Translate,
        "analyze",
    )
    def test_text_in_ocr(self, mock_translate, _):
        mock_translate.return_value = ("Translation complete.", "ja")
        client_context = "def"
        response_text = self.post(
            "/targets/",
            json={
                "client_context": client_context,
                "content_type": "IMAGE",
                "content_bytes": self.test_text_image_b64,
            },
            expected_status=http.HTTPStatus.CREATED,
        )

        target = Target.objects.get(id=response_text.json["id"])
        self.assertEqual(
            "The API was called properly.", target.feature_set.image.ocr_text.data
        )
        self.assertEqual(
            "Translation complete.",
            target.feature_set.image.ocr_text.translated_data,
        )
        self.assertEqual(
            "ja",
            target.feature_set.image.ocr_text.detected_language_code,
        )

    def test_safe_search_data(self):
        client_context = "def"

        response_text = self.post(
            "/targets/",
            json={
                "client_context": client_context,
                "content_type": "IMAGE",
                "content_bytes": self.test_text_image_b64,
            },
            expected_status=http.HTTPStatus.CREATED,
        )

        target = Target.objects.get(id=response_text.json["id"])
        self.assertEqual(3, target.feature_set.image.adult_likelihood)
        self.assertEqual(3, target.feature_set.image.spoof_likelihood)
        self.assertEqual(3, target.feature_set.image.medical_likelihood)
        self.assertEqual(3, target.feature_set.image.violence_likelihood)
        self.assertEqual(3, target.feature_set.image.racy_likelihood)


if __name__ == "__main__":
    absltest.main()
