"""Synthetic editorial state tests; never read actual assistant records or credentials."""
import contextlib,io,json,sys,tempfile,unittest
from pathlib import Path
from datetime import datetime
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'editorial'))
from collector import clean,collect
from runtime import merge_sources,next_slots,quality,write,read,execute,notify,TZ

class Editorial(unittest.TestCase):
    def test_redacts_quoted_credentials_and_auth(self):
        for source in ['"token": "synthetic secret with spaces"',"'APIKEY': 'syntheticsecret'",'Authorization: Bearer syntheticsecret','Authorization: Basic c3ludGhldGlj', '-----BEGIN PRIVATE KEY-----\nsyntheticsecret\n-----END PRIVATE KEY-----']:
            result=clean(source);self.assertNotIn('syntheticsecret',result);self.assertNotIn('c3ludGhldGlj',result);self.assertNotIn('synthetic secret',result)
    def test_redacts_private_locations(self):
        self.assertNotIn('192.168.',clean('https://private.invalid/x /Users/example/project a@example.invalid 192.168.1.2'))
    def test_collector_omits_tools_and_internal_reasoning(self):
        with tempfile.TemporaryDirectory() as directory:
            home=Path(directory);folder=home/'.claude/projects/project';folder.mkdir(parents=True)
            rows=[{'type':'user','sessionId':'synthetic-session','timestamp':'2026-11-24T10:00:00Z','message':{'content':'Revisar el formato de fechas'}}, {'type':'assistant','timestamp':'2026-11-24T10:01:00Z','message':{'model':'synthetic-model','content':[{'type':'text','text':'Ajusté el formato; falta verificar.'},{'type':'thinking','thinking':'reasoning-not-for-export'},{'type':'tool_use','name':'Read','input':{'value':'tool-payload-not-for-export'}}]}}]
            (folder/'session.jsonl').write_text('\n'.join(json.dumps(x) for x in rows))
            result=collect(home);body=json.dumps(result)
            self.assertNotIn('reasoning-not-for-export',body);self.assertNotIn('tool-payload-not-for-export',body)
            self.assertEqual(result['sessions'][0]['model_evidence'][0]['model_id'],'synthetic-model')
    def session(self,last,text):return {'key':'same','last_event':last,'assistant_text':[text],'user_text_candidates':['specification']}
    def test_newer_local_evidence_wins_over_verbose_archive(self):
        local=self.session('2026-11-24T10:00:00Z','new');old=self.session('2026-10-01T10:00:00Z','old '*200)
        item=merge_sources([local],[('retired-server',[old])])[0]
        self.assertEqual(item['assistant_text'],['new']);self.assertFalse(item['archived_only']);self.assertFalse(item['source_freshness']['retired-server'])
    def test_archived_source_is_not_fresh(self):
        self.assertTrue(merge_sources([],[('retired-server',[self.session('2026-10-01','old')])])[0]['archived_only'])
    def test_calendar_preserves_slots_and_daily_limit(self):
        current=datetime(2026,11,24,13,tzinfo=TZ)
        posts=[{'status':s,'date':d} for s,d in [('publish','2026-11-24T09:00:00'),('future','2026-11-24T16:00:00'),('future','2026-11-25T08:00:00'),('future','2026-11-25T16:00:00')]]
        original=json.dumps(posts);self.assertEqual(next_slots(posts,current),['2026-11-26 08:00:00','2026-11-26 16:00:00']);self.assertEqual(json.dumps(posts),original)
    def test_calendar_margin_and_normal_cadence(self):
        self.assertEqual(next_slots([],datetime(2026,11,24,15,45,tzinfo=TZ),False,1),['2026-11-25 08:00:00'])
        self.assertEqual(next_slots([],datetime(2026,11,24,15,45,tzinfo=TZ),True,1),['2026-11-25 08:00:00'])
    def test_incomplete_or_sensitive_story_fails_quality(self):
        post={'content':{'raw':'<p>/Users/example/private</p>'},'featured_media':0,'categories':[],'excerpt':{}}
        result=quality(post,{})
        self.assertTrue(result['problems']);self.assertIn('posible dato privado',result['problems'])
    def test_complete_story_passes(self):
        post={'content':{'raw':'<p>'+('experiencia '*450)+'</p>'},'featured_media':1,'categories':[1],'excerpt':{'raw':'Resumen'}}
        media={1:{'mime_type':'image/webp','alt_text':'Diagrama de decisiones','media_details':{'width':1200,'height':630,'filesize':22000}}}
        self.assertEqual(quality(post,media)['problems'],[])
    def test_atomic_private_state(self):
        with tempfile.TemporaryDirectory() as directory:
            path=Path(directory)/'state.json';write(path,{'status':'verified'});self.assertEqual(read(path),{'status':'verified'});self.assertEqual(path.stat().st_mode&0o777,0o600)
    def test_before_13_does_not_collect_or_run_agent(self):
        from argparse import Namespace
        args=Namespace(force=False,health=False,verify_only=False,collect_only=False)
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory);write(root/'editorial-config.json',{})
            with patch('runtime.now',return_value=datetime(2026,11,24,7,tzinfo=TZ)),patch('runtime.collect') as collector:
                self.assertEqual(execute(root,args),0);collector.assert_not_called()
            self.assertEqual(read(root/'private/last-wakeup.json')['stage'],'not_due')

    def test_completed_day_does_not_recollect_or_spawn_writer(self):
        from argparse import Namespace
        args=Namespace(force=False,health=False,verify_only=False,collect_only=False)
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory);write(root/'editorial-config.json',{});write(root/'private/last-success.json',{'date':'2026-11-24','post_ids':[1,2]})
            with patch('runtime.now',return_value=datetime(2026,11,24,14,tzinfo=TZ)),patch('runtime.collect') as collector,patch('runtime.subprocess.Popen') as writer,contextlib.redirect_stdout(io.StringIO()):
                self.assertEqual(execute(root,args),0);collector.assert_not_called();writer.assert_not_called()
            self.assertEqual(read(root/'private/last-wakeup.json')['stage'],'already_completed')

    def run_writer_case(self,wrong_slot):
        from argparse import Namespace
        args=Namespace(force=False,health=False,verify_only=False,collect_only=False,credentials=Path('unused'))
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory);write(root/'editorial-config.json',{'archived_sources':[]});write(root/'queue.json',{'posts':[]});(root/'DAILY-TASK.txt').write_text('Use {{CHECK_POST}}. Preserve privacy.')
            item={'key':'synthetic','first_event':'2026-11-24','last_event':'2026-11-24','project_key':'synthetic','source_digest':'synthetic','assistant_text':[],'user_text_candidates':[]}
            snapshots=[{'posts':[],'issues':[],'next_slots':['2026-11-25 08:00:00']},{'posts':[{'id':22,'status':'future','date':'2026-11-26T08:00:00' if wrong_slot else '2026-11-25T08:00:00'}],'issues':[]}]
            class FakeWP:
                def __init__(self,*a):pass
                def get(self,*a):return [],1
            class Writer:
                returncode=0
                def communicate(self,prompt,timeout):
                    self.prompt=prompt
            with patch('runtime.now',return_value=datetime(2026,11,24,14,tzinfo=TZ)),patch('runtime.collect',return_value={'sessions':[item]}),patch('runtime.WordPress',FakeWP),patch('runtime.reconcile',side_effect=snapshots),patch('runtime.shutil.which',return_value='/synthetic/codex'),patch('runtime.subprocess.Popen',return_value=Writer()) as process,patch('runtime.notify') as alert,contextlib.redirect_stdout(io.StringIO()):
                result=execute(root,args)
                self.assertEqual(process.call_args.args[0][process.call_args.args[0].index('-s')+1],'workspace-write')
                self.assertEqual(result,1 if wrong_slot else 0)
                if wrong_slot:
                    alert.assert_called_once();self.assertIsNone(read(root/'private/last-success.json'));self.assertEqual(read(root/'daily-status.json')['stage'],'failed')
                else:
                    alert.assert_not_called();self.assertEqual(read(root/'private/last-success.json')['post_ids'],[22]);self.assertEqual(read(root/'daily-status.json')['stage'],'verified')
    def test_writer_success_requires_verified_remote_slot(self):self.run_writer_case(False)
    def test_exit_zero_with_wrong_slot_is_not_success(self):self.run_writer_case(True)

    def test_alerts_are_once_per_type_per_day(self):
        from types import SimpleNamespace
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory)
            with patch('runtime.now',return_value=datetime(2026,11,24,14,tzinfo=TZ)),patch('runtime.subprocess.run',return_value=SimpleNamespace(returncode=0)) as popup:
                notify(root,'health_failed','Synthetic health alert');notify(root,'run_failed','Synthetic run alert');notify(root,'health_failed','Synthetic health alert')
                self.assertEqual(popup.call_count,2)
    def test_normal_mode_grandfathers_existing_two_post_days(self):
        posts=[{'status':'future','date':'2026-11-25T08:00:00'},{'status':'future','date':'2026-11-25T16:00:00'}]
        self.assertEqual(next_slots(posts,datetime(2026,11,24,14,tzinfo=TZ),False,1),['2026-11-26 08:00:00'])

if __name__=='__main__':unittest.main()
