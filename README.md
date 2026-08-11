# Seven's Calendar

A private, local-only temporal instrument for durable events, orientation, and a human-readable dusk-toned calendar. SQLite is canonical storage. No auth, deployment, network writes, or cron are included.

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

The read-only JSON endpoint is `/api/events?start=...&end=...`; `/events` is an equivalent alias. FullCalendar month, week, day, and list views are available in the browser. The UI uses the free MIT FullCalendar core from jsDelivr, so the first browser load needs CDN access; the API and CLI remain fully local and dependency-free.

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
