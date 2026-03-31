---
title: Testing
description: Test structure and conventions.
---

## Structure

```
packages/glicko2/tests/
├── unit/
│   ├── test_glicko2_math.py      # g(), E(), update_rating() vs paper values
│   ├── test_engine.py            # PlayerPool, MatchResult, RatingEngine
│   ├── test_inflation.py         # drift, normalize, soft_reset, phi_floor
│   └── test_scheduler.py         # formats, scheduler, stopping criteria
└── integration/
    ├── test_full_tournament.py   # end-to-end round-robin + storage round-trips
    └── test_storage_conformance.py  # shared contract tests for all backends
```

## Conventions

**Unit tests** cover a single module in isolation. No I/O, no storage, no external calls.

**Integration tests** exercise multiple layers together. Storage tests use `":memory:"` SQLite — no files written to disk.

**Storage conformance** — every `AbstractStorage` implementation must pass `StorageConformanceTests`. To add a new backend:

1. Implement the backend
2. Add a subclass to `test_storage_conformance.py`:

```python
class TestMyBackendConformance(StorageConformanceTests):
    @pytest.fixture()
    def storage(self) -> MyBackend:
        s = MyBackend(...)
        yield s
        s.close()
```

## Reference values

The Glickman (2012) worked example is the ground truth for all math tests:

| | Expected |
|---|---|
| New rating | 1464.06 ± 0.1 |
| New RD | 151.52 ± 0.1 |
| New σ | 0.059996 ± 1e-5 |

These values are checked in `test_glicko2_math.py::TestUpdateRating`.

## Running with uv

```bash
uv run pytest packages/glicko2/tests/ -q
uv run pytest packages/glicko2/tests/ -v --tb=short
```
