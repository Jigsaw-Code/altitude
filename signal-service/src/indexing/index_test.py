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
"""Tests for the index module."""

import pathlib

from absl.testing import absltest
from threatexchange.signal_type.pdq import PdqSignal

from indexing.index import Index, IndexEntryMetadata, IndexMatch, IndexNotFoundError
from models.signal import Content, Signal, Source, Sources
from testing import test_case

TEST_SIGNALS = [
    Signal(
        id="signal-id-1",
        content=[
            Content(
                value="0000000000000000000000000000000000000000000000000000000000000000",
                content_type=Content.ContentType.HASH_PDQ,
            )
        ],
        sources=Sources(sources=[Source()]),
    ),
    Signal(
        id="signal-id-2",
        content=[
            Content(
                value="000000000000000000000000000000000000000000000000000000000000ffff",
                content_type=Content.ContentType.HASH_PDQ,
            )
        ],
        sources=Sources(sources=[Source()]),
    ),
    Signal(
        id="signal-id-3",
        content=[
            Content(
                value="0f0f0f0f0f0f0f0f0f0f0f0f0f0f0f0f0f0f0f0f0f0f0f0f0f0f0f0f0f0f0f0f",
                content_type=Content.ContentType.HASH_PDQ,
            )
        ],
        sources=Sources(sources=[Source()]),
    ),
    Signal(
        id="signal-id-4",
        content=[
            Content(
                value="f0f0f0f0f0f0f0f0f0f0f0f0f0f0f0f0f0f0f0f0f0f0f0f0f0f0f0f0f0f0f0f0",
                content_type=Content.ContentType.HASH_PDQ,
            )
        ],
        sources=Sources(sources=[Source()]),
    ),
    Signal(
        id="signal-id-5",
        content=[
            Content(
                value="ffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff",
                content_type=Content.ContentType.HASH_PDQ,
            )
        ],
        sources=Sources(sources=[Source()]),
    ),
]


class IndexMatchTest(test_case.TestCase):
    """Tests for the IndexMatch class."""

    def test_serialize(self):
        match = IndexMatch(
            query="foobar", metadata=IndexEntryMetadata(signal_id="signal1")
        )

        observed = match.serialize()

        self.assertEqual(
            {"query": "foobar", "metadata": {"signal_id": "signal1"}}, observed
        )

    def test_deserialize(self):
        match = {"query": "foobar", "metadata": {"signal_id": "signal1"}}

        observed = IndexMatch.deserialize(match)

        self.assertEqual(
            IndexMatch(
                query="foobar", metadata=IndexEntryMetadata(signal_id="signal1")
            ),
            observed,
        )

    def test_to_and_deserialize(self):
        match = IndexMatch(
            query="foobar", metadata=IndexEntryMetadata(signal_id="signal1")
        )

        observed = IndexMatch.deserialize(match.serialize())

        self.assertEqual(match, observed)


class IndexTest(test_case.TestCase):
    """Tests for the IndexMatch class."""

    def setUp(self):
        super().setUp()
        Index.STORAGE_PATH_DIR = pathlib.Path(self.create_tempdir())
        self.index = Index(index_type=PdqSignal)

    def test_save_and_load_index_pickles_index_correctly(self):
        self.index.build(signals=TEST_SIGNALS)
        self.index.save()

        reconstructed_index = Index.load(index_type=PdqSignal)

        self.assertIsInstance(reconstructed_index, Index)
        self.assertEqual(reconstructed_index.index_type, self.index.index_type)

    def test_save_unbuilt_index_raises_error(self):
        with self.assertRaises(TypeError):
            self.index.save()

    def test_query_unbuilt_index_raises_error(self):
        with self.assertRaises(TypeError):
            list(self.index.query(TEST_SIGNALS[0].content))

    def test_load_unsaved_index_raises_error(self):
        with self.assertRaises(IndexNotFoundError):
            Index.load(index_type=PdqSignal)

    def test_build_index_with_entries_creates_correctly_sized_index(self):
        self.index.build(signals=TEST_SIGNALS)

        self.assertLen(self.index, 5)

    def test_build_index_with_signals_that_contain_other_types(self):
        signal = Signal(
            id="signal-id",
            content=[
                Content(
                    value="http://example.com/foobar.jpg",
                    content_type=Content.ContentType.URL,
                ),
                Content(
                    value="0000000000000000000000000000000000000000000000000000000000000000",
                    content_type=Content.ContentType.HASH_PDQ,
                ),
            ],
            sources=Sources(sources=[Source()]),
        )
        self.index.build(signals=[signal])

        self.assertLen(self.index, 1)

    def test_query_index_returns_matches(self):
        self.index.build(signals=TEST_SIGNALS)

        matches = list(self.index.query(TEST_SIGNALS[1].content[0].value))

        self.assertLen(matches, 2)
        self.assertEqual(
            "000000000000000000000000000000000000000000000000000000000000ffff",
            matches[0].query,
        )
        self.assertEqual("signal-id-2", matches[0].metadata.signal_id)
        self.assertEqual(
            "000000000000000000000000000000000000000000000000000000000000ffff",
            matches[1].query,
        )
        self.assertEqual("signal-id-1", matches[1].metadata.signal_id)

    def test_query_reconstructed_index_returns_matches(self):
        self.index.build(signals=TEST_SIGNALS)
        self.index.save()
        reconstructed_index = Index.load(index_type=PdqSignal)
        self.assertNotEqual(reconstructed_index, self.index)

        matches = list(
            reconstructed_index.query(
                "000000000000000000000000000000000000000000000000000000000000ffff"
            )
        )

        self.assertLen(matches, 2)
        self.assertEqual("signal-id-2", matches[0].metadata.signal_id)
        self.assertEqual("signal-id-1", matches[1].metadata.signal_id)

    def test_query_index_returns_empty_list_if_no_matches_found(self):
        self.index.build(signals=TEST_SIGNALS)

        matches = list(
            self.index.query(
                "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa"
            )
        )

        self.assertEmpty(matches)


if __name__ == "__main__":
    absltest.main()
