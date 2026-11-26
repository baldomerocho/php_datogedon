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
                self.assertIn('permissions.datogedon-editorial.extends=":workspace"',process.call_args.args[0])
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


class Cycles(unittest.TestCase):
    def test_independent_windows_and_no_missed_burst(self):
        from cycles import due
        current=datetime(2026,11,25,11,20,tzinfo=TZ)
        self.assertTrue(due(current,'news')['key'].endswith('news:1100'))
        self.assertIsNone(due(current,'experience'))
        self.assertIsNone(due(datetime(2026,11,25,8,tzinfo=TZ),'news'))
        self.assertIsNone(due(datetime(2026,11,25,5,59,tzinfo=TZ),'news'))
    def test_three_experience_windows_and_normal_transition(self):
        from cycles import due
        for hour in [13,15,18]:self.assertTrue(due(datetime(2026,11,25,hour,tzinfo=TZ),'experience')['key'].endswith(str(hour)+'00'))
        self.assertIsNone(due(datetime(2026,11,25,18,tzinfo=TZ),'experience',False))
    def test_success_is_per_cycle_not_per_day(self):
        from runtime import success_path
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory)
            write(root/'private/cycle-context.json',{'key':'2026-11-25:news:0600'})
            a=success_path(root)
            write(root/'private/cycle-context.json',{'key':'2026-11-25:news:0900'})
            self.assertNotEqual(a,success_path(root))
    def test_attempt_is_durable_and_no_blind_retry(self):
        from cycles import run
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory);write(root/'editorial-config.json',{})
            write(root/'private/cycles.json',{'2026-11-25:experience:1300':{'status':'failed'}})
            with patch('cycles.now',return_value=datetime(2026,11,25,13,tzinfo=TZ)),patch('cycles.execute') as worker:
                self.assertEqual(run(root,'experience')['stage'],'already_attempted');worker.assert_not_called()
    def test_internal_audit_rejects_self_duplicates_and_unpublished(self):
        from internal_links import audit
        catalog=[{'id':1,'status':'publish','link':'https://datogedon.com/one/'},{'id':2,'status':'future','link':'https://datogedon.com/two/'}]
        result=audit({'id':1,'content':{'raw':'<p><a href="/one/">Context</a><a href="/one/">More</a><a href="/two/">Future</a></p>'}},catalog)
        self.assertEqual(len(result['problems']),4)
    def test_no_internal_links_is_valid(self):
        from internal_links import audit
        self.assertEqual(audit({'id':1,'content':{'raw':'<p>Nothing relevant to link.</p>'}},[])['problems'],[])


