"""Core Glicko-2 math — pure functions, no side effects.

All values are in Glicko-2 internal scale (μ, φ, σ) unless noted.

Reference: Mark Glickman, "Example of the Glicko-2 system" (2012).
http://www.glicko.net/glicko/glicko2.pdf
"""

import math
from typing import NamedTuple

from glicko2.exceptions import ConvergenceError

# Glickman's recommended system constant τ; constrains σ change per period.
# Typical range: 0.3 – 1.2. Lower = more stable volatility.
DEFAULT_TAU: float = 0.5

# Illinois algorithm convergence tolerance (Step 5 of the algorithm).
_EPSILON: float = 1e-6

# Maximum iterations for the Illinois (regula falsi) root-finding loop.
_MAX_ITER: int = 500


# ---------------------------------------------------------------------------
# Elementary functions (Steps 1–3 of Glickman's algorithm)
# ---------------------------------------------------------------------------

def g(phi: float) -> float:
    """g(φ) — reduction factor for opponent deviation (Glickman eq. 1).

    g(φ) = 1 / sqrt(1 + 3φ² / π²)

    Args:
        phi (float): Rating deviation in Glicko-2 internal scale.

    Returns:
        float: Reduction factor in (0, 1].
    """
    return 1.0 / math.sqrt(1.0 + 3.0 * phi ** 2 / math.pi ** 2)


def E(mu: float, mu_j: float, phi_j: float) -> float:
    """Expected score E(μ, μⱼ, φⱼ) — win probability (Glickman eq. 2).

    E = 1 / (1 + exp(−g(φⱼ) · (μ − μⱼ)))

    Uses a numerically stable formulation to avoid overflow for large
    rating differences.

    Args:
        mu (float): Player's rating in Glicko-2 internal scale.
        mu_j (float): Opponent's rating in Glicko-2 internal scale.
        phi_j (float): Opponent's rating deviation in Glicko-2 internal scale.

    Returns:
        float: Expected score in (0, 1).
    """
    # Numerically stable logistic: avoid exp overflow for large |x|.
    # z = g(φⱼ) · (μ − μⱼ); E = 1 / (1 + exp(−z))
    z = g(phi_j) * (mu - mu_j)
    if z >= 0:
        return 1.0 / (1.0 + math.exp(-z))
    ez = math.exp(z)
    return ez / (1.0 + ez)


# ---------------------------------------------------------------------------
# Variance and update intermediates (Steps 3–4)
# ---------------------------------------------------------------------------

class _Intermediates(NamedTuple):
    v: float       # estimated variance of the player's rating
    delta: float   # estimated improvement


def _compute_intermediates(
    mu: float,
    opponents: list[tuple[float, float, float]],  # (mu_j, phi_j, score_j)
) -> _Intermediates:
    """Compute v and Δ from a list of opponents and outcomes.

    Args:
        mu (float): Player's rating in Glicko-2 internal scale.
        opponents (list[tuple[float, float, float]]): List of (μⱼ, φⱼ, sⱼ) tuples.

    Returns:
        _Intermediates: Named tuple of (v, delta). v is inf when opponents is empty.
    """
    if not opponents:
        # No games played; v is undefined but we signal with inf so the
        # caller knows to skip the improvement step.
        return _Intermediates(v=float("inf"), delta=0.0)

    v_inv = 0.0
    delta_sum = 0.0
    for mu_j, phi_j, s_j in opponents:
        g_j = g(phi_j)
        e_j = E(mu, mu_j, phi_j)
        v_inv += g_j ** 2 * e_j * (1.0 - e_j)
        delta_sum += g_j * (s_j - e_j)

    v = 1.0 / v_inv
    delta = v * delta_sum
    return _Intermediates(v=v, delta=delta)


# ---------------------------------------------------------------------------
# Illinois (regula falsi) root-finding for new σ (Step 5)
# ---------------------------------------------------------------------------

