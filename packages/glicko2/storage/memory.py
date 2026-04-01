"""InMemoryStorage — for testing and ephemeral use."""

import copy

from glicko2.exceptions import StorageError
from glicko2.models.match_result import MatchResult
from glicko2.models.player import Player
from glicko2.models.rating_period import RatingPeriod
from glicko2.storage.base import AbstractStorage


class InMemoryStorage(AbstractStorage):
    """Thread-unsafe in-memory backend. Intended for tests and examples."""

    def __init__(self) -> None:
        self._players: dict[str, Player] = {}
        self._periods: dict[str, RatingPeriod] = {}

    # -- Players --

    def save_player(self, player: Player) -> None:
        self._players[player.id] = copy.deepcopy(player)

    def load_player(self, player_id: str) -> Player | None:
        p = self._players.get(player_id)
        return copy.deepcopy(p) if p else None

    def load_all_players(self) -> list[Player]:
        return [copy.deepcopy(p) for p in self._players.values()]

    def delete_player(self, player_id: str) -> None:
        self._players.pop(player_id, None)

    # -- Periods --

    def save_period(self, period: RatingPeriod) -> None:
        header = copy.deepcopy(period)
        header.matches = []
        self._periods[period.id] = header

    def load_period(self, period_id: str) -> RatingPeriod | None:
        p = self._periods.get(period_id)
        return copy.deepcopy(p) if p else None

    def load_all_periods(self) -> list[RatingPeriod]:
        return sorted(
            (copy.deepcopy(p) for p in self._periods.values()),
            key=lambda p: p.opened_at,
        )

    # -- Matches --

    def append_match(self, period_id: str, match: MatchResult) -> None:
        period = self._periods.get(period_id)
        if period is None:
            raise StorageError(f"Period {period_id!r} not found")
        period.matches.append(copy.deepcopy(match))
