# Linting migration

> Temporary doc. Once the series is complete: delete this file, add a pre-commit hook, and add a short section to the README.

## Why

In order to support bigger changes and maintenance, developers and reviewers need to see the logic, not whitespace or other noise.

Therefore this will be part of a series of PRs to establish a consistent baseline with `ruff` for linting and formatting.

A big bang cleanup would cover ~60 files, too large to review, so the proposal is to roll out an incremental approach,
by applying updates to **one directory at a time per PR**, formatting and imports only, no behaviour changes.

## The approach (apply per directory)

```bash
ruff check --fix <dir>   # safe auto-fixes: imports, unused imports, whitespace
ruff format <dir>        # quotes, commas, line wrapping
ruff check <dir>         # anything left gets `# noqa + TODO`
```

Issues ruff can't auto-fix are tagged inline rather than fixed, and formatting PRs don't touch logic.

```python
def chunk(l):  # noqa: E741  TODO: rename `l` — ambiguous name
    for i in xrange(0, len(l), 2):  # noqa: F821  TODO: `xrange` → `range`
```

Typical TODOs: Py3 incompatibilities, == None, bare except, SQL injection, complex functions, undefined names.
Each gets its own PR with tests where needed.

## PR 1 (this one)

- `pyproject.toml` with ruff config
- `ruff>=0.15` in `dev-requirements.txt`
- `make lint` / `make format` / `make fix` targets
- `ckanext/datagovuk/lib/` formatted as the example

## Directory order for follow-up PRs

Low-risk → higher-risk:

1. `bin/python_scripts/`
2. `ckanext/datagovuk/logic/` + `auth/`
3. `ckanext/datagovuk/ckan_patches/` + `forms/`
4. `ckanext/datagovuk/views/` + `controllers/`
5. `ckanext/datagovuk/action/`
6. `ckanext/datagovuk/harvesters/`
7. `ckanext/datagovuk/tests/`
8. Root modules (`plugin.py`, `schema.py`, `helpers.py`, `pii_helpers.py`, `upload.py`)

Each PR: title `Format <dir> with ruff`, body links this doc, no logic changes.

## After the series

Add `make lint` to pre-commit / CI, then start fixing the `# noqa TODO` markers
(security issues and Py3 bugs first).

## Running locally

```bash
pip install -r dev-requirements.txt
make lint     # check
make format   # apply formatting
make fix      # auto-fix + format
```