def _illinois(
    sigma: float,
    phi: float,
    v: float,
    delta: float,
    tau: float,
) -> float:
    """Find the new volatility σ′ via the Illinois algorithm (Glickman Step 5).

    Solves f(x) = 0 where:
        f(x) = exp(x) · (Δ² − φ² − v − exp(x)) / (2(φ² + v + exp(x))²)
               − (x − ln σ²) / τ²

    Args:
        sigma (float): Current volatility σ.
        phi (float): Current rating deviation φ in Glicko-2 internal scale.
        v (float): Estimated variance of the player's rating.
        delta (float): Estimated improvement over the period.
        tau (float): System constant τ constraining volatility change.

    Raises:
        ConvergenceError: If the root-finding loop does not converge within
            _MAX_ITER iterations.

    Returns:
        float: New volatility σ′.
    """
    a = math.log(sigma ** 2)
    phi2 = phi ** 2
    tau2 = tau ** 2

    def f(x: float) -> float:
        ex = math.exp(x)
        numer = ex * (delta ** 2 - phi2 - v - ex)
        denom = 2.0 * (phi2 + v + ex) ** 2
        return numer / denom - (x - a) / tau2

    # Step 5.2 — initialise the bracketing interval [A, B]
    A = a
    fa = f(A)

    if delta ** 2 > phi2 + v:
        B = math.log(delta ** 2 - phi2 - v)
    else:
        k = 1
        while f(a - k * tau) < 0:
            k += 1
        B = a - k * tau
    fb = f(B)

    # Step 5.3 — Illinois iteration
    for _ in range(_MAX_ITER):
        C = A + (A - B) * fa / (fb - fa)
        fc = f(C)

        if fc * fb <= 0:
            A, fa = B, fb
        else:
            fa /= 2.0

        B, fb = C, fc

        if abs(B - A) < _EPSILON:
            break
    else:
        raise ConvergenceError(
            f"σ update did not converge after {_MAX_ITER} iterations "
            f"(|B−A|={abs(B-A):.2e})"
        )

    return math.exp(B / 2.0)


# ---------------------------------------------------------------------------
# Full period update (Steps 5–7)
# ---------------------------------------------------------------------------

class UpdatedRating(NamedTuple):
    mu: float
    phi: float
    sigma: float


def update_rating(
    mu: float,
    phi: float,
    sigma: float,
    opponents: list[tuple[float, float, float]],  # (mu_j, phi_j, score_j)
    tau: float = DEFAULT_TAU,
) -> UpdatedRating:
    """Compute new (μ′, φ′, σ′) after one rating period.

    If the player had no games, only the RD is inflated (φ* step) and μ, σ
    are unchanged — as specified in Glickman Step 6.

    Args:
        mu (float): Current μ in Glicko-2 internal scale. Must be finite.
        phi (float): Current φ in Glicko-2 internal scale. Must be > 0.
        sigma (float): Current volatility σ. Must be > 0.
        opponents (list[tuple[float, float, float]]): List of (μⱼ, φⱼ, sⱼ)
            tuples for each game played in the period. Pass an empty list if
            the player had no games. Each sⱼ must be in [0, 1] and each φⱼ
            must be > 0.
        tau (float): System constant τ. Must be > 0. Defaults to 0.5.

    Raises:
        ValueError: If phi, sigma, or tau are not positive, if mu is not
            finite, or if any opponent score is outside [0, 1].

    Returns:
        UpdatedRating: Named tuple of (mu, phi, sigma) in Glicko-2 internal scale.
    """
    if not math.isfinite(mu):
        raise ValueError(f"mu must be finite, got {mu}")
    if phi <= 0:
        raise ValueError(f"phi must be > 0, got {phi}")
    if sigma <= 0:
        raise ValueError(f"sigma must be > 0, got {sigma}")
    if tau <= 0:
        raise ValueError(f"tau must be > 0, got {tau}")
    for i, (mu_j, phi_j, s_j) in enumerate(opponents):
        if not math.isfinite(mu_j):
            raise ValueError(f"opponents[{i}]: mu_j must be finite, got {mu_j}")
        if phi_j <= 0:
            raise ValueError(f"opponents[{i}]: phi_j must be > 0, got {phi_j}")
        if not 0.0 <= s_j <= 1.0:
            raise ValueError(f"opponents[{i}]: score must be in [0, 1], got {s_j}")

    # Step 6: if no games, only inflate RD
    if not opponents:
        phi_star = math.sqrt(phi ** 2 + sigma ** 2)
        return UpdatedRating(mu=mu, phi=phi_star, sigma=sigma)

    inter = _compute_intermediates(mu, opponents)
    v, delta = inter.v, inter.delta

    # Step 5: new volatility
    sigma_new = _illinois(sigma, phi, v, delta, tau)

    # Step 6: new pre-rating-period deviation φ*
    phi_star = math.sqrt(phi ** 2 + sigma_new ** 2)

    # Step 7: update φ′ and μ′
    phi_new = 1.0 / math.sqrt(1.0 / phi_star ** 2 + 1.0 / v)
    mu_new = mu + phi_new ** 2 * sum(
        g(phi_j) * (s_j - E(mu, mu_j, phi_j))
        for mu_j, phi_j, s_j in opponents
    )

    return UpdatedRating(mu=mu_new, phi=phi_new, sigma=sigma_new)