class NewsRuntime(unittest.TestCase):
    def run_case(self,author):
        from argparse import Namespace
        from runtime import success_path
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory);write(root/'editorial-config.json',{'publication_schedule':{'catch_up':True}});write(root/'queue.json',{'posts':[]})
            write(root/'private/cycle-context.json',{'key':'2026-11-25:news:0600','mode':'news'})
            (root/'NEWS-TASK.txt').write_text('Research news; {{CHECK_POST}}')
            post={'id':22,'status':'publish','author':author,'date':'2026-11-25T06:20:00','featured_media':1,'categories':[1],'excerpt':{'raw':'Summary'},'content':{'raw':'<p>'+('fact '*100)+'</p>'}}
            media={'mime_type':'image/webp','alt_text':'Diagram','media_details':{'width':1200,'height':630,'filesize':20000}}
            class FakeWP:
                def __init__(self,*a):pass
                def get(self,path):
                    if path=='posts/22?context=edit':return post,1
                    if path.startswith('media/'):return media,1
                    return [],1
            class Writer:
                returncode=0
                def communicate(self,*a,**kw):pass
            snapshots=[{'posts':[],'issues':[],'next_slots':[]},{'posts':[post],'issues':[]}]
            args=Namespace(force=False,health=False,verify_only=False,collect_only=False,credentials=Path('unused'))
            with patch('runtime.now',return_value=datetime(2026,11,25,6,20,tzinfo=TZ)),patch('runtime.collect') as collector,patch('runtime.WordPress',FakeWP),patch('runtime.reconcile',side_effect=snapshots),patch('runtime.shutil.which',return_value='/synthetic/codex'),patch('runtime.subprocess.Popen',return_value=Writer()) as worker,patch('runtime.notify'),contextlib.redirect_stdout(io.StringIO()):
                result=execute(root,args)
                collector.assert_not_called();self.assertIn('--search',worker.call_args.args[0])
                self.assertEqual(result,0 if author==135 else 1)
                self.assertEqual(success_path(root).exists(),author==135)
    def test_previous_failed_draft_does_not_count_as_a_new_article(self):
        from runtime import cycle_changes
        before=[{'id':1,'status':'publish'},{'id':2,'status':'draft'}]
        after=before+[{'id':3,'status':'draft'}]
        queue={'posts':[{'post_id':2,'cycle_key':'old'},{'post_id':3,'cycle_key':'current'}]}
        self.assertEqual([p['id'] for p in cycle_changes(before,after,queue,{'key':'current'})],[3])
        after[-1]['status']='publish'
        self.assertEqual([p['id'] for p in cycle_changes(before,after,queue,{'key':'current'})],[3])
    def test_only_a_published_draft_owned_by_this_cycle_is_resumed(self):
        from runtime import cycle_changes
        before=[{'id':2,'status':'draft'},{'id':3,'status':'draft'}]
        queue={'posts':[{'post_id':2,'cycle_key':'old'},{'post_id':3,'cycle_key':'current'}]}
        self.assertEqual(cycle_changes(before,before,queue,{'key':'current'}),[])
        after=[{'id':2,'status':'draft'},{'id':3,'status':'publish'}]
        self.assertEqual([p['id'] for p in cycle_changes(before,after,queue,{'key':'current'})],[3])
    def test_writer_has_network_without_unrestricted_filesystem_access(self):
        from runtime import writer_command
        command=writer_command('/synthetic/codex',Path('/synthetic/news'),True)
        self.assertIn('permissions.datogedon-editorial.network.enabled=true',command)
        self.assertIn('permissions.datogedon-editorial.extends=":workspace"',command)
        self.assertNotIn('danger-full-access',command)
        self.assertIn('--search',command)

    def test_news_publishes_same_day_without_private_collection(self):self.run_case(135)
    def test_wrong_author_cannot_be_marked_success(self):self.run_case(1)


class PublicationDateReconciliation(unittest.TestCase):
    def test_preflight_failure_records_details_without_starting_writer(self):
        from argparse import Namespace
        args=Namespace(force=False,health=False,verify_only=False,collect_only=False,credentials=Path('unused'))
        issues=[{'post_id':1,'issue':'fecha remota distinta; no se modificó'}]
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory);write(root/'editorial-config.json',{});write(root/'private/cycle-context.json',{'key':'2026-11-26:news:0900','mode':'news'})
            with patch('runtime.WordPress'),patch('runtime.reconcile',return_value={'issues':issues}),patch('runtime.notify'),patch('runtime.subprocess.Popen') as writer,contextlib.redirect_stdout(io.StringIO()):
                self.assertEqual(execute(root,args),1);writer.assert_not_called()
            report=read(root/'daily-status.json');self.assertEqual(report['failed_stage'],'preflight');self.assertEqual(report['preflight_issues'],issues);self.assertTrue(report['runtime_release'])

    def test_equivalent_formats_do_not_block_but_real_changes_do(self):
        from runtime import reconcile
        class WP:
            def get(self,*args):return {'id':1,'status':'publish','date':'2026-11-25T13:36:32','date_gmt':'2026-11-25T19:36:32','featured_media':1},1
            def posts(self,*args):return []
        for date,blocked in [('2026-11-25T13:36:32',False),('2026-11-25 13:36:32',False),('2026-11-25T19:36:32Z',False),('2026-11-25T13:36:33',True),('invalid',True)]:
            with self.subTest(date=date),tempfile.TemporaryDirectory() as directory:
                root=Path(directory);write(root/'queue.json',{'posts':[{'post_id':1,'date':date}]});write(root/'editorial-config.json',{'publication_schedule':{'catch_up':True}})
                result=reconcile(root,WP());self.assertEqual(bool(result['issues']),blocked)
                self.assertEqual(read(root/'queue.json')['posts'][0]['date'],date)


