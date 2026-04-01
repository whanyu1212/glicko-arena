"""Confidence interval computation and calibration checks."""

import math

from glicko2.math.conversions import mu_to_rating, phi_to_rd


def rating_interval(
    mu: float,
    phi: float,
    z: float = 1.96,
) -> tuple[float, float]:
    """Confidence interval in display rating units.

    The interval is μ ± z·φ in Glicko-2 scale, converted to display units.
    Defaults to a 95% interval (z=1.96).

    Args:
        mu (float): Player's rating in Glicko-2 internal scale.
        phi (float): Player's rating deviation in Glicko-2 internal scale.
        z (float): Z-score for the desired confidence level. Defaults to 1.96 (95%).

    Returns:
        tuple[float, float]: (lower, upper) bounds in display rating units.
    """
    rd = phi_to_rd(phi)
    r = mu_to_rating(mu)
    return r - z * rd, r + z * rd


def intervals_overlap(
    mu_a: float, phi_a: float,
    mu_b: float, phi_b: float,
    z: float = 1.96,
) -> bool:
    """Return True if the confidence intervals of two players overlap.

    Args:
        mu_a (float): Player A's rating in Glicko-2 internal scale.
        phi_a (float): Player A's rating deviation in Glicko-2 internal scale.
        mu_b (float): Player B's rating in Glicko-2 internal scale.
        phi_b (float): Player B's rating deviation in Glicko-2 internal scale.
        z (float): Z-score for the confidence level. Defaults to 1.96 (95%).

    Returns:
        bool: True if the two intervals overlap, False if they are disjoint.
    """
    lo_a, hi_a = rating_interval(mu_a, phi_a, z)
    lo_b, hi_b = rating_interval(mu_b, phi_b, z)
    return lo_a <= hi_b and lo_b <= hi_a


def win_probability(mu: float, phi: float, mu_opp: float, phi_opp: float) -> float:
    """Approximate win probability accounting for both players' uncertainty.

    Uses the logistic approximation from Glickman (1999), simplified via
    the Glicko-2 g() function:
        g_combined = g(sqrt(φ² + φ_opp²))
        P = 1 / (1 + exp(−g_combined · (μ − μ_opp)))

    Args:
        mu (float): Player's rating in Glicko-2 internal scale.
        phi (float): Player's rating deviation in Glicko-2 internal scale.
        mu_opp (float): Opponent's rating in Glicko-2 internal scale.
        phi_opp (float): Opponent's rating deviation in Glicko-2 internal scale.

    Returns:
        float: Estimated win probability for the player in (0, 1).
    """
    phi_combined = math.sqrt(phi ** 2 + phi_opp ** 2)
    from glicko2.math.algorithm import g
    g_c = g(phi_combined)
    return 1.0 / (1.0 + math.exp(-g_c * (mu - mu_opp)))
