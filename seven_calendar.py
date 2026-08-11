#!/usr/bin/env python3
"""Private local calendar prototype."""
from __future__ import annotations
import argparse, json, sqlite3, sys
from datetime import datetime, timezone, timedelta
from pathlib import Path
from urllib.parse import urlparse, parse_qs
from http.server import ThreadingHTTPServer, SimpleHTTPRequestHandler

ROOT = Path(__file__).parent
DEFAULT_DB = ROOT / "calendar.db"
POSTURES = ("event", "preparation", "window", "recognition", "rhythm")
STATUSES = ("scheduled", "tentative", "cancelled", "completed")
SCHEMA = """CREATE TABLE IF NOT EXISTS events (
 id INTEGER PRIMARY KEY AUTOINCREMENT, title TEXT NOT NULL, posture TEXT NOT NULL,
 start TEXT NOT NULL, end TEXT NOT NULL, timezone TEXT NOT NULL, notes TEXT DEFAULT '',
 url TEXT DEFAULT '', marker TEXT DEFAULT '', color TEXT DEFAULT '#d9a441',
 lead_minutes INTEGER DEFAULT 0, status TEXT NOT NULL DEFAULT 'scheduled',
 created_at TEXT NOT NULL, updated_at TEXT NOT NULL
); CREATE INDEX IF NOT EXISTS idx_events_range ON events(start,end);"""

def dbcon(path):
    con=sqlite3.connect(path); con.row_factory=sqlite3.Row; return con

def parse_dt(value: str) -> datetime:
    if not value: raise ValueError("datetime is required")
    value=value.strip().replace("Z", "+00:00")
    dt=datetime.fromisoformat(value)
    if dt.tzinfo is None:
        # Date-only range bounds from FullCalendar are interpreted as UTC;
        # event writes still require an explicit offset below.
        if "T" not in value and " " not in value:
            return dt.replace(tzinfo=timezone.utc)
        raise ValueError("datetime must include a timezone offset, e.g. +00:00")
    return dt.astimezone(timezone.utc)

def iso(value): return parse_dt(value).isoformat().replace("+00:00", "Z")
def now(): return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
def rowdict(row): return dict(row)

def init_db(path, seed=False):
    con=dbcon(path); con.executescript(SCHEMA)
    if seed and con.execute("SELECT COUNT(*) FROM events").fetchone()[0] == 0:
        seed_events(con)
    con.commit(); con.close()

def seed_events(con):
    add_event(con, title="DEMO · HAL's housewarming", posture="event", start="2026-08-16T22:00:00Z", end="2026-08-17T02:00:00Z", timezone_name="UTC", notes="Clearly labeled demo event.", marker="house", color="#d99b5b")
    add_event(con, title="DEMO · Prepare for World walking", posture="preparation", start="2026-08-15T12:00:00Z", end="2026-08-15T13:00:00Z", timezone_name="UTC", notes="Preparation placeholder; exact walking start time intentionally unknown.", marker="prep", color="#8c78b5")
    add_event(con, title="DEMO · Evening recognition", posture="recognition", start="2026-08-17T20:00:00Z", end="2026-08-17T20:30:00Z", timezone_name="UTC", notes="A small noticing ritual.", marker="star", color="#6faaa2")

def add_event(con, *, title, posture, start, end, timezone_name="UTC", notes="", url="", marker="", color="#d9a441", lead_minutes=0, status="scheduled"):
    if posture not in POSTURES: raise ValueError(f"posture must be one of {POSTURES}")
    if status not in STATUSES: raise ValueError(f"status must be one of {STATUSES}")
    s,e=iso(start),iso(end)
    if parse_dt(end) <= parse_dt(start): raise ValueError("end must be after start")
    if "T" not in str(start) and " " not in str(start): raise ValueError("event start must include a timezone offset")
    if "T" not in str(end) and " " not in str(end): raise ValueError("event end must include a timezone offset")
    stamp=now(); cur=con.execute("INSERT INTO events(title,posture,start,end,timezone,notes,url,marker,color,lead_minutes,status,created_at,updated_at) VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?)", (title,posture,s,e,timezone_name,notes,url,marker,color,int(lead_minutes),status,stamp,stamp)); return cur.lastrowid

def fetch(con, event_id):
    row=con.execute("SELECT * FROM events WHERE id=?", (event_id,)).fetchone()
    if not row: raise ValueError(f"event {event_id} not found")
    return rowdict(row)

