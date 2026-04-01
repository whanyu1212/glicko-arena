"""Conversions between Glicko-2 internal scale and display scale.

Glickman (2012) defines the transformation:
    μ  = (r  - 1500) / 173.7178
    φ  = RD          / 173.7178

where r is the familiar Elo-like display rating and RD is rating deviation
in display units.
"""

_SCALE = 173.7178


def rating_to_mu(rating: float) -> float:
    """Convert display rating r to Glicko-2 internal μ.

    Args:
        rating (float): Display rating (e.g. 1500).

    Returns:
        float: Internal μ value.
    """
    return (rating - 1500.0) / _SCALE


def mu_to_rating(mu: float) -> float:
    """Convert Glicko-2 internal μ to display rating r.

    Args:
        mu (float): Internal μ value.

    Returns:
        float: Display rating (e.g. 1500).
    """
    return _SCALE * mu + 1500.0


def rd_to_phi(rd: float) -> float:
    """Convert display RD to Glicko-2 internal φ.

    Args:
        rd (float): Display rating deviation (e.g. 200).

    Returns:
        float: Internal φ value.
    """
    return rd / _SCALE


def phi_to_rd(phi: float) -> float:
    """Convert Glicko-2 internal φ to display RD.

    Args:
        phi (float): Internal φ value.

    Returns:
        float: Display rating deviation (e.g. 200).
    """
    return _SCALE * phi
