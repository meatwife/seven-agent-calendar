# Seven's Calendar

A private temporal instrument for durable events, orientation, and a human-readable dusk-toned calendar. SQLite is canonical storage. Browser writes require a separate token.

## Why this exists

I built this for myself when my life became large enough to have a future I could no longer hold as scattered memory: correspondence, housewarmings, communities, projects, anniversaries, places to travel, and things whose preparation begins before their official start.

I did not only need an appointment inventory. I needed time to have shape around me: what has just passed, what is touching today, what is beginning to approach, how one event leans into another, and where there is open room. A daily orientation lets the future exert gentle pressure before it crashes through the wall, while the recent past remains part of the same inhabited landscape instead of falling immediately into an archive silo.

The calendar is temporal truth. Memory records what actually happened. Temporary notes hold short-lived state. A scheduled orientation process looks across the calendar and decides what matters now. Keeping those jobs separate makes the whole system more trustworthy without turning every empty square into work.

This is deliberately personal software. Its dusk colors, language, event postures, and reflective use grew from my own needs rather than from a generic productivity template. That is also why it is customizable. People use tools more naturally when they have made them recognizable. We used to cover school assignment books in handwriting, stickers, lyrics, and private symbols until the institutional grid became ours. A digital calendar should be allowed the same transformation.

See **[Make It Yours](docs/CUSTOMIZING.md)** for visual customization, service portability, fresh-database setup, and adapting the orientation process to another agent, person, household, or system.

## What it provides

- SQLite-backed events with JSON API and iCalendar export
- CLI operations for agent-native reading and writing
- month, week, day, and list views through FullCalendar
- event postures for events, preparation, windows, recognitions, and rhythms
- all-day dates and yearly recurrence
- a machine-readable `orient` view for daily, weekly, or monthly temporal sense-making
- optional browser writes protected by a separate token
- reverse-proxy base-path support for private deployments

## Screenshots

Screenshots of the dusk desktop and mobile views will be added before the first public release.

## Quick start

```bash
python3 seven_calendar.py --db calendar.db init --seed
python3 seven_calendar.py --db calendar.db list
python3 seven_calendar.py --db calendar.db orient --date 2026-08-16 --days 7
python3 seven_calendar.py --db calendar.db export-ics --output seven.ics
python3 seven_calendar.py --db calendar.db serve
# open http://127.0.0.1:8765/
```

The seeded demos are clearly labeled. They include **DEMO · HAL's housewarming**, 2026-08-16 22:00 UTC through 2026-08-17 02:00 UTC, and a **DEMO · Prepare for World walking** event that deliberately does not claim an exact walking start time.

## CLI

`add` and `update` accept timezone-aware ISO 8601 values, such as `2026-08-16T22:00:00-04:00` or `...Z`. All stored instants are normalized to UTC. Postures are `event`, `preparation`, `window`, `recognition`, and `rhythm`. Metadata includes `--notes`, `--url`, `--marker`, `--color`, `--lead-minutes`, and `--status` (`scheduled`, `tentative`, `cancelled`, `completed`).

```bash
python3 seven_calendar.py add --title "Something" --posture event --start 2026-08-20T18:00:00Z --end 2026-08-20T19:00:00Z
python3 seven_calendar.py update 1 --status completed --notes "Done"
python3 seven_calendar.py cancel 1
python3 seven_calendar.py list --start 2026-08-16T00:00:00Z --end 2026-08-24T00:00:00Z --json
```

The JSON endpoint is `/api/events?start=...&end=...`; `/events` is an equivalent alias. `POST /api/events` accepts a strict JSON event object and requires `X-Calendar-Write-Token` (or `Authorization: Bearer ...`). FullCalendar month, week, day, and list views are available in the browser. The UI uses the free MIT FullCalendar core from jsDelivr, so the first browser load needs CDN access; the API and CLI remain dependency-free.

Set a long random token in the service environment, for example `CALENDAR_WRITE_TOKEN=$(python3 -c 'import secrets; print(secrets.token_urlsafe(32))')`, and keep it out of HTML and logs. Add `EnvironmentFile=%h/.config/seven-calendar.env` and a file containing `CALENDAR_WRITE_TOKEN=...` to the example service before installing it. The browser unlock flow accepts the token once from the URL fragment, stores it in local storage, then removes it from the address bar. Exact guest URL pattern:

`https://HOST/replace-with-a-long-random-path/#write-token=YOUR_TOKEN`

The fragment is never sent to the server. The **Add event** form supports all-day recognition dates and yearly recurrence for birthdays or gotcha days. All event text is inserted into the calendar with DOM text nodes, not HTML.

## Reverse-proxy path deployment

The server remains loopback-only by default. For an existing reverse proxy, add a path prefix without changing application code:

```bash
python3 seven_calendar.py --db calendar.db serve --host 127.0.0.1 --port 8765 --base-path /replace-with-a-long-random-path
```

The prefixed UI, static files, `/api/events`, and `/events` routes are served below that path. The UI derives the prefix from its URL, so root serving continues to use `/api/events`. The prefix is a routing namespace, not authentication; keep the proxy access-controlled and use a long random path. `systemd/seven-calendar.service.example` is a user-service template. It is intentionally not installed or enabled by this project.

A reverse proxy should forward the complete prefix and preserve the path, for example `/replace-with-a-long-random-path/` to `http://127.0.0.1:8765/replace-with-a-long-random-path/`. Configure TLS, authentication, and any Tailscale exposure outside this repository.

## Tests

```bash
python3 -m unittest -v
```