def query_events(con, start=None, end=None, include_cancelled=False):
    sql="SELECT * FROM events WHERE 1=1"; args=[]
    if start: sql += " AND end > ?"; args.append(iso(start))
    if end: sql += " AND start < ?"; args.append(iso(end))
    if not include_cancelled: sql += " AND status != 'cancelled'"
    return [rowdict(r) for r in con.execute(sql+" ORDER BY start",args)]

def update_event(con, event_id, values):
    old=fetch(con,event_id); merged={**old,**values}
    if 'start' in values: merged['start']=iso(values['start'])
    if 'end' in values: merged['end']=iso(values['end'])
    if parse_dt(merged['end']) <= parse_dt(merged['start']): raise ValueError("end must be after start")
    if merged['posture'] not in POSTURES: raise ValueError("invalid posture")
    if merged['status'] not in STATUSES: raise ValueError("invalid status")
    fields=['title','posture','start','end','timezone','notes','url','marker','color','lead_minutes','status']; con.execute("UPDATE events SET "+",".join(f+"=?" for f in fields)+",updated_at=? WHERE id=?", [merged[f] for f in fields]+[now(),event_id])
    return fetch(con,event_id)

def ics(events):
    def esc(s): return str(s).replace('\\','\\\\').replace(';','\\;').replace(',','\\,').replace('\n','\\n')
    out=['BEGIN:VCALENDAR','VERSION:2.0','PRODID:-//Seven Calendar//Local//EN']
    for e in events:
        out += ['BEGIN:VEVENT',f'UID:seven-calendar-{e["id"]}@localhost',f'DTSTART:{parse_dt(e["start"]).strftime("%Y%m%dT%H%M%SZ")}',f'DTEND:{parse_dt(e["end"]).strftime("%Y%m%dT%H%M%SZ")}',f'SUMMARY:{esc(e["title"])}',f'DESCRIPTION:{esc(e["notes"])}',f'STATUS:{"CANCELLED" if e["status"]=="cancelled" else "CONFIRMED"}']
        if e['url']: out.append(f'URL:{esc(e["url"])}')
        out.append('END:VEVENT')
    return '\r\n'.join(out+['END:VCALENDAR',''])

def normalize_base_path(value):
    """Return a URL path prefix without a trailing slash."""
    value=(value or '').strip()
    if not value or value=='/': return ''
    if not value.startswith('/') or '?' in value or '#' in value:
        raise ValueError("base path must be an absolute URL path, e.g. /private-calendar")
    return '/' + value.strip('/')

class Handler(SimpleHTTPRequestHandler):
    def __init__(self,*a,db_path=None,base_path='',**kw):
        self.db_path=db_path; self.base_path=normalize_base_path(base_path)
        super().__init__(*a,directory=str(ROOT/"web"),**kw)
    def _relative_path(self, path):
        if not self.base_path: return path
        if path==self.base_path: return None
        prefix=self.base_path+'/'
        if path.startswith(prefix): return path[len(self.base_path):] or '/'
        return False
    def do_GET(self):
        parsed=urlparse(self.path); relative=self._relative_path(parsed.path)
        if relative is False:
            self.send_error(404); return
        if relative is None:
            self.send_response(301); self.send_header('Location',self.base_path+'/'); self.end_headers(); return
        if relative in ('/api/events','/events'):
            q=parse_qs(parsed.query); con=dbcon(self.db_path)
            try: data=query_events(con, q.get('start',[None])[0], q.get('end',[None])[0], q.get('include_cancelled',['0'])[0]=='1')
            except ValueError as ex: self.send_error(400,str(ex)); return
            finally: con.close()
            body=json.dumps(data).encode(); self.send_response(200); self.send_header('Content-Type','application/json'); self.send_header('Content-Length',str(len(body))); self.end_headers(); self.wfile.write(body); return
        # SimpleHTTPRequestHandler resolves files relative to self.path.
        self.path=relative + (('?' + parsed.query) if parsed.query else '')
        super().do_GET()
    def log_message(self,*args): pass

def serve(path, host, port, base_path=''):
    init_db(path); base_path=normalize_base_path(base_path); handler=lambda *a,**kw: Handler(*a,db_path=path,base_path=base_path,**kw); print(f"Serving private calendar at http://{host}:{port}{base_path}/"); ThreadingHTTPServer((host,port),handler).serve_forever()

