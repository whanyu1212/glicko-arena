from dataclasses import dataclass, field
from datetime import UTC, datetime

from glicko2.models.match_result import MatchResult


@dataclass
class RatingPeriod:
    """A batch of matches to be processed together.

    In Glicko-2 all matches within a period are treated as simultaneous.
    Ratings are updated once at the end of the period.

    Attributes:
        id (str): Unique identifier (e.g. "2024-Q1" or an auto-generated UUID).
        matches (list[MatchResult]): All match results recorded during this period.
        opened_at (datetime): When the period started.
        closed_at (datetime | None): When the period was closed; None if still open.
    """

    id: str
    matches: list[MatchResult] = field(default_factory=list)
    opened_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    closed_at: datetime | None = None

    @property
    def is_open(self) -> bool:
        return self.closed_at is None

    def add_match(self, result: MatchResult) -> None:
        if not self.is_open:
            raise RuntimeError(f"Cannot add match to closed period {self.id!r}")
        self.matches.append(result)

    def close(self) -> None:
        if not self.is_open:
            raise RuntimeError(f"Period {self.id!r} is already closed")
        self.closed_at = datetime.now(UTC)

    def player_ids(self) -> set[str]:
        """All player IDs that appear in this period.

        Returns:
            set[str]: Union of all player_id and opponent_id values across matches.
        """
        ids: set[str] = set()
        for m in self.matches:
            ids.add(m.player_id)
            ids.add(m.opponent_id)
        return ids

    def results_for(self, player_id: str) -> list[MatchResult]:
        """All results where `player_id` is the rated player.

        Args:
            player_id (str): The player to filter by.

        Returns:
            list[MatchResult]: Matches where player_id is the rated side.
        """
        return [m for m in self.matches if m.player_id == player_id]
