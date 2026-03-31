"""Rating drift detection, normalization, and soft-reset utilities."""


from glicko2.engine.player_pool import PlayerPool
from glicko2.models.player import Player


def detect_inflation(pool: PlayerPool, baseline_mu: float = 0.0) -> float:
    """Return the mean μ drift from `baseline_mu` across all players.

    Args:
        pool (PlayerPool): The pool to measure.
        baseline_mu (float): The expected mean μ. Defaults to 0.0.

    Returns:
        float: Mean drift. Positive means the pool has inflated upward.
    """
    players = pool.all()
    if not players:
        return 0.0
    return sum(p.mu - baseline_mu for p in players) / len(players)


def normalize_ratings(pool: PlayerPool, target_mu: float = 0.0) -> None:
    """Shift all player μ values so the pool mean equals `target_mu`.

    This is a lossless operation — relative orderings are preserved.

    Args:
        pool (PlayerPool): The pool to normalize in-place.
        target_mu (float): The desired pool mean μ. Defaults to 0.0.
    """
    drift = detect_inflation(pool, baseline_mu=target_mu)
    for player in pool.all():
        updated = Player(
            id=player.id,
            mu=player.mu - drift,
            phi=player.phi,
            sigma=player.sigma,
            num_periods=player.num_periods,
            metadata=player.metadata,
        )
        pool.update(updated)


def soft_reset(
    pool: PlayerPool,
    compression: float = 0.5,
    target_mu: float = 0.0,
    target_phi: float = 2.014761,
) -> None:
    """Move each player partway back toward default ratings.

    Args:
        pool (PlayerPool): The pool to update in-place.
        compression (float): 0.0 = no change, 1.0 = full reset to defaults.
            Defaults to 0.5.
        target_mu (float): The μ to compress toward. Defaults to 0.0.
        target_phi (float): The φ to compress toward. Defaults to 2.014761 (RD 350).

    Raises:
        ValueError: If compression is not in [0, 1].
    """
    if not 0.0 <= compression <= 1.0:
        raise ValueError(f"compression must be in [0, 1], got {compression}")

    for player in pool.all():
        new_mu = player.mu + compression * (target_mu - player.mu)
        new_phi = player.phi + compression * (target_phi - player.phi)
        updated = Player(
            id=player.id,
            mu=new_mu,
            phi=new_phi,
            sigma=player.sigma,
            num_periods=player.num_periods,
            metadata=player.metadata,
        )
        pool.update(updated)


def phi_floor(pool: PlayerPool, min_phi: float = 0.5) -> None:
    """Ensure no player's φ falls below `min_phi`, preventing over-certainty.

    Args:
        pool (PlayerPool): The pool to update in-place.
        min_phi (float): Minimum allowed φ. Defaults to 0.5.
    """
    for player in pool.all():
        if player.phi < min_phi:
            updated = Player(
                id=player.id,
                mu=player.mu,
                phi=min_phi,
                sigma=player.sigma,
                num_periods=player.num_periods,
                metadata=player.metadata,
            )
            pool.update(updated)
