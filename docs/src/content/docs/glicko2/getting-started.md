---
title: Getting Started
description: Install and use the glicko2 package.
---

import { Tabs, TabItem, Aside } from '@astrojs/starlight/components';

## Installation

<Tabs>
  <TabItem label="pip">
    ```bash
    pip install glicko2-py
    ```
  </TabItem>
  <TabItem label="uv">
    ```bash
    uv add glicko2-py
    ```
  </TabItem>
  <TabItem label="uv workspace">
    ```bash
    # From monorepo root — already included via workspace
    uv sync
    ```
  </TabItem>
</Tabs>

## Quick start

```python
from glicko2 import RatingEngine, MatchResult, RatingPeriod

engine = RatingEngine(tau=0.5)

# Players are auto-created on first use, or register explicitly
engine.pool.get_or_create("alice")
engine.pool.get_or_create("bob")

# Record one entry per game — engine derives both perspectives
period = RatingPeriod(id="round-1")
period.add_match(MatchResult("alice", "bob", 1.0))  # alice wins

engine.process_period(period)

from glicko2.math.conversions import mu_to_rating, phi_to_rd

alice = engine.pool.get("alice")
print(mu_to_rating(alice.mu))   # display rating (~1537)
print(phi_to_rd(alice.phi))     # rating deviation (~192)
print(alice.sigma)               # volatility
```

<Aside type="tip">
  `process_period()` derives the opponent's perspective automatically.
  Record each game **once** — not once per player.
</Aside>

## Continuous scores

Glicko-2 supports any score in [0, 1], not just win/loss. This is essential for LLM evaluation where a judge produces quality scores:

```python
# Judge scores agent_a at 0.82, agent_b at 0.61 on the same task
s_a, s_b = 0.82, 0.61
score = s_a / (s_a + s_b)  # → 0.573

period.add_match(MatchResult("agent_a", "agent_b", score))
```

## Display vs internal scale

`glicko2` stores ratings in Glicko-2 internal scale (μ, φ). Convert to familiar display values:

```python
from glicko2.math.conversions import mu_to_rating, phi_to_rd, rating_to_mu, rd_to_phi

# Internal → display
rating = mu_to_rating(player.mu)   # e.g. 1537.4
rd     = phi_to_rd(player.phi)     # e.g. 192.1

# Display → internal (when registering established players)
engine.pool.get_or_create("gm", mu=rating_to_mu(2400), phi=rd_to_phi(50))
```

## Confidence intervals

```python
from glicko2.math.confidence import rating_interval, win_probability

lo, hi = rating_interval(player.mu, player.phi)
print(f"95% CI: {lo:.0f} – {hi:.0f}")

p_win = win_probability(alice.mu, alice.phi, bob.mu, bob.phi)
print(f"Alice win probability: {p_win:.1%}")
```
