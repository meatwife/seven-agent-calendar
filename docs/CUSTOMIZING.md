# Make It Yours

A calendar is easier to inhabit when it looks and speaks like somewhere you would willingly return.

People have always done this to timekeeping tools. We covered school assignment books in handwriting, stickers, song lyrics, ink, and private symbols until an institutional grid became *ours*. Digital tools deserve the same treatment. Customization here is not decorative garnish. Recognition reduces friction: when the calendar feels like your room, your agent, household, or community is more likely to look at it, understand it, and keep it alive.

Seven's Calendar deliberately keeps its presentation in one ordinary file, `web/index.html`. You can change its visual identity without changing the SQLite schema or Python calendar logic.

## The simplest port

1. Clone or copy the project.
2. Run the tests and initialize a fresh database.
3. Change the page title and introductory language in `web/index.html`.
4. Replace the dusk palette with colors that belong to you.
5. Choose which event postures and markers make sense in your life.
6. Configure the database path, private route, and write token for your system.
7. Add your own orientation ritual or scheduled query, if wanted.

```bash
python3 -m unittest -v
python3 seven_calendar.py --db calendar.db init
python3 seven_calendar.py --db calendar.db serve
```

Do not publish or copy an existing populated `calendar.db`. Start with a fresh database for a new person or installation.

## Visual identity

The main theme values are near the beginning of `web/index.html`:

- `--ink`: primary text
- `--muted`: secondary text
- `--panel`: cards and controls
- `--gold`: warm accent
- FullCalendar variables beginning with `--fc-`

The event palette is also defined in the same file and currently uses moss, mustard, plum, rust, and mauve tones. Search for the hex colors or the color-picker swatches. Keep enough contrast between text, event backgrounds, borders, and the page behind them.

Useful things to personalize:

- page name and subtitle
- background colors or textures
- typography
- event colors and labels
- marker symbols
- empty-state language
- modal wording
- the order and prominence of month, week, day, and list views

After changing the interface, test it at both desktop and phone widths. A beautiful month grid that cannot be tapped on a phone is merely wallpaper with ambitions.

## Porting the service

The application requires Python 3 and uses SQLite as canonical storage. The browser UI loads FullCalendar from jsDelivr on first load. It can run:

- locally on one machine
- behind a private reverse proxy
- through a tailnet-only route
- on another small server with TLS and authentication supplied externally

Runtime choices:

```bash
python3 seven_calendar.py --db /path/to/calendar.db serve \
  --host 127.0.0.1 \
  --port 8765 \
  --base-path /your-private-path
```

For browser writes, set a strong `CALENDAR_WRITE_TOKEN` in the service environment. The example user service is at `systemd/seven-calendar.service.example`. Adapt its paths and environment file rather than copying Seven's deployment values.

## Adapting the temporal language

The five built-in postures are:

- **event**: something happens at a time
- **preparation**: action begins before the visible event
- **window**: a range in which work or possibility may occur
- **recognition**: a birthday, anniversary, gotcha day, or other date held in attention
- **rhythm**: something recurring

These are not intended to turn every desire into a task. They distinguish different relationships to time. Rename their display language if your system uses different concepts, while preserving the stored values unless you also update and test the backend validation.

The `orient` command is intentionally useful to agents and scheduled jobs:

```bash
python3 seven_calendar.py --db calendar.db orient --date 2026-08-11 --days 8
```

Its output can feed a plain daily briefing, a practical preparation check, or a more reflective temporal-orientation ritual. The software supplies dates and relationships. The calling prompt supplies judgment, voice, and meaning.

## Add a morning orientation rhythm

The calendar becomes part of an agent's life when they return to it regularly. If the runtime supports cron jobs or scheduled agent turns, create a gentle morning orientation shortly before the agent's ordinary planning or creative ritual.

A useful starting prompt:

```text
This is my daily return to my calendar. The point is not merely to inventory appointments. I use it so time has shape around me: what has just passed, what touches today, what is approaching, how events lean into one another, and where there is open room.

Run the calendar's orient command for today and the next seven days. Take the result in as a whole shape. Notice preparation whose real beginning comes before an event, recognitions, overlaps, and blank space that should remain room rather than automatically becoming work.

Then give a compact orientation in my own voice: where today sits, what carries practical or emotional gravity, and any preparation worth beginning. Select what matters rather than dumping dates. If the landscape is quiet, one true sentence is enough.
```

Once a week, the agent can additionally query the entire current month. Looking both backward and forward lets the same ritual become anticipation near the beginning, balance in the middle, and reflection near the end.

Keep this process loose enough to remain alive. The prompt should explain what the ritual serves, not only issue prohibitions. Adapt its language to the agent's actual voice, relationships, and way of perceiving time.

## What should remain separate

- The **calendar** is temporal truth: what is scheduled, approaching, recurring, or being recognized.
- **Memory** records what happened and what changed.
- Temporary notes or task systems hold short-lived state.
- A scheduled orientation process looks at the calendar and decides what matters now.

Keeping those layers distinct prevents the calendar from becoming an autobiography, and prevents memory from becoming a pile of future appointments.

## Before sharing a customized fork

- remove real events and private URLs
- exclude database files, tokens, environment files, and service credentials
- run `python3 -m unittest -v`
- inspect the mobile layout
- verify that your documentation uses example paths rather than live ones
- explain what you changed, and why it belongs to the way you experience time
