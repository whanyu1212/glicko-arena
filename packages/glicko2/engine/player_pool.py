"""PlayerPool — in-memory collection of players."""

from glicko2.exceptions import UnknownPlayerError
from glicko2.models.player import Player


class PlayerPool:
    """Manages a mutable collection of Player objects keyed by ID."""

    def __init__(self) -> None:
        self._players: dict[str, Player] = {}

    def add(self, player: Player) -> None:
        """Add a player to the pool, overwriting any existing entry with the same ID.

        Args:
            player (Player): The player to add.
        """
        self._players[player.id] = player

    def get(self, player_id: str) -> Player:
        """Retrieve a player by ID.

        Args:
            player_id (str): The player's unique identifier.

        Raises:
            UnknownPlayerError: If no player with that ID exists in the pool.

        Returns:
            Player: The matching player.
        """
        try:
            return self._players[player_id]
        except KeyError:
            raise UnknownPlayerError(player_id) from None

    def get_or_create(
        self,
        player_id: str,
        *,
        mu: float = 0.0,
        phi: float = 2.014761,
        sigma: float = 0.06,
    ) -> Player:
        """Return the player if they exist, otherwise create them with default ratings.

        Args:
            player_id (str): The player's unique identifier.
            mu (float): Initial μ if the player is new. Defaults to 0.0 (display 1500).
            phi (float): Initial φ if the player is new. Defaults to 2.014761 (RD 350).
            sigma (float): Initial volatility if the player is new. Defaults to 0.06.

        Returns:
            Player: The existing or newly created player.
        """
        if player_id not in self._players:
            self._players[player_id] = Player(
                id=player_id, mu=mu, phi=phi, sigma=sigma
            )
        return self._players[player_id]

    def update(self, player: Player) -> None:
        """Replace an existing player's entry in the pool.

        Args:
            player (Player): Updated player instance. Must already exist in the pool.

        Raises:
            UnknownPlayerError: If the player's ID is not found in the pool.
        """
        if player.id not in self._players:
            raise UnknownPlayerError(player.id)
        self._players[player.id] = player

    def __contains__(self, player_id: str) -> bool:
        return player_id in self._players

    def __len__(self) -> int:
        return len(self._players)

    def all(self) -> list[Player]:
        """Return all players in the pool.

        Returns:
            list[Player]: All players as a list (unordered).
        """
        return list(self._players.values())

    def ids(self) -> list[str]:
        """Return all player IDs in the pool.

        Returns:
            list[str]: All player IDs as a list (unordered).
        """
        return list(self._players.keys())
