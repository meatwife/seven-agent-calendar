import json, subprocess, sys, tempfile, threading, unittest
from http.client import HTTPConnection
from datetime import datetime, timezone
from pathlib import Path
from seven_calendar import Handler, dbcon, init_db, add_event, query_events, update_event, ics
from http.server import ThreadingHTTPServer

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

 def test_root_routes_unchanged(self):
  server=ThreadingHTTPServer(('127.0.0.1',0),lambda *a,**kw: Handler(*a,db_path=self.db,**kw))
  thread=threading.Thread(target=server.serve_forever,daemon=True); thread.start()
  try:
   conn=HTTPConnection(*server.server_address)
   conn.request('GET','/'); response=conn.getresponse(); self.assertEqual(response.status,200); self.assertIn('BASE_PATH',response.read().decode())
   conn.request('GET','/api/events'); response=conn.getresponse(); self.assertEqual(response.status,200); self.assertEqual(json.loads(response.read()),[])
   conn.close()
  finally: server.shutdown(); server.server_close(); thread.join()

 def test_prefixed_html_and_api_routes(self):
  add_event(self.con,title='prefixed',posture='event',start='2026-08-16T22:00:00Z',end='2026-08-17T02:00:00Z'); self.con.commit()
  server=ThreadingHTTPServer(('127.0.0.1',0),lambda *a,**kw: Handler(*a,db_path=self.db,base_path='/private-calendar',**kw))
  thread=threading.Thread(target=server.serve_forever,daemon=True); thread.start()
  try:
   conn=HTTPConnection(*server.server_address)
   conn.request('GET','/private-calendar/'); response=conn.getresponse(); html=response.read().decode()
   self.assertEqual(response.status,200); self.assertIn("BASE_PATH",html); self.assertIn("BASE_PATH+'/api/events",html)
   conn.request('GET','/private-calendar/api/events?start=2026-08-16T00%3A00%3A00Z&end=2026-08-18T00%3A00%3A00Z'); response=conn.getresponse(); data=json.loads(response.read())
   self.assertEqual(response.status,200); self.assertEqual([e['title'] for e in data],['prefixed'])
   conn.request('GET','/api/events'); response=conn.getresponse(); response.read(); self.assertEqual(response.status,404)
   conn.close()
  finally: server.shutdown(); server.server_close(); thread.join()

 def test_post_write_and_validation(self):
  server=ThreadingHTTPServer(('127.0.0.1',0),lambda *a,**kw: Handler(*a,db_path=self.db,base_path='/private-calendar',write_token='secret',**kw)); thread=threading.Thread(target=server.serve_forever,daemon=True); thread.start()
  try:
   conn=HTTPConnection(*server.server_address); body=json.dumps({'title':'birthday','posture':'recognition','start':'2026-02-03','end':'2026-02-04','all_day':True,'recurrence':'yearly','marker':'heart','color':'#d9a441'}).encode()
   conn.request('POST','/private-calendar/api/events',body,{'Content-Type':'application/json','X-Calendar-Write-Token':'secret'}); r=conn.getresponse(); self.assertEqual(r.status,201); created=json.loads(r.read()); self.assertTrue(created['all_day']); self.assertEqual(created['recurrence'],'yearly')
   conn.request('POST','/private-calendar/api/events',json.dumps({'title':'bad','posture':'nope','start':'2026-01-01T00:00:00Z','end':'2026-01-01T01:00:00Z'}),{'Content-Type':'application/json','X-Calendar-Write-Token':'secret'}); self.assertEqual(conn.getresponse().status,400)
  finally: server.shutdown(); server.server_close(); thread.join()

 def test_prefixed_post_and_yearly_query(self):
  add_event(self.con,title='gotcha day',posture='recognition',start='2026-05-06',end='2026-05-07',all_day=True,recurrence='yearly'); self.con.commit()
  found=query_events(self.con,'2028-05-01T00:00:00Z','2028-05-10T00:00:00Z'); self.assertEqual(found[0]['start'],'2028-05-06T00:00:00Z'); self.assertTrue(found[0]['id'])

 def test_all_day_range_is_canonical_utc_midnight_and_end_exclusive(self):
  eid=add_event(self.con,title='date only',posture='event',start='2026-08-20',end='2026-08-22T23:59:00-04:00',all_day=True); self.con.commit()
  event=query_events(self.con,include_cancelled=True)[0]
  self.assertEqual(event['id'],eid)
  self.assertEqual(event['start'],'2026-08-20T00:00:00Z')
  self.assertEqual(event['end'],'2026-08-21T00:00:00Z')
  self.assertEqual(len(query_events(self.con,'2026-08-21T00:00:00Z','2026-08-22T00:00:00Z')),0)

 def test_form_has_date_only_toggle_and_curated_palette(self):
  html=(Path(__file__).parent/'web'/'index.html').read_text()
  self.assertIn("startInput.type='date'",html)
  self.assertIn('endInput.disabled=on',html)
  for color in ('#3f7652','#8a6716','#655080','#176b73','#8b4a32','#87505f','#304a73'):
   self.assertIn(color,html)
  self.assertNotIn('type="color"',html)
if __name__=='__main__': unittest.main()
