"""Stopping criteria for tournaments."""

from glicko2.engine.player_pool import PlayerPool
from glicko2.math.confidence import intervals_overlap


def all_below_rd_threshold(pool: PlayerPool, max_phi: float = 1.5) -> bool:
    """Return True when every player's φ is below `max_phi`.

    A common stopping criterion: keep playing until all RDs are
    sufficiently small (reliable ratings).

    Args:
        pool (PlayerPool): The pool to check.
        max_phi (float): Maximum allowed φ. Defaults to 1.5.

    Returns:
        bool: True if all players have φ ≤ max_phi.
    """
    return all(p.phi <= max_phi for p in pool.all())


def top_k_separated(pool: PlayerPool, k: int = 3, z: float = 1.96) -> bool:
    """Return True when the top-k players have non-overlapping CIs.

    Useful as a stopping criterion when you only care about the leaderboard
    top, not precise ratings for everyone.

    Args:
        pool (PlayerPool): The pool to check.
        k (int): Number of top players to consider. Defaults to 3.
        z (float): Z-score for the confidence level. Defaults to 1.96 (95%).

    Returns:
        bool: True if consecutive CIs among the top-k players are all disjoint.
    """
    players = sorted(pool.all(), key=lambda p: p.mu, reverse=True)
    top = players[:k]
    for i in range(len(top) - 1):
        if intervals_overlap(top[i].mu, top[i].phi, top[i + 1].mu, top[i + 1].phi, z):
            return False
    return True
