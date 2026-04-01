---
title: Tournament Formats
description: Scheduling, pairing strategies, and stopping criteria.
---

## Formats

```python
from glicko2.tournament import round_robin, double_round_robin, swiss, adaptive
```

### Round robin

Every player faces every other player exactly once. C(n, 2) pairs total.

```python
pairs = round_robin(["a", "b", "c", "d"])
# → [("a","b"), ("a","c"), ("a","d"), ("b","c"), ("b","d"), ("c","d")]
```

### Double round robin

Every ordered pair plays — each player is home and away once.

```python
pairs = double_round_robin(["a", "b", "c"])
# → [("a","b"), ("a","c"), ("b","a"), ("b","c"), ("c","a"), ("c","b")]
```

### Swiss

Each round pairs players with similar current μ. Good for large fields where full round-robin is too expensive.

```python
schedule = swiss(engine.pool, rounds=5, seed=42)
# → [[("a","b"), ("c","d")], [("a","c"), ("b","d")], ...]
```

### Adaptive

Each round selects the most informative pairings — those where the expected win probability is closest to 50/50. Maximises rating information per match.

```python
schedule = adaptive(engine.pool, rounds=5, matches_per_round=4)
```

## Scheduler

Lower-level functions for custom pairing logic:

```python
from glicko2.tournament import most_uncertain_pair, closest_rated_pair, adaptive_pairs

# Pair with highest combined φ — maximises information gain
pair = most_uncertain_pair(engine.pool)

# Pair closest in μ — most competitive game
pair = closest_rated_pair(engine.pool)

# N pairs closest to target win probability
pairs = adaptive_pairs(engine.pool, n=6, target_win_prob=0.5)
```

## Stopping criteria

Know when to stop running matches:

```python
from glicko2.tournament import all_below_rd_threshold, top_k_separated

# Stop when all players have RD below a threshold (reliable ratings)
if all_below_rd_threshold(engine.pool, max_phi=1.5):
    print("All ratings have converged")

# Stop when top-3 players have non-overlapping 95% CIs
if top_k_separated(engine.pool, k=3):
    print("Leaderboard top-3 is statistically separated")
```

## Rating inflation utilities

Between seasons or after a large pool update:

```python
from glicko2.engine import detect_inflation, normalize_ratings, soft_reset

# How much has the pool mean drifted?
drift = detect_inflation(engine.pool)

# Shift all ratings so the mean returns to 0
normalize_ratings(engine.pool)

# Move ratings halfway back toward defaults (e.g. new season)
soft_reset(engine.pool, compression=0.5)
```
