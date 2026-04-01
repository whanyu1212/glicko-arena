"""Unit tests for core Glicko-2 math.

Reference values taken directly from Mark Glickman's worked example (2012):
http://www.glicko.net/glicko/glicko2.pdf
"""

import math

import pytest
from glicko2.math.algorithm import E, g, update_rating
from glicko2.math.conversions import mu_to_rating, phi_to_rd, rating_to_mu, rd_to_phi

# ---------------------------------------------------------------------------
# Conversions
# ---------------------------------------------------------------------------

class TestConversions:
    def test_rating_to_mu_default(self):
        assert rating_to_mu(1500) == pytest.approx(0.0)

    def test_mu_to_rating_default(self):
        assert mu_to_rating(0.0) == pytest.approx(1500.0)

    def test_round_trip_rating(self):
        for r in (1000, 1200, 1500, 1800, 2200):
            assert mu_to_rating(rating_to_mu(r)) == pytest.approx(r)

    def test_rd_to_phi(self):
        assert rd_to_phi(173.7178) == pytest.approx(1.0, rel=1e-4)

    def test_phi_to_rd(self):
        assert phi_to_rd(1.0) == pytest.approx(173.7178, rel=1e-4)

    def test_round_trip_rd(self):
        for rd in (30, 100, 200, 350):
            assert phi_to_rd(rd_to_phi(rd)) == pytest.approx(rd)


# ---------------------------------------------------------------------------
# Elementary functions g() and E()
# ---------------------------------------------------------------------------

class TestGFunction:
    def test_g_zero_phi(self):
        # g(0) = 1 / sqrt(1) = 1.0
        assert g(0.0) == pytest.approx(1.0)

    def test_g_decreasing(self):
        # g is strictly decreasing in φ
        assert g(0.5) > g(1.0) > g(2.0)

    def test_g_paper_value(self):
        # From Glickman (2012): opponent RD=30 → φ=30/173.7178 ≈ 0.17269
        phi = rd_to_phi(30)
        assert g(phi) == pytest.approx(0.9955, abs=1e-4)

    def test_g_always_positive(self):
        for phi in (0.01, 0.5, 1.0, 3.0, 10.0):
            assert g(phi) > 0


class TestEFunction:
    def test_equal_ratings(self):
        # Equal μ, any φ → E = 0.5
        assert E(0.0, 0.0, 1.0) == pytest.approx(0.5)

    def test_higher_mu_favoured(self):
        assert E(1.0, 0.0, 1.0) > 0.5
        assert E(-1.0, 0.0, 1.0) < 0.5

    def test_large_phi_compresses_toward_half(self):
        # Large opponent φ → g(φ) small → E closer to 0.5
        e_small_phi = E(1.0, 0.0, 0.1)
        e_large_phi = E(1.0, 0.0, 5.0)
        assert abs(e_large_phi - 0.5) < abs(e_small_phi - 0.5)

    def test_e_bounds(self):
        for mu, mu_j, phi_j in [(2, 0, 1), (-2, 0, 1), (0, 0, 0.01)]:
            e = E(mu, mu_j, phi_j)
            assert 0.0 < e < 1.0


# ---------------------------------------------------------------------------
# update_rating — Glickman (2012) worked example
# ---------------------------------------------------------------------------