class VideoDrafts(unittest.TestCase):
    def brief(self):
        return {'post_id':1,'account':'@datogedon','article_url':'https://datogedon.com/synthetic/','sources':['https://example.invalid/source'],'topic_label':'Synthetic technology','date_label':'Synthetic date','source_label':'Synthetic source','scenes':[{'headline':'A concise synthetic headline','visual':'context','visual_data':{'title':'Context','labels':['One','Two']},'chunks':['A synthetic description explaining a verified change and its scope without adding unsupported claims.']} for _ in range(3)]}
    def test_real_video_brief_validates_without_external_runtime(self):
        from video import validate
        self.assertEqual(validate(self.brief())['post_id'],1)
    def test_explanation_can_exceed_old_budget_but_remains_bounded(self):
        from video import validate
        b=self.brief()
        for scene in b['scenes']:scene['chunks']=[' '.join(['detail']*20)+'.']*4
        self.assertIs(validate(b),b)  # 240 words, still short subtitle chunks.
        for scene in b['scenes']:scene['chunks'].append(' '.join(['detail']*21)+'.')
        with self.assertRaises(ValueError):validate(b)
    def test_missing_visual_data_never_reuses_other_news_figures(self):
        from video import validate
        b=self.brief();b['scenes'][0]['visual_data']={}
        with self.assertRaises(ValueError):validate(b)
    def test_private_paths_are_not_exported_to_video(self):
        from video import validate
        b=self.brief();b['scenes'][0]['chunks'].append('/Users/example/private')
        with self.assertRaises(ValueError):validate(b)
    def test_subtitles_round_over_minute_boundary(self):
        from video import timestamp
        self.assertEqual(timestamp(59.9999),'00:01:00,000')
        self.assertEqual(timestamp(59.9999,True),'0:01:00.00')
    def test_missing_brief_is_durable_and_does_not_publish(self):
        from video import enqueue
        with tempfile.TemporaryDirectory() as d:
            root=Path(d);config={'state_dir':str(root/'state'),'output_dir':str(root/'output')}
            post={'id':1,'status':'publish','slug':'synthetic','link':'https://datogedon.com/synthetic/'}
            with patch('video.subprocess.Popen') as renderer:
                job=enqueue(root,post,config);renderer.assert_not_called()
            self.assertEqual(job['status'],'needs_brief');self.assertEqual(read(root/'state/queue.json')['jobs']['1']['status'],'needs_brief')
    def test_unpublished_article_is_not_rendered(self):
        from video import enqueue
        with tempfile.TemporaryDirectory() as d:
            with self.assertRaises(ValueError):enqueue(Path(d),{'id':1,'status':'draft'}, {})
    def test_mismatched_brief_is_recorded_failed(self):
        from video import enqueue
        with tempfile.TemporaryDirectory() as d:
            root=Path(d);b=self.brief();b['post_id']=2;write(root/'private/video-brief-1.json',b)
            config={'state_dir':str(root/'state'),'output_dir':str(root/'output')}
            post={'id':1,'status':'publish','slug':'synthetic','link':'https://datogedon.com/synthetic/'}
            with patch('video.subprocess.Popen') as renderer:
                job=enqueue(root,post,config);renderer.assert_not_called()
            self.assertEqual(job['status'],'failed');self.assertFalse(job['published'])


