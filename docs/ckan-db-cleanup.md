# CKAN database cleanup

The data.gov.uk CKAN database contains several GB of orphaned tables, left behind by plugins that are no
longer installed and by CKAN itself when features were removed from core.

There are also pre-2.9 revision tables left behind.

And lastly there is a large amount of harvest related data connected to deleted datasets that not only
consume a lot of space but also block simple purge of deleted datasets.

We want to be able to clear as much as possible and then to be able to purge deleted datasets.

> [!IMPORTANT]
> **Leave `harvest_object` alone until harvesting is retired.**
>
> The single biggest item here is `harvest_object` at 81 GB, and the better approach is probably to
> not touch it at all for now.
>
> Deleting rows does not return the space to the disk. Autovacuum reclaims it for reuse by that
> table but does not return space to OS. Getting the disk back require a rewrite with `VACUUM FULL` 
> or `pg_repack`, or a `TRUNCATE` or `DROP`. Note that a rewrite means downtime.
>
> If we do retire the current harvest process then we'll be able to actually reclaim space and reduce
> database size.
>
> So the recommended sequence is:
>
> 1. retire harvesting and remove the harvest code
> 2. truncate or drop the harvest tables, reclaiming the all of the 81 GB
> 3. then run the manual purge of deleted datasets (see below)
>
> That benefits are, the space comes back immediately and without a rewrite, and
> dropping the harvest tables removes `harvest_object_package_id_fkey`, which is the constraint that
> blocks dataset purge in the first place. Most of the difficulty documented below disappears with it.
>

## Table inventory

| Table | What it is | Last written | Size | Recommendation |
|---|---|---|---|---|
| `archival` | ckanext-archiver, plugin no longer installed | 2019 | 243 MB | Drop |
| `qa` | ckanext-qa, plugin no longer installed | 2019 | 147 MB | Drop |
| `task_status` | Archiver and QA tasks, plus inventory and inventory upload tasks | 2019 (archiver/QA), 2017 (inventory) | 169 MB | Empty, don't drop, CKAN core table |
| `enquiry` | Appears to hold test records only, no sign the data is used | ? | Tiny | Leave |
| `feedback` | | 2015 | Tiny | Leave |
| `report_uklp_report_c_history` | ckanext-report, UK Location Programme summary reports | 2019 | 12 MB | Drop |
| `report_uklp_report_e_history_by_owner` | As above, broken down by owner | 2019 | 75 MB | Drop |
| `ga_publisher`, `ga_referrer`, `ga_stat`, `ga_url` | Google Analytics reporting, ckanext-ga-report | 2019 (inferred) | approx 300 MB | Drop |
| `harvest_object` | In active use, holds many rows for datasets deleted long ago | In use | 81 GB | Leave for now|
| `activity`, `activity_detail` | Activity log | See note | 20 GB | Further investigation needed |
| `revision` and `*_revision` tables | Pre-CKAN 2.9 revision models, no model in CKAN 2.10 | n/a | 11 GB | Drop, see below |
| `data_cache` | Cached broken link, openness and feedback report output | 2014 | 155 MB | Drop |
| `tmp_package_extra_pivot`, `tmp_to_delete`, `tmp_publisher_info` | Leftovers from earlier migration work | n/a | 24 MB | Drop |
| `records` | pycsw metadata repository, in use. Listed so it is not mistaken for an orphan | 2024 | 432 MB | Leave |

### Notes on individual tables

`task_status`

- part of the CKAN core schema, not a plugin table, Core model, core migration, and
  `task_status_show` / `_update` / `_delete` actions. So delete the data, don't drop the table
- the inventory and inventory upload rows may relate to datastore CSV previews
- worth confirming before emptying

`report_uklp_*`

