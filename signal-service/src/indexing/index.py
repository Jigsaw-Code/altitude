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

"""Module to build and search an index."""

from __future__ import annotations

import logging
import pathlib
import pickle
from dataclasses import asdict, dataclass
from typing import Iterable, Iterator, TypedDict, cast

from threatexchange.signal_type import index as tx_index
from threatexchange.signal_type.signal_base import SignalType

from models.signal import Signal


class Error(Exception):
    """Base class for exceptions in this module."""


class IndexNotFoundError(Error):
    """A chosen index does not exist."""


class SerializedIndexEntryMetadata(TypedDict):
    signal_id: str


class SerializedIndexMatch(TypedDict):
    query: str
    metadata: SerializedIndexEntryMetadata


@dataclass
class IndexEntryMetadata:
    """Data class to hold index entry metadata."""

    signal_id: str

    @classmethod
    def deserialize(cls, data: SerializedIndexEntryMetadata) -> IndexEntryMetadata:
        return cls(**data)

    def serialize(self) -> SerializedIndexEntryMetadata:
        """Creates a dictionary representation of an instance of IndexEntryMetadata."""
        return cast(SerializedIndexEntryMetadata, asdict(self))


@dataclass
class IndexMatch:
    """Data class representing a match on the index."""

    query: str
    metadata: IndexEntryMetadata

    @classmethod
    def deserialize(cls, data: SerializedIndexMatch) -> IndexMatch:
        return cls(
            query=data["query"],
            metadata=IndexEntryMetadata.deserialize(data["metadata"]),
        )

    def serialize(self) -> SerializedIndexMatch:
        """Creates a dictionary representation of an instance of IndexMatch."""
        return cast(SerializedIndexMatch, asdict(self))


IndexEntry = tuple[str, IndexEntryMetadata]


class Index:
    """Thin wrapper around ThreatExchange index with some added functionality.

    This index understands our model entities and can be saved to/loaded from a file.
    """

    STORAGE_PATH_DIR = pathlib.Path("/data/index")

    def __init__(self, index_type: SignalType):
        """Constructor.

        Args:
            index_type: The index type to create an index for.
        """
        super().__init__()
        self.index_type = index_type
        self._index: tx_index.SignalTypeIndex = None

    def __len__(self):
        if self._index is None:
            raise TypeError("Cannot determine length of index that has not been built.")
        return self._index.index.faiss_index.ntotal

    @classmethod
    def _get_index_name(cls, index_type: SignalType) -> str:
        """A unique representation of the index type, used in logging and filenames."""
        index_cls = index_type.get_index_cls()
        return f"{index_cls.__module__}.{index_cls.__name__}"

    @classmethod
    def _get_index_filepath(cls, index_type: SignalType):
        """Create a unique filepath to store a given index by its type."""
        index_name = cls._get_index_name(index_type)
        return cls.STORAGE_PATH_DIR.joinpath(index_name)

    def save(self):
        """Saves the index by pickling it and writing it to a local file."""
        index_name = self._get_index_name(self.index_type)
        logging.info("Saving `%s` index.", index_name)
        if self._index is None:
            raise TypeError("Cannot save index that has not been built.")
        storage_path = self._get_index_filepath(self.index_type)
        storage_path.parent.mkdir(parents=True, exist_ok=True)
        with storage_path.open(mode="wb+") as file:
            pickle.dump(self, file)
        logging.info("Saved `%s` index of size %d", index_name, len(self))

    @classmethod
    def load(cls, index_type: SignalType) -> Index:
        """Loads an index by unpickling it from a local file based on its type.

        Args:
            index_type: The index type to try and load an index for.

        Raises:
            IndexNotFoundError: If no index exists yet for the given index type.
        """
        storage_path = cls._get_index_filepath(index_type)
        if not storage_path.exists():
            raise IndexNotFoundError(
                f"No index found for `{cls._get_index_name(index_type)}`"
            )

        with open(storage_path, "rb") as file:
            self = pickle.load(file)
        logging.info(
            "Loaded `%s` index of size %d",
            cls._get_index_name(self.index_type),
            len(self),
        )
        return self

    def build(self, signals: Iterable[Signal]) -> Index:
        """Builds a new index based on a collection of signals."""
        index_name = self._get_index_name(self.index_type)
        logging.info("Building `%s` index.", index_name)
        entries: list[IndexEntry] = []
        for signal in signals:
            for content in signal.content:
                if content.content_type.value == self.index_type.INDICATOR_TYPE:
                    entries.append(
                        (content.value, IndexEntryMetadata(signal_id=str(signal.id)))
                    )
        self._index = self.index_type.get_index_cls().build(entries)
        logging.info("Built `%s` index of size %d", index_name, len(self))
        return self

    def query(self, value: str) -> Iterator[IndexMatch]:
        """Queries the index for a given value.

        Args:
            value: The value to check against the index, such as a hash digest.

        Returns:
            A list of index entry matches.
        """
        if self._index is None:
            raise TypeError("Cannot query index that has not been built.")

        matches: list[tx_index.IndexMatch[IndexEntryMetadata]] = self._index.query(
            value
        )
        if not matches:
            logging.info(
                "No matches found in index %s", self._get_index_name(self.index_type)
            )
            return

        for match in matches:
            yield IndexMatch(
                query=value,
                metadata=match.metadata,
            )
