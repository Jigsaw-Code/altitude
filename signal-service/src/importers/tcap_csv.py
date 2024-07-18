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

"""Define class for importing Signals from TCAP CSVs into the DB."""
import csv
import datetime
import os
from typing import Iterable

from importers import importer
from models.case import Review
from models.job import Job
from models.signal import (
    Content,
    ContentFeatures,
    ContentStatus,
    Signal,
    Source,
    Sources,
)


class TcapCsvImporter(importer.Importer):
    """Importer compatible with Tech Against Terrorism's TCAP CSV files."""

    _SOURCE_SIGNAL_ID_COL = "ID"
    _CREATED_ON_COL = "Created On"
    _DESCRIPTION_COL = "Description"
    _URL_COL = "URL"
    _VIOLENT_OR_GRAPHIC_COL = "Extreme Content"
    _PII_COL = "Pi I"  # This is incorrectly spelled in the original CSV.
    _TERRORIST_ENTITY_COL = "Core Terrorist Group - Terrorist Group Fk → Name"

    SIGNAL_SOURCE = Source.Name.TCAP

    def __init__(
        self,
        filepath: str,
    ):
        super().__init__(Job.JobSource.TCAP_CSV)
        self._filepath = filepath

    def _get_confidence(self, confidence_value: str) -> ContentFeatures.Confidence:
        """Convert 'YES', 'NO', 'NTS' to confidence enums.

        'NTS' is short for 'Not too sure' and is represented by UNSURE."""
        confidence_value = confidence_value.upper().strip()
        if confidence_value == "NTS":
            return ContentFeatures.Confidence.UNSURE
        return ContentFeatures.Confidence[confidence_value]

    def _tcap_date_to_datetime(self, tcap_date: str) -> datetime.datetime:
        """Converts dates like '12/21/22 16:41:59' to datetime."""
        return datetime.datetime.strptime(tcap_date, "%m/%d/%y %H:%M:%S")

    def pre_check(self) -> None:
        """Checks whether the importer is configured correctly."""
        if not os.path.isfile(self._filepath):
            raise importer.PreCheckError(f"{self._filepath} is not a file.")

    def _send_decisions(self, decisions: Iterable[tuple[str, Review.Decision]]) -> None:
        """Send the given decisions to the platform."""
        # Manually uploaded CSVs don't have a reciever for decisions.
        return

    def _get_data(
        self,
    ) -> Iterable[tuple[Signal, importer.Action]]:
        """Gets the raw data from the CSV."""
        with open(self._filepath, encoding="utf-8") as csv_file:
            csvreader = csv.DictReader(csv_file)
            for line in csvreader:
                features = ContentFeatures(
                    description=line[self._DESCRIPTION_COL],
                    associated_terrorist_organizations=[
                        line[self._TERRORIST_ENTITY_COL]
                    ],
                    is_violent_or_graphic=self._get_confidence(
                        line[self._VIOLENT_OR_GRAPHIC_COL]
                    ),
                    contains_pii=self._get_confidence(line[self._PII_COL]),
                )
                source = Source(
                    name=Source.Name.TCAP,
                    report_date=self._tcap_date_to_datetime(line[self._CREATED_ON_COL]),
                    source_signal_id=line[self._SOURCE_SIGNAL_ID_COL],
                )
                content_status = ContentStatus(
                    last_checked_date=self._tcap_date_to_datetime(
                        line[self._CREATED_ON_COL]
                    ),
                    most_recent_status=ContentStatus.Status.ACTIVE,
                    verifier=ContentStatus.Verifier.TCAP,
                )
                signal = Signal(
                    content=[
                        Content(
                            value=line[self._URL_COL],
                            content_type=Content.ContentType.URL,
                        )
                    ],
                    sources=Sources(sources=[source]),
                    content_features=features,
                    content_status=content_status,
                )
                yield (signal, importer.Action.UPDATE_OR_INSERT)
