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
"""Tests for the job data models."""

from absl.testing import absltest

from models.job import Job
from testing import test_case


class JobTest(test_case.TestCase):
    def test_start_creates_new_job(self):
        Job.start()

        job = Job.objects.get()
        self.assertIsNotNone(job.id)
        self.assertEqual(Job.JobStatus.IN_PROGRESS, job.status)

    def test_end_updates_job(self):
        job = Job.start()
        job.status = Job.JobStatus.FAILURE
        job.end()

        job = Job.objects.get()
        self.assertEqual(Job.JobStatus.FAILURE, job.status)

    def test_end_updates_job_with_unknown_status(self):
        Job.start().end()

        job = Job.objects.get()
        self.assertEqual(Job.JobStatus.UNKNOWN, job.status)


if __name__ == "__main__":
    absltest.main()
