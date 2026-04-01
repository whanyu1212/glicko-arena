"""Basic Glicko-2 usage — rate a few head-to-head matches.

Run from the monorepo root:
    uv run python packages/glicko2/examples/01_basic.py
"""

from glicko2 import MatchResult, RatingEngine, RatingPeriod
from glicko2.math.conversions import mu_to_rating, phi_to_rd

engine = RatingEngine(tau=0.5)

# Register players (optional — they auto-register on first match)
engine.pool.get_or_create("alice")
engine.pool.get_or_create("bob")
engine.pool.get_or_create("carol")

# Create a rating period and record results.
# Each match is recorded once from one player's perspective;
# the engine derives the opponent's view automatically.
period = RatingPeriod(id="week-1")
period.add_match(MatchResult("alice", "bob", 1.0))    # alice beats bob
period.add_match(MatchResult("bob", "carol", 1.0))    # bob beats carol
period.add_match(MatchResult("carol", "alice", 0.5))  # carol draws alice

engine.process_period(period)

# Print a leaderboard
print("=== After Week 1 ===")
print(f"{'Player':<10} {'Rating':>8} {'RD':>8}")
print("-" * 28)
for player in sorted(engine.pool.all(), key=lambda p: p.mu, reverse=True):
    rating = mu_to_rating(player.mu)
    rd = phi_to_rd(player.phi)
    print(f"{player.id:<10} {rating:>8.1f} {rd:>8.1f}")
