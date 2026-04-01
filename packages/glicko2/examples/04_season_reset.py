"""Detect rating inflation and apply a between-season soft reset.

Run from the monorepo root:
    uv run python packages/glicko2/examples/04_season_reset.py
"""

import random

from glicko2 import MatchResult, RatingEngine, RatingPeriod
from glicko2.engine.drift import detect_inflation, normalize_ratings, soft_reset
from glicko2.math.conversions import mu_to_rating, phi_to_rd
from glicko2.tournament.formats import round_robin

PLAYERS = ["alpha", "bravo", "charlie", "delta", "echo", "foxtrot"]

engine = RatingEngine(tau=0.5)
rng = random.Random(99)


def simulate_season(engine: RatingEngine, season: int, rounds: int = 8) -> None:
    """Play several round-robin periods with random outcomes."""
    for r in range(rounds):
        period = RatingPeriod(id=f"s{season}-r{r}")
        for a, b in round_robin(PLAYERS):
            score = rng.choice([0.0, 0.5, 1.0])
            period.add_match(MatchResult(a, b, score))
        engine.process_period(period)


def print_pool(engine: RatingEngine, label: str) -> None:
    drift = detect_inflation(engine.pool)
    print(f"\n{label}  (mean drift: {drift:+.4f})")
    print(f"  {'Player':<12} {'Rating':>8} {'RD':>6}")
    print(f"  {'-'*28}")
    for p in sorted(engine.pool.all(), key=lambda p: p.mu, reverse=True):
        print(f"  {p.id:<12} {mu_to_rating(p.mu):>8.1f} {phi_to_rd(p.phi):>6.1f}")


# --- Season 1 ---
simulate_season(engine, season=1)
print_pool(engine, "After Season 1")

# --- Between seasons: soft reset ---
# Compress ratings 30% toward defaults (less aggressive than a full reset)
soft_reset(engine.pool, compression=0.3)
print_pool(engine, "After soft reset (30% compression)")

# --- Season 2 ---
simulate_season(engine, season=2)
print_pool(engine, "After Season 2")

# Normalize to remove any accumulated drift
normalize_ratings(engine.pool)
print_pool(engine, "After normalization")
