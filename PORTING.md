# Porting and Agent Integration

Seven's Agent Calendar is a small standalone application, not an OpenClaw plugin. Its calendar logic, SQLite store, command-line interface, HTTP server, and browser UI do not import an agent SDK. OpenClaw is how Seven currently calls the calendar and schedules an orientation ritual, but it is not required to run the project.

That makes the project harness-agnostic in a precise sense: another agent runtime can call the CLI or HTTP API without rewriting the calendar. The runtime-specific work is deciding **when** to consult it, **which commands** the agent may run, and **how** calendar results enter the model's context.

This repository is not a drop-in skill or extension for Claude Code, Codex, Letta, Hermes, or another companion platform. Those systems have different tool, scheduling, permission, and prompt mechanisms. Adapt the connection to the harness rather than inventing dependencies inside the calendar.

## A prompt you can give your agent

> Inspect this repository and my current agent setup before changing anything. Integrate the calendar through its existing CLI or JSON API instead of copying Seven's OpenClaw-specific paths or rituals. Use a fresh SQLite database, pass its path explicitly, keep the HTTP server on a private interface, and preserve my runtime's existing permission boundaries. Add a scheduled orientation only if my harness supports one. Verify the database path, read/write behavior, restart persistence, time-zone handling, and the exact text placed in model context.

## What is actually in this repository

| Part | Location | Contract |
| --- | --- | --- |
| Calendar logic and schema | `seven_calendar.py` | Python 3 standard library and SQLite |
| Agent-friendly CLI | `seven_calendar.py` | `init`, `add`, `update`, `cancel`, `list`, `orient`, `export-ics`, `serve` |
| Read API | `GET /api/events` or `GET /events` | JSON event list; optional `start` and `end` query bounds |
| Browser-create API | `POST /api/events` or `POST /events` | Strict JSON object plus a write token |
| Browser UI | `web/index.html` | FullCalendar loaded from jsDelivr; month, week, day, and list views |
| Service example | `systemd/seven-calendar.service.example` | A template only; it contains example deployment paths |
| Visual and ritual customization | `docs/CUSTOMIZING.md` | Theme, temporal language, and orientation guidance |

There is no bundled scheduler, model client, prompt injector, authentication proxy, TLS configuration, or agent-tool registration. Those belong to the surrounding system.

## Smallest local proof

Run this before adding any harness integration:

```bash
git clone https://github.com/meatwife/seven-agent-calendar.git
cd seven-agent-calendar
python3 -m unittest -v

python3 seven_calendar.py --db ./calendar.db init
python3 seven_calendar.py --db ./calendar.db add \
  --title "Test event" \
  --posture event \
  --start 2026-10-04T15:00:00Z \
  --end 2026-10-04T15:30:00Z
python3 seven_calendar.py --db ./calendar.db orient --date 2026-10-04 --days 7
```

The global `--db` option must appear before the subcommand. Always pass it explicitly in an integration. The program's default is a `calendar.db` beside the source file, which is convenient for a demo but easy to confuse with the live database used by a service.

Do not copy somebody else's populated database. Initialize a fresh one for each installation, and keep `*.db` files out of version control.

## Choose an integration boundary

### 1. Let the agent call the CLI

This is the simplest and usually the safest option for a local agent harness. Register a narrow command or tool that invokes the script with a fixed absolute database path. The useful read operations are:

```bash
python3 /path/to/seven_calendar.py --db /path/to/calendar.db list \
  --start 2026-10-04T00:00:00Z \
  --end 2026-10-12T00:00:00Z \
  --json

python3 /path/to/seven_calendar.py --db /path/to/calendar.db orient \
  --date 2026-10-04 \
  --days 8
```

The human-readable `orient` output is suitable for a scheduled model turn. `list --json` is better when the harness should parse events before deciding what to show the model.

For writes, expose only the operations the agent should actually have:

- `add` creates timed events;
- `update ID` changes supplied fields;
- `cancel ID` marks an event cancelled rather than deleting it;
- `export-ics` emits an iCalendar feed or file.

The current CLI creates timed events. All-day events and yearly recurrence are currently created through the browser/API path, not CLI flags. Do not document imaginary `--all-day` or `--recurrence` options when wrapping it.

A coding harness such as Claude Code or Codex can invoke these commands directly within its shell permissions. A persistent companion runtime will usually expose them as narrow tools so the model does not need unrestricted shell access.

### 2. Use the JSON API

Run the built-in server on loopback or another private interface:

```bash
CALENDAR_WRITE_TOKEN="replace-with-a-long-random-token" \
  python3 seven_calendar.py --db /path/to/calendar.db serve \
  --host 127.0.0.1 \
  --port 8765 \
  --base-path /your-private-path
```

An integration may read a bounded range with:

```text
GET /your-private-path/api/events?start=2026-10-04T00:00:00Z&end=2026-10-12T00:00:00Z
```

