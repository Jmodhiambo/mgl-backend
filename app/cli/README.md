# MGLTickets Admin CLI

A `typer`-based CLI that sits alongside your FastAPI app and talks to the
**same service layer** the routers use (`app/services/*.py`) — never to
repositories directly. That keeps validation, idempotency guards, and
business rules in one place regardless of whether a change comes from the
web app or the CLI.

## Install

```bash
pip install typer --break-system-packages   # if not already installed
```

## Run

From your project root (wherever `alembic.ini` / your `app/` package lives):

```bash
python -m app.cli --help
```

## Bootstrapping your first admin

This is the answer to your original question — how to become an admin
without already being one:

```bash
python -m app.cli users promote-admin martin@mgltickets.com --bootstrap
```

`--bootstrap` is meant for exactly this one-time case. It skips the
`--as <admin-email>` requirement every other mutating command has, and
logs the audit entry with `admin_id=None` (valid — `AuditLog.admin_id` is
nullable) and `admin_name="CLI (bootstrap — no admin account existed yet)"`.

After that, use `--as` for everything else:

```bash
python -m app.cli events approve 42 --as martin@mgltickets.com
```

## Command groups

### `users`
- `list [--role] [--active-only]`
- `search <name>`
- `show <email>`
- `set-role <email> <role> [--as | --bootstrap]`
- `promote-admin <email> [--as | --bootstrap]`
- `demote <email> --as <admin-email>`
- `deactivate <email> --as <admin-email>`
- `reactivate <email> --as <admin-email>`
- `force-verify-email <email> --as <admin-email>`

### `events`
- `pending` — list events awaiting approval
- `list [--organizer-id]`
- `show <event_id>` — full detail incl. commission/revenue breakdown
- `approve <event_id> --as <admin-email>`
- `reject <event_id> --as <admin-email> [--reason]`
- `set-status <event_id> <status> --as <admin-email>`
- `confirm-deletion <event_id> --as <admin-email>` — pending_deletion → deleted

### `settings`
- `show`
- `set <key> <value> --as <admin-email>`

### `audit`
- `list [--admin-id] [--action] [--target-type] [--limit]`
- `show <log_id>`
- `my-activity <admin_id> [--limit]`

### `sessions`
- `cleanup [--hours]` — purge expired/revoked refresh sessions
- `list-active <email>`
- `force-logout <email>` — revokes every session for that user

## What's deliberately NOT here

Orders, payments (including M-Pesa STK reconciliation), ticket
instances/check-in, notifications, organizer bulk emails, contact
messages, and analytics. These are either customer-facing flows that
assume real request context, or — in the case of payment reconciliation —
depend on logic (`POST /admin/payments/reconcile-stuck`, the STK Query
resolution path) that wasn't in the files I had access to when building
this. Say the word and I'll add any of these as their own command group.

## Two things worth double-checking on your end

1. **`settings set`** assumes `app/schemas/settings.py`'s
   `PlatformSettingsUpdate` exposes the same field names as the
   `PlatformSettings` model (all optional, for partial updates). I haven't
   seen that schema file — if a key errors out, send it over and I'll
   align the CLI's field list.

2. **New audit action tag**: `events set-status` logs an
   `"event_status_changed"` action for any transition other than
   `deleted`. That's not in the existing recognised-actions list in
   `audit_log_services.py` — per the reminder comment already in that
   file, add `"event_status_changed"` to the frontend filter list in
   `AuditLogs.tsx` so it displays and filters correctly in the admin UI.