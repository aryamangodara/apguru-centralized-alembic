# APGuru Centralized Alembic Migrations

The single source of truth for **database schema migrations** of the APGuru
platform. It is intentionally **standalone** — it depends on no application
code, so any teammate or service can clone it, point it at a database, and run
migrations.

Migrations were extracted from `apguru-analytics-dashboard` (which no longer
carries them). The migration chain and every `revision` id are preserved
verbatim, so the existing `alembic_version` pointer in each environment stays
valid and `alembic upgrade head` continues from wherever the DB currently is.

## Conventions

- **Hand-written, raw SQL.** Migrations use `op.execute(...)` / `op.create_table(...)`
  with explicit DDL. There are **no SQLAlchemy models** here and
  **`alembic revision --autogenerate` is not supported** (`target_metadata = None`).
- Files are numbered sequentially: `001_…` … `030_…`. Each declares
  `revision` / `down_revision` forming one linear chain.
- The target MySQL database is reached with the **sync** PyMySQL driver
  (`mysql+pymysql://…`), not aiomysql.

## Setup

```bash
python -m venv .venv
# Windows: .venv\Scripts\activate   |   macOS/Linux: source .venv/bin/activate
pip install -r requirements.txt

cp .env.example .env
# then edit .env and set DATABASE_URL (or the DB_* vars) for the target DB
```

`env.py` reads the connection from the environment: it uses `DATABASE_URL` if
set, otherwise composes one from `DB_HOST` / `DB_PORT` / `DB_USER` /
`DB_PASSWORD` / `DB_NAME`.

## Commands

```bash
# Inspect (read-only — safe against any DB)
alembic current      # the revision the target DB is currently at
alembic history      # the full chain
alembic heads        # should be exactly ONE head (no branches)

# Apply
alembic upgrade head        # bring the DB up to the latest revision
alembic downgrade -1        # roll back one revision

# Author a new migration (no autogenerate — write the SQL yourself)
alembic revision -m "add widget table"
#   → edit the generated file: fill in upgrade()/downgrade() with op.execute(...)
```

## Deployment contract

**Migrations are no longer bundled with the application.** A deploy that
changes the schema must run `alembic upgrade head` from **this** repo against
the target database as an explicit step. Do not assume the app applies
migrations on boot — it does not.

## Migration-history notes

Two historical hazards, both already resolved and baked into the current chain
(kept here so the context travels with the migrations):

- **Duplicate `005` (resolved 2026-04-16).** Two files once declared
  `revision = "005"`. The dead one (`005_add_source_columns_to_generated_error_types`)
  was removed — `004` already creates those columns — leaving
  `005_widen_error_type_columns` (`revision="005"`, `down_revision="004"`). The
  chain is linear again.
- **Duplicate `029` multi-head (resolved).** A merge briefly produced two heads
  at `029`, blocking deploys; the chain was reconciled to a single head. Always
  confirm `alembic heads` returns exactly one entry before deploying.

If you ever see more than one head, **stop** — reconcile the branch (rebase the
stray revision's `down_revision`) before upgrading.