To create an event, send a JSON object to the same endpoint with either `X-Calendar-Write-Token` or `Authorization: Bearer ...`. Required fields are `title`, `posture`, `start`, and `end`; unknown fields are rejected. Accepted fields are:

```text
title, posture, start, end, timezone, notes, url, marker, color,
lead_minutes, status, all_day, recurrence, recognition_date
```

Important current boundaries:

- `GET` is not token-authenticated. Privacy depends on loopback binding, a private network, or an authenticating reverse proxy.
- `POST` creates events only. The HTTP API does not currently update, cancel, or delete them.
- The built-in server does not provide TLS or user accounts.
- The URL prefix is routing, not authentication.
- The browser stores the write token in that browser's local storage after accepting it from a URL fragment or prompt.

Keep these constraints when writing an adapter. Do not expose the server publicly merely because the POST route has a token.

### 3. Import the Python module

Python code can import functions such as `init_db`, `query_events`, `add_event`, or `update_event` from `seven_calendar.py`. This is useful for a tightly controlled local integration, but those functions are an internal module surface rather than a separately versioned SDK. Prefer the CLI or API when process isolation and a stable text/JSON boundary are more valuable.

## Connecting the calendar to an agent's day

A useful agent integration has three pieces:

1. **A fixed source of temporal truth** — one explicit SQLite database path.
2. **A narrow read/write connection** — CLI tools or private API calls allowed by the harness.
3. **A return rhythm** — an optional scheduled turn that queries the calendar and places selected results in context.

The calendar does not inject itself into model context. In OpenClaw, a scheduled agent turn can run `orient`; another runtime might use a cron task, hook, workflow, MCP-style local tool, or application code around each model request. Follow the supported mechanism of the installed harness.

Keep the schedule outside this repository. A portable scheduled prompt can say:

```text
Query the calendar's orient view for today and the next seven days using the
configured database. Notice events, preparation windows, recognitions,
overlaps, and genuinely open space. Return a short orientation that selects
what matters instead of dumping every row. Do not turn blank space into work.
```

Adapt that language to the agent's real voice and role. `docs/CUSTOMIZING.md` contains Seven's fuller ritual as an example, not a universal system prompt.

## Data and time contracts

- SQLite is canonical storage. The `events` table is created and additively migrated by `init_db`.
- Timed event writes require an ISO 8601 offset such as `Z` or `+01:00`; stored instants are normalized to UTC.
- All-day values are dates. They are stored as a half-open UTC range ending at midnight on the following day.
- Yearly recurrence is supported only for all-day events. Occurrences are materialized while querying a bounded date range.
- Postures are `event`, `preparation`, `window`, `recognition`, and `rhythm`.
- Statuses are `scheduled`, `tentative`, `cancelled`, and `completed`.
- Normal reads omit cancelled events unless the CLI/API query explicitly includes them.

If an adapter maps from another calendar or tool schema, preserve these semantics at the boundary and test daylight-saving offsets and all-day dates explicitly.

## Deployment adaptation

The example systemd user service is intentionally not installed by this project. Before using it:

1. replace its `WorkingDirectory`, script path, and database path;
2. create a private environment file containing `CALENDAR_WRITE_TOKEN`;
3. keep the process bound to `127.0.0.1` unless a trusted private-network design requires otherwise;
4. configure TLS, access control, and any reverse proxy outside this repository;
5. make the database directory writable by the service user;
6. verify the service restarts against the same database path.

The browser UI needs network access to jsDelivr on first load because FullCalendar is not vendored. The CLI and API use only Python's standard library and work without that frontend dependency.

For an ephemeral container host, mount persistent storage for the database. A successful deploy followed by an empty calendar after restart means the filesystem boundary was wrong, not that SQLite failed to save.

## Customization without coupling

You can change presentation and language without changing the agent integration:

- edit `web/index.html` for title, colors, markers, and browser wording;
- adapt the orientation prompt in the scheduler or harness;
- rename displayed posture language while retaining stored values;
- place a different human-facing UI in front of the same API;
- omit the browser entirely and use only CLI tools.

If you change stored posture values, validation rules, recurrence behavior, or the event schema, that is a data-model fork. Update both backend validation and tests rather than only changing labels in the page.

## Port verification checklist

Before calling an adaptation complete, verify all of the following:

- `python3 -m unittest -v` passes in the repository;
- the integration uses the intended absolute database path;
- a created event survives a process or service restart;
- the agent can read a bounded range without receiving unrelated files or shell access;
- writes require the intended permission boundary;
- unauthenticated HTTP reads are unreachable outside the trusted boundary;
- time-zone offsets normalize correctly and all-day events do not shift dates;
- cancelled events behave as expected;
- model context contains only the intended calendar result, not credentials or raw private configuration;
- any scheduled orientation runs in the correct time zone and fails softly when the calendar is unavailable;
- the UI works below the configured base path, if one is used;
- the public documentation and service template contain examples rather than live paths, URLs, tokens, or events.

The portable part is the calendar's temporal contract. The harness supplies permission, scheduling, and judgment; the human and agent supply the life that makes the dates matter.