class GeminiAudio(unittest.TestCase):
    def response(self):
        import base64,wave
        audio=io.BytesIO()
        with wave.open(audio,'wb') as stream:
            stream.setnchannels(1);stream.setsampwidth(2);stream.setframerate(24000);stream.writeframes(b'\0\0'*2400)
        return {'steps':[{'type':'model_output','content':[{'type':'audio','data':base64.b64encode(audio.getvalue()).decode()}]}],'usage':{'total_tokens':12}}
    def setup_client(self,directory):
        from gemini_tts import GeminiSpeech
        root=Path(directory);env=root/'voice.env';env.write_text('PUBLIC_APIKEY=primary-example\nAPIKEY=paid-example\n');env.chmod(0o600)
        return GeminiSpeech({'env_file':str(env),'cache_dir':str(root/'cache')}),root
    def test_primary_is_first_and_cache_avoids_repeat_charges(self):
        with tempfile.TemporaryDirectory() as directory:
            client,root=self.setup_client(directory)
            with patch('gemini_tts.request',return_value=self.response()) as api:
                client.synthesize('Synthetic speech.',root/'one.wav');client.synthesize('Synthetic speech.',root/'two.wav')
                api.assert_called_once();self.assertEqual(api.call_args.args[1],'primary-example')
            self.assertEqual((root/'one.wav').read_bytes(),(root/'two.wav').read_bytes());self.assertEqual(client.report()['cache_hits'],1)
    def test_paid_only_after_primary_quota_and_sticky_for_this_render(self):
        from gemini_tts import SpeechError
        with tempfile.TemporaryDirectory() as directory:
            client,root=self.setup_client(directory)
            with patch('gemini_tts.request',side_effect=[SpeechError(429,'QUOTA_EXHAUSTED'),self.response(),self.response()]) as api:
                client.synthesize('First sentence.',root/'one.wav');client.synthesize('Second sentence.',root/'two.wav')
                self.assertEqual([c.args[1] for c in api.call_args_list],['primary-example','paid-example','paid-example'])
            self.assertTrue(client.report()['paid_fallback_used'])
    def test_brief_quota_delay_retries_primary_before_paying(self):
        from gemini_tts import SpeechError
        with tempfile.TemporaryDirectory() as directory:
            client,root=self.setup_client(directory)
            with patch('gemini_tts.time.sleep') as sleep,patch('gemini_tts.request',side_effect=[SpeechError(429,'QUOTA_EXHAUSTED',2),self.response()]) as api:
                client.synthesize('Synthetic speech.',root/'one.wav');sleep.assert_called_once_with(2)
                self.assertEqual([c.args[1] for c in api.call_args_list],['primary-example','primary-example'])
            self.assertFalse(client.report()['paid_fallback_used'])
    def test_nonquota_errors_do_not_use_paid_key(self):
        from gemini_tts import SpeechError
        for status in [400,401,403,404,500,503,0]:
            with tempfile.TemporaryDirectory() as directory:
                client,root=self.setup_client(directory)
                with patch('gemini_tts.request',side_effect=SpeechError(status)) as api:
                    with self.assertRaises(SpeechError):client.synthesize('Synthetic speech.',root/'one.wav')
                    api.assert_called_once();self.assertEqual(api.call_args.args[1],'primary-example')
    def test_paid_failure_does_not_retry_billable_generation(self):
        from gemini_tts import SpeechError
        with tempfile.TemporaryDirectory() as directory:
            client,root=self.setup_client(directory)
            with patch('gemini_tts.request',side_effect=[SpeechError(429),SpeechError(503)]) as api:
                with self.assertRaises(SpeechError):client.synthesize('Synthetic speech.',root/'one.wav')
                self.assertEqual(api.call_count,2)
    def test_invalid_audio_is_not_cached_or_retried_with_paid(self):
        from gemini_tts import SpeechError
        with tempfile.TemporaryDirectory() as directory:
            client,root=self.setup_client(directory)
            with patch('gemini_tts.request',return_value={'steps':[]}) as api:
                with self.assertRaises(SpeechError):client.synthesize('Synthetic speech.',root/'one.wav')
                api.assert_called_once()
            self.assertFalse((root/'one.wav').exists())
    def test_error_and_usage_report_do_not_export_credentials(self):
        from gemini_tts import SpeechError
        with tempfile.TemporaryDirectory() as directory:
            client,root=self.setup_client(directory)
            with patch('gemini_tts.request',return_value=self.response()):client.synthesize('Synthetic speech.',root/'one.wav')
            report=json.dumps(client.report())+str(SpeechError(429))
            self.assertNotIn('primary-example',report);self.assertNotIn('paid-example',report)
    def test_env_must_be_private(self):
        from gemini_tts import credentials,SpeechError
        with tempfile.TemporaryDirectory() as directory:
            env=Path(directory)/'voice.env';env.write_text('PUBLIC_APIKEY=example');env.chmod(0o644)
            with self.assertRaises(SpeechError):credentials(env)


