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

"""Job-related models."""

from __future__ import annotations

import datetime
import enum

from mongoengine import Document, fields


class Job(Document):
    """Corresponds to the representation of a Job in the DB."""

    @enum.unique
    class JobStatus(str, enum.Enum):
        IN_PROGRESS = "IN_PROGRESS"
        SUCCESS = "SUCCESS"
        FAILURE = "FAILURE"
        UNKNOWN = "UNKNOWN"

    @enum.unique
    class JobType(str, enum.Enum):
        SIGNAL_IMPORT = "SIGNAL_IMPORT"
        UNKNOWN = "UNKNOWN"

    @enum.unique
    class JobSource(str, enum.Enum):
        TCAP_CSV = "TCAP_CSV"
        TCAP_API = "TCAP_API"
        THREAT_EXCHANGE_API = "THREAT_EXCHANGE_API"
        UNKNOWN = "UNKNOWN"

    status = fields.EnumField(JobStatus, default=JobStatus.UNKNOWN)
    type = fields.EnumField(JobType, default=JobType.UNKNOWN, required=True)
    source = fields.EnumField(JobSource, default=JobSource.UNKNOWN, required=True)
    start_time = fields.DateTimeField(default=datetime.datetime.utcnow)
    import_size = fields.IntField(default=0)
    update_size = fields.IntField(default=0)
    delete_size = fields.IntField(default=0)
    continuation_token = fields.StringField()
    # The continuation token of the last succesful call.
    last_successful_continuation_token = fields.StringField()

    @classmethod
    def start(cls, **kwargs) -> Job:
        self = cls(**kwargs, status=Job.JobStatus.IN_PROGRESS)
        return self.save()

    def end(self) -> Job:
        if self.status == Job.JobStatus.IN_PROGRESS:
            # We expect the job to be in a resting state. `IN_PROGRESS` means something
            # unexpected happened, and the job is still in an unexpected active state.
            self.status = Job.JobStatus.UNKNOWN
        return self.save()
