---
title: Architecture
description: How the packages fit together.
---

import { Aside } from '@astrojs/starlight/components';

## Package layering

```
┌─────────────────────────────────┐
│           glicko_eval           │  LLM eval harness
│  tasks · judges · arena · CLI   │  (in development)
└──────────────┬──────────────────┘
               │ depends on
┌──────────────▼──────────────────┐
│             glicko2             │  Pure rating library
│  models · math · engine ·       │  (stable, PyPI)
│  tournament · storage           │
└─────────────────────────────────┘
```

`glicko2` is a general-purpose Glicko-2 library with no knowledge of LLMs or agents. It can be used independently for any rating application (games, sports, benchmarks).

`glicko_eval` depends on `glicko2` and adds the LLM-specific layer: task definitions, judge implementations, pipeline wrappers, and the arena orchestration logic.

## glicko2 internals

```
glicko2/
├── models/          Data containers (Player, MatchResult, RatingPeriod)
├── math/            Pure functions — algorithm, conversions, confidence
├── engine/          Stateful — RatingEngine, PlayerPool, drift utilities
├── tournament/      Scheduling, formats, stopping criteria
└── storage/         Persistence — SQLite (stable), Postgres (planned)
```

The dependency direction is strictly downward — `engine` imports from `math` and `models`, never the reverse.

## glicko_eval internals (planned)

```
glicko_eval/
├── tasks/           Task definitions and registry
├── judges/          Scoring implementations (exact, fuzzy, LLM, tool)
├── pipelines/       Agent and RAG pipeline wrappers
├── arena/           Arena orchestration — one RatingEngine per category
├── analysis/        Dimension breakdown, trajectory, volatility diagnosis
└── leaderboard/     Per-category + global leaderboard rendering
```

## Multi-engine design

Each task category gets its own `RatingEngine`. Every match also feeds a global engine. This means:

- Category ratings converge independently
- You can stop a category early when its stopping criterion is met
- The global engine is always available for cross-category comparison

```python
arena.engines = {
    "factual":      RatingEngine(tau=0.5),
    "tool_calling": RatingEngine(tau=0.5),
    "multihop":     RatingEngine(tau=0.5),
    "global":       RatingEngine(tau=0.5),
}
```

<Aside type="note">
  The `tau` parameter can be tuned per category. A higher τ allows ratings to
  change more sharply after a pipeline update — useful for fast-moving categories.
</Aside>
