---
title: Storage Backends
description: Persisting players and rating periods.
---

import { Aside, Badge } from '@astrojs/starlight/components';

## Overview

All backends implement `AbstractStorage` and expose the same interface. Swap backends by changing one constructor call.

```python
from glicko2.storage import InMemoryStorage, SQLiteStorage
```

## InMemoryStorage <Badge text="Stable" variant="success" />

No persistence. All data is lost when the process exits. Intended for tests and ephemeral runs.

```python
from glicko2.storage import InMemoryStorage

storage = InMemoryStorage()
storage.save_player(engine.pool.get("alice"))
alice = storage.load_player("alice")
```

## SQLiteStorage <Badge text="Stable" variant="success" />

Zero-infrastructure persistence backed by a local SQLite file. Uses WAL journal mode and foreign key constraints. Safe for single-process use.

```python
from glicko2.storage import SQLiteStorage

storage = SQLiteStorage("ratings.db")

# Save all players after a period
for player in engine.pool.all():
    storage.save_player(player)

# Save a period and its matches
storage.save_period(period)
for match in period.matches:
    storage.append_match(period.id, match)

# Load back
alice = storage.load_player("alice")
all_periods = storage.load_all_periods()  # ordered by opened_at

storage.close()
```

## PostgresStorage <Badge text="Not Implemented" variant="danger" />

<Aside type="caution">
  `PostgresStorage` connects and migrates the schema successfully, but all CRUD
  methods raise `NotImplementedError`. Do not use in production.
</Aside>

Planned for shared team leaderboards where multiple processes need to write ratings concurrently.

```bash
# Optional dependency
pip install "glicko2-py[postgres]"
```

## Storage contract

All backends guarantee:

- `load_all_periods()` returns periods ordered by `opened_at` ascending
- `append_match()` raises `StorageError` if the period does not exist
- `save_player()` upserts — safe to call repeatedly
- `load_player()` returns `None` for unknown IDs (never raises)
- `delete_player()` is silent for unknown IDs (never raises)

These contracts are enforced by the shared conformance test suite in `tests/integration/test_storage_conformance.py`.