class TestUpdateRating:
    """Verify against Glickman's own reference values (Table 1, p. 3)."""

    @pytest.fixture()
    def paper_inputs(self):
        mu    = rating_to_mu(1500)   # 0.0
        phi   = rd_to_phi(200)       # ≈ 1.1513
        sigma = 0.06
        opponents = [
            (rating_to_mu(1400), rd_to_phi(30),  1.0),
            (rating_to_mu(1550), rd_to_phi(100), 0.0),
            (rating_to_mu(1700), rd_to_phi(300), 0.0),
        ]
        return mu, phi, sigma, opponents

    def test_new_rating(self, paper_inputs):
        mu, phi, sigma, opps = paper_inputs
        result = update_rating(mu, phi, sigma, opps, tau=0.5)
        assert mu_to_rating(result.mu) == pytest.approx(1464.06, abs=0.1)

    def test_new_rd(self, paper_inputs):
        mu, phi, sigma, opps = paper_inputs
        result = update_rating(mu, phi, sigma, opps, tau=0.5)
        assert phi_to_rd(result.phi) == pytest.approx(151.52, abs=0.1)

    def test_new_sigma(self, paper_inputs):
        mu, phi, sigma, opps = paper_inputs
        result = update_rating(mu, phi, sigma, opps, tau=0.5)
        assert result.sigma == pytest.approx(0.059996, abs=1e-5)

    def test_no_games_inflates_rd_only(self):
        mu, phi, sigma = 0.0, 1.0, 0.06
        result = update_rating(mu, phi, sigma, [], tau=0.5)
        assert result.mu == pytest.approx(mu)
        assert result.sigma == pytest.approx(sigma)
        expected_phi = math.sqrt(phi**2 + sigma**2)
        assert result.phi == pytest.approx(expected_phi)

    def test_win_increases_rating(self):
        mu = rating_to_mu(1500)
        phi = rd_to_phi(200)
        result = update_rating(mu, phi, 0.06, [(rating_to_mu(1500), phi, 1.0)])
        assert result.mu > mu

    def test_loss_decreases_rating(self):
        mu = rating_to_mu(1500)
        phi = rd_to_phi(200)
        result = update_rating(mu, phi, 0.06, [(rating_to_mu(1500), phi, 0.0)])
        assert result.mu < mu

    def test_draw_against_equal_no_mu_change(self):
        mu = rating_to_mu(1500)
        phi = rd_to_phi(200)
        result = update_rating(mu, phi, 0.06, [(mu, phi, 0.5)])
        assert result.mu == pytest.approx(mu, abs=1e-9)

    def test_phi_always_decreases_with_games(self):
        mu, phi, sigma = 0.0, 1.5, 0.06
        opponents = [(0.0, 1.0, 1.0), (0.5, 0.8, 0.0)]
        result = update_rating(mu, phi, sigma, opponents)
        # φ should shrink when games are played (more certainty)
        assert result.phi < phi

    def test_tau_affects_sigma(self):
        mu, phi, sigma = 0.0, 1.1513, 0.06
        opps = [(rating_to_mu(1400), rd_to_phi(30), 1.0)]
        r_low_tau  = update_rating(mu, phi, sigma, opps, tau=0.2)
        r_high_tau = update_rating(mu, phi, sigma, opps, tau=1.2)
        # Higher τ allows more volatility change
        assert abs(r_high_tau.sigma - sigma) >= abs(r_low_tau.sigma - sigma)


# ---------------------------------------------------------------------------
# Input validation
# ---------------------------------------------------------------------------

class TestUpdateRatingValidation:
    def test_non_finite_mu_raises(self):
        with pytest.raises(ValueError, match="mu"):
            update_rating(float("inf"), 1.0, 0.06, [])

    def test_zero_phi_raises(self):
        with pytest.raises(ValueError, match="phi"):
            update_rating(0.0, 0.0, 0.06, [])

    def test_negative_phi_raises(self):
        with pytest.raises(ValueError, match="phi"):
            update_rating(0.0, -1.0, 0.06, [])

    def test_zero_sigma_raises(self):
        with pytest.raises(ValueError, match="sigma"):
            update_rating(0.0, 1.0, 0.0, [])

    def test_zero_tau_raises(self):
        with pytest.raises(ValueError, match="tau"):
            update_rating(0.0, 1.0, 0.06, [(0.0, 1.0, 1.0)], tau=0.0)

    def test_negative_tau_raises(self):
        with pytest.raises(ValueError, match="tau"):
            update_rating(0.0, 1.0, 0.06, [(0.0, 1.0, 1.0)], tau=-0.1)

    def test_opponent_score_out_of_range_raises(self):
        with pytest.raises(ValueError, match="score"):
            update_rating(0.0, 1.0, 0.06, [(0.0, 1.0, 1.5)])

    def test_opponent_phi_zero_raises(self):
        with pytest.raises(ValueError, match="phi_j"):
            update_rating(0.0, 1.0, 0.06, [(0.0, 0.0, 1.0)])

    def test_opponent_mu_non_finite_raises(self):
        with pytest.raises(ValueError, match="mu_j"):
            update_rating(0.0, 1.0, 0.06, [(float("nan"), 1.0, 1.0)])


# ---------------------------------------------------------------------------
# Numerical stability
# ---------------------------------------------------------------------------

class TestNumericalStability:
    def test_extreme_rating_gap_does_not_overflow(self):
        """E() must not raise OverflowError for very large rating differences."""
        mu = rating_to_mu(3000)
        mu_j = rating_to_mu(100)
        phi_j = rd_to_phi(350)
        result = E(mu, mu_j, phi_j)
        assert math.isfinite(result)
        assert result > 0.99  # strong favourite

    def test_extreme_underdog_does_not_underflow(self):
        mu = rating_to_mu(100)
        mu_j = rating_to_mu(3000)
        phi_j = rd_to_phi(350)
        result = E(mu, mu_j, phi_j)
        assert math.isfinite(result)
        assert result < 0.01  # strong underdog

    def test_update_rating_extreme_gap_is_finite(self):
        mu = rating_to_mu(3000)
        phi = rd_to_phi(200)
        mu_j = rating_to_mu(100)
        phi_j = rd_to_phi(350)
        result = update_rating(mu, phi, 0.06, [(mu_j, phi_j, 0.0)])
        assert math.isfinite(result.mu)
        assert math.isfinite(result.phi)
        assert math.isfinite(result.sigma)
