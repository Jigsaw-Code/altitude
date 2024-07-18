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

"""Define abstract class for importing Signals from difference sources into the DB."""

import abc
import datetime
import enum
import logging
from typing import Iterable

from bson.objectid import ObjectId

from models.case import Case, Review
from models.job import Job
from models.signal import Signal, Source
from utils import iterators


class Error(Exception):
    """Base class for exceptions in this module."""


class PreCheckError(Error):
    """Raised when an importer failed pre-check."""


class SourceResponseError(Error):
    """Raised when a remote source sends a bad response."""


@enum.unique
class Action(str, enum.Enum):
    DELETE = "DELETE"
    UPDATE_OR_INSERT = "UPDATE_OR_INSERT"


class Importer(metaclass=abc.ABCMeta):
    """An abstract base class for importing Signals from different sources."""

    SIGNAL_SOURCE = Source.Name.UNKNOWN

    def __init__(self, source: Job.JobSource):
        job_type = Job.JobType.SIGNAL_IMPORT
        logging.info("Starting job with type=%s, source=%s", job_type, source)
        self._job: Job = Job.start(type=job_type, source=source)
        logging.info("Job %s started", self._job.id)

    def __del__(self):
        if getattr(self, "_job", None) is not None:
            # We found an orphaned job that wasn't closed properly. Try to close it now.
            self._close()

    def _close(self):
        logging.info("Closing job %s", self._job.id)
        self._job.end()
        self._job = None

    def _get_last_job(self):
        """Gets the last job with a successful continuation token."""
        return (
            Job.objects(
                type=Job.JobType.SIGNAL_IMPORT,
                source=self._job.source,
                last_successful_continuation_token__exists=True,
            )
            .order_by("-start_time")
            .first()
        )

    def _get_decisions(
        self, start: datetime.datetime, end: datetime.datetime
    ) -> Iterable[tuple[Signal, Review.Decision]]:
        """Get all the decisions made in the time period from the source."""

        cases = Case.objects(
            review_history__match={
                "update_time__gte": start,
                "update_time__lt": end,
            }
        )
        for case in cases:
            try:
                signal = Signal.objects(
                    id__in=case.signal_ids, sources__sources__name=self.SIGNAL_SOURCE
                ).get()
            except Signal.DoesNotExist:
                continue

            reviews = (
                r
                for r in reversed(case.review_history)
                if r.update_time >= _make_tz_aware(start)
                and r.update_time <= _make_tz_aware(end)
            )
            review = max(reviews, key=lambda x: x.update_time)
            if not review:
                continue

            yield signal, review.decision

    @abc.abstractmethod
    def pre_check(self) -> None:
        """Checks whether the importer is ready.

        Raises:
            PreCheckError: If the pre-check failed.
        """
        raise NotImplementedError()

    @abc.abstractmethod
    def _get_data(self) -> Iterable[tuple[Signal, Action]]:
        """Gets the data from the source."""
        raise NotImplementedError()

    @abc.abstractmethod
    def _send_decisions(
        self, decisions: Iterable[tuple[Signal, Review.Decision]]
    ) -> None:
        """Send the given decisions to the platform."""
        raise NotImplementedError()

    def send_diagnostics(
        self, start: datetime.datetime, end: datetime.datetime
    ) -> None:
        """Send diagnostics information back to the source.

        This sends 'agree' and 'disagree' decisions back for the source data
        that was actioned upon.

        Args:
            start: the start time of the time period to send
                diagnostics for
            end: the end time of the time period to send
                diagnostics for
        """
        decisions = self._get_decisions(start=start, end=end)
        self._send_decisions(decisions)

    def _insert_signal(self, signal) -> ObjectId:
        signal.save()
        self._job.import_size += 1
        return signal.id

    def _update_signal(self, signal) -> ObjectId | None:
        # New imports should only have one item in signal content
        existing_signal = Signal.objects.get(content__value=signal.content[0].value)
        if signal == existing_signal:
            return None
        signal.merge(existing_signal)
        signal.save()
        self._job.update_size += 1
        return signal.id

    def _delete_signal(self, signal) -> ObjectId | None:
        source_name = signal.sources.sources[0].name
        try:
            # TODO: Check against all content items.
            signal = Signal.objects.get(content=signal.content)
        except Signal.DoesNotExist:
            logging.info(
                "Cannot redact Signal that does not exist. "
                "No Signal found with content `%s`",
                signal.content,
            )
            return None
        signal.redact(source_name)
        signal.save()
        self._job.delete_size += 1
        return signal.id

    def _run(self) -> Iterable[ObjectId]:
        """Imports the data retrieved from the source and updates the database."""
        for signal, action in self._get_data():
            if action == Action.UPDATE_OR_INSERT:
                try:
                    self._update_signal(signal)
                except Signal.DoesNotExist:
                    yield self._insert_signal(signal)
            elif action == Action.DELETE:
                self._delete_signal(signal)
            else:
                raise ValueError(f"Unknown action {action}, expected one of {Action}")
            self._job.save()
        self._job.status = Job.JobStatus.SUCCESS

    def run(self, chunk_size) -> Iterable[tuple[ObjectId]]:
        """Runs the importer job.

        Args:
            chunk_size: The number of signal IDs to return at a time.

        Returns:
            Chunks of new signal IDs that have been imported.
        """
        try:
            self.pre_check()
            yield from iterators.grouper(self._run(), chunk_size)
        except:
            self._job.status = Job.JobStatus.FAILURE
            raise
        finally:
            self._close()


def _make_tz_aware(date: datetime.datetime) -> datetime.datetime:
    """Adds default timezone if one is not provided"""
    if date.tzinfo is None or date.tzinfo.utcoffset(date) is None:
        return date.replace(tzinfo=datetime.timezone.utc)
    return date
