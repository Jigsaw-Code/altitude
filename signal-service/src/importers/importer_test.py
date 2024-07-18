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
"""Test that the Signal Importer behaves as expected."""

import copy
import datetime
from typing import Iterable
from unittest import mock

from importers import importer
from models.case import Case, Review
from models.job import Job
from models.signal import Content, Signal, Source, Sources
from testing import test_case
from testing.test_entities import (
    TEST_CASE_RESOLVED_APPROVAL,
    TEST_CASE_RESOLVED_BLOCKED,
    TEST_SIGNAL,
)

SIGNAL_1 = Signal(
    sources=Sources(sources=[Source()]),
    content=[Content(value="abc.xyz", content_type=Content.ContentType.URL)],
)
SIGNAL_2 = Signal(
    sources=Sources(sources=[Source()]),
    content=[Content(value="hello.com", content_type=Content.ContentType.URL)],
)
SIGNAL_3 = Signal(
    sources=Sources(sources=[Source()]),
    content=[Content(value="foo.bar", content_type=Content.ContentType.URL)],
)
SIGNAL_4 = Signal(
    sources=Sources(sources=[Source()]),
    content=[Content(value="hello2.com", content_type=Content.ContentType.URL)],
)
SIGNAL_5 = Signal(
    sources=Sources(sources=[Source(), Source()]),
    content=[Content(value="abc.xyz", content_type=Content.ContentType.URL)],
)


class TestImporterWithPrecheck(importer.Importer):
    def _get_data(self):
        pass

    def pre_check(self):
        pass

    def _send_decisions(self, decisions: Iterable[tuple[str, Review.Decision]]) -> None:
        pass

    def get_decisions(self, start: datetime.datetime, end: datetime.datetime):
        return self._get_decisions(start, end)


