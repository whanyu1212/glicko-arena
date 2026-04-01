"""Adaptive matchup selection — choose the most informative pairings."""


from glicko2.engine.player_pool import PlayerPool
from glicko2.math.confidence import win_probability


def most_uncertain_pair(pool: PlayerPool) -> tuple[str, str] | None:
    """Return the pair of players with the highest combined φ (most uncertain).

    This maximises information gain per match.

    Args:
        pool (PlayerPool): The pool to select from.

    Returns:
        tuple[str, str] | None: A (player_a_id, player_b_id) pair, or None if
            fewer than two players exist in the pool.
    """
    players = pool.all()
    if len(players) < 2:
        return None

    best: tuple[str, str] | None = None
    best_score = -1.0
    for i in range(len(players)):
        for j in range(i + 1, len(players)):
            score = players[i].phi + players[j].phi
            if score > best_score:
                best_score = score
                best = (players[i].id, players[j].id)
    return best


def closest_rated_pair(pool: PlayerPool) -> tuple[str, str] | None:
    """Return the pair closest in μ (most competitive match).

    Args:
        pool (PlayerPool): The pool to select from.

    Returns:
        tuple[str, str] | None: A (player_a_id, player_b_id) pair, or None if
            fewer than two players exist in the pool.
    """
    players = sorted(pool.all(), key=lambda p: p.mu)
    if len(players) < 2:
        return None

    best: tuple[str, str] | None = None
    best_diff = float("inf")
    for i in range(len(players) - 1):
        diff = abs(players[i].mu - players[i + 1].mu)
        if diff < best_diff:
            best_diff = diff
            best = (players[i].id, players[i + 1].id)
    return best


def adaptive_pairs(
    pool: PlayerPool,
    n: int,
    target_win_prob: float = 0.55,
) -> list[tuple[str, str]]:
    """Select up to `n` pairs where expected win probability is near 50/50.

    Pairs are chosen greedily; the same player may appear in multiple pairs
    within a period.

    Args:
        pool (PlayerPool): The pool to select from.
        n (int): Maximum number of pairs to return.
        target_win_prob (float): Target win probability to optimise toward.
            Defaults to 0.55.

    Returns:
        list[tuple[str, str]]: Up to `n` (player_a_id, player_b_id) pairs,
            sorted by closeness to `target_win_prob`.
    """
    players = pool.all()
    if len(players) < 2:
        return []

    candidates: list[tuple[float, str, str]] = []
    for i in range(len(players)):
        for j in range(i + 1, len(players)):
            p = win_probability(players[i].mu, players[i].phi,
                                players[j].mu, players[j].phi)
            # score = closeness to target_win_prob (50/50 by default)
            score = -abs(p - target_win_prob)
            candidates.append((score, players[i].id, players[j].id))

    candidates.sort(reverse=True)
    return [(a, b) for _, a, b in candidates[:n]]
