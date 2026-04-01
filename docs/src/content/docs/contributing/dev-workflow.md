---
title: Dev Workflow
description: Setting up the monorepo for local development.
---

## Prerequisites

- Python 3.11+
- [uv](https://docs.astral.sh/uv/) — used for all Python dependency management
- Node.js 18+ — only needed if working on the docs site

## Setup

```bash
git clone https://github.com/whanyu1212/glicko-arena
cd glicko-arena

# Create the shared venv and install all workspace packages + dev deps
uv sync
```

One venv at the repo root. All workspace packages (`packages/glicko2`, etc.) are installed as editable. No per-package venvs needed.

## Running tests

```bash
# All packages
uv run pytest

# Specific package
uv run pytest packages/glicko2/tests/

# With coverage
uv run pytest packages/glicko2/tests/ --cov=glicko2
```

## Linting and formatting

```bash
uv run ruff check .
uv run ruff format .
```

## Type checking

```bash
uv run mypy packages/glicko2
```

## Docs site

```bash
cd docs
npm install
npm run dev      # dev server at localhost:4321
npm run build    # production build
```

## Adding a new package

1. Create `packages/<name>/` with its own `pyproject.toml`
2. The workspace glob `members = ["packages/*"]` picks it up automatically
3. Run `uv sync` to reinstall
