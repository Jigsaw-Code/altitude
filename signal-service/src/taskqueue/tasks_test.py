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
"""Tests for taskqueue tasks."""

import copy
import datetime
import http
import json
import os
import pathlib
from typing import Any, Dict
from unittest import mock

import requests
from absl.testing import absltest
from bson.objectid import ObjectId
from threatexchange.signal_type.pdq import PdqSignal

from analyzers import ocr, perspective, safe_search, translation
from importers import importer
from indexing.index import Index, IndexEntryMetadata, IndexMatch, IndexNotFoundError
from models import features
from models.case import Case, Review
from models.importer import Credential, ImporterConfig
from models.signal import Content, Signal, Source, Sources
from models.target import FeatureSet, Target
from taskqueue import tasks
from testing import test_case, test_entities

MOCK_SCORES = {
    "TOXICITY": 0.4,
    "SEVERE_TOXICITY": 0.1,
    "INSULT": 0.1,
    "PROFANITY": 0.1,
    "THREAT": 0.1,
    "IDENTITY_ATTACK": 0.1,
}


def _make_response(
    content: Dict[str, Any], status: int = http.HTTPStatus.OK
) -> requests.Response:
    response = requests.Response()
    response.status_code = status
    # pylint: disable=protected-access
    response._content = json.dumps(content).encode("utf-8")
    return response


