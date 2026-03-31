---
title: Releasing
description: How to publish packages to PyPI.
---

import { Aside } from '@astrojs/starlight/components';

## glicko2

`glicko2` is a standalone, publishable package. It has no dependency on `glicko_eval` or any other monorepo package.

### Version bump

Update the version in `packages/glicko2/pyproject.toml`:

```toml
[project]
version = "0.2.0"
```

### Build

```bash
uv build --package glicko2
# outputs to dist/glicko2-0.2.0-py3-none-any.whl
```

### Publish

```bash
uv publish --package glicko2
```

<Aside type="note">
  CI will handle publishing automatically on a version tag push once the
  `.github/workflows/publish.yml` workflow is configured.
</Aside>

## Versioning policy

`glicko2` follows [Semantic Versioning](https://semver.org/):

- **Patch** (0.1.x) — bug fixes, no API changes
- **Minor** (0.x.0) — new features, backwards compatible
- **Major** (x.0.0) — breaking API changes

Breaking changes to public API (anything in `glicko2/__init__.py`, `glicko2/math/__init__.py`, `glicko2/engine/__init__.py`) require a major version bump.
