---
title: Introduction
description: What Glicko Arena is and why it exists.
---

Glicko Arena is a monorepo for evaluating LLM agents and pipelines using the **Glicko-2 rating system** — the same statistical framework used by chess federations, online game servers, and competitive sports leagues to produce reliable, uncertainty-aware rankings.

## The problem

Benchmarks tell you how a pipeline scores on a fixed test set. They don't tell you:

- Which of two agents is *reliably* better on a given task type
- How confident you should be in that ordering
- How many comparisons you actually need before the ranking stabilises
- Whether a new pipeline version is a genuine improvement or noise

Glicko Arena answers these questions by treating agent evaluation as a **competitive rating problem**.

## How it works

Two agents attempt the same task independently. A judge scores both. The relative score becomes a match outcome. Ratings update. Repeat.

```
agent_A vs agent_B on task_X
  → judge scores: s_A = 0.82, s_B = 0.61
  → match outcome: 0.57 / 0.43
  → RatingEngine updates both agents' μ, φ, σ
```

Every agent carries a **rating** (μ), a **rating deviation** (φ, uncertainty), and a **volatility** (σ, consistency). The system knows not just who is better, but *how confident* that ordering is.

## Packages

| Package | Status | Description |
|---|---|---|
| [`glicko2`](/glicko2/getting-started) | Stable | Pure Glicko-2 library — standalone, zero dependencies |
| `glicko_eval` | In development | LLM eval harness built on top of `glicko2` |

## Design principles

- **One match entry per game.** Record `MatchResult("agent_a", "agent_b", score)` once. The engine derives the opponent's perspective automatically.
- **Continuous scores.** Judge outputs are floats in [0, 1], not win/loss. The math handles it natively.
- **Per-category engines.** Factual, tool-calling, and multi-hop tasks each maintain independent ratings. A global engine runs in parallel for cross-category comparison.
- **Mathematically honest.** Rating deviations are real — a new agent starts with high uncertainty and converges as matches accumulate.
