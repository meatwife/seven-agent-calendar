import json, subprocess, sys, tempfile, unittest
from datetime import datetime, timezone
from pathlib import Path
from seven_calendar import dbcon, init_db, add_event, query_events, update_event, ics

class CalendarTests(unittest.TestCase):
 def setUp(self): self.tmp=tempfile.TemporaryDirectory(); self.db=Path(self.tmp.name)/'x.db'; init_db(self.db); self.con=dbcon(self.db)
 def tearDown(self): self.con.close(); self.tmp.cleanup()
 def test_overlap_boundaries(self):
  add_event(self.con,title='one',posture='event',start='2026-08-16T22:00:00Z',end='2026-08-17T02:00:00Z'); self.con.commit()
  self.assertEqual(len(query_events(self.con,'2026-08-17T00:00:00+00:00','2026-08-17T01:00:00+00:00')),1)
  self.assertEqual(len(query_events(self.con,'2026-08-17T02:00:00+00:00','2026-08-17T03:00:00+00:00')),0)
 def test_crud_and_cancel(self):
  eid=add_event(self.con,title='draft',posture='window',start='2026-01-01T00:00:00+00:00',end='2026-01-01T01:00:00+00:00'); self.con.commit(); self.assertEqual(update_event(self.con,eid,{'title':'updated'})['title'],'updated'); self.con.commit(); self.assertEqual(len(query_events(self.con)),1); update_event(self.con,eid,{'status':'cancelled'}); self.con.commit(); self.assertEqual(query_events(self.con),[]); self.assertEqual(len(query_events(self.con,include_cancelled=True)),1)
 def test_ics(self):
  eid=add_event(self.con,title='ics, thing',posture='recognition',start='2026-01-01T00:00:00Z',end='2026-01-01T01:00:00Z'); self.con.commit(); self.assertIn('UID:seven-calendar-%s@localhost'%eid,ics(query_events(self.con))); self.assertIn('SUMMARY:ics\\, thing',ics(query_events(self.con)))
 def test_cli_seed(self):
  r=subprocess.run([sys.executable,'seven_calendar.py','--db',str(self.db),'init','--seed'],capture_output=True,text=True); self.assertEqual(r.returncode,0); self.assertIn("HAL's housewarming",subprocess.check_output([sys.executable,'seven_calendar.py','--db',str(self.db),'list'],text=True))
if __name__=='__main__': unittest.main()
