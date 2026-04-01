"""RatingEngine — orchestrates period processing and state management."""

from collections import defaultdict

from glicko2.engine.player_pool import PlayerPool
from glicko2.math.algorithm import DEFAULT_TAU, update_rating
from glicko2.models.player import Player
from glicko2.models.rating_period import RatingPeriod


class RatingEngine:
    """Processes rating periods and keeps player ratings up to date.

    Each MatchResult represents one game. The engine derives the opponent's
    perspective internally — callers must not insert both sides manually.

    Usage::

        engine = RatingEngine(tau=0.5)
        engine.pool.get_or_create("alice")
        engine.pool.get_or_create("bob")

        period = RatingPeriod(id="round-1")
        period.add_match(MatchResult("alice", "bob", 1.0))  # one entry per game

        engine.process_period(period)
        print(engine.pool.get("alice").mu)
        print(engine.pool.get("bob").mu)
    """

    def __init__(self, tau: float = DEFAULT_TAU) -> None:
        self.tau = tau
        self.pool = PlayerPool()

    def process_period(self, period: RatingPeriod) -> None:
        """Update all player ratings based on the matches in `period`.

        Each MatchResult is treated as one game. The mirror (opponent's
        perspective) is derived automatically, so callers must record each
        game exactly once. All rating updates are computed from pre-period
        state and applied atomically.

        The period may be open or closed; this method does not close it.
        Players that appear in the period but are not yet in the pool are
        auto-created with default ratings before processing.

        Args:
            period (RatingPeriod): The period containing matches to process.
        """
        # Auto-register unknown players
        for pid in period.player_ids():
            self.pool.get_or_create(pid)

        # Build opponent lists for both sides of every recorded game
        games: dict[str, list[tuple[float, float, float]]] = defaultdict(list)
        for match in period.matches:
            player = self.pool.get(match.player_id)
            opponent = self.pool.get(match.opponent_id)
            # Rated player's perspective
            games[match.player_id].append(
                (opponent.mu, opponent.phi, match.score)
            )
            # Opponent's perspective — derived from the mirror
            games[match.opponent_id].append(
                (player.mu, player.phi, 1.0 - match.score)
            )

        # Compute all updates using pre-period ratings, then apply atomically
        updates: dict[str, Player] = {}
        for player in self.pool.all():
            opp_list = games.get(player.id, [])
            result = update_rating(
                player.mu, player.phi, player.sigma, opp_list, tau=self.tau
            )
            updates[player.id] = Player(
                id=player.id,
                mu=result.mu,
                phi=result.phi,
                sigma=result.sigma,
                num_periods=player.num_periods + (1 if opp_list else 0),
                metadata=player.metadata,
            )

        for updated in updates.values():
            self.pool.update(updated)
