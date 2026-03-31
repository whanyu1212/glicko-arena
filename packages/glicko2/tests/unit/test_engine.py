"""Unit tests for RatingEngine and PlayerPool."""

import pytest

from glicko2 import MatchResult, RatingEngine, RatingPeriod
from glicko2.engine.player_pool import PlayerPool
from glicko2.exceptions import InvalidMatchError, UnknownPlayerError
from glicko2.models.player import Player


class TestPlayerPool:
    def test_add_and_get(self):
        pool = PlayerPool()
        p = Player(id="alice")
        pool.add(p)
        assert pool.get("alice").id == "alice"

    def test_get_unknown_raises(self):
        pool = PlayerPool()
        with pytest.raises(UnknownPlayerError):
            pool.get("ghost")

    def test_get_or_create(self):
        pool = PlayerPool()
        p = pool.get_or_create("alice")
        assert p.id == "alice"
        # Second call returns existing player
        p2 = pool.get_or_create("alice")
        assert p2.id == "alice"
        assert len(pool) == 1

    def test_contains(self):
        pool = PlayerPool()
        pool.get_or_create("alice")
        assert "alice" in pool
        assert "bob" not in pool

    def test_update_unknown_raises(self):
        pool = PlayerPool()
        with pytest.raises(UnknownPlayerError):
            pool.update(Player(id="ghost"))

    def test_all_and_ids(self):
        pool = PlayerPool()
        pool.get_or_create("a")
        pool.get_or_create("b")
        assert set(pool.ids()) == {"a", "b"}
        assert len(pool.all()) == 2


class TestMatchResult:
    def test_same_player_raises(self):
        with pytest.raises(InvalidMatchError):
            MatchResult("alice", "alice", 1.0)

    def test_invalid_score_raises(self):
        with pytest.raises(InvalidMatchError):
            MatchResult("alice", "bob", 1.5)

    def test_continuous_score_accepted(self):
        m = MatchResult("alice", "bob", 0.73)
        assert m.score == 0.73
        assert m.mirror().score == pytest.approx(0.27)

    def test_mirror(self):
        m = MatchResult("alice", "bob", 1.0)
        mirrored = m.mirror()
        assert mirrored.player_id == "bob"
        assert mirrored.opponent_id == "alice"
        assert mirrored.score == 0.0


class TestRatingEngine:
    def test_auto_registers_unknown_players(self):
        engine = RatingEngine()
        period = RatingPeriod(id="p1")
        period.add_match(MatchResult("alice", "bob", 1.0))
        engine.process_period(period)
        assert "alice" in engine.pool
        assert "bob" in engine.pool

    def test_winner_gains_rating(self):
        engine = RatingEngine()
        engine.pool.get_or_create("alice")
        engine.pool.get_or_create("bob")
        mu_before = engine.pool.get("alice").mu

        period = RatingPeriod(id="p1")
        period.add_match(MatchResult("alice", "bob", 1.0))
        engine.process_period(period)

        assert engine.pool.get("alice").mu > mu_before

    def test_loser_loses_rating(self):
        engine = RatingEngine()
        engine.pool.get_or_create("alice")
        engine.pool.get_or_create("bob")
        mu_before = engine.pool.get("bob").mu

        period = RatingPeriod(id="p1")
        period.add_match(MatchResult("alice", "bob", 1.0))
        engine.process_period(period)

        assert engine.pool.get("bob").mu < mu_before

    def test_single_entry_updates_both_players(self):
        """One MatchResult must update both player_id and opponent_id."""
        engine = RatingEngine()
        engine.pool.get_or_create("alice")
        engine.pool.get_or_create("bob")
        mu_alice_before = engine.pool.get("alice").mu
        mu_bob_before = engine.pool.get("bob").mu

        period = RatingPeriod(id="p1")
        period.add_match(MatchResult("alice", "bob", 1.0))
        engine.process_period(period)

        assert engine.pool.get("alice").mu != mu_alice_before
        assert engine.pool.get("bob").mu != mu_bob_before

    def test_num_periods_increments_only_for_active_players(self):
        """num_periods must only increment for players who played that period."""
        engine = RatingEngine()
        engine.pool.get_or_create("alice")
        engine.pool.get_or_create("bob")
        engine.pool.get_or_create("carol")  # never plays

        for i in range(3):
            period = RatingPeriod(id=f"p{i}")
            period.add_match(MatchResult("alice", "bob", 1.0))
            engine.process_period(period)

        assert engine.pool.get("alice").num_periods == 3
        assert engine.pool.get("bob").num_periods == 3
        assert engine.pool.get("carol").num_periods == 0

    def test_inactive_player_phi_inflates(self):
        engine = RatingEngine()
        engine.pool.get_or_create("alice")
        engine.pool.get_or_create("bob")
        engine.pool.get_or_create("carol")  # will never play
        phi_before = engine.pool.get("carol").phi

        period = RatingPeriod(id="p1")
        period.add_match(MatchResult("alice", "bob", 1.0))
        engine.process_period(period)

        assert engine.pool.get("carol").phi > phi_before

    def test_ratings_computed_from_pre_period_state(self):
        """All ratings must be computed using pre-period μ/φ, applied atomically."""
        engine = RatingEngine()
        engine.pool.get_or_create("a")
        engine.pool.get_or_create("b")
        engine.pool.get_or_create("c")

        period = RatingPeriod(id="p1")
        # a beats b, b beats c, c beats a — symmetric cycle, one entry per game
        period.add_match(MatchResult("a", "b", 1.0))
        period.add_match(MatchResult("b", "c", 1.0))
        period.add_match(MatchResult("c", "a", 1.0))

        # All start equal; after one symmetric cycle the sum of μ should be ~0
        engine.process_period(period)
        total_mu = sum(p.mu for p in engine.pool.all())
        assert total_mu == pytest.approx(0.0, abs=1e-9)
