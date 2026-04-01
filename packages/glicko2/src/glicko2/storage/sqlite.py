"""SQLiteStorage — zero-infrastructure persistent backend."""

import json
import sqlite3
from datetime import datetime
from pathlib import Path

from glicko2.exceptions import StorageError
from glicko2.models.match_result import MatchResult
from glicko2.models.player import Player
from glicko2.models.rating_period import RatingPeriod
from glicko2.storage.base import AbstractStorage

_CREATE_PLAYERS = """
CREATE TABLE IF NOT EXISTS players (
    id          TEXT PRIMARY KEY,
    mu          REAL NOT NULL,
    phi         REAL NOT NULL,
    sigma       REAL NOT NULL,
    num_periods INTEGER NOT NULL DEFAULT 0,
    metadata    TEXT NOT NULL DEFAULT '{}'
)
"""

_CREATE_PERIODS = """
CREATE TABLE IF NOT EXISTS periods (
    id          TEXT PRIMARY KEY,
    opened_at   TEXT NOT NULL,
    closed_at   TEXT
)
"""

_CREATE_MATCHES = """
CREATE TABLE IF NOT EXISTS matches (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    period_id   TEXT NOT NULL REFERENCES periods(id),
    player_id   TEXT NOT NULL,
    opponent_id TEXT NOT NULL,
    score       REAL NOT NULL,
    timestamp   TEXT NOT NULL,
    metadata    TEXT NOT NULL DEFAULT '{}'
)
"""


class SQLiteStorage(AbstractStorage):
    """Persistent SQLite backend. Safe for single-process use."""

    def __init__(self, path: str | Path = ":memory:") -> None:
        self._conn = sqlite3.connect(str(path), check_same_thread=False)
        self._conn.row_factory = sqlite3.Row
        self._conn.execute("PRAGMA journal_mode=WAL")
        self._conn.execute("PRAGMA foreign_keys=ON")
        self._migrate()

    def _migrate(self) -> None:
        with self._conn:
            self._conn.execute(_CREATE_PLAYERS)
            self._conn.execute(_CREATE_PERIODS)
            self._conn.execute(_CREATE_MATCHES)

    # -- Players --

    def save_player(self, player: Player) -> None:
        with self._conn:
            self._conn.execute(
                """INSERT INTO players (id, mu, phi, sigma, num_periods, metadata)
                   VALUES (?, ?, ?, ?, ?, ?)
                   ON CONFLICT(id) DO UPDATE SET
                       mu=excluded.mu, phi=excluded.phi, sigma=excluded.sigma,
                       num_periods=excluded.num_periods, metadata=excluded.metadata""",
                (
                    player.id, player.mu, player.phi, player.sigma,
                    player.num_periods, json.dumps(player.metadata),
                ),
            )

    def load_player(self, player_id: str) -> Player | None:
        row = self._conn.execute(
            "SELECT * FROM players WHERE id=?", (player_id,)
        ).fetchone()
        return self._row_to_player(row) if row else None

    def load_all_players(self) -> list[Player]:
        rows = self._conn.execute("SELECT * FROM players").fetchall()
        return [self._row_to_player(r) for r in rows]

    def delete_player(self, player_id: str) -> None:
        with self._conn:
            self._conn.execute("DELETE FROM players WHERE id=?", (player_id,))

    @staticmethod
    def _row_to_player(row: sqlite3.Row) -> Player:
        return Player(
            id=row["id"],
            mu=row["mu"],
            phi=row["phi"],
            sigma=row["sigma"],
            num_periods=row["num_periods"],
            metadata=json.loads(row["metadata"]),
        )

    # -- Periods --

    def save_period(self, period: RatingPeriod) -> None:
        with self._conn:
            self._conn.execute(
                """INSERT INTO periods (id, opened_at, closed_at)
                   VALUES (?, ?, ?)
                   ON CONFLICT(id) DO UPDATE SET closed_at=excluded.closed_at""",
                (
                    period.id,
                    period.opened_at.isoformat(),
                    period.closed_at.isoformat() if period.closed_at else None,
                ),
            )

    def load_period(self, period_id: str) -> RatingPeriod | None:
        row = self._conn.execute(
            "SELECT * FROM periods WHERE id=?", (period_id,)
        ).fetchone()
        if not row:
            return None
        period = RatingPeriod(
            id=row["id"],
            opened_at=datetime.fromisoformat(row["opened_at"]),
            closed_at=datetime.fromisoformat(row["closed_at"]) if row["closed_at"] else None,
        )
        match_rows = self._conn.execute(
            "SELECT * FROM matches WHERE period_id=? ORDER BY id", (period_id,)
        ).fetchall()
        period.matches = [self._row_to_match(r) for r in match_rows]
        return period

    def load_all_periods(self) -> list[RatingPeriod]:
        rows = self._conn.execute("SELECT id FROM periods ORDER BY opened_at").fetchall()
        return [self.load_period(r["id"]) for r in rows]  # type: ignore[misc]

    # -- Matches --

    def append_match(self, period_id: str, match: MatchResult) -> None:
        try:
            with self._conn:
                self._conn.execute(
                    """INSERT INTO matches
                           (period_id, player_id, opponent_id, score, timestamp, metadata)
                       VALUES (?, ?, ?, ?, ?, ?)""",
                    (
                        period_id,
                        match.player_id, match.opponent_id, match.score,
                        match.timestamp.isoformat(), json.dumps(match.metadata),
                    ),
                )
        except sqlite3.IntegrityError as exc:
            raise StorageError(
                f"Cannot append match: period {period_id!r} does not exist"
            ) from exc

    @staticmethod
    def _row_to_match(row: sqlite3.Row) -> MatchResult:
        return MatchResult(
            player_id=row["player_id"],
            opponent_id=row["opponent_id"],
            score=row["score"],
            timestamp=datetime.fromisoformat(row["timestamp"]),
            metadata=json.loads(row["metadata"]),
        )

    # -- Lifecycle --

    def close(self) -> None:
        self._conn.close()