class SocialDistribution(unittest.TestCase):
    def fixture(self,root):
        import hashlib
        from social import enqueue
        write(root/'editorial-config.json',{'video':{'distribution':{'enabled':True}}})
        output=root/'output';output.mkdir();(output/'video.mp4').write_bytes(b'verified-synthetic-master')
        post={'id':1,'status':'publish','link':'https://datogedon.com/synthetic/','title':{'raw':'Synthetic headline'}}
        video={'post_id':1,'status':'ready_for_review','article_url':post['link'],'output':str(output),
               'video_sha256':hashlib.sha256((output/'video.mp4').read_bytes()).hexdigest()}
        return post,video,enqueue(root,post,video,'news')
    def test_outbox_is_durable_idempotent_and_rejects_a_different_master(self):
        import hashlib
        from social import enqueue,location
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory);post,video,job=self.fixture(root);before=(location(root)/'outbox.json').read_bytes()
            self.assertEqual(enqueue(root,post,video,'news'),job)
            self.assertEqual((location(root)/'outbox.json').read_bytes(),before)
            (Path(video['output'])/'video.mp4').write_bytes(b'changed');video['video_sha256']=hashlib.sha256(b'changed').hexdigest()
            with self.assertRaises(ValueError):enqueue(root,post,video,'news')
    def test_existing_public_platform_is_not_uploaded_again(self):
        from social import enqueue,location,eligible
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory);post,video,_=self.fixture(root);(location(root)/'outbox.json').unlink()
            video['platforms']={'youtube':{'status':'published','url':'https://www.youtube.com/shorts/abcdefghijk'}}
            job=enqueue(root,post,video,'news');self.assertFalse(eligible(job['platforms']['youtube']));self.assertTrue(eligible(job['platforms']['tiktok']))
    def test_platform_receipt_cannot_claim_success_without_identity_and_public_proof(self):
        from social import record,location
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory);self.fixture(root)
            with self.assertRaises(ValueError):record(root,1,'youtube','published','https://www.youtube.com/shorts/abcdefghijk',{})
            self.assertEqual(read(location(root)/'outbox.json')['jobs']['1']['platforms']['youtube']['status'],'pending')
            with self.assertRaises(ValueError):record(root,1,'tiktok','draft','https://www.tiktok.com/@other/video/123')
    def test_confirmed_receipt_is_independent_and_its_url_cannot_change(self):
        from social import record,location,CHANNEL
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory);self.fixture(root);proofpath=root/'Movies/Datogedon/review/proof.txt';proofpath.parent.mkdir(parents=True);proofpath.write_text('Synthetic Studio publication confirmation')
            proof={key:True for key in ['owner_verified','public_verified','ai_label_verified','caption_verified','playback_verified']}
            proof.update(channel_id=CHANNEL,snapshot_path=str(proofpath))
            with patch('social.Path.home',return_value=root):record(root,1,'youtube','published','https://www.youtube.com/shorts/abcdefghijk',proof)
            job=read(location(root)/'outbox.json')['jobs']['1'];self.assertEqual(job['platforms']['youtube']['status'],'published');self.assertEqual(job['platforms']['instagram']['status'],'pending')
            with self.assertRaises(ValueError):record(root,1,'youtube','draft','https://www.youtube.com/shorts/otherid1234')
    def test_active_or_uncertain_attempt_waits_for_its_persisted_deadline(self):
        from social import eligible
        current=datetime(2026,11,26,12,tzinfo=TZ)
        with patch('social.now',return_value=current):
            self.assertFalse(eligible({'status':'in_progress','attempts':1,'next_attempt_at':'2026-11-26T12:20:00-06:00'}))
            self.assertTrue(eligible({'status':'uncertain','attempts':1,'next_attempt_at':'2026-11-26T11:20:00-06:00'}))
            self.assertFalse(eligible({'status':'uncertain','attempts':3}))
    def test_unavailable_article_blocks_social_without_launching_browser_or_affecting_article(self):
        from social import run,location
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory);self.fixture(root)
            with patch('social.WordPress'),patch('social.verify_article',side_effect=ValueError('Article unavailable')),patch('social.subprocess.Popen') as worker,patch('social.notify'):
                report=run(root);worker.assert_not_called()
            self.assertEqual(report['status'],'pending');self.assertEqual(len(report['pending']),3)
            self.assertTrue(all(e['status']=='blocked' for e in read(location(root)/'outbox.json')['jobs']['1']['platforms'].values()))
    def test_social_installer_uses_event_wakeup_and_bounded_calendar_recovery(self):
        import importlib.util
        spec=importlib.util.spec_from_file_location('installer',Path(__file__).resolve().parents[1]/'editorial/install-mac.py');module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
        definitions=module.social_plists(Path('/synthetic'),'/python',Path('/runtime'),'/node')
        worker=next(d for name,d in definitions if name.endswith('publisher'))
        self.assertNotIn('StartInterval',worker);self.assertNotIn('KeepAlive',worker)
        self.assertEqual([item['Hour'] for item in worker['StartCalendarInterval']],[6,9,11,13,15,18])
    def test_render_completion_and_social_receipts_preserve_each_others_jobs(self):
        from social import location,sync_receipts
        from video import store_job
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory);_,video,_=self.fixture(root)
            path=root/'videos/queue.json';write(path,{'jobs':{'1':video,'2':{'status':'rendering'}}})
            outbox=read(location(root)/'outbox.json');outbox['jobs']['1']['platforms']['tiktok'].update(status='published',url='https://www.tiktok.com/@datogedon/video/123',blog_reference='linked');write(location(root)/'outbox.json',outbox)
            sync_receipts(root);self.assertTrue(read(path)['jobs']['1']['published']);self.assertEqual(read(path)['jobs']['2']['status'],'rendering')
            store_job(path,'2',{'status':'ready_for_review'})
            self.assertEqual(read(path)['jobs']['1']['platforms']['tiktok']['url'],'https://www.tiktok.com/@datogedon/video/123')

