"""Unit tests for inflation / drift utilities."""

import pytest

from glicko2.engine.drift import detect_inflation, normalize_ratings, phi_floor, soft_reset
from glicko2.engine.player_pool import PlayerPool
from glicko2.models.player import Player


def _pool(*mus: float) -> PlayerPool:
    pool = PlayerPool()
    for i, mu in enumerate(mus):
        pool.add(Player(id=str(i), mu=mu, phi=1.0, sigma=0.06))
    return pool


class TestDetectInflation:
    def test_zero_drift(self):
        pool = _pool(-1.0, 0.0, 1.0)
        assert detect_inflation(pool) == pytest.approx(0.0)

    def test_positive_drift(self):
        pool = _pool(1.0, 2.0, 3.0)  # mean = 2.0
        assert detect_inflation(pool) == pytest.approx(2.0)

    def test_empty_pool(self):
        assert detect_inflation(PlayerPool()) == pytest.approx(0.0)


class TestNormalizeRatings:
    def test_mean_becomes_zero(self):
        pool = _pool(1.0, 2.0, 3.0)
        normalize_ratings(pool)
        mean = sum(p.mu for p in pool.all()) / len(pool)
        assert mean == pytest.approx(0.0, abs=1e-10)

    def test_relative_order_preserved(self):
        pool = _pool(1.0, 3.0, 5.0)
        before = sorted(pool.ids(), key=lambda pid: pool.get(pid).mu)
        normalize_ratings(pool)
        after = sorted(pool.ids(), key=lambda pid: pool.get(pid).mu)
        assert before == after

    def test_phi_unchanged(self):
        pool = _pool(1.0, 2.0, 3.0)
        phis_before = {p.id: p.phi for p in pool.all()}
        normalize_ratings(pool)
        for pid, phi in phis_before.items():
            assert pool.get(pid).phi == pytest.approx(phi)


class TestSoftReset:
    def test_compression_zero_no_change(self):
        pool = _pool(2.0, -1.0, 3.0)
        mus_before = {p.id: p.mu for p in pool.all()}
        soft_reset(pool, compression=0.0)
        for pid, mu in mus_before.items():
            assert pool.get(pid).mu == pytest.approx(mu)

    def test_compression_one_full_reset(self):
        pool = _pool(2.0, -1.0, 3.0)
        soft_reset(pool, compression=1.0, target_mu=0.0)
        for p in pool.all():
            assert p.mu == pytest.approx(0.0)

    def test_compression_half(self):
        pool = _pool(2.0)
        soft_reset(pool, compression=0.5, target_mu=0.0)
        assert pool.get("0").mu == pytest.approx(1.0)

    def test_invalid_compression_raises(self):
        pool = _pool(1.0)
        with pytest.raises(ValueError):
            soft_reset(pool, compression=1.5)


class TestPhiFloor:
    def test_low_phi_raised(self):
        pool = PlayerPool()
        pool.add(Player(id="a", mu=0.0, phi=0.1, sigma=0.06))
        phi_floor(pool, min_phi=0.5)
        assert pool.get("a").phi == pytest.approx(0.5)

    def test_high_phi_unchanged(self):
        pool = PlayerPool()
        pool.add(Player(id="a", mu=0.0, phi=1.0, sigma=0.06))
        phi_floor(pool, min_phi=0.5)
        assert pool.get("a").phi == pytest.approx(1.0)