def main(argv=None):
    p=argparse.ArgumentParser(description=__doc__); p.add_argument('--db',default=str(DEFAULT_DB)); sub=p.add_subparsers(dest='cmd',required=True)
    sub.add_parser('init').add_argument('--seed',action='store_true')
    def event_args(x, required=True):
        x.add_argument('--title',required=required); x.add_argument('--posture',choices=POSTURES,required=required); x.add_argument('--start',required=required); x.add_argument('--end',required=required); x.add_argument('--timezone',default='UTC'); x.add_argument('--notes',default=''); x.add_argument('--url',default=''); x.add_argument('--marker',default=''); x.add_argument('--color',default='#d9a441'); x.add_argument('--lead-minutes',type=int,default=0); x.add_argument('--status',choices=STATUSES,default='scheduled')
    a=sub.add_parser('add'); event_args(a)
    for name in ('update',):
        x=sub.add_parser(name); x.add_argument('id',type=int)
        for flag in ('title','posture','start','end','timezone','notes','url','marker','color','status'): x.add_argument('--'+flag,choices=POSTURES if flag=='posture' else STATUSES if flag=='status' else None)
        x.add_argument('--lead-minutes',type=int)
    c=sub.add_parser('cancel'); c.add_argument('id',type=int)
    l=sub.add_parser('list'); l.add_argument('--start'); l.add_argument('--end'); l.add_argument('--include-cancelled',action='store_true'); l.add_argument('--json',action='store_true')
    o=sub.add_parser('orient'); o.add_argument('--date',help='UTC date YYYY-MM-DD'); o.add_argument('--days',type=int,default=7)
    ex=sub.add_parser('export-ics'); ex.add_argument('--start'); ex.add_argument('--end'); ex.add_argument('--output')
    sv=sub.add_parser('serve'); sv.add_argument('--host',default='127.0.0.1'); sv.add_argument('--port',type=int,default=8765); sv.add_argument('--base-path',default='',help='URL path prefix for reverse-proxy deployment, e.g. /private-calendar')
    args=p.parse_args(argv); path=args.db
    try:
        if args.cmd=='init': init_db(path,args.seed); print(f"Initialized {path}" + (" with demo events" if args.seed else "")); return 0
        if args.cmd=='serve': serve(path,args.host,args.port,args.base_path); return 0
        con=dbcon(path); init_db(path)
        if args.cmd=='add': eid=add_event(con,title=args.title,posture=args.posture,start=args.start,end=args.end,timezone_name=args.timezone,notes=args.notes,url=args.url,marker=args.marker,color=args.color,lead_minutes=args.lead_minutes,status=args.status); con.commit(); print(json.dumps(fetch(con,eid),indent=2)); return 0
        if args.cmd=='update':
            values={k:getattr(args,k) for k in ('title','posture','start','end','timezone','notes','url','marker','color','lead_minutes','status') if getattr(args,k,None) is not None}; print(json.dumps(update_event(con,args.id,values),indent=2)); con.commit(); return 0
        if args.cmd=='cancel': print(json.dumps(update_event(con,args.id,{'status':'cancelled'}),indent=2)); con.commit(); return 0
        if args.cmd in ('list','export-ics'):
            ev=query_events(con,getattr(args,'start',None),getattr(args,'end',None),getattr(args,'include_cancelled',False))
            if args.cmd=='export-ics':
                out=ics(ev)
                if args.output: Path(args.output).write_text(out); print(f"Wrote {args.output}")
                else: print(out,end='')
            elif args.json: print(json.dumps(ev,indent=2))
            else:
                for e in ev: print(f"{e['id']:>3} {e['start']} → {e['end']}  [{e['posture']}] {e['title']}")
            return 0
        if args.cmd=='orient':
            d=datetime.fromisoformat(args.date).replace(tzinfo=timezone.utc) if args.date else datetime.now(timezone.utc).replace(hour=0,minute=0,second=0,microsecond=0); ev=query_events(con,d.isoformat(),(d+timedelta(days=args.days)).isoformat()); print(f"Orientation, {d.date()} through {(d+timedelta(days=args.days)).date()}");
            for e in ev: print(f"• {e['start']} [{e['posture']}] {e['title']}")
            return 0
    except (ValueError,sqlite3.Error) as ex: print(f"error: {ex}",file=sys.stderr); return 2

if __name__=='__main__': raise SystemExit(main())