class VideoFinishing(unittest.TestCase):
    def test_logo_consumes_body_visual_time_without_delaying_narration(self):
        from video_finish import intro_timeline,outro_timeline
        original=[{'file':'hook.png','duration':4.2,'kind':'hook'},
                  {'file':'body.png','duration':.4,'kind':'body'},
                  {'file':'next.png','duration':8,'kind':'body'}]
        for mode in ['news','experience']:
            config={'enabled':True,'mode':mode,'intro_seconds':1,'outro_seconds':3}
            result=outro_timeline(intro_timeline(original,config),config)
            self.assertEqual(sum(s['frame_count'] for s in result),378)
            intro=next(s for s in result if s['kind']=='intro')
            self.assertEqual((intro['start_frame'],intro['frame_count']),(126,30))
            self.assertEqual(intro['brand_style'],mode)
            self.assertEqual(original[1]['duration'],.4)
            self.assertAlmostEqual(sum(s['duration'] for s in result),12.6)
    def test_news_sound_is_below_voice_and_does_not_change_timing_or_other_samples(self):
        import wave,math
        from array import array
        from video_finish import news_ident
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory);source=root/'voice.wav';target=root/'mix.wav';rate=24000
            samples=array('h',(round(8000*math.sin(2*math.pi*220*i/rate)) for i in range(rate*3)))
            with wave.open(str(source),'wb') as out:
                out.setnchannels(1);out.setsampwidth(2);out.setframerate(rate);out.writeframes(samples.tobytes())
            _,report=news_ident(source,target,1,True)
            with wave.open(str(target),'rb') as stream:
                self.assertEqual(stream.getnframes(),len(samples));mixed=array('h');mixed.frombytes(stream.readframes(stream.getnframes()))
            self.assertEqual(mixed[:rate],samples[:rate]);self.assertEqual(mixed[round(1.48*rate):],samples[round(1.48*rate):])
            difference=[a-b for a,b in zip(mixed[rate:round(1.48*rate)],samples[rate:round(1.48*rate)])]
            rms=lambda values:math.sqrt(sum(x*x for x in values)/len(values))
            self.assertGreater(rms(difference),0);self.assertLessEqual(rms(difference)/rms(samples[rate:round(1.48*rate)]),.251)
            self.assertFalse(report['adds_duration'])
            source_result,disabled=news_ident(source,root/'experience.wav',1,False)
            self.assertEqual(source_result,source);self.assertFalse(disabled['enabled']);self.assertFalse((root/'experience.wav').exists())
    def test_renderer_updates_preserve_distributed_video_and_queue(self):
        from video import enqueue
        for platform in ['tiktok','youtube','instagram']:
            with self.subTest(platform=platform),tempfile.TemporaryDirectory() as directory:
                root=Path(directory);path=root/'state/queue.json'
                previous={'post_id':1,'status':'ready_for_review','video_sha256':'published-master',
                          'platforms':{platform:{'status':'published','url':'https://example.invalid/confirmed'}}}
                write(path,{'jobs':{'1':previous}});before=path.read_bytes()
                with patch('video.subprocess.Popen') as renderer:
                    self.assertEqual(enqueue(root,{'id':1,'status':'publish'},{'state_dir':str(path.parent)}),previous)
                    renderer.assert_not_called();self.assertEqual(path.read_bytes(),before)
    def phases(self):return [{'file':'hook.png','duration':4.2,'kind':'hook'},{'file':'intro.png','duration':1,'kind':'intro'},{'file':'body.png','duration':12,'kind':'body'},{'file':'final.png','duration':5.3,'kind':'body'}]
    def test_intro_is_30_frames_outro_overlaps_final_audio(self):
        from video_finish import outro_timeline
        phases=outro_timeline(self.phases(),{'enabled':True,'outro_seconds':3})
        self.assertEqual([p['frame_count'] for p in phases if p['kind']=='intro'],[30])
        self.assertEqual(phases[-1]['kind'],'outro');self.assertEqual(phases[-1]['frame_count'],90)
        self.assertEqual(sum(p['frame_count'] for p in phases),round(sum(p['duration'] for p in self.phases())*30))
    def test_outro_can_start_before_a_short_final_scene_without_cutting_audio(self):
        from video_finish import outro_timeline
        scenes=self.phases();scenes[-1]['duration']=.8
        phases=outro_timeline(scenes,{'enabled':True,'outro_seconds':3})
        self.assertEqual(phases[-1]['frame_count'],90);self.assertEqual(phases[0]['duration'],4.2)
        self.assertAlmostEqual(sum(p['duration'] for p in phases),sum(p['duration'] for p in scenes))
    def test_logo_hash_changes_when_source_changes(self):
        from video_finish import branding_spec
        with tempfile.TemporaryDirectory() as directory:
            logo=Path(directory)/'logo.png';logo.write_bytes(b'synthetic-logo')
            before=branding_spec({'enabled':True,'logo_path':str(logo)})
            logo.write_bytes(b'updated-logo');after=branding_spec({'enabled':True,'logo_path':str(logo)})
            self.assertNotEqual(before['logo_sha256'],after['logo_sha256'])
    def test_missing_logo_and_wrong_intro_duration_fail_closed(self):
        from video_finish import branding_spec
        with self.assertRaises(ValueError):branding_spec({'enabled':True,'logo_path':'/synthetic/missing.png'})
        with tempfile.TemporaryDirectory() as directory:
            logo=Path(directory)/'logo.png';logo.write_bytes(b'fixture')
            with self.assertRaises(ValueError):branding_spec({'enabled':True,'logo_path':str(logo),'intro_seconds':2})
    def test_nonfinite_audio_measurement_is_rejected(self):
        from video_finish import parse_measurements
        with self.assertRaises(RuntimeError):parse_measurements('no measurements')
        data={'input_i':'-inf','input_tp':'-2','input_lra':'3','input_thresh':'-25','target_offset':'0'}
        with self.assertRaises(RuntimeError):parse_measurements(json.dumps(data))
    def test_truncated_encoded_video_is_rejected(self):
        from types import SimpleNamespace
        from video_finish import verify_frames
        stream={'nb_frames':'1101','width':1080,'height':1920,'r_frame_rate':'30/1','duration':'36.7'}
        with patch('video_finish.subprocess.run',return_value=SimpleNamespace(stdout=json.dumps({'streams':[stream]}))):
            with self.assertRaises(RuntimeError):verify_frames('synthetic.mp4',1191)
        stream.update(nb_frames='1191',duration='39.7')
        with patch('video_finish.subprocess.run',return_value=SimpleNamespace(stdout=json.dumps({'streams':[stream]}))):self.assertEqual(verify_frames('synthetic.mp4',1191)['frames'],1191)
    def test_encoded_peak_and_loudness_are_checked(self):
        from video_finish import verify_mastering
        with patch('video_finish.measure',return_value={'input_i':-16.1,'input_tp':-1.4}):self.assertIn('encoded_aac',verify_mastering({},'synthetic.mp4'))
        for values in [{'input_i':-12,'input_tp':-1.4},{'input_i':-16,'input_tp':-.1}]:
            with patch('video_finish.measure',return_value=values):
                with self.assertRaises(RuntimeError):verify_mastering({},'synthetic.mp4')

