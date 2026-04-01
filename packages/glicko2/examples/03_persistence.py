"""Persist ratings to SQLite and reload them across sessions.

Run from the monorepo root:
    uv run python packages/glicko2/examples/03_persistence.py
"""

import tempfile
from pathlib import Path

from glicko2 import MatchResult, RatingEngine, RatingPeriod
from glicko2.math.conversions import mu_to_rating, phi_to_rd
from glicko2.storage.sqlite import SQLiteStorage

db_path = Path(tempfile.mkdtemp()) / "ratings.db"

# --- Session 1: play matches and save ---

engine = RatingEngine(tau=0.5)
period = RatingPeriod(id="week-1")
period.add_match(MatchResult("alice", "bob", 1.0))
period.add_match(MatchResult("bob", "carol", 0.0))
engine.process_period(period)

storage = SQLiteStorage(db_path)

# Save the period header, then each match
storage.save_period(period)
for match in period.matches:
    storage.append_match(period.id, match)

# Save player ratings
for player in engine.pool.all():
    storage.save_player(player)

storage.close()
print(f"Session 1: saved to {db_path}")

# --- Session 2: reload and continue ---

storage = SQLiteStorage(db_path)

# Rebuild engine state from storage
engine2 = RatingEngine(tau=0.5)
for player in storage.load_all_players():
    engine2.pool.add(player)

print("\nReloaded players:")
for p in sorted(engine2.pool.all(), key=lambda p: p.mu, reverse=True):
    print(f"  {p.id}: {mu_to_rating(p.mu):.1f} (RD {phi_to_rd(p.phi):.1f})")

# Play another period
period2 = RatingPeriod(id="week-2")
period2.add_match(MatchResult("carol", "alice", 1.0))  # upset!
engine2.process_period(period2)

# Save updated ratings
for player in engine2.pool.all():
    storage.save_player(player)

storage.close()

print("\nAfter week 2:")
for p in sorted(engine2.pool.all(), key=lambda p: p.mu, reverse=True):
    print(f"  {p.id}: {mu_to_rating(p.mu):.1f} (RD {phi_to_rd(p.phi):.1f})")

print(f"\nDatabase at: {db_path}")
