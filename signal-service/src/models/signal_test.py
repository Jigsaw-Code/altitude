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
"""Tests for the signal data models."""

import datetime

from absl.testing import absltest, parameterized
from bson.objectid import ObjectId

from models.signal import (
    Content,
    ContentFeatures,
    ContentStatus,
    Signal,
    Source,
    Sources,
)
from testing import test_case


class SignalTest(parameterized.TestCase, test_case.TestCase):
    def test_signal_get_only_pdq_types(self):
        Signal(
            content=[Content(value="foo1", content_type=Content.ContentType.URL)],
            sources=Sources(sources=[Source()]),
        ).save()
        Signal(
            content=[
                Content(value="pdq-hash", content_type=Content.ContentType.HASH_PDQ)
            ],
            sources=Sources(sources=[Source()]),
        ).save()
        Signal(
            content=[Content(value="foo3", content_type=Content.ContentType.URL)],
            sources=Sources(sources=[Source()]),
        ).save()
        Signal(
            content=[Content(value="foo4", content_type=Content.ContentType.URL)],
            sources=Sources(sources=[Source()]),
        ).save()
        Signal(
            content=[
                Content(value="foo5", content_type=Content.ContentType.URL),
                Content(value="pdq-hash-2", content_type=Content.ContentType.HASH_PDQ),
            ],
            sources=Sources(sources=[Source()]),
        ).save()

        signals = list(Signal.pdq)

        self.assertLen(signals, 2)
        self.assertEqual("pdq-hash", signals[0].content[0].value)
        self.assertEqual("pdq-hash-2", signals[1].content[1].value)

    def test_redact_signal_with_one_source_redacts_content_and_source(self):
        signal = Signal(
            content=[
                Content(
                    value="https://abc.xyz/",
                    content_type=Content.ContentType.URL,
                ),
                Content(
                    value="https://def.xyz/",
                    content_type=Content.ContentType.URL,
                ),
            ],
            sources=Sources(sources=[Source(name=Source.Name.TCAP)]),
            content_features=ContentFeatures(),
            content_status=ContentStatus(),
        )
        self.assertFalse(signal.sources.sources[0].is_redacted)

        signal.redact(Source.Name.TCAP)

        self.assertTrue(signal.sources.sources[0].is_redacted)
        self.assertLen(signal.content, 1)
        self.assertEqual("[REDACTED]", signal.content[0].value)

    def test_redact_signal_with_multiple_sources_does_not_redact_content(self):
        signal = Signal(
            content=[
                Content(
                    value="https://abc.xyz/",
                    content_type=Content.ContentType.URL,
                )
            ],
            sources=Sources(
                sources=[
                    Source(name=Source.Name.TCAP),
                    Source(name=Source.Name.GIFCT),
                ]
            ),
            content_features=ContentFeatures(),
            content_status=ContentStatus(),
        )
        self.assertFalse(signal.sources.sources[0].is_redacted)
        self.assertFalse(signal.sources.sources[1].is_redacted)

        signal.redact(Source.Name.TCAP)

        self.assertTrue(signal.sources.sources[0].is_redacted)
        self.assertFalse(signal.sources.sources[1].is_redacted)
        self.assertEqual("https://abc.xyz/", signal.content[0].value)

    def test_redact_signal_with_multiple_sources_redacts_content_if_all_sources_redacted(
        self,
    ):
        signal = Signal(
            content=[
                Content(
                    value="https://abc.xyz/",
                    content_type=Content.ContentType.URL,
                ),
                Content(
                    value="https://def.xyz/",
                    content_type=Content.ContentType.URL,
                ),
            ],
            sources=Sources(
                sources=[
                    Source(name=Source.Name.TCAP),
                    Source(name=Source.Name.GIFCT, is_redacted=True),
                ]
            ),
            content_features=ContentFeatures(),
            content_status=ContentStatus(),
        )
        self.assertFalse(signal.sources.sources[0].is_redacted)
        self.assertTrue(signal.sources.sources[1].is_redacted)

        signal.redact(Source.Name.TCAP)

        self.assertTrue(signal.sources.sources[0].is_redacted)
        self.assertTrue(signal.sources.sources[1].is_redacted)
        self.assertLen(signal.content, 1)
        self.assertEqual("[REDACTED]", signal.content[0].value)

    @parameterized.named_parameters(
        (
            "not_equal",
            Signal(
                content=[
                    Content(
                        value="https://abc.xyz/",
                        content_type=Content.ContentType.URL,
                    )
                ],
                sources=Sources(
                    sources=[
                        Source(),
                        Source(name=Source.Name.TCAP, is_redacted=True),
                    ]
                ),
                content_features=ContentFeatures(),
                content_status=ContentStatus(),
            ),
            Signal(
                content=[
                    Content(
                        value="https://def.xyz/",
                        content_type=Content.ContentType.URL,
                    )
                ],
                sources=Sources(
                    sources=[
                        Source(),
                        Source(name=Source.Name.TCAP, is_redacted=True),
                    ]
                ),
                content_features=ContentFeatures(),
                content_status=ContentStatus(),
            ),
            False,
        ),
        (
            "ids_do_not_match",
            Signal(
                id=ObjectId(),
                content=[
                    Content(
                        value="https://abc.xyz/",
                        content_type=Content.ContentType.URL,
                    ),
                    Content(
                        value="https://def.xyz/",
                        content_type=Content.ContentType.URL,
                    ),
                ],
                sources=Sources(
                    sources=[
                        Source(),
                        Source(name=Source.Name.TCAP, is_redacted=True),
                    ]
                ),
                content_features=ContentFeatures(),
                content_status=ContentStatus(),
            ),
            Signal(
                id=ObjectId(),
                content=[
                    Content(
                        value="https://abc.xyz/",
                        content_type=Content.ContentType.URL,
                    ),
                    Content(
                        value="https://def.xyz/",
                        content_type=Content.ContentType.URL,
                    ),
                ],
                sources=Sources(
                    sources=[
                        Source(),
                        Source(name=Source.Name.TCAP, is_redacted=True),
                    ]
                ),
                content_features=ContentFeatures(),
                content_status=ContentStatus(),
            ),
            True,
        ),
    )
    def test_equals(self, signal_1: Signal, signal_2: Signal, expected: bool):
        signal_1.validate()
        signal_2.validate()
        self.assertEqual(signal_1 == signal_2, expected)

    @parameterized.named_parameters(
        (
            "append_new_source",
            Signal(
                id=ObjectId(),
                content=[
                    Content(
                        value="https://abc.xyz/",
                        content_type=Content.ContentType.URL,
                    )
                ],
                sources=Sources(
                    sources=[
                        Source(),
                        Source(name=Source.Name.TCAP, is_redacted=True),
                    ]
                ),
                content_features=ContentFeatures(),
                content_status=ContentStatus(),
            ),
            Signal(
                content=[
                    Content(
                        value="https://abc.xyz/",
                        content_type=Content.ContentType.URL,
                    )
                ],
                sources=Sources(sources=[Source(name=Source.Name.GIFCT)]),
                content_features=ContentFeatures(),
                content_status=ContentStatus(),
            ),
            Signal(
                content=[
                    Content(
                        value="https://abc.xyz/",
                        content_type=Content.ContentType.URL,
                    )
                ],
                sources=Sources(
                    sources=[
                        Source(),
                        Source(name=Source.Name.TCAP, is_redacted=True),
                        Source(name=Source.Name.GIFCT),
                    ]
                ),
                content_features=ContentFeatures(),
                content_status=ContentStatus(),
            ),
        ),
        (
            "edit_existing_source",
            Signal(
                id=ObjectId(),
                content=[
                    Content(
                        value="https://abc.xyz/",
                        content_type=Content.ContentType.URL,
                    )
                ],
                sources=Sources(
                    sources=[
                        Source(),
                        Source(name=Source.Name.TCAP),
                    ]
                ),
                content_features=ContentFeatures(),
                content_status=ContentStatus(),
            ),
            Signal(
                content=[
                    Content(
                        value="https://abc.xyz/",
                        content_type=Content.ContentType.URL,
                    )
                ],
                sources=Sources(
                    sources=[
                        Source(
                            name=Source.Name.TCAP,
                            source_signal_id="this is added since it's a new field",
                        ),
                    ]
                ),
                content_features=ContentFeatures(),
                content_status=ContentStatus(),
            ),
            Signal(
                content=[
                    Content(
                        value="https://abc.xyz/",
                        content_type=Content.ContentType.URL,
                    )
                ],
                sources=Sources(
                    sources=[
                        Source(),
                        Source(
                            name=Source.Name.TCAP,
                            source_signal_id="this is added since it's a new field",
                        ),
                    ]
                ),
                content_features=ContentFeatures(),
                content_status=ContentStatus(),
            ),
        ),
        (
            "no_existing_status_use_new",
            Signal(
                id=ObjectId(),
                content=[
                    Content(
                        value="https://abc.xyz/",
                        content_type=Content.ContentType.URL,
                    )
                ],
                sources=Sources(sources=[Source()]),
                content_features=ContentFeatures(),
                content_status=ContentStatus(),
            ),
            Signal(
                content=[
                    Content(
                        value="https://abc.xyz/",
                        content_type=Content.ContentType.URL,
                    )
                ],
                sources=Sources(sources=[Source()]),
                content_features=ContentFeatures(),
                content_status=ContentStatus(
                    last_checked_date=datetime.datetime(
                        2000, 12, 25, tzinfo=datetime.timezone.utc
                    ),
                    most_recent_status=ContentStatus.Status.ACTIVE,
                ),
            ),
            Signal(
                content=[
                    Content(
                        value="https://abc.xyz/",
                        content_type=Content.ContentType.URL,
                    )
                ],
                sources=Sources(sources=[Source()]),
                content_features=ContentFeatures(),
                content_status=ContentStatus(
                    last_checked_date=datetime.datetime(
                        2000, 12, 25, tzinfo=datetime.timezone.utc
                    ),
                    most_recent_status=ContentStatus.Status.ACTIVE,
                ),
            ),
        ),
        (
            "ignore_unknown_status",
            Signal(
                id=ObjectId(),
                content=[
                    Content(
                        value="https://abc.xyz/",
                        content_type=Content.ContentType.URL,
                    )
                ],
                sources=Sources(sources=[Source()]),
                content_features=ContentFeatures(),
                content_status=ContentStatus(),
            ),
            Signal(
                content=[
                    Content(
                        value="https://abc.xyz/",
                        content_type=Content.ContentType.URL,
                    )
                ],
                sources=Sources(sources=[Source()]),
                content_features=ContentFeatures(),
                content_status=ContentStatus(
                    last_checked_date=datetime.datetime(
                        2000, 12, 25, tzinfo=datetime.timezone.utc
                    ),
                    most_recent_status=ContentStatus.Status.UNKNOWN,
                ),
            ),
            Signal(
                content=[
                    Content(
                        value="https://abc.xyz/",
                        content_type=Content.ContentType.URL,
                    )
                ],
                sources=Sources(sources=[Source()]),
                content_features=ContentFeatures(),
                content_status=ContentStatus(),
            ),
        ),
        (
            "replace_status_if_more_recent",
            Signal(
                id=ObjectId(),
                content=[
                    Content(
                        value="https://abc.xyz/",
                        content_type=Content.ContentType.URL,
                    )
                ],
                sources=Sources(sources=[Source()]),
                content_features=ContentFeatures(),
                content_status=ContentStatus(
                    last_checked_date=datetime.datetime(
                        2000, 12, 21, tzinfo=datetime.timezone.utc
                    ),
                    most_recent_status=ContentStatus.Status.REMOVED_BY_MODERATOR,
                ),
            ),
            Signal(
                content=[
                    Content(
                        value="https://abc.xyz/",
                        content_type=Content.ContentType.URL,
                    )
                ],
                sources=Sources(sources=[Source()]),
                content_features=ContentFeatures(),
                content_status=ContentStatus(
                    last_checked_date=datetime.datetime(
                        2000, 12, 25, tzinfo=datetime.timezone.utc
                    ),
                    most_recent_status=ContentStatus.Status.ACTIVE,
                ),
            ),
            Signal(
                content=[
                    Content(
                        value="https://abc.xyz/",
                        content_type=Content.ContentType.URL,
                    )
                ],
                sources=Sources(sources=[Source()]),
                content_features=ContentFeatures(),
                content_status=ContentStatus(
                    last_checked_date=datetime.datetime(
                        2000, 12, 25, tzinfo=datetime.timezone.utc
                    ),
                    most_recent_status=ContentStatus.Status.ACTIVE,
                ),
            ),
        ),
        (
            "compare_timezone_unaware_date",
            Signal(
                id=ObjectId(),
                content=[
                    Content(
                        value="https://abc.xyz/",
                        content_type=Content.ContentType.URL,
                    )
                ],
                sources=Sources(sources=[Source()]),
                content_features=ContentFeatures(),
                content_status=ContentStatus(
                    last_checked_date=datetime.datetime(2000, 12, 21),
                    most_recent_status=ContentStatus.Status.REMOVED_BY_MODERATOR,
                ),
            ),
            Signal(
                content=[
                    Content(
                        value="https://abc.xyz/",
                        content_type=Content.ContentType.URL,
                    )
                ],
                sources=Sources(sources=[Source()]),
                content_features=ContentFeatures(),
                content_status=ContentStatus(
                    last_checked_date=datetime.datetime(
                        2000, 12, 25, tzinfo=datetime.timezone.utc
                    ),
                    most_recent_status=ContentStatus.Status.ACTIVE,
                ),
            ),
            Signal(
                content=[
                    Content(
                        value="https://abc.xyz/",
                        content_type=Content.ContentType.URL,
                    )
                ],
                sources=Sources(sources=[Source()]),
                content_features=ContentFeatures(),
                content_status=ContentStatus(
                    last_checked_date=datetime.datetime(
                        2000, 12, 25, tzinfo=datetime.timezone.utc
                    ),
                    most_recent_status=ContentStatus.Status.ACTIVE,
                ),
            ),
        ),
        (
            "add_new_content_features",
            Signal(
                id=ObjectId(),
                content=[
                    Content(
                        value="https://abc.xyz/",
                        content_type=Content.ContentType.URL,
                    )
                ],
                sources=Sources(sources=[Source()]),
                content_features=ContentFeatures(trust=0.7),
                content_status=ContentStatus(),
            ),
            Signal(
                content=[
                    Content(
                        value="https://abc.xyz/",
                        content_type=Content.ContentType.URL,
                    )
                ],
                sources=Sources(sources=[Source()]),
                content_features=ContentFeatures(
                    trust=0.6, contains_pii=ContentFeatures.Confidence.YES
                ),
                content_status=ContentStatus(),
            ),
            Signal(
                content=[
                    Content(
                        value="https://abc.xyz/",
                        content_type=Content.ContentType.URL,
                    )
                ],
                sources=Sources(sources=[Source()]),
                content_features=ContentFeatures(
                    trust=0.7, contains_pii=ContentFeatures.Confidence.YES
                ),
                content_status=ContentStatus(),
            ),
        ),
    )
    def test_merge(self, signal_1: Signal, signal_2: Signal, expected_merge: Signal):
        signal_1.validate()
        signal_2.validate()
        signal_1.merge(signal_2)
        self.assertEqual(signal_1, expected_merge)


if __name__ == "__main__":
    absltest.main()
