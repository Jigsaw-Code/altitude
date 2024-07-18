# Copyright 2024 Google LLC
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

"""Canonical test entities that can be re-used in tests."""

import datetime

from bson.objectid import ObjectId

from models import features
from models.case import Case, Review
from models.signal import Content, Signal, Source, Sources
from models.target import FeatureSet, Target

# A basic Case.
TEST_CASE = Case(
    signal_ids=[ObjectId("bbbbbbbbbbbbbbbbbbbbbbbb")],
    target_id=ObjectId("cccccccccccccccccccccccc"),
    create_time=datetime.datetime(2000, 12, 25, tzinfo=datetime.timezone.utc),
    state=Case.State.RESOLVED,
    review_history=[
        Review(
            id=ObjectId(),
            create_time=datetime.datetime(2000, 12, 26, tzinfo=datetime.timezone.utc),
            state=Review.State.PUBLISHED,
            decision=Review.Decision.APPROVE,
            user="user1",
            delivery_status=Review.DeliveryStatus.PENDING,
        )
    ],
    notes="Hello World",
)

TEST_CASE_SPARSE_DATA = Case(
    signal_ids=[ObjectId("bbbbbbbbbbbbbbbbbbbbbbbb")],
    create_time=datetime.datetime(2000, 12, 25, tzinfo=datetime.timezone.utc),
    state=Case.State.ACTIVE,
)

TEST_CASE_ACTIVE = Case(
    signal_ids=[ObjectId("bbbbbbbbbbbbbbbbbbbbbbbb")],
    target_id=ObjectId("cccccccccccccccccccccccc"),
    create_time=datetime.datetime(2000, 12, 25, tzinfo=datetime.timezone.utc),
    state=Case.State.ACTIVE,
)

TEST_CASE_RESOLVED_APPROVAL = Case(
    signal_ids=[ObjectId("bbbbbbbbbbbbbbbbbbbbbbbb")],
    target_id=ObjectId("cccccccccccccccccccccccc"),
    create_time=datetime.datetime(2000, 12, 25, tzinfo=datetime.timezone.utc),
    state=Case.State.RESOLVED,
    review_history=[
        Review(
            id=ObjectId("dddddddddddddddddddddddd"),
            create_time=datetime.datetime(2000, 12, 26, tzinfo=datetime.timezone.utc),
            state=Review.State.PUBLISHED,
            decision=Review.Decision.APPROVE,
            user="user2",
        )
    ],
)

TEST_CASE_RESOLVED_BLOCKED = Case(
    signal_ids=[ObjectId("bbbbbbbbbbbbbbbbbbbbbbbb")],
    target_id=ObjectId("cccccccccccccccccccccccc"),
    create_time=datetime.datetime(2000, 12, 25, tzinfo=datetime.timezone.utc),
    state=Case.State.RESOLVED,
    review_history=[
        Review(
            id=ObjectId("eeeeeeeeeeeeeeeeeeeeeeee"),
            create_time=datetime.datetime(2000, 12, 26, tzinfo=datetime.timezone.utc),
            state=Review.State.PUBLISHED,
            decision=Review.Decision.BLOCK,
            user="user3",
        )
    ],
)

TEST_TARGET = Target(
    create_time=datetime.datetime(2011, 6, 12, tzinfo=datetime.timezone.utc),
    client_context="abc-context",
    feature_set=FeatureSet(
        creator=features.user.User(ip_address="1.2.3.4"),
        image=features.image.Image(
            title="Title", description="description", data=b"imagebytes"
        ),
    ),
)

TEST_SIGNAL = Signal(
    id=ObjectId("bbbbbbbbbbbbbbbbbbbbbbbb"),
    content=[Content(value="example.com", content_type=Content.ContentType.URL)],
    sources=Sources(
        sources=[
            Source(
                name=Source.Name.TCAP,
                source_signal_id="123",
                report_date=datetime.datetime(
                    2022, 12, 21, 16, 41, 59, tzinfo=datetime.timezone.utc
                ),
            ),
            Source(
                name=Source.Name.GIFCT,
                source_signal_id="456",
                report_date=datetime.datetime(
                    2023, 4, 2, 19, 3, 44, tzinfo=datetime.timezone.utc
                ),
            ),
        ]
    ),
)
