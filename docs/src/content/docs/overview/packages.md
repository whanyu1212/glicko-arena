---
title: Packages
description: All packages in the monorepo.
---

import { Badge } from '@astrojs/starlight/components';

## glicko2 <Badge text="Stable" variant="success" />

A pure Python implementation of the Glicko-2 rating system.

- **Zero runtime dependencies**
- Fully typed, `py.typed` marker included
- SQLite persistence built in
- Usable standalone — no dependency on `glicko_eval`

```bash
pip install glicko2
```

[Documentation →](/glicko2/getting-started)

---

## glicko_eval <Badge text="In Development" variant="caution" />

The LLM evaluation harness. Provides task definitions, judge implementations, pipeline wrappers, and the arena orchestration that ties everything together.

- Depends on `glicko2`
- Per-category rating engines
- LLM-as-judge scoring
- CLI for running evaluations and viewing leaderboards

Not yet published to PyPI.