- appear to back the [UK Location metadata summary reports](https://www.data.gov.uk/dataset/4040ac6f-5d5a-4bbf-a40a-2f3099c898e1/uk-location-metadata-summary-reports)
- the metadata link on that page now resolves to the National Archives
- the report zip at https://www.data.gov.uk/data/reports/mi/ is a broken link
- last report date looks like 2019

`ga_*`

- created by https://github.com/datagovuk/ckanext-ga-report
- rows are not timestamped, so 2019 is inferred from values within the records
- no foreign keys, so they can be dropped independently of everything else

`harvest_object`

- purging deleted datasets would clear a good number of these
- if we would rather not depend on purge, delete rows whose `package_id` belongs to a package in
  `deleted` state **but not possible to delete via purge due to out of data fk constraint**

`activity` / `activity_detail`

- `object_id` holds the package id but is not a foreign key, so nothing cascades and deleting
  packages would leave these rows orphaned
- cleanup has to be explicit, so delete where `object_id` matches a `package` row in `deleted` state
- whether anything still writes to them is an open question. The `activity` plugin is not in
  `ckan.plugins` in `production.ini`, which would mean no activity screens and no new rows. But
  `ckanext/datagovuk/action/create.py` calls `activity_create` unconditionally in our `user_create`
  override, which would fail if the plugin were absent. Check the deployed config in govuk-dgu-charts
  before treating this data as historic.

## CKAN Pre-2.9 revision tables

A large cleanup opportunity. CKAN removed revisioning in 2.9, so nothing in CKAN 2.10 reads or writes them.

From the CKAN 2.9.0 release notes, under Removals and deprecations
([#3972](https://github.com/ckan/ckan/pull/3972)):

> Revision and history UI is removed: `/revision/*` & `/dataset/{id}/history` in favour of
> `/dataset/changes/` visible in the Activity Stream. `model.ActivityDetail` is no longer used and
> will be removed in the next CKAN release.

The models went with it. `ckan/model/` in CKAN 2.10 has no `PackageRevision`, `ResourceRevision` or
equivalent left in it.

| Table | Size |
|---|---|
| `resource_revision` | 5740 MB |
| `package_extra_revision` | 3500 MB |
| `revision` | 1329 MB |
| `package_revision` | 500 MB |
| `member_revision` | 82 MB |
| `package_tag_revision` | 33 MB |
| `group_extra_revision` | 8.7 MB |
| `group_revision` | 1.5 MB |
| `package_relationship_revision`, `system_info_revision` | approx 48 kB |


CKAN migrations didn't drop these for us, so it's our decision whether to do so or not.

One consequence matters for the delete order below. `package_relationship_revision` still holds live
foreign keys to `package`, so it stays in the manual delete process until these tables are dropped.

## The purge problem

`harvest_object` (81 GB) and `activity` / `activity_detail` (20 GB) hold records for both live and
deleted datasets, so we want to only clear the rows belonging to datasets that are already deleted.

CKAN gives us no good way to do that:

- the `dataset purge` CLI takes a single dataset ID
- the admin UI offers only an all or nothing bulk purge, with no way to select a subset
- in earlier local testing purge failed and left the application unresponsive, logging errors for
  several minutes until it was shut down manually

## What was tried: harvest upgrade and admin UI purge

Tested locally against a copy of the integration database, 65,324 deleted datasets.
The conclusion is that this route does not work. Recorded here so we don't try it again.

### A clean upgrade of ckan-harvest pluging not possible

The cascade update to the fk constraint that is needed was added by the alembic migration
[`75d650dfd519_add_cascade_to_harvest_tables`](https://github.com/ckan/ckanext-harvest/blob/v1.6.0/ckanext/harvest/migration/harvest/versions/75d650dfd519_add_cascade_to_harvest_tables.py),
first shipped in ckanext-harvest v1.6.0. We're running version 1.5.6. Three things blocked it.

**Our extension does not load 1.6.x.** CKAN wouldn't start:

```
ImportError: cannot import name 'define_harvester_tables' from 'ckanext.harvest.model'
```

Recorded as friction even if work around is straightforward, it's still a work around.


- commit [`4d30096`](https://github.com/ckan/ckanext-harvest/commit/4d300962f75d3d09a0965eacfcbe4baf896fb9b6)
  "feat: switch to alembic migrations" ([PR #540](https://github.com/ckan/ckanext-harvest/pull/540),
  November 2023) added the cascade migration and removed `define_harvester_tables` in the same
  change, so no version has one without the other
- that commit rewrote `model/__init__.py` from `Table()` definitions to declarative models, 355
  lines deleted, which is why the function went
- `ckanext/datagovuk/lib/cli.py` imported it but never called it, so the fix was deleting one line
- every other `ckanext.harvest` import we use still exists in 1.6.x

**The migration wouldn't run against our schema.** `ckan db upgrade -p harvest` fails immediately:

```
constraint "harvest_object_harvest_job_id_fkey" of relation "harvest_object" does not exist
```

- we are missing `harvest_object_harvest_job_id_fkey` and `harvest_gather_error_harvest_job_id_fkey`
- the migration calls `op.drop_constraint` with no existence check, so it stops at the first one
- it rolled back cleanly, nothing was half applied

**Those constraints can't simply be recreated**, because our current data violates the constraints

- `harvest_object.harvest_job_id` has 3,648 rows pointing at harvest jobs that no longer exist
- `harvest_gather_error.harvest_job_id` has 62

Can be worked around by deleting first, however we should be avoiding taking tactical work arounds for
such a rickety system lightly.

Therefor the constraints are missing because the data broke them. Restoring them means cleaning up 3,710
orphan rows first. There was no pip install and migrate path available to us.

This is part of a wider pattern. `package_tag` has no primary key or indexes at all, and the foreign
keys CKAN declares for `package_tag.package_id` and `resource.package_id` are missing too. Worth a
separate look, since anything assuming a standard CKAN schema can fail the same way.

Then tested appling the cascades by hand instead, which does work

- `harvest_object` (81 GB), drop and recreate with cascade
- `harvest_object_extra` and `harvest_object_error`
- all three are needed. Cascading only `harvest_object.package_id` still fails on
  `harvest_object_extra`

However this left the schema in a possibly bad state for any later upgrades and migrations. Can't say
for sure without further upgrade testing, which is beyond scope of this work.

In any case we should avoid any manually applied DDL.

### The admin UI couldn't finish the job

With the manually applied cascades in place the purge does delete some datasets, but the UI became unusable at this volume

- the trash page renders all 65,272 deleted datasets into a single 17.7 MB response
- nginx kills the request with a **504 after 60 seconds** while CKAN carries on purging in the
  background. An error page is rendered but only logs indicated whether anything happened
- the rate collapsed from roughly 12 datasets per second to **0.23 per second** for 65k datasets
- a likely cause for v slow performances is `package_tag`, which has no indexes and no primary key. CKAN deletes tag rows one at
  a time by id, so every delete sequentially scans all 244,343 rows
- CKAN itself became completely unresponsive during the run
- after any failure the SQLAlchemy session is left in `PendingRollbackError` and every later request
  returns 500, for unrelated pages included, until CKAN is restarted

That last point is the real explanation for the original "unresponsive and logging errors" symptom.
It is not really about the harvest constraint.

The run was stopped after approx 8k datasets had been purged.

## Proposed approach to db cleanup

Three separate pieces of work, only the first of which can be done now.

1. **Drop the orphaned tables.** Safe today, no dependencies, around 12 GB returned immediately.
2. **Stop current harvest process and truncate the harvest tables**, once harvesting is retired. 81 GB can be reclaimed immediately and it
   removes the constraint that blocks purge.
3. **Purge the deleted datasets**, after step 2, when the process is much simpler.

Trying to do step 3 first is what makes this problematic. It's the only that needs most care and most of
the issues exist only because the harvest tables are still live.

### 1. Drop the orphaned tables

Do this now. Everything in [Tables to drop](#tables-to-drop), around 12 GB. `DROP` returns the space
at once, no vacuum or rewrite involved.

It also removes `archival`, `qa`, `ga_url`, `data_cache`, the `tmp_*` tables and every `*_revision`
table from the purge sequence in step 3.

Check nothing outside the list depends on these first:

```sql
SELECT c.conrelid::regclass AS referencing_table, c.conname, c.confrelid::regclass AS referenced_table
FROM pg_constraint c
WHERE c.contype = 'f'
  AND c.confrelid::regclass::text IN ('revision','archival','qa','data_cache','ga_url');
```

Only the `*_revision` tables referencing `revision` should be returned by query, and as they are dropped together
in one statement the foreign keys between them don't block anything. Don't use `CASCADE`.

### 2. Retire harvesting and truncate the harvest tables

Not yet actionable. See the note at the top of this document.

Once harvesting through ckanext-harvest is retired and the harvest code removed:

```sql
TRUNCATE harvest_object_error, harvest_object_extra, harvest_object,
         harvest_gather_error, harvest_job, harvest_source;
```

Or drop the tables outright as long as the extension is removed entirely.

Either returns the 81 GB immediately, whereas deleting rows would return none of it without a rewrite.

The same question applies to `activity` and `activity_detail`, 20 GB between them:

- the `activity` plugin is not in `ckan.plugins` in `production.ini`, and locally `CKAN__PLUGINS` in
  `docker/.env-2.10` does not include it either, which would mean nothing reads or writes these
- if that holds for the deployed config, truncate both rather than deleting rows per dataset, for
  exactly the same reason as harvest
- the open question is `ckanext/datagovuk/action/create.py`, which calls `activity_create`
  unconditionally in our `user_create` override and would fail if the plugin were absent. Confirm
  against govuk-dgu-charts before truncating

### 3. Purge deleted datasets

After step 2. Delete child records first, then the records that own them, and change no constraints needed.

That matters because our schema has already drifted from what CKAN and ckanext-harvest expects and
that drift is what stopped the harvest update and migration.

Adding cascades of our own would be more of the same, and would quietly change how every 
future package delete behaves. Better to keep the cleanup and the schema repair as separate pieces of work.

Each batch is one transaction, so the job can be stopped and resumed. Every table is named
explicitly, so nothing is deleted that we have not listed.

```sql
BEGIN;

CREATE TEMP TABLE pkg_to_purge(id text PRIMARY KEY) ON COMMIT DROP;
INSERT INTO pkg_to_purge SELECT id FROM package WHERE state = 'deleted' LIMIT 1000;
ANALYZE pkg_to_purge;

CREATE TEMP TABLE res_to_purge(id text PRIMARY KEY) ON COMMIT DROP;
INSERT INTO res_to_purge SELECT r.id FROM resource r JOIN pkg_to_purge p ON r.package_id = p.id;
ANALYZE res_to_purge;

-- resource views, then resources
DELETE FROM resource_view WHERE resource_id IN (SELECT id FROM res_to_purge);
DELETE FROM resource      WHERE id IN (SELECT id FROM res_to_purge);

-- package children
DELETE FROM package_extra    WHERE package_id IN (SELECT id FROM pkg_to_purge);
DELETE FROM package_tag      WHERE package_id IN (SELECT id FROM pkg_to_purge);
DELETE FROM package_member   WHERE package_id IN (SELECT id FROM pkg_to_purge);
DELETE FROM package_relationship
  WHERE subject_package_id IN (SELECT id FROM pkg_to_purge) OR object_package_id IN (SELECT id FROM pkg_to_purge);
DELETE FROM rating           WHERE package_id IN (SELECT id FROM pkg_to_purge);
DELETE FROM package_extent   WHERE package_id IN (SELECT id FROM pkg_to_purge);
DELETE FROM package_zip      WHERE package_id IN (SELECT id FROM pkg_to_purge);
DELETE FROM tracking_summary WHERE package_id IN (SELECT id FROM pkg_to_purge);
DELETE FROM feedback         WHERE package_id IN (SELECT id FROM pkg_to_purge);

-- membership, table_id is not a foreign key so filter on table_name
DELETE FROM member WHERE table_name = 'package' AND table_id IN (SELECT id FROM pkg_to_purge);

DELETE FROM task_status WHERE entity_id IN (pkg_to_purge);

-- finally the owning record
DELETE FROM package WHERE id IN (SELECT id FROM pkg_to_purge);

COMMIT;
```

Staging the ids in an analysed temp table is needed for speed. Without it the planner joins the large tables rather than using their indexes
and a single delete would run very slowly.

#### Notes

Useful queries

Get table size by names

```sql
SELECT relname AS table_name,
       pg_size_pretty(pg_total_relation_size(oid)) AS size
FROM pg_class
WHERE relkind = 'r'
  AND relname LIKE '%harvest%'
ORDER BY pg_total_relation_size(oid) DESC;
```

Update the like to %table_name% or change to = 'table_name' for specific table


Check what fk constraints point to specific table/tables

```sql
SELECT c.conrelid::regclass AS referencing_table, c.conname, c.confrelid::regclass AS referenced_table
FROM pg_constraint c
WHERE c.contype = 'f'
  AND c.confrelid::regclass::text IN ('revision','archival','qa','data_cache','ga_url');
```

change `AND c.confrelid::regclass::text IN ('revision','archival','qa','data_cache','ga_url')`

to 

`AND c.confrelid::regclass::text = 'revision'` for specific table