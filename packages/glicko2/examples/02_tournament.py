"""Run a multi-round round-robin tournament and track rating evolution.

Run from the monorepo root:
    uv run python packages/glicko2/examples/02_tournament.py
"""

import random

from glicko2 import MatchResult, RatingEngine, RatingPeriod
from glicko2.math.confidence import rating_interval, win_probability
from glicko2.math.conversions import mu_to_rating, phi_to_rd
from glicko2.tournament.formats import round_robin

PLAYERS = ["alice", "bob", "carol", "dave", "eve"]
ROUNDS = 5

engine = RatingEngine(tau=0.5)
rng = random.Random(42)

for round_num in range(1, ROUNDS + 1):
    period = RatingPeriod(id=f"round-{round_num}")

    # Generate all pairings for this round
    pairings = round_robin(PLAYERS)
    for a, b in pairings:
        pa = engine.pool.get_or_create(a)
        pb = engine.pool.get_or_create(b)

        # Simulate outcome weighted by current ratings
        p_win = win_probability(pa.mu, pa.phi, pb.mu, pb.phi)
        roll = rng.random()
        if roll < p_win * 0.8:
            score = 1.0  # a wins
        elif roll > 1.0 - (1.0 - p_win) * 0.8:
            score = 0.0  # b wins
        else:
            score = 0.5  # draw

        period.add_match(MatchResult(a, b, score))

    engine.process_period(period)

    # Print standings after each round
    ranked = sorted(engine.pool.all(), key=lambda p: p.mu, reverse=True)
    leader = ranked[0]
    print(
        f"Round {round_num}: leader = {leader.id} "
        f"({mu_to_rating(leader.mu):.0f} ± {phi_to_rd(leader.phi):.0f})"
    )

# Final leaderboard with confidence intervals
print("\n=== Final Standings ===")
print(f"{'#':<3} {'Player':<10} {'Rating':>8} {'RD':>6} {'95% CI':>20}")
print("-" * 50)
for i, player in enumerate(
    sorted(engine.pool.all(), key=lambda p: p.mu, reverse=True), 1
):
    lo, hi = rating_interval(player.mu, player.phi)
    print(
        f"{i:<3} {player.id:<10} {mu_to_rating(player.mu):>8.1f} "
        f"{phi_to_rd(player.phi):>6.1f} "
        f"[{lo:>7.1f}, {hi:>7.1f}]"
    )
