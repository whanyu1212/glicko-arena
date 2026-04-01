"""Integration tests — full tournament runs end-to-end."""

import pytest
from glicko2 import MatchResult, RatingEngine, RatingPeriod
from glicko2.storage.memory import InMemoryStorage
from glicko2.storage.sqlite import SQLiteStorage
from glicko2.tournament.formats import round_robin
from glicko2.tournament.stopping import all_below_rd_threshold, top_k_separated

PLAYERS = ["alpha", "beta", "gamma", "delta"]


def _run_round_robin_period(engine: RatingEngine, period_id: str) -> RatingPeriod:
    """Run one full round-robin period where alpha always beats everyone."""
    period = RatingPeriod(id=period_id)
    for a, b in round_robin(PLAYERS):
        # alpha always wins; everyone else 50/50 otherwise
        # One entry per game — engine derives the opponent's perspective
        score = 1.0 if a == "alpha" else (0.0 if b == "alpha" else 0.5)
        period.add_match(MatchResult(a, b, score))
    engine.process_period(period)
    return period


class TestRoundRobinTournament:
    @pytest.fixture()
    def engine(self) -> RatingEngine:
        e = RatingEngine(tau=0.5)
        for pid in PLAYERS:
            e.pool.get_or_create(pid)
        return e

    def test_alpha_rises_after_five_periods(self, engine):
        mu_before = engine.pool.get("alpha").mu
        for i in range(5):
            _run_round_robin_period(engine, f"p{i}")
        assert engine.pool.get("alpha").mu > mu_before

    def test_alpha_ranked_first_after_five_periods(self, engine):
        for i in range(5):
            _run_round_robin_period(engine, f"p{i}")
        ranked = sorted(PLAYERS, key=lambda pid: engine.pool.get(pid).mu, reverse=True)
        assert ranked[0] == "alpha"

    def test_rd_decreases_with_activity(self, engine):
        phi_before = {pid: engine.pool.get(pid).phi for pid in PLAYERS}
        for i in range(5):
            _run_round_robin_period(engine, f"p{i}")
        for pid in PLAYERS:
            assert engine.pool.get(pid).phi < phi_before[pid]

    def test_stopping_criterion_eventually_met(self, engine):
        for i in range(20):
            _run_round_robin_period(engine, f"p{i}")
        # After enough rounds all RDs should be well below the default 350
        assert all_below_rd_threshold(engine.pool, max_phi=1.5)

    def test_top_k_separated_after_many_rounds(self, engine):
        for i in range(30):
            _run_round_robin_period(engine, f"p{i}")
        assert top_k_separated(engine.pool, k=2)


class TestStorageRoundTrip:
    def test_inmemory_player_round_trip(self):
        storage = InMemoryStorage()
        engine = RatingEngine()
        for pid in PLAYERS:
            engine.pool.get_or_create(pid)

        _run_round_robin_period(engine, "p0")

        for p in engine.pool.all():
            storage.save_player(p)

        for p in engine.pool.all():
            loaded = storage.load_player(p.id)
            assert loaded is not None
            assert loaded.mu == pytest.approx(p.mu)
            assert loaded.phi == pytest.approx(p.phi)
            assert loaded.sigma == pytest.approx(p.sigma)

    def test_sqlite_player_round_trip(self):
        storage = SQLiteStorage(":memory:")
        engine = RatingEngine()
        for pid in PLAYERS:
            engine.pool.get_or_create(pid)

        _run_round_robin_period(engine, "p0")

        for p in engine.pool.all():
            storage.save_player(p)

        all_players = storage.load_all_players()
        assert len(all_players) == len(PLAYERS)

        for p in engine.pool.all():
            loaded = storage.load_player(p.id)
            assert loaded is not None
            assert loaded.mu == pytest.approx(p.mu)
            assert loaded.phi == pytest.approx(p.phi)

        storage.close()

    def test_sqlite_period_round_trip(self):
        storage = SQLiteStorage(":memory:")
        engine = RatingEngine()
        for pid in PLAYERS:
            engine.pool.get_or_create(pid)

        period = _run_round_robin_period(engine, "p0")
        storage.save_period(period)
        for match in period.matches:
            storage.append_match("p0", match)

        loaded = storage.load_period("p0")
        assert loaded is not None
        assert len(loaded.matches) == len(period.matches)
        storage.close()
