---
title: glicko_eval Overview
description: The LLM evaluation harness — coming soon.
---

import { Aside } from '@astrojs/starlight/components';

<Aside type="caution">
  `glicko_eval` is in active development and not yet published. This page
  describes the planned design.
</Aside>

## What it does

`glicko_eval` is the LLM-specific evaluation harness built on top of `glicko2`. It handles everything above the rating math:

- Task definitions and registry
- Judge implementations (exact match, fuzzy, LLM-as-judge, tool-call scoring)
- Pipeline wrappers for RAG and agent systems
- Arena orchestration — one `RatingEngine` per task category
- Per-category and global leaderboards
- CLI for running evaluations

## Planned usage

```python
from glicko_eval import Arena
from glicko_eval.pipelines import AgentPipeline

arena = Arena.from_config("configs/arena/default.yaml")

arena.register(AgentPipeline("agent_v1", ...))
arena.register(AgentPipeline("agent_v2", ...))

arena.run(rounds=10)

arena.leaderboard(category="tool_calling")
```

## Task categories

| Category | Description |
|---|---|
| `factual` | Direct lookup, paraphrase, negation, multi-entity |
| `tool_calling` | Single tool, sequential, error recovery, hallucination |
| `multihop` | Multi-step reasoning across documents |

Each category maintains an independent `RatingEngine`. A global engine aggregates all matches for cross-category ranking.

## Score normalisation

Judges return a float in [0, 1] for each agent. The arena normalises to a match outcome:

```python
score_a = s_a / (s_a + s_b)   # continuous — preserves magnitude
```

This flows directly into `MatchResult` and the `glicko2` rating update without any modification to the core library.
