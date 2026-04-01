---
title: Algorithm
description: The Glicko-2 math — g(), E(), Illinois volatility update, and the full period update.
---

import { Aside } from '@astrojs/starlight/components';

The math lives entirely in `glicko2.math.algorithm` as pure functions with no side effects. Reference: Glickman (2012), *"Example of the Glicko-2 system"*.

## Scale

All internal computation uses Glicko-2 scale (μ, φ), not display scale (r, RD):

```
μ  = (r  − 1500) / 173.7178
φ  = RD          / 173.7178
```

## Step 1 — g(φ)

Reduction factor for an opponent's rating deviation. A higher opponent φ (more uncertain) reduces how much their rating difference matters:

```
g(φ) = 1 / √(1 + 3φ² / π²)
```

```python
from glicko2.math.algorithm import g

g(0.0)   # → 1.0    (opponent with zero uncertainty)
g(1.15)  # → 0.953  (RD ≈ 200)
g(2.01)  # → 0.849  (RD ≈ 350, new player)
```

## Step 2 — E(μ, μⱼ, φⱼ)

Expected score — the probability the player wins against opponent j:

```
E(μ, μⱼ, φⱼ) = 1 / (1 + exp(−g(φⱼ) · (μ − μⱼ)))
```

The implementation uses a **numerically stable logistic** that avoids overflow for extreme rating gaps (e.g. 3000 vs 100):

```python
from glicko2.math.algorithm import E
from glicko2.math.conversions import rating_to_mu, rd_to_phi

E(rating_to_mu(1500), rating_to_mu(1500), rd_to_phi(200))  # → 0.5
E(rating_to_mu(1700), rating_to_mu(1500), rd_to_phi(200))  # → 0.686
```

## Steps 3–4 — Variance v and improvement Δ

For a player with opponents [(μ₁, φ₁, s₁), ...]:

```
v   = 1 / Σ g(φⱼ)² · E(μ, μⱼ, φⱼ) · (1 − E(μ, μⱼ, φⱼ))
Δ   = v · Σ g(φⱼ) · (sⱼ − E(μ, μⱼ, φⱼ))
```

## Step 5 — New volatility σ′ (Illinois algorithm)

The most complex step. Finds the new σ by solving:

```
f(x) = exp(x)·(Δ²−φ²−v−exp(x)) / 2(φ²+v+exp(x))² − (x − ln σ²) / τ²  = 0
```

Uses the **Illinois (modified regula falsi) method** — a bracketed root-finding algorithm that is guaranteed to converge and typically does so in under 20 iterations.

<Aside type="note">
  `tau` (τ) constrains how much σ can change per period. Glickman recommends
  0.3–1.2. Lower = more stable volatility. Default is 0.5.
</Aside>

## Steps 6–7 — New φ′ and μ′

```
φ*  = √(φ² + σ′²)          # inflate before updating
φ′  = 1 / √(1/φ*² + 1/v)   # tighten based on games played
μ′  = μ + φ′² · Σ g(φⱼ)·(sⱼ − E(μ, μⱼ, φⱼ))
```

If the player had **no games**, only Step 6 inflation applies — φ grows, μ and σ are unchanged.

## Reference values

From Glickman's worked example (Table 1):

| | Before | After |
|---|---|---|
| Rating (r) | 1500 | **1464.06** |
| RD | 200 | **151.52** |
| σ | 0.06 | **0.059996** |

The implementation matches to 4 decimal places.

## Input validation

`update_rating()` validates all inputs before entering the algorithm:

- `phi > 0`, `sigma > 0`, `tau > 0`
- `mu` must be finite
- Each opponent: `phi_j > 0`, `mu_j` finite, `score ∈ [0, 1]`

Violations raise `ValueError` with a descriptive message.
