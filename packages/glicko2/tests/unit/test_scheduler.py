"""Unit tests for tournament scheduler and stopping criteria."""


from glicko2.engine.player_pool import PlayerPool
from glicko2.models.player import Player
from glicko2.tournament.formats import double_round_robin, round_robin
from glicko2.tournament.scheduler import adaptive_pairs, closest_rated_pair, most_uncertain_pair
from glicko2.tournament.stopping import all_below_rd_threshold, top_k_separated


def _pool(**kwargs: tuple[float, float]) -> PlayerPool:
    """Build a pool from {id: (mu, phi)} pairs."""
    pool = PlayerPool()
    for pid, (mu, phi) in kwargs.items():
        pool.add(Player(id=pid, mu=mu, phi=phi, sigma=0.06))
    return pool


class TestScheduler:
    def test_most_uncertain_pair_returns_highest_phi(self):
        pool = _pool(a=(0.0, 2.0), b=(0.0, 0.5), c=(0.0, 1.0))
        pair = most_uncertain_pair(pool)
        assert pair is not None
        assert set(pair) == {"a", "c"}  # a(2.0) + c(1.0) = 3.0 > a+b or b+c

    def test_most_uncertain_pair_none_if_single_player(self):
        pool = _pool(a=(0.0, 1.0))
        assert most_uncertain_pair(pool) is None

    def test_closest_rated_pair(self):
        pool = _pool(a=(0.0, 1.0), b=(0.1, 1.0), c=(5.0, 1.0))
        pair = closest_rated_pair(pool)
        assert pair is not None
        assert set(pair) == {"a", "b"}

    def test_adaptive_pairs_returns_n(self):
        pool = _pool(a=(0.0, 1.0), b=(0.5, 1.0), c=(1.0, 1.0), d=(1.5, 1.0))
        pairs = adaptive_pairs(pool, n=3)
        assert len(pairs) == 3

    def test_adaptive_pairs_empty_pool(self):
        assert adaptive_pairs(PlayerPool(), n=5) == []


class TestFormats:
    def test_round_robin_count(self):
        ids = ["a", "b", "c", "d"]
        pairs = round_robin(ids)
        assert len(pairs) == 6  # C(4,2)

    def test_round_robin_no_self_play(self):
        for a, b in round_robin(["a", "b", "c"]):
            assert a != b

    def test_double_round_robin_count(self):
        ids = ["a", "b", "c"]
        pairs = double_round_robin(ids)
        assert len(pairs) == 6  # 3 * 2 ordered pairs

    def test_double_round_robin_both_directions(self):
        pairs = double_round_robin(["a", "b"])
        assert ("a", "b") in pairs
        assert ("b", "a") in pairs


class TestStopping:
    def test_all_below_rd_threshold_true(self):
        pool = _pool(a=(0.0, 1.0), b=(0.0, 1.2))
        assert all_below_rd_threshold(pool, max_phi=1.5) is True

    def test_all_below_rd_threshold_false(self):
        pool = _pool(a=(0.0, 1.0), b=(0.0, 2.0))
        assert all_below_rd_threshold(pool, max_phi=1.5) is False

    def test_top_k_separated_true(self):
        # Players far apart — no CI overlap
        pool = _pool(a=(10.0, 0.1), b=(0.0, 0.1), c=(-10.0, 0.1))
        assert top_k_separated(pool, k=3) is True

    def test_top_k_separated_false(self):
        # Players identical — CIs fully overlap
        pool = _pool(a=(0.0, 1.0), b=(0.0, 1.0), c=(0.0, 1.0))
        assert top_k_separated(pool, k=3) is False