class TasksTest(test_case.TestCase):
    def setUp(self):
        super().setUp()
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
            mock.patch.object(
                perspective.Perspective,
                "analyze",
                return_value={},
            )
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

        tasks.ENABLE_PERSPECTIVE_API = True
        tasks.ENABLE_SAFE_SEARCH_API = True
        tasks.ENABLE_TRANSLATION_API = True
        ocr.ENABLE_VISION_OCR_API = True
        requests_get_patch = mock.patch.object(requests, "get", autospec=True)
        self.mock_get = requests_get_patch.start()
        requests_post_patch = mock.patch.object(requests, "post", autospec=True)
        self.mock_post = requests_post_patch.start()
        self.mock_post.return_value = _make_response({})
        mock_datetime_patch = mock.patch("models.case.datetime", wraps=datetime)
        self.mock_datetime = mock_datetime_patch.start()
        self.mock_datetime.datetime.utcnow.return_value = datetime.datetime(
            2001, 5, 10, tzinfo=datetime.timezone.utc
        )

    def file_to_bytes(self, path: str):
        img_file_path = self.root_path.joinpath(path)
        with open(img_file_path, "rb") as img_file:
            return img_file.read()

    def test_generate_cases_creates_case_with_correct_signals(self):
        tasks.generate_cases(
            [["222222222222222222222222", "333333333333333333333333"], None],
            target_id="111111111111111111111111",
        )
        cases = Case.objects
        self.assertLen(cases, 1)
        self.assertCountEqual(
            [
                ObjectId("222222222222222222222222"),
                ObjectId("333333333333333333333333"),
            ],
            cases[0].signal_ids,
        )

    def test_generate_cases_creates_no_case(self):
        tasks.generate_cases([None, None, None], target_id="22222222222222222222")
        cases = Case.objects
        self.assertEmpty(cases)

    def test_generate_cases_merges_with_active_case(self):
        Case(
            target_id=ObjectId("111111111111111111111111"),
            signal_ids=[ObjectId("222222222222222222222222")],
        ).save()

        tasks.generate_cases(
            [["333333333333333333333333"], None],
            target_id="111111111111111111111111",
        )

        cases = Case.objects
        self.assertLen(cases, 1)
        self.assertCountEqual(
            [
                ObjectId("222222222222222222222222"),
                ObjectId("333333333333333333333333"),
            ],
            cases[0].signal_ids,
        )

    def test_generate_hashes_stores_pdq_hash_on_target(self):
        test_image_bytes = self.file_to_bytes("testing/testdata/logo.png")
        target = Target(
            feature_set=FeatureSet(image=features.image.Image(data=test_image_bytes))
        )
        target.save()

        tasks.generate_hashes(str(target.id))

        target.reload()
        self.assertEqual(
            "9c66cd9c49893672e671c3339a72ecf94d8c384eb06cc7924d32f07196db0d8e",
            target.feature_set.image.pdq_digest,
        )

    @mock.patch.object(
        perspective.Perspective,
        "analyze",
        return_value={
            "TOXICITY": 0.9,
            "SEVERE_TOXICITY": 0.9,
            "INSULT": 0.9,
            "PROFANITY": 0.9,
            "THREAT": 0.9,
            "IDENTITY_ATTACK": 0.9,
        },
    )
    @mock.patch.object(
        ocr.OCR,
        "analyze",
        return_value="The API was called properly.",
    )
    def test_process_ocr_returns_signal_for_passing_threshhold(self, *_):
        test_image_bytes = self.file_to_bytes("testing/testdata/jigsaw.png")
        target = Target(
            feature_set=FeatureSet(image=features.image.Image(data=test_image_bytes))
        )
        target.save()
        signal = Signal(
            content=[
                Content(
                    value="http://abc.xyz",
                    content_type=Content.ContentType.API,
                )
            ],
            sources=Sources(sources=[Source(name=Source.Name.PERSPECTIVE)]),
        )
        signal.save()

        observed_signal_ids = tasks.process_ocr(str(target.id))

        self.assertEqual(observed_signal_ids, [str(signal.id)])

    def test_process_ocr_returns_none_for_low_scores(self):
        test_image_bytes = self.file_to_bytes("testing/testdata/jigsaw.png")
        target = Target(
            feature_set=FeatureSet(image=features.image.Image(data=test_image_bytes))
        )
        target.save()
        self.assertIsNone(tasks.process_ocr(str(target.id)))

    @mock.patch.object(
        ocr.OCR,
        "analyze",
        return_value="The API was called properly.",
    )
    @mock.patch.object(
        translation.Translate, "analyze", return_value=("Translation complete.", "ja")
    )
    @mock.patch.object(perspective.Perspective, "analyze", return_value=MOCK_SCORES)
    def test_process_ocr_text_stores_proper_results_on_target(self, *_):
        test_image_bytes = self.file_to_bytes("testing/testdata/jigsaw.png")
        target = Target(
            feature_set=FeatureSet(image=features.image.Image(data=test_image_bytes))
        )
        target.save()

        tasks.process_ocr(str(target.id))

        target.reload()
        self.assertEqual(
            "The API was called properly.",
            target.feature_set.image.ocr_text.data,
        )
        self.assertEqual(
            "Translation complete.",
            target.feature_set.image.ocr_text.translated_data,
        )
        self.assertEqual(
            "ja",
            target.feature_set.image.ocr_text.detected_language_code,
        )
        self.assertLen(
            target.feature_set.image.ocr_text.perspective_scores,
            len(perspective.ATTRIBUTES),
        )
        self.assertEqual(
            0.4, target.feature_set.image.ocr_text.perspective_scores["TOXICITY"]
        )

    def test_empty_ocr_text(self):
        test_image_bytes = self.file_to_bytes("testing/testdata/jigsaw.png")
        target = Target(
            feature_set=FeatureSet(image=features.image.Image(data=test_image_bytes))
        )
        target.save()

        tasks.process_ocr(str(target.id))

        target.reload()
        self.assertIsNone(target.feature_set.image.ocr_text)

    @mock.patch.object(
        ocr.OCR,
        "analyze",
        return_value="The API was called properly.",
    )
    @mock.patch.object(
        translation.Translate, "analyze", return_value=("Translation complete.", "ja")
    )
    @mock.patch.object(
        perspective.Perspective, "analyze", side_effect=perspective.Error
    )
    def test_process_ocr_text_saves_no_scores_when_api_raises(self, *_):
        """Tests that we gracefully handle errors thrown by the Perspective analyzer."""
        test_image_bytes = self.file_to_bytes("testing/testdata/jigsaw.png")
        target = Target(
            feature_set=FeatureSet(image=features.image.Image(data=test_image_bytes))
        )
        target.save()

        tasks.process_ocr(str(target.id))

        target.reload()
        self.assertEmpty(target.feature_set.image.ocr_text.perspective_scores)

    def test_process_safe_search_returns_signal_for_passing_threshhold(self):
        test_image_bytes = self.file_to_bytes("testing/testdata/jigsaw.png")
        target = Target(
            feature_set=FeatureSet(image=features.image.Image(data=test_image_bytes))
        )
        target.save()
        signal = Signal(
            content=[
                Content(
                    value="http://abc.xyz",
                    content_type=Content.ContentType.API,
                )
            ],
            sources=Sources(sources=[Source(name=Source.Name.SAFE_SEARCH)]),
        )
        signal.save()

        observed_signal_ids = tasks.process_safe_search(str(target.id))

        self.assertEqual(observed_signal_ids, [str(signal.id)])

    @mock.patch.object(
        safe_search.SafeSearch,
        "analyze",
        return_value={"adult": 1, "spoof": 1, "medical": 1, "violence": 1, "racy": 1},
    )
    def test_process_safe_search_returns_none_for_low_scores(self, _):
        test_image_bytes = self.file_to_bytes("testing/testdata/jigsaw.png")
        target = Target(
            feature_set=FeatureSet(image=features.image.Image(data=test_image_bytes))
        )
        target.save()
        self.assertIsNone(tasks.process_safe_search(str(target.id)))

    def test_query_indices_returns_matches(self):
        Index.STORAGE_PATH_DIR = pathlib.Path(self.create_tempdir())
        signal = Signal(
            content=[
                Content(
                    value="000000000000000000000000000000000000000000000000000000000000ffff",
                    content_type=Content.ContentType.HASH_PDQ,
                )
            ],
            sources=Sources(sources=[Source()]),
        )
        signal.save()
        Signal(
            content=[
                Content(
                    value="0000000000000000000000000000000000000000000000000000000000000000",
                    content_type=Content.ContentType.HASH_PDQ,
                )
            ],
            sources=Sources(sources=[Source()]),
        ).save()

        tasks.rebuild_indices()

        matches = tasks.query_indices(
            "000000000000000000000000000000000000000000000000000000000000ffff",
            target_id="123",
        )

        self.assertLen(matches, 1)
        self.assertEqual(
            str(signal.id), IndexMatch.deserialize(matches[0]).metadata.signal_id
        )

    def test_process_matches_returns_signal_list_containing_each_match(self):
        matches = [
            IndexMatch(
                query="foo",
                metadata=IndexEntryMetadata(signal_id="111111111111111111111111"),
            ).serialize(),
            IndexMatch(
                query="foo",
                metadata=IndexEntryMetadata(signal_id="222222222222222222222222"),
            ).serialize(),
        ]

        result = tasks.process_matches(matches, target_id="333333333333333333333333")

        self.assertLen(result, 2)
        self.assertEqual("111111111111111111111111", result[0])
        self.assertEqual("222222222222222222222222", result[1])

    def test_process_matches_returns_empty_signals_list(self):
        tasks.process_matches([], target_id="444444444444444444444444")

        self.assertIsNone(
            tasks.process_matches([], target_id="444444444444444444444444")
        )

    def test_process_new_signals_creates_case_for_not_hashed_url_signal(self):
        self.mock_get.return_value.content = None
        signal1 = Signal(
            content=[
                Content(
                    value="http://abc.xyz",
                    content_type=Content.ContentType.URL,
                )
            ],
            sources=Sources(sources=[Source()]),
        )
        signal1.save()
        signal2 = Signal(
            content=[
                Content(
                    value="f0f0f0f0f0f0f0f0f0f0f0f0f0f0f0f0f0f0f0f0f0f0f0f0f0f0f0f0f0f0f0f0",
                    content_type=Content.ContentType.HASH_PDQ,
                )
            ],
            sources=Sources(sources=[Source()]),
        )
        signal2.save()

        tasks.process_new_signals([str(signal1.id), str(signal2.id)])

        cases = Case.objects
        self.assertLen(cases, 1)
        self.assertEqual(signal1.id, cases[0].signal_ids[0])

    def test_process_new_signals_hashes_url_signal_and_no_case_creation(self):
        test_image_bytes = self.file_to_bytes("testing/testdata/logo.png")
        self.mock_get.return_value.content = test_image_bytes

        signal = Signal(
            content=[
                Content(
                    value="http://abc.xyz",
                    content_type=Content.ContentType.URL,
                )
            ],
            sources=Sources(sources=[Source()]),
        )
        signal.save()

        tasks.process_new_signals([str(signal.id)])

        signal.reload()

        contents = signal.content
        self.assertLen(contents, 2)
        self.assertEqual(
            contents[1].value,
            "9c66cd9c49893672e671c3339a72ecf94d8c384eb06cc7924d32f07196db0d8e",
        )
        self.assertEqual(contents[1].content_type, Content.ContentType.HASH_PDQ)

        cases = Case.objects
        self.assertEmpty(cases)

    def test_rebuild_indices_creates_index(self):
        with self.assertRaises(IndexNotFoundError):
            Index.load(index_type=PdqSignal)
        Signal(
            content=[
                Content(
                    value="f0f0f0f0f0f0f0f0f0f0f0f0f0f0f0f0f0f0f0f0f0f0f0f0f0f0f0f0f0f0f0f0",
                    content_type=Content.ContentType.HASH_PDQ,
                )
            ],
            sources=Sources(sources=[Source()]),
        ).save()

        tasks.rebuild_indices()

        index = Index.load(index_type=PdqSignal)
        self.assertIsNotNone(index)
        self.assertLen(index, 1)

    def test_publish_review_on_draft_updates_case_and_review_states(self):
        case = copy.deepcopy(test_entities.TEST_CASE)
        case.target_id = copy.deepcopy(test_entities.TEST_TARGET).save().id
        review = case.review_history[0]
        review.state = Review.State.DRAFT
        case.save()

        tasks.publish_review(str(case.id), str(review.id))

        case.reload()
        self.assertEqual(case.review_history[0].state, Review.State.PUBLISHED)
        self.assertEqual(case.state, Case.State.RESOLVED)

    def test_publish_review_on_published_is_a_noop(self):
        case = copy.deepcopy(test_entities.TEST_CASE)
        review = case.review_history[0]
        review.state = Review.State.PUBLISHED
        case.save()

        tasks.publish_review(str(case.id), str(review.id))

        case.reload()
        self.assertEqual(case.review_history[0].state, Review.State.PUBLISHED)
        self.assertEqual(case.state, Case.State.RESOLVED)
        self.mock_post.assert_not_called()

    def test_publish_review_delivers_review_to_receiver_webhook(self):
        tasks.ACTION_RECEIVER_URL = "http://test-url/"
        case = copy.deepcopy(test_entities.TEST_CASE_RESOLVED_APPROVAL)
        case.target_id = copy.deepcopy(test_entities.TEST_TARGET).save().id
        review = case.review_history[0]
        review.state = Review.State.DRAFT
        case.save()

        tasks.publish_review(str(case.id), str(review.id))

        self.mock_post.assert_called_with(
            "http://test-url/",
            json={
                "client_context": "abc-context",
                "decision": "APPROVE",
                "decision_time": "2000-12-26T00:00:00+00:00",
            },
            timeout=mock.ANY,
        )
        case.reload()
        review.delivery_status = Review.DeliveryStatus.ACCEPTED

    @mock.patch("taskqueue.tasks.datetime", wraps=datetime)
    def test_publish_review_without_receiver_webhook_logs_to_file(self, mock_datetime):
        # The filename will be the current date. We mock it so we can test the correct filename.
        mock_datetime.date.today.return_value = datetime.date(2010, 2, 17)
        tasks.ACTION_RECEIVER_URL = None
        case = copy.deepcopy(test_entities.TEST_CASE_RESOLVED_APPROVAL)
        case.target_id = copy.deepcopy(test_entities.TEST_TARGET).save().id
        review = case.review_history[0]
        review.state = Review.State.DRAFT
        case.save()

        tasks.publish_review(str(case.id), str(review.id))

        self.mock_post.assert_not_called()
        output_dir = os.path.join(tasks.LOG_FILEPATH + "/verdict-notifier")
        observed_files = os.listdir(output_dir)
        self.assertEqual(["20100217.txt"], observed_files)
        with open(
            os.path.join(output_dir, observed_files[0]), encoding="utf-8"
        ) as log_file:
            self.assertEqual(
                log_file.readline(),
                '{"client_context": "abc-context", "decision": "APPROVE", '
                '"decision_time": "2000-12-26T00:00:00+00:00"}\n',
            )

    @mock.patch("celery.app.task.Task.request")
    def test_deliver_review_failing_receiver_throws_exception(self, mock_request):
        tasks.ACTION_RECEIVER_URL = "http://test-url/"
        case = copy.deepcopy(test_entities.TEST_CASE_RESOLVED_APPROVAL)
        case.target_id = copy.deepcopy(test_entities.TEST_TARGET).save().id
        review = case.review_history[0]
        review.state = Review.State.DRAFT
        case.save()
        self.mock_post.return_value = _make_response({}, http.HTTPStatus.NOT_FOUND)

        mock_request.retries = 3
        with self.assertRaises(requests.exceptions.HTTPError):
            tasks.deliver_review(str(case.id), str(review.id))

        self.assertEqual(
            Case.objects.get(id=case.id)
            .review_history.get(id=review.id)
            .delivery_status,
            Review.DeliveryStatus.PENDING,
        )

    @mock.patch("celery.app.task.Task.request")
    def test_deliver_review_failing_receiver_webhook_updates_delivery_status(
        self, mock_request
    ):
        case = copy.deepcopy(test_entities.TEST_CASE_RESOLVED_APPROVAL)
        case.target_id = copy.deepcopy(test_entities.TEST_TARGET).save().id
        review = case.review_history[0]
        review.state = Review.State.DRAFT
        case.save()
        self.mock_post.return_value = _make_response({}, http.HTTPStatus.NOT_FOUND)

        mock_request.retries = 5
        tasks.deliver_review(str(case.id), str(review.id))

        self.assertEqual(
            Case.objects.get(id=case.id)
            .review_history.get(id=review.id)
            .delivery_status,
            Review.DeliveryStatus.FAILED,
        )

    @mock.patch.object(perspective.Perspective, "analyze")
    def test_generate_perspective_scores(self, mock_get_scores):
        """Tests 'generate_perspective_scores' by mocking perspective.get_response."""
        mock_get_scores.return_value = MOCK_SCORES
        target = Target(
            create_time=datetime.datetime(2011, 6, 12, tzinfo=datetime.timezone.utc),
            client_context="abc",
            feature_set=FeatureSet(text=features.text.Text(data="Test Message")),
        )
        target.save()

        tasks.generate_perspective_scores(str(target.id))

        target.reload()
        self.assertEqual(target.feature_set.text.perspective_scores, MOCK_SCORES)

    @mock.patch.object(perspective.Perspective, "analyze")
    def test_generate_perspective_scores_skips_scoring_if_api_disabled(self, _):
        """Tests that no perspective scores are requested if the API is disabled."""
        tasks.ENABLE_PERSPECTIVE_API = False
        target = Target(
            create_time=datetime.datetime(2011, 6, 12, tzinfo=datetime.timezone.utc),
            client_context="abc",
            feature_set=FeatureSet(text=features.text.Text(data="Test Message")),
        )
        target.save()

        tasks.generate_perspective_scores(str(target.id))

        target.reload()
        self.assertEmpty(target.feature_set.text.perspective_scores)

    @mock.patch.object(perspective.Perspective, "analyze")
    def test_generate_perspective_scores_saves_no_scores_when_api_raises(
        self, mock_get_scores
    ):
        """Tests that we gracefully handle errors thrown by the Perspective analyzer."""
        mock_get_scores.side_effect = perspective.Error
        target = Target(
            create_time=datetime.datetime(2011, 6, 12, tzinfo=datetime.timezone.utc),
            client_context="abc",
            feature_set=FeatureSet(text=features.text.Text(data="Test Message")),
        )
        target.save()

        tasks.generate_perspective_scores(str(target.id))

        target.reload()
        self.assertEmpty(target.feature_set.text.perspective_scores)

    def test_process_perspective_scores(self):
        score1 = {
            "TOXICITY": 0.5,
            "INSULT": 0.4,
            "THREAT": 0.7,
        }
        score2 = {
            "TOXICITY": 0.2,
            "INSULT": 0.4,
            "THREAT": 0.5,
        }
        target1 = Target(
            create_time=datetime.datetime(2011, 6, 12, tzinfo=datetime.timezone.utc),
            client_context="abc",
            feature_set=FeatureSet(
                text=features.text.Text(data="Test Message", perspective_scores=score1)
            ),
        )
        target1.save()
        target2 = Target(
            create_time=datetime.datetime(2011, 6, 12, tzinfo=datetime.timezone.utc),
            client_context="abc",
            feature_set=FeatureSet(
                text=features.text.Text(data="Test Message", perspective_scores=score2)
            ),
        )
        target2.save()

        signal = Signal(
            content=[
                Content(
                    value="http://abc.xyz",
                    content_type=Content.ContentType.API,
                )
            ],
            sources=Sources(sources=[Source(name=Source.Name.PERSPECTIVE)]),
        )
        signal.save()

        tasks.process_perspective_scores(score1, target1.id)
        tasks.process_perspective_scores(score2, target2.id)

        cases = Case.objects
        self.assertLen(cases, 1)
        self.assertEqual(target1.id, cases[0].target_id)

    @mock.patch.object(
        ocr.OCR,
        "analyze",
        return_value="OCR text was created.",
    )
    def test_disabled_perspective_api_on_process_ocr(self, _):
        tasks.ENABLE_PERSPECTIVE_API = False
        test_image_bytes = self.file_to_bytes("testing/testdata/jigsaw.png")
        target = Target(
            feature_set=FeatureSet(image=features.image.Image(data=test_image_bytes))
        )
        target.save()

        tasks.process_ocr(str(target.id))

        target.reload()
        self.assertEqual(
            "OCR text was created.",
            target.feature_set.image.ocr_text.data,
        )

        self.assertEmpty(target.feature_set.image.ocr_text.perspective_scores)

    @mock.patch.object(
        ocr.OCR,
        "analyze",
        return_value="OCR text was created.",
    )
    def test_disabled_translation_api_on_process_ocr(self, _):
        tasks.ENABLE_TRANSLATION_API = False
        test_image_bytes = self.file_to_bytes("testing/testdata/jigsaw.png")
        target = Target(
            feature_set=FeatureSet(image=features.image.Image(data=test_image_bytes))
        )
        target.save()

        tasks.process_ocr(str(target.id))

        target.reload()
        self.assertEqual(
            "OCR text was created.",
            target.feature_set.image.ocr_text.data,
        )

        self.assertIsNone(target.feature_set.image.ocr_text.translated_data)
        self.assertIsNone(target.feature_set.image.ocr_text.detected_language_code)

    @mock.patch("taskqueue.tasks.datetime", wraps=datetime)
    @mock.patch.object(
        ImporterConfig,
        "to_importer",
    )
    def test_export_signal_diagnostics(self, mock_to_importer, mock_datetime):
        tcap_api_config = ImporterConfig(
            state=ImporterConfig.State.ACTIVE,
            type=ImporterConfig.Type.TCAP_API,
            diagnostics_state=ImporterConfig.State.ACTIVE,
            credential=Credential(identifier="username", token="password"),
        )
        tcap_api_config.save()
        threat_exchange_config = ImporterConfig(
            state=ImporterConfig.State.ACTIVE,
            type=ImporterConfig.Type.THREAT_EXCHANGE_API,
            diagnostics_state=ImporterConfig.State.ACTIVE,
            credential=Credential(identifier="username", token="password"),
        )
        threat_exchange_config.save()
        mock_datetime.datetime.now.return_value = datetime.date(2010, 2, 17)
        mock_importer = mock.create_autospec(importer.Importer)
        mock_to_importer.return_value = mock_importer
        tasks.export_signal_diagnostic(ImporterConfig.Type.THREAT_EXCHANGE_API)
        mock_importer.send_diagnostics.assert_called_with(
            datetime.date(2010, 2, 10), datetime.date(2010, 2, 17)
        )


if __name__ == "__main__":
    absltest.main()
