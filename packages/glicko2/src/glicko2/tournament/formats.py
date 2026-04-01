"""Tournament format generators — produce lists of (player_a, player_b) pairings."""

import itertools
import random

from glicko2.engine.player_pool import PlayerPool
from glicko2.tournament.scheduler import adaptive_pairs


def round_robin(player_ids: list[str]) -> list[tuple[str, str]]:
    """Every player faces every other player exactly once.

    Args:
        player_ids (list[str]): List of player IDs to pair.

    Returns:
        list[tuple[str, str]]: C(n, 2) unordered pairs.
    """
    return list(itertools.combinations(player_ids, 2))


def double_round_robin(player_ids: list[str]) -> list[tuple[str, str]]:
    """Every ordered pair plays — each player is home and away once.

    Args:
        player_ids (list[str]): List of player IDs to pair.

    Returns:
        list[tuple[str, str]]: n*(n-1) ordered pairs.
    """
    pairs = []
    for a, b in itertools.combinations(player_ids, 2):
        pairs.append((a, b))
        pairs.append((b, a))
    return pairs


def swiss(
    pool: PlayerPool,
    rounds: int,
    *,
    seed: int | None = None,
) -> list[list[tuple[str, str]]]:
    """Swiss-style pairing: each round pairs players with similar records.

    Players are sorted by μ before each round and paired sequentially.

    Args:
        pool (PlayerPool): The pool to draw players from.
        rounds (int): Number of rounds to generate.
        seed (int | None): Optional RNG seed for reproducibility. Defaults to None.

    Returns:
        list[list[tuple[str, str]]]: A list of rounds, each round being a list
            of (player_a_id, player_b_id) pairs.
    """
    rng = random.Random(seed)
    players = pool.ids()
    schedule: list[list[tuple[str, str]]] = []

    for _ in range(rounds):
        sorted_players = sorted(players, key=lambda pid: pool.get(pid).mu, reverse=True)
        # Shuffle within score groups to avoid always matching the same pair
        rng.shuffle(sorted_players)
        sorted_players.sort(key=lambda pid: pool.get(pid).mu, reverse=True)

        round_pairs: list[tuple[str, str]] = []
        unpaired = list(sorted_players)
        while len(unpaired) >= 2:
            a = unpaired.pop(0)
            b = unpaired.pop(0)
            round_pairs.append((a, b))
        schedule.append(round_pairs)

    return schedule


def adaptive(
    pool: PlayerPool,
    rounds: int,
    matches_per_round: int = 4,
) -> list[list[tuple[str, str]]]:
    """Adaptive format: each round selects the most informative pairings.

    Args:
        pool (PlayerPool): The pool to draw players from.
        rounds (int): Number of rounds to generate.
        matches_per_round (int): Maximum pairs per round. Defaults to 4.

    Returns:
        list[list[tuple[str, str]]]: A list of rounds, each round being a list
            of (player_a_id, player_b_id) pairs selected by `adaptive_pairs`.
    """
    schedule: list[list[tuple[str, str]]] = []
    for _ in range(rounds):
        pairs = adaptive_pairs(pool, n=matches_per_round)
        schedule.append(pairs)
    return schedule
