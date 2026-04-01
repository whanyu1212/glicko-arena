---
title: Core Concepts
description: Player, MatchResult, RatingPeriod, and RatingEngine.
---

import { Aside } from '@astrojs/starlight/components';

## Player

A `Player` holds three values in Glicko-2 internal scale:

| Field | Symbol | Meaning | Default (display) |
|---|---|---|---|
| `mu` | μ | Rating | 1500 |
| `phi` | φ | Rating deviation (uncertainty) | RD 350 |
| `sigma` | σ | Volatility (consistency) | 0.06 |
| `num_periods` | — | Periods actively competed in | 0 |

**φ is the key signal for reliability.** A new player starts at φ ≈ 2.015 (RD 350). As they play more games, φ shrinks. A player who hasn't played in a while will have their φ inflated automatically at each period update.

```python
from glicko2.models.player import Player

# Register with known starting point
player = Player(
    id="agent_v2",
    mu=rating_to_mu(1600),
    phi=rd_to_phi(120),
    sigma=0.06,
)
```

## MatchResult

One `MatchResult` represents **one game**. The score is from `player_id`'s perspective:

```python
from glicko2 import MatchResult

# Binary outcome
MatchResult("alice", "bob", 1.0)   # alice wins
MatchResult("alice", "bob", 0.0)   # alice loses
MatchResult("alice", "bob", 0.5)   # draw

# Continuous outcome (LLM eval)
MatchResult("agent_a", "agent_b", 0.573)  # normalised judge scores
```

<Aside type="caution">
  Record each game **once**. `RatingEngine.process_period()` derives the
  opponent's update internally. Inserting both sides manually will double-count
  the game and produce incorrect ratings.
</Aside>

## RatingPeriod

A `RatingPeriod` batches matches together. All matches in a period are treated as simultaneous — ratings update once at the end.

```python
from glicko2 import RatingPeriod

period = RatingPeriod(id="2024-Q1")
period.add_match(MatchResult("a", "b", 1.0))
period.add_match(MatchResult("a", "c", 0.5))
period.close()  # marks the period as done
```

**How long should a period be?** Glickman recommends grouping matches that happen "around the same time." For LLM eval, one evaluation run or one day of comparisons is a natural period boundary.

## RatingEngine

`RatingEngine` is the central orchestrator. It owns a `PlayerPool` and processes periods atomically.

```python
from glicko2 import RatingEngine

engine = RatingEngine(tau=0.5)

# All updates within process_period() use pre-period ratings
# Players not present in a period still get their φ inflated
engine.process_period(period)
```

**Atomicity matters.** If Alice plays Bob and Carol in the same period, Bob's rating used to compute Alice's update is his *pre-period* rating, not any intermediate value. This prevents ordering effects.

## PlayerPool

`PlayerPool` is the in-memory registry that `RatingEngine` owns. You can query it directly:

```python
pool = engine.pool

pool.get("alice")                    # Player or UnknownPlayerError
pool.get_or_create("new_agent")      # creates with defaults if missing
pool.all()                           # list of all Players
pool.ids()                           # list of all IDs

"alice" in pool                      # True / False
len(pool)                            # number of registered players
```
