"""Storage backend conformance tests.

Every AbstractStorage implementation must pass these tests unchanged.
Add a new subclass below for each new backend.
"""

from datetime import UTC, datetime

import pytest
from glicko2.exceptions import StorageError
from glicko2.models.match_result import MatchResult
from glicko2.models.player import Player
from glicko2.models.rating_period import RatingPeriod
from glicko2.storage.base import AbstractStorage
from glicko2.storage.memory import InMemoryStorage
from glicko2.storage.sqlite import SQLiteStorage


class StorageConformanceTests:
    """Abstract conformance suite. Subclasses must implement `storage()`."""

    @pytest.fixture()
    def storage(self) -> AbstractStorage:
        raise NotImplementedError

    # -- Players --

    def test_save_and_load_player(self, storage: AbstractStorage) -> None:
        p = Player(id="alice", mu=0.5, phi=1.0, sigma=0.06)
        storage.save_player(p)
        loaded = storage.load_player("alice")
        assert loaded is not None
        assert loaded.id == "alice"
        assert loaded.mu == pytest.approx(0.5)
        assert loaded.phi == pytest.approx(1.0)

    def test_load_missing_player_returns_none(self, storage: AbstractStorage) -> None:
        assert storage.load_player("ghost") is None

    def test_save_player_upserts(self, storage: AbstractStorage) -> None:
        storage.save_player(Player(id="alice", mu=0.0, phi=1.0, sigma=0.06))
        storage.save_player(Player(id="alice", mu=1.5, phi=0.8, sigma=0.06))
        loaded = storage.load_player("alice")
        assert loaded is not None
        assert loaded.mu == pytest.approx(1.5)

    def test_load_all_players(self, storage: AbstractStorage) -> None:
        storage.save_player(Player(id="alice"))
        storage.save_player(Player(id="bob"))
        players = storage.load_all_players()
        assert {p.id for p in players} == {"alice", "bob"}

    def test_delete_player(self, storage: AbstractStorage) -> None:
        storage.save_player(Player(id="alice"))
        storage.delete_player("alice")
        assert storage.load_player("alice") is None

    def test_delete_nonexistent_player_is_silent(self, storage: AbstractStorage) -> None:
        storage.delete_player("ghost")  # must not raise

    # -- Periods --

    def test_save_and_load_period(self, storage: AbstractStorage) -> None:
        period = RatingPeriod(id="p1")
        storage.save_period(period)
        loaded = storage.load_period("p1")
        assert loaded is not None
        assert loaded.id == "p1"

    def test_load_missing_period_returns_none(self, storage: AbstractStorage) -> None:
        assert storage.load_period("ghost") is None

    def test_load_all_periods_ordered_by_opened_at(self, storage: AbstractStorage) -> None:
        t1 = datetime(2024, 1, 1, tzinfo=UTC)
        t2 = datetime(2024, 6, 1, tzinfo=UTC)
        t3 = datetime(2025, 1, 1, tzinfo=UTC)
        # Insert out of order
        storage.save_period(RatingPeriod(id="p3", opened_at=t3))
        storage.save_period(RatingPeriod(id="p1", opened_at=t1))
        storage.save_period(RatingPeriod(id="p2", opened_at=t2))
        periods = storage.load_all_periods()
        assert [p.id for p in periods] == ["p1", "p2", "p3"]

    # -- Matches --

    def test_append_match_and_reload(self, storage: AbstractStorage) -> None:
        period = RatingPeriod(id="p1")
        storage.save_period(period)
        match = MatchResult("alice", "bob", 1.0)
        storage.append_match("p1", match)
        loaded = storage.load_period("p1")
        assert loaded is not None
        assert len(loaded.matches) == 1
        assert loaded.matches[0].player_id == "alice"
        assert loaded.matches[0].score == pytest.approx(1.0)

    def test_save_period_with_matches_then_append(self, storage: AbstractStorage) -> None:
        """save_period must persist only the header; pre-attached matches must not leak."""
        period = RatingPeriod(id="p1")
        period.matches.append(MatchResult("alice", "bob", 1.0))
        storage.save_period(period)

        storage.append_match("p1", MatchResult("carol", "dave", 0.5))

        loaded = storage.load_period("p1")
        assert loaded is not None
        assert len(loaded.matches) == 1
        assert loaded.matches[0].player_id == "carol"

    def test_append_match_missing_period_raises_storage_error(
        self, storage: AbstractStorage
    ) -> None:
        match = MatchResult("alice", "bob", 1.0)
        with pytest.raises(StorageError):
            storage.append_match("nonexistent", match)


class TestInMemoryStorageConformance(StorageConformanceTests):
    @pytest.fixture()
    def storage(self) -> InMemoryStorage:
        return InMemoryStorage()


class TestSQLiteStorageConformance(StorageConformanceTests):
    @pytest.fixture()
    def storage(self) -> SQLiteStorage:
        s = SQLiteStorage(":memory:")
        yield s
        s.close()
