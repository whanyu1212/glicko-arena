"""PostgresStorage — shared team leaderboards via psycopg3.

Install the optional dependency:
    pip install "glicko2-py[postgres]"   # i.e. psycopg[binary]>=3.1
"""

from __future__ import annotations

from glicko2.exceptions import StorageError
from glicko2.models.match_result import MatchResult
from glicko2.models.player import Player
from glicko2.models.rating_period import RatingPeriod
from glicko2.storage.base import AbstractStorage


class PostgresStorage(AbstractStorage):
    """Persistent PostgreSQL backend using psycopg3.

    Args:
        dsn: A libpq connection string, e.g.
             "postgresql://user:pass@host:5432/dbname"
    """

    def __init__(self, dsn: str) -> None:
        try:
            import psycopg  # noqa: F401
        except ImportError as exc:
            raise StorageError(
                "PostgresStorage requires psycopg. "
                'Install it with: pip install "glicko2-py[postgres]"'
            ) from exc

        import psycopg

        self._conn: psycopg.Connection[tuple[object, ...]] = psycopg.connect(dsn)
        self._migrate()

    def _migrate(self) -> None:
        with self._conn.cursor() as cur:
            cur.execute("""
                CREATE TABLE IF NOT EXISTS players (
                    id          TEXT PRIMARY KEY,
                    mu          DOUBLE PRECISION NOT NULL,
                    phi         DOUBLE PRECISION NOT NULL,
                    sigma       DOUBLE PRECISION NOT NULL,
                    num_periods INTEGER NOT NULL DEFAULT 0,
                    metadata    JSONB NOT NULL DEFAULT '{}'
                )
            """)
            cur.execute("""
                CREATE TABLE IF NOT EXISTS periods (
                    id          TEXT PRIMARY KEY,
                    opened_at   TIMESTAMPTZ NOT NULL,
                    closed_at   TIMESTAMPTZ
                )
            """)
            cur.execute("""
                CREATE TABLE IF NOT EXISTS matches (
                    id          BIGSERIAL PRIMARY KEY,
                    period_id   TEXT NOT NULL REFERENCES periods(id),
                    player_id   TEXT NOT NULL,
                    opponent_id TEXT NOT NULL,
                    score       DOUBLE PRECISION NOT NULL,
                    timestamp   TIMESTAMPTZ NOT NULL,
                    metadata    JSONB NOT NULL DEFAULT '{}'
                )
            """)
        self._conn.commit()

    # The full CRUD methods follow the same pattern as SQLiteStorage.
    # They are intentionally left as stubs — implement when the feature is needed.

    def save_player(self, player: Player) -> None:
        raise NotImplementedError

    def load_player(self, player_id: str) -> Player | None:
        raise NotImplementedError

    def load_all_players(self) -> list[Player]:
        raise NotImplementedError

    def delete_player(self, player_id: str) -> None:
        raise NotImplementedError

    def save_period(self, period: RatingPeriod) -> None:
        raise NotImplementedError

    def load_period(self, period_id: str) -> RatingPeriod | None:
        raise NotImplementedError

    def load_all_periods(self) -> list[RatingPeriod]:
        raise NotImplementedError

    def append_match(self, period_id: str, match: MatchResult) -> None:
        raise NotImplementedError

    def close(self) -> None:
        self._conn.close()