class ImporterLibTest(test_case.TestCase):
    def test_creating_importer_starts_job(self):
        class TestImporter(TestImporterWithPrecheck):
            def _get_data(self):
                yield copy.deepcopy(SIGNAL_1), importer.Action.UPDATE_OR_INSERT

        # We need to create an unused variable here so the `Importer` object doesn't
        # immediately get destroyed, which would "stop" the job.
        _ = TestImporter(Job.JobSource.UNKNOWN)  # pylint: disable=unused-variable

        job = Job.objects.get()
        self.assertEqual(Job.JobType.SIGNAL_IMPORT, job.type)
        self.assertEqual(Job.JobSource.UNKNOWN, job.source)
        self.assertEqual(Job.JobStatus.IN_PROGRESS, job.status)

    def test_job_deleted_on_failure(self):
        class TestImporter(TestImporterWithPrecheck):
            def _get_data(self):
                yield copy.deepcopy(SIGNAL_1), importer.Action.UPDATE_OR_INSERT

        test_importer = TestImporter(Job.JobSource.UNKNOWN)

        with (
            mock.patch.object(test_importer, "_run", side_effect=ValueError),
            self.assertRaises(ValueError),
        ):
            list(test_importer.run(20))

        self.assertEqual(
            1, Job.objects.count(), "Job failure should not have created a new job"
        )
        job = Job.objects.get()
        self.assertEqual(Job.JobStatus.FAILURE, job.status)

    def test_job_deleted_on_destruction(self):
        class TestImporter(TestImporterWithPrecheck):
            def _get_data(self):
                yield copy.deepcopy(SIGNAL_1), importer.Action.UPDATE_OR_INSERT

        test_importer = TestImporter(Job.JobSource.UNKNOWN)

        del test_importer

        self.assertEqual(
            1, Job.objects.count(), "Job deletion should not have created a new job"
        )
        job = Job.objects.get()
        self.assertEqual(Job.JobStatus.UNKNOWN, job.status)

    def test_job_updated_on_successful_run(self):
        class TestImporter(TestImporterWithPrecheck):
            def _get_data(self):
                yield copy.deepcopy(SIGNAL_1), importer.Action.UPDATE_OR_INSERT
                yield copy.deepcopy(SIGNAL_2), importer.Action.UPDATE_OR_INSERT

        list(TestImporter(Job.JobSource.UNKNOWN).run(20))

        job = Job.objects.get()
        self.assertEqual(Job.JobStatus.SUCCESS, job.status)
        self.assertEqual(2, job.import_size)
        self.assertEqual(0, job.update_size)
        self.assertEqual(0, job.delete_size)

    def test_run_successfully_imports_data(self):
        class TestImporter(TestImporterWithPrecheck):
            def _get_data(self):
                yield copy.deepcopy(SIGNAL_1), importer.Action.UPDATE_OR_INSERT
                yield copy.deepcopy(SIGNAL_2), importer.Action.UPDATE_OR_INSERT

        list(TestImporter(Job.JobSource.UNKNOWN).run(20))

        self.assertEqual(2, Signal.objects.count())
        signals = tuple(Signal.objects)
        self.assertEqual(SIGNAL_1, signals[0])
        self.assertEqual(SIGNAL_2, signals[1])

    def test_run_successfully_returns_imported_identifiers_in_chunks(self):
        class TestImporter(TestImporterWithPrecheck):
            def _get_data(self):
                yield copy.deepcopy(SIGNAL_1), importer.Action.UPDATE_OR_INSERT
                yield copy.deepcopy(SIGNAL_2), importer.Action.UPDATE_OR_INSERT
                yield copy.deepcopy(SIGNAL_3), importer.Action.DELETE
                yield copy.deepcopy(SIGNAL_4), importer.Action.UPDATE_OR_INSERT

        result = list(TestImporter(Job.JobSource.UNKNOWN).run(2))

        self.assertLen(result, 2)
        self.assertLen(result[0], 2)
        self.assertLen(result[1], 1)

    def test_run_successfully_redacts_data(self):
        class TestImporter(TestImporterWithPrecheck):
            def _get_data(self):
                yield copy.deepcopy(SIGNAL_1), importer.Action.DELETE

        signal = copy.deepcopy(SIGNAL_1)
        signal.save()

        list(TestImporter(Job.JobSource.UNKNOWN).run(20))

        signal.reload()
        self.assertTrue(signal.sources.sources[0].is_redacted)
        self.assertEqual("[REDACTED]", signal.content[0].value)

    def test_run_skips_redacting_data_if_signal_not_found(self):
        class TestImporter(TestImporterWithPrecheck):
            def _get_data(self):
                yield copy.deepcopy(SIGNAL_1), importer.Action.DELETE

        list(TestImporter(Job.JobSource.UNKNOWN).run(20))

        self.assertEqual(0, Signal.objects.count())

    def test_run_skips_updating_data_if_already_exists(self):
        class TestImporter(TestImporterWithPrecheck):
            def _get_data(self):
                yield copy.deepcopy(SIGNAL_1), importer.Action.UPDATE_OR_INSERT

        signal = copy.deepcopy(SIGNAL_1)
        signal.save()

        list(TestImporter(Job.JobSource.UNKNOWN).run(20))

        self.assertEqual(1, Signal.objects.count())
        job = Job.objects.get()
        self.assertEqual(0, job.update_size)

    def test_run_updates_data(self):
        class TestImporter(TestImporterWithPrecheck):
            def _get_data(self):
                yield copy.deepcopy(SIGNAL_1), importer.Action.UPDATE_OR_INSERT

        signal = copy.deepcopy(SIGNAL_1)
        signal.sources.sources[0].name = Source.Name.TCAP
        signal.save()

        list(TestImporter(Job.JobSource.UNKNOWN).run(20))

        job = Job.objects.get()
        self.assertEqual(1, job.update_size)

    def test_get_decisions_returns_decisions(self):
        signal = copy.deepcopy(TEST_SIGNAL)
        signal.sources.sources[0].name = Source.Name.TCAP
        signal.save()
        case1 = copy.deepcopy(TEST_CASE_RESOLVED_APPROVAL).save()
        case2 = copy.deepcopy(TEST_CASE_RESOLVED_BLOCKED).save()
        test_importer = TestImporterWithPrecheck(Job.JobSource.TCAP_API)
        test_importer.SIGNAL_SOURCE = Source.Name.TCAP

        observed = list(
            test_importer.get_decisions(
                min(case1.create_time, case2.create_time), datetime.datetime(3000, 1, 1)
            )
        )

        self.assertEqual(
            [(signal, Review.Decision.APPROVE), (signal, Review.Decision.BLOCK)],
            observed,
        )

    def test_get_decisions_returns_none_before_start_time(self):
        signal = copy.deepcopy(TEST_SIGNAL)
        signal.sources.sources[0].name = Source.Name.TCAP
        signal.save()
        case = copy.deepcopy(TEST_CASE_RESOLVED_APPROVAL).save()
        test_importer = TestImporterWithPrecheck(Job.JobSource.TCAP_API)
        test_importer.SIGNAL_SOURCE = Source.Name.TCAP

        observed = list(
            test_importer.get_decisions(
                case.review_history[0].update_time + datetime.timedelta(seconds=1),
                datetime.datetime(3000, 1, 1),
            )
        )

        self.assertEmpty(observed)

    def test_get_decisions_returns_none_after_end_time(self):
        signal = copy.deepcopy(TEST_SIGNAL)
        signal.sources.sources[0].name = Source.Name.TCAP
        signal.save()
        case = copy.deepcopy(TEST_CASE_RESOLVED_APPROVAL).save()
        test_importer = TestImporterWithPrecheck(Job.JobSource.TCAP_API)
        test_importer.SIGNAL_SOURCE = Source.Name.TCAP

        observed = list(
            test_importer.get_decisions(
                datetime.datetime(2000, 1, 1), case.review_history[-1].update_time
            )
        )

        self.assertEmpty(observed)

    def test_get_decisions_returns_none_from_other_sources(self):
        signal = copy.deepcopy(TEST_SIGNAL)
        signal.sources.sources[0].name = Source.Name.TCAP
        signal.save()
        copy.deepcopy(TEST_CASE_RESOLVED_APPROVAL).save()
        test_importer = TestImporterWithPrecheck(Job.JobSource.UNKNOWN)
        test_importer.SIGNAL_SOURCE = Source.Name.UNKNOWN

        observed = list(
            test_importer.get_decisions(
                datetime.datetime(2000, 1, 1), datetime.datetime(3000, 1, 1)
            )
        )

        self.assertEmpty(observed)
