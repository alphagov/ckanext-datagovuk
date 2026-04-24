# Script runbook

### Link checking

Two-step cycle: scan for broken links → reindex affected packages.

### 1. `check_links.py`

Scans active resource URLs on active datasets, classifies each response, and (in `live` mode) marks 404/410 resources as deleted and bumps `package.metadata_modified`. Writes a CSV report and a `packages_to_reindex_*.txt` list feeding into `solr_reindex_package_ids.py`.

Then run:

Set environment variable for: `POSTGRES_URL`

```bash
    python check_links.py --mode dry-run --workers 50
```

CSV output will show results, including column `to-delete` which which show resources that would be updated in live mode.

To update db instead of `--mode dry-run` use `--mode live`

### What to tune

1. **Reduce `--workers` first** (if container memory climbing, CPU saturating) - try 50 → 25 → 10.
2. **Then `--http-timeout-read`** (e.g. 5s → 4s) to decrease total runtime
3. **Possibly `--http-timeout-connect` defaults to 5s** — a healthy host should easily connect in less time so can be reduced

### Defaults

| Flag | Default |
|---|---|
| `--workers` | 25 (recommend **50**) |
| `--http-timeout-connect` | 5 s |
| `--http-timeout-read` | 5 s |

### Outputs (written to cwd, timestamped)

- `check_links_{ts}.log` — run log
- `check_links_report_{ts}.csv` — one row per resource (category + `to-delete` flag)
- `packages_to_reindex_{ts}.txt` — unique package IDs that had a 404/410 - feeds into `solr_reindex_package_ids.py`

### 2. `revert_link_deletions.py`

Reverses a prior `check_links.py --mode live` run using its CSV report. Every row with `to-delete == "true"` has its resource `state` reverted to `active` (if currently `deleted`) and `package.metadata_modified` updated to NOW().

Set environment variable for: `POSTGRES_URL`

Then run: 

```bash
    python revert_link_deletions.py --input check_links_report_<ts>.csv --mode dry-run
```

`--mode` defaults to `dry-run` (no db writes, only logs and writes the revert reindex file). 

Use `--mode live` to actually restore.

Writes `packages_to_reindex_revert_{ts}.txt` - also creates input for  `solr_reindex_package_ids.py`.

Note: the original pre-deletion `metadata_modified` can't be recovered, it gets udpated to NOW() on revert.