class VideoMotion(unittest.TestCase):
    def test_entrances_wait_for_their_stagger_and_settle(self):
        from video_motion import progress
        self.assertEqual(progress(-1,.2,.4),0)
        self.assertEqual(progress(.2,.2,.4),0)
        self.assertAlmostEqual(progress(.6,.2,.4),1)
        self.assertEqual(progress(10,.2,.4),1)
        values=[progress(t/30,.2,.4) for t in range(31)]
        self.assertEqual(values,sorted(values))
        with self.assertRaises(ValueError):progress(1,0,0)


class ShortHookAndExtendedGuides(unittest.TestCase):
    def test_new_scripts_open_with_one_useful_sentence_and_visual_mechanism(self):
        from video import validate
        brief=VideoDrafts().brief();brief['script_version']=2
        brief['scenes'][0].update(visual='flow',visual_data={'from':['Sesión abierta'],'to':['Correo confirmado'],'condition':'Validar código','check':'La sesión continúa'})
        validate(brief)
        brief['scenes'][0]['chunks']=['palabra '*23]
        with self.assertRaises(ValueError):validate(brief)
        brief['scenes'][0]['chunks']=['Una frase breve.'];brief['scenes'][0]['visual']='context'
        with self.assertRaises(ValueError):validate(brief)
    def test_draft_or_unowned_guides_never_get_an_outro_link(self):
        from extended_catalog import public_guides,related_guide,outro_target,CHANNEL
        with tempfile.TemporaryDirectory() as directory:
            state=Path(directory);guide={'post_id':1,'title':'A complete guide','url':'https://www.youtube.com/watch?v=abcdefghijk','channel_id':CHANNEL,'status':'draft','owner_verified':True,'public_verified':True}
            write(state/'extended-catalog.json',{'videos':{'one':guide}});self.assertEqual(public_guides(state),[]);self.assertIsNone(outro_target({'extended_video':guide}))
            guide['status']='published';write(state/'extended-catalog.json',{'videos':{'one':guide}})
            target=related_guide(state,{'post_id':1});self.assertEqual(outro_target({'extended_video':target})['url'],guide['url'])
            self.assertIsNone(related_guide(state,{'post_id':2}));self.assertEqual(related_guide(state,{'post_id':2,'extended_post_id':1})['url'],guide['url'])
            guide['owner_verified']=False;write(state/'extended-catalog.json',{'videos':{'one':guide}});self.assertEqual(public_guides(state),[])
            (state/'extended-catalog.json').write_text('{broken');self.assertEqual(public_guides(state),[])
    def test_explanatory_routing_matrix_includes_override_and_paused_rules(self):
        from extended_video import expected_route
        self.assertEqual(expected_route('on',False),'VPN');self.assertEqual(expected_route('off',True),'Sin VPN')
        self.assertEqual(expected_route('default',False),'Sin VPN');self.assertEqual(expected_route('default',True),'VPN')
        self.assertEqual(expected_route('on',True,True),'Sin VPN')
        with self.assertRaises(ValueError):expected_route('unknown',True)

