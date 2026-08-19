# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Commands

### Local development

```bash
make bootstrap   # Pull datagovuk_find and ckan-mock-harvest-sources repos
make build       # Build Docker images
make run         # Start all services
make down        # Stop all services
```

Services once running:
- CKAN (publishing): http://localhost:5001
- Find (public discovery): http://localhost:4001
- Solr: http://localhost:8983/solr

### Tests

```bash
# Run full test suite
make test

# Exec into container first, then run a single test file or specific test
docker exec -it ckan-2.10 bash
cd /usr/lib/ckan/venv/src/ckanext-datagovuk
PROMETHEUS_MULTIPROC_DIR=/tmp pytest --ckan-ini=test.ini ckanext/datagovuk/tests/path/to/test_file.py::test_name -v
```

Tests require the full Docker stack (Postgres + Solr + Redis). The `test.ini` config points to those services.

### Test data

Run inside the `ckan-2.10` container with `CKAN_INI` set:

```bash
ckan datagovuk create-dgu-test-data
ckan datagovuk reindex-organisations  # required for Find app to show organisations
ckan datagovuk remove-dgu-test-data
```

## Architecture

### Plugin registration (`plugin.py`)

`DatagovukPlugin` is the single entry point. It implements multiple CKAN interfaces:

| Interface | What it does |
|---|---|
| `IDatasetForm` | Adds custom schema fields (`theme-primary`, `licence-custom`, `schema-vocabulary`, `codelist`, contact/FOI fields) stored as CKAN extras |
| `IActions` | Overrides `package_search`, `package_show`, `organization_show`, `resource_create`, `user_create`, `user_update`, `user_auth` |
| `IAuthFunctions` | Restricts `group_create`, `organization_create` |
| `IBlueprint` | Registers Flask routes: `/healthcheck`, `/metrics`, `/api/search/dataset`, `/api/3/search/dataset`, `/publisher`, user register/edit |
| `IValidators` | Adds `correct_email_suffix`, `valid_theme`, `user_password_validator_dgu` |
| `ITemplateHelpers` | Exposes helpers for themes, schemas, codelists etc. to Jinja2 templates |
| `IMiddleware` | Initialises Sentry and Prometheus metrics (Gunicorn-only) |
| `IResourceController` | Intercepts resource create/update to enforce S3 upload config |

### Monkey-patching CKAN core (`ckan_patches/`)

`plugin.py` imports `ckan_patches.cli`, `.logic`, `.query`, `.helpers` at class body level, which executes the patches when the plugin loads. This is how behaviour in CKAN core is overridden without forking CKAN. Changes to these files affect core CKAN functions directly — be careful about unintended side effects.

### Schema customisation

Custom dataset fields use CKAN's extras mechanism: `convert_to_extras` on write, `convert_from_extras` on read. The canonical list is in `plugin.py:_modify_package_schema`. Reference data (valid themes, schemas, codelists) lives in `ckanext/datagovuk/data/`.

### S3 resource uploads (`upload.py`)

Before any resource create/update, `plugin.py:before_create_or_update` checks that S3 config exists. The actual upload logic is in `upload.py`. Non-API, non-link resources are expected to be backed by S3.

### Harvesting

`InventoryHarvester` (in `harvesters/`) ingests datasets from external XML/CSV sources. Harvest jobs attach metadata to datasets via `HarvestObject`; `after_dataset_show` in the plugin reads these back and injects `harvest` extras into the dataset dict.

### Sentry filtering

`plugin.py:before_send` suppresses Sentry events on localhost/integration environments and for a known list of data-quality errors that publishers are expected to fix. Do not add generic errors to `IGNORED_DATA_ERRORS` — only errors that are definitively a publisher's responsibility.

## Deployment

- **Integration**: merge to `main` → GitHub Action builds image → auto-PR in `govuk-dgu-charts` → merge that PR
- **Staging / Production**: create a GitHub release with a version tag → two PRs are auto-created in `govuk-dgu-charts`

Base/core image changes (i.e. changes to CKAN itself or Dockerfiles) require manually triggering `build_push_core` then `build_push_base` in GitHub Actions, and bumping the version/patch in `build-config.yaml` first.
