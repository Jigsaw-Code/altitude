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
"""Test that the TCAP CSV Signal Importer behaves as expected."""

import csv
import datetime
import random
from unittest import mock

from absl.testing import parameterized

from importers import tcap_csv
from models.signal import (
    Content,
    ContentFeatures,
    ContentStatus,
    Signal,
    Source,
    Sources,
)
from testing import test_case


class TcapCsvImporterLibTest(parameterized.TestCase, test_case.TestCase):
    @mock.patch.object(random, "randrange", return_value=2)
    def test_csv_get_data(self, _):
        input_csv = self.create_tempfile(mode="wt")
        with input_csv.open_text("w") as csv_file:  # pylint: disable=no-member
            writer = csv.writer(csv_file)
            # Add a header.
            writer.writerow(
                [
                    "ID",
                    "Description",
                    "URL",
                    "Domain",
                    "Created On",
                    "Content Data Type",
                    "Extreme Content",
                    "Pi I",
                    "Protocol",
                    "Core Tech Platform - Tech Platform → Name",
                    "Core Terrorist Group - Terrorist Group Fk → Name",
                    "Core Terrorist Group - Terrorist Group Fk → Entity Type",
                    "Core Terrorist Group - Terrorist Group Fk → Ideology",
                ]
            )
            # Add a row of content.
            writer.writerow(
                [
                    "123",
                    "This is bad content because it is.",
                    "google.com/123",
                    "google.com",
                    "12/21/22 16:41:59",
                    "URL",
                    "NO",
                    "NTS",
                    "https://",
                    "Google",
                    "Terrorist Entity ABC",
                    "GRP",
                    "ISM",
                ]
            )

        tcap_importer = tcap_csv.TcapCsvImporter(
            input_csv.full_path,  # pylint: disable=no-member
        )

        new_ids = list(sum(tcap_importer.run(20), ()))
        del tcap_importer

        self.assertLen(new_ids, 1)
        expected = Signal(
            id=new_ids[0],
            content=[
                Content(
                    value="google.com/123",
                    content_type=Content.ContentType.URL,
                )
            ],
            sources=Sources(
                sources=[
                    Source(
                        name=Source.Name.TCAP,
                        report_date=datetime.datetime(
                            2022, 12, 21, 16, 41, 59, tzinfo=datetime.timezone.utc
                        ),
                        source_signal_id="123",
                    )
                ]
            ),
            content_features=ContentFeatures(
                description="This is bad content because it is.",
                associated_terrorist_organizations=["Terrorist Entity ABC"],
                contains_pii=ContentFeatures.Confidence.UNSURE,
                is_violent_or_graphic=ContentFeatures.Confidence.NO,
            ),
            content_status=ContentStatus(
                last_checked_date=datetime.datetime(
                    2022, 12, 21, 16, 41, 59, tzinfo=datetime.timezone.utc
                ),
                most_recent_status=ContentStatus.Status.ACTIVE,
                verifier=ContentStatus.Verifier.TCAP,
            ),
        )
        self.assertEqual(
            expected,
            Signal.objects.get(id=new_ids[0]),
        )
