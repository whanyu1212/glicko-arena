"""AbstractStorage — interface all storage backends must implement."""

from abc import ABC, abstractmethod

from glicko2.models.match_result import MatchResult
from glicko2.models.player import Player
from glicko2.models.rating_period import RatingPeriod


class AbstractStorage(ABC):
    """Persistence interface for players and rating periods."""

    # -- Players --

    @abstractmethod
    def save_player(self, player: Player) -> None:
        """Persist a player, inserting or updating as needed.

        Args:
            player (Player): The player to save.
        """
        ...

    @abstractmethod
    def load_player(self, player_id: str) -> Player | None:
        """Load a single player by ID.

        Args:
            player_id (str): The player's unique identifier.

        Returns:
            Player | None: The player if found, otherwise None.
        """
        ...

    @abstractmethod
    def load_all_players(self) -> list[Player]:
        """Load all persisted players.

        Returns:
            list[Player]: All players in storage.
        """
        ...

    @abstractmethod
    def delete_player(self, player_id: str) -> None:
        """Delete a player from storage.

        Args:
            player_id (str): The player's unique identifier.
        """
        ...

    # -- Periods --

    @abstractmethod
    def save_period(self, period: RatingPeriod) -> None:
        """Persist a rating period header (without matches).

        Args:
            period (RatingPeriod): The period to save.
        """
        ...

    @abstractmethod
    def load_period(self, period_id: str) -> RatingPeriod | None:
        """Load a rating period and all its matches by ID.

        Args:
            period_id (str): The period's unique identifier.

        Returns:
            RatingPeriod | None: The period with matches if found, otherwise None.
        """
        ...

    @abstractmethod
    def load_all_periods(self) -> list[RatingPeriod]:
        """Load all persisted rating periods.

        Returns:
            list[RatingPeriod]: All periods in storage, ordered by opened_at.
        """
        ...

    # -- Matches --

    @abstractmethod
    def append_match(self, period_id: str, match: MatchResult) -> None:
        """Append a match result to an existing period.

        Args:
            period_id (str): The period to append the match to.
            match (MatchResult): The match result to persist.

        Raises:
            StorageError: If the period does not exist.
        """
        ...

    # -- Lifecycle --

    def close(self) -> None:
        """Optional teardown — close connections and flush buffers."""
        return None
