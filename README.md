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

## Tests

```bash
python3 -m unittest -v
```
