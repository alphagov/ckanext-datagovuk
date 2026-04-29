# Script runbook

## Prerequisites

- Set environment variable `POSTGRES_URL`
- Value from `docker/.env.example` == `postgresql://ckan:ckan@db/ckan`

***

### Link checking

Two-step cycle: scan for broken links → reindex affected packages.

### 1. `check_links.py`

Scans active resource URLs on active datasets, classifies each response, and (in `live` mode) marks 404/410 resources as deleted and updates `package.metadata_modified`. Writes a CSV report and a `packages_to_reindex_*.txt` list feeding into `solr_reindex_package_ids.py`.

Then run:

Set environment variable for: `POSTGRES_URL`

```bash
    python check_links.py --mode dry-run
```

CSV output will show results, including column `to-delete` which shows resources that would be updated in live mode.

To update db instead of `--mode dry-run` use `--mode live`.

### CLI flags

| Flag | Required | Default | Purpose |
|---|---|---|---|
| `--mode` | no | `dry-run` | `dry-run` reports only; `live` marks 404/410 resources deleted |
| `--output-dir` | no | `.` (cwd) | directory for the CSV report and reindex list |

Filenames are module-level constants (`LOG_FILE` = `check_links.log`, `REPORT_FILE` = `check_links_report_{ts}.csv`, `REINDEX_FILE` = `packages_to_reindex_{ts}.txt`). 
The CSV report and reindex list are timestamped per run and placed in current directory or `--output-dir`.

Tuning config (worker count, timeouts) remain module-level constants — see "What to tune" below.

### What to tune

1. **Reduce `WORKERS` first** (if container memory climbing or CPU saturating) — try 50 → 25 → 10.
2. **Then `HTTP_TIMEOUT`** (a `(connect, read)` tuple) — a healthy host should connect in well under allowed time. Reducing the read timeout shortens total runtime on slow hosts.

### Config

| Constant | Current value | What it does |
|---|---|---|
| `WORKERS` | 50 | concurrent HTTP workers |
| `HTTP_TIMEOUT` | `(5, 5)` | `(connect, read)` seconds |

These are module constants near top of script. Change if needed according to tuning section above.

### Outputs

- `check_links.log` — run log (stable name, always current dir)
- `check_links_report_{ts}.csv` — one row per resource (category + `to-delete` flag) - current dir unless `--output-dir` set
- `packages_to_reindex_{ts}.txt` — unique package IDs that had a 404/410 — used as input to `solr_reindex_package_ids.py` - cuirrent dir unless `--output-dir` set

### 2. `revert_link_deletions.py`

Reverses a prior `check_links.py --mode live` run using its CSV report. Every row with `to-delete == "true"` has its resource `state` reverted to `active` (if currently `deleted`) and `package.metadata_modified` updated to NOW().

Run (inside the container, with `POSTGRES_URL` set):

```bash
    python revert_link_deletions.py --input check_links_report_<ts>.csv --mode dry-run
```

`--mode` defaults to `dry-run` (no db writes, only logs and writes the revert reindex file). Use `--mode live` to actually restore.

### CLI flags

| Flag | Required | Default | Purpose |
|---|---|---|---|
| `--input` | **yes** | — | check_links CSV report to reverse (full path) |
| `--mode` | no | `dry-run` | `dry-run` reports only; `live` restores deleted resources |
| `--output-dir` | no | `.` (current dir) | directory for the reindex list |

Same convention as `check_links.py`: filenames are module-level constants (`LOG_FILE` = `check_links_revert.log`, `REINDEX_FILE` = `packages_to_reindex_revert_{ts}.txt`). The log file uses a stable name and written to the current working directory. The reindex list is timestamped per run and outputs to current dir or `--output-dir`.

The reindex output used as input to `solr_reindex_package_ids.py`.

Note: the original `metadata_modified` that was updated in check links, can't be recovered, it gets updated to NOW() on revert.

---

## Testing locally

### 1. Shell into running container

Assumes in another terminal you've built and brought up local compose stack

```bash
docker exec -it ckan-2.10 bash
cd $CKAN_VENV/src/ckanext-datagovuk/bin/python_scripts
```

### 2. Run tests

```bash
pytest tests/test_check_links.py
pytest tests/test_revert_link_deletions.py
```

### 3. Test against local db

Requires test data in the db (run `ckan datagovuk create-dgu-test-data`):

```bash
export POSTGRES_URL=postgresql://ckan:ckan@db/ckan
python check_links.py
```

You can add the arg: 

`--limit 10`

which limits number of resources. Useful if you have a lot of test data. With the `create-dgu-test-data` task
there aren't many so you don't need it.

Test revert

```bash
export POSTGRES_URL=postgresql://ckan:ckan@db/ckan
python revert_link_deletions --input [report_file.csv]
```
