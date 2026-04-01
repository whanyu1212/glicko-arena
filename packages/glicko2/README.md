# glicko2

A pure Python implementation of the [Glicko-2 rating system](http://www.glicko.net/glicko/glicko2.pdf) (Glickman, 2012).

Zero dependencies. Fully typed. Usable as a standalone library or as the rating backend for `glicko_eval`.

## Installation

```bash
pip install glicko2-py
# with PostgreSQL support:
pip install "glicko2-py[postgres]"
```

## Quick start

```python
from glicko2 import RatingEngine, MatchResult, RatingPeriod

engine = RatingEngine(tau=0.5)

# Players are auto-created on first use, or register explicitly:
engine.pool.get_or_create("alice")
engine.pool.get_or_create("bob")

period = RatingPeriod(id="round-1")
period.add_match(MatchResult("alice", "bob", 1.0))  # one entry per game

engine.process_period(period)  # engine derives bob's perspective automatically

from glicko2.math.conversions import mu_to_rating, phi_to_rd

alice = engine.pool.get("alice")
print(mu_to_rating(alice.mu))   # display rating  (~1537)
print(phi_to_rd(alice.phi))     # rating deviation (~192)
```

## Core concepts

| Concept | Description |
|---|---|
| `Player` | Holds `μ`, `φ`, `σ` in Glicko-2 internal scale |
| `MatchResult` | One game outcome: `score` is any float in [0, 1] from `player_id`'s view; engine derives opponent's perspective automatically |
| `RatingPeriod` | A batch of matches processed together (all treated as simultaneous) |
| `RatingEngine` | Runs period updates; owns a `PlayerPool` |

## Math

All rating math lives in `glicko2.math` and is composed of pure functions with no side effects.

```python
from glicko2.math import g, E, update_rating
from glicko2.math import rating_to_mu, rd_to_phi, mu_to_rating, phi_to_rd
from glicko2.math import rating_interval, win_probability
```

The `update_rating()` function implements the full Glickman algorithm including the **Illinois (regula falsi)** root-finding method for the iterative volatility update (Step 5).

### Reference values (Glickman 2012, Table 1)

| | Before | After |
|---|---|---|
| Rating | 1500 | **1464.06** |
| RD | 200 | **151.52** |
| Volatility σ | 0.06 | **0.059996** |

## Tournament formats

```python
from glicko2.tournament import round_robin, swiss, adaptive
from glicko2.tournament import all_below_rd_threshold, top_k_separated
```

| Format | Description |
|---|---|
| `round_robin` | Every player faces every other player once |
| `double_round_robin` | Every ordered pair plays |
| `swiss` | μ-sorted pairing each round |
| `adaptive` | Select pairings closest to 50/50 win probability |

## Storage backends

| Backend | Status | Use case |
|---|---|---|
| `InMemoryStorage` | Stable | Tests, ephemeral runs |
| `SQLiteStorage` | Stable | Default persistent backend, zero infra |
| `PostgresStorage` | Not yet implemented | Planned for shared team leaderboards |

```python
from glicko2.storage import SQLiteStorage

storage = SQLiteStorage("ratings.db")
storage.save_player(engine.pool.get("alice"))
alice = storage.load_player("alice")
```

> **Note:** `PostgresStorage` connects and migrates the schema but all CRUD methods
> raise `NotImplementedError`. Do not use it in production yet.

## Rating inflation utilities

```python
from glicko2.engine import detect_inflation, normalize_ratings, soft_reset

# Detect mean drift
drift = detect_inflation(engine.pool)

# Shift all ratings so the mean returns to 0
normalize_ratings(engine.pool)

# Move ratings halfway back toward defaults (e.g. between seasons)
soft_reset(engine.pool, compression=0.5)
```

## Parameter guidance

| Parameter | Default | Notes |
|---|---|---|
| `tau` (τ) | `0.5` | System constant. Range 0.3–1.2. Lower = more stable volatility. |
| Initial RD | `350` | φ = 350/173.7178 ≈ 2.015. Reduce for established players. |
| Initial σ | `0.06` | Glickman's recommended default. |

## Running tests

From the monorepo root:

```bash
uv run pytest packages/glicko2/tests/
```