class VideoReference(unittest.TestCase):
    def reference(self,content,url='https://www.tiktok.com/@datogedon/video/12345'):
        import runpy
        return runpy.run_path(str(Path(__file__).resolve().parents[1]/'editorial/link-video.py'))['reference'](content,url)
    def test_reference_preserves_sources_and_is_idempotent(self):
        body='<p>Original</p><h2>Fuentes</h2><ul><li>Source</li></ul>'
        result=self.reference(body)
        self.assertTrue(result.endswith('<h2>Fuentes</h2><ul><li>Source</li></ul>'))
        self.assertEqual(self.reference(result),result)
        self.assertIn('<p>Original</p>',result)
    def test_reference_rejects_other_accounts_and_ambiguous_markers(self):
        for url in ['https://www.tiktok.com/@other/video/123','https://www.tiktok.com/@datogedon/video/123?x=1','https://example.invalid/video/123']:
            with self.assertRaises(ValueError):self.reference('Original',url)
        with self.assertRaises(ValueError):self.reference('<!-- datogedon-video:start -->')
    def test_cross_platform_references_preserve_each_other_and_sources(self):
        body='<p>Original</p><h2>Fuentes</h2><p>Source</p>'
        urls=['https://www.tiktok.com/@datogedon/video/12345','https://www.youtube.com/shorts/iug5hEtAbL0','https://www.instagram.com/datogedon/reel/DgLbn82IKew/']
        for url in urls:body=self.reference(body,url)
        for url in urls:
            self.assertEqual(body.count(url),1)
            self.assertEqual(self.reference(body,url),body)
        self.assertTrue(body.endswith('<h2>Fuentes</h2><p>Source</p>'))
    def test_reference_rejects_conflicting_video_and_host_spoofing(self):
        body=self.reference('Original','https://www.youtube.com/shorts/iug5hEtAbL0')
        for url in ['https://www.youtube.com/shorts/aaaaaaaaaaa','https://www.youtube.com.evil.test/shorts/iug5hEtAbL0','https://www.youtube.com/shorts/iug5hEtAbL0?x=1','https://www.instagram.com/other/reel/abc/']:
            with self.assertRaises(ValueError):self.reference(body,url)
        with self.assertRaises(ValueError):self.reference('<!-- datogedon-video:end --><!-- datogedon-video:start -->')
    def test_extended_guide_preserves_the_existing_short_and_other_platforms(self):
        short='https://www.youtube.com/shorts/iug5hEtAbL0';guide='https://www.youtube.com/watch?v=abcdefghijk'
        body=self.reference('<p>Original</p><h2>Fuentes</h2><p>Source</p>',short)
        body=self.reference(body,guide);self.assertIn(short,body);self.assertIn(guide,body);self.assertIn('Ver la guía completa en YouTube',body)
        self.assertEqual(self.reference(body,guide),body);self.assertTrue(body.endswith('<h2>Fuentes</h2><p>Source</p>'))

if __name__=='__main__':unittest.main()
