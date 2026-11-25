"""Render an editorial vertical-video brief locally. Never uploads or posts to TikTok."""
import argparse,hashlib,json,os,re,signal,subprocess,sys,wave
from pathlib import Path

def validate(brief):
    if not isinstance(brief.get('post_id'),int) or brief['post_id']<1:raise ValueError('post_id required')
    if brief.get('account')!='@datogedon':raise ValueError('Unexpected target account')
    if not 3<=len(brief.get('scenes',[]))<=8:raise ValueError('Use 3–8 scenes')
    if not brief.get('sources'):raise ValueError('Cited sources required')
    for key in ['topic_label','date_label','source_label']:
        if not isinstance(brief.get(key),str) or not 1<=len(brief[key])<=70:raise ValueError('Editorial labels required')
    for scene in brief['scenes']:
        if scene.get('visual') not in ['parallel','comparison','metric','context','question']:raise ValueError('Unsupported visual')
        if not scene.get('headline') or len(scene['headline'])>100:raise ValueError('Short headline required')
        if not scene.get('chunks'):raise ValueError('Narration missing')
        data=scene.get('visual_data',{})
        required={'parallel':['label','note'],'comparison':['rows'],'metric':['value','detail','scope','note'],'context':['title','labels'],'question':['line1','line2','comparison','note']}[scene['visual']]
        if any(key not in data for key in required):raise ValueError('Visual data missing; never reuse unrelated numbers')
        if scene['visual']=='comparison' and len(data['rows'])!=2:raise ValueError('Comparison requires two rows')
        if scene['visual']=='context' and not 1<=len(data['labels'])<=3:raise ValueError('Use at most three contextual labels')
        for chunk in scene['chunks']:
            if not isinstance(chunk,str) or not chunk.strip() or len(chunk)>155:raise ValueError('Short caption chunks required')
    words=sum(len(re.findall(r'\w+',c)) for scene in brief['scenes'] for c in scene['chunks'])
    if not 40<=words<=180:raise ValueError('Use a concise 40–180 word script')
    public_text=' '.join(c for scene in brief['scenes'] for c in scene['chunks'])
    if re.search(r'/Users/|/home/|(?:ghp_|sk-proj-|github_pat_)[A-Za-z0-9_-]{20,}',public_text):raise ValueError('Possible private data in video')
    return brief

def timestamp(seconds,ass=False):
    units=round(seconds*(100 if ass else 1000));scale=100 if ass else 1000
    whole,fraction=divmod(units,scale);hours,remainder=divmod(whole,3600);minutes,secs=divmod(remainder,60)
    return f'{hours}:{minutes:02}:{secs:02}.{fraction:02}' if ass else f'{hours:02}:{minutes:02}:{secs:02},{fraction:03}'

def card(scene,index,total,brief,path):
    from PIL import Image,ImageDraw,ImageFont
    im=Image.new('RGB',(1080,1920),'#111820');d=ImageDraw.Draw(im)
    d.polygon([(730,0),(1080,0),(1080,1920),(940,1920)],fill='#19252e')
    regular='/System/Library/Fonts/Supplemental/Arial.ttf';bold='/System/Library/Fonts/Supplemental/Arial Bold.ttf'
    font=lambda size,b=False:ImageFont.truetype(bold if b else regular,size)
    white='#fff8ed';orange='#ff966f';muted='#b9c6ce';panel='#202e38';stroke='#3c505c'
    def centered(text,y,size=40,color=white,b=False):
        f=font(size,b);w=d.textlength(text,font=f)
        while w>740 and size>22:size-=2;f=font(size,b);w=d.textlength(text,font=f)
        if w>740:raise ValueError('Graphic label overflows safe area')
        d.text(((960-w)/2,y),text,font=f,fill=color)
    d.text((90,145),brief['topic_label'],font=font(26,True),fill=orange)
    d.text((90,190),brief['date_label'],font=font(24),fill=muted)
    lines=[]
    for word in scene['headline'].split():
        if lines and d.textlength(lines[-1]+' '+word,font=font(78,True))<790:lines[-1]+=' '+word
        else:lines.append(word)
    if len(lines)>3:raise ValueError('Headline overflows video safe area')
    for n,line in enumerate(lines):
        if d.textlength(line,font=font(78,True))>790:raise ValueError('Headline word too wide')
        d.text((86,260+n*94),line,font=font(78,True),fill=white)
    d.rounded_rectangle((90,620,880,1070),radius=30,fill=panel,outline=stroke,width=2)
    visual=scene['visual'];data=scene['visual_data']
    if visual=='parallel':
        d.text((130,665),data['label'],font=font(28,True),fill=orange)
        for row in range(2):
            y=755+row*102
            for col in range(4):
                x=135+col*178;d.rounded_rectangle((x,y,x+145,y+65),radius=12,fill=orange if row==0 else '#d8e4d5')
        d.text((130,990),data['note'],font=font(24),fill=muted)
    elif visual=='comparison':
        for n,(label,main,detail,color) in enumerate([(row['label'],row['main'],row['detail'],orange if i==0 else white) for i,row in enumerate(data['rows'])]):
            y=650+n*195;d.text((130,y),label,font=font(25,True),fill=color);d.text((130,y+38),main,font=font(63,True),fill=color);d.text((130,y+112),detail,font=font(26),fill=muted)
    elif visual=='metric':
        centered(data['value'],680,124,orange,True);centered(data['detail'],842,34);centered(data['scope'],929,27,muted,True)
        centered(data['note'],1002,25,muted)
    elif visual=='context':
        centered(data['title'],673,48,orange,True)
        for n,label in enumerate(data['labels']):
            y=765+n*87;d.rounded_rectangle((135,y,835,y+65),radius=12,fill='#293b47');centered(label,y+13,31)
    else:
        centered(data['line1'],690,43,white,True);centered(data['line2'],770,43,white,True);centered(data['comparison'],893,52,orange,True);centered(data['note'],994,27,muted)
    d.text((90,1120),brief['source_label'],font=font(24),fill=muted)
    d.line((90,1175,880,1175),fill=stroke,width=3)
    width=790/total
    for n in range(total):d.rectangle((90+n*width,1173,90+(n+1)*width-9,1179),fill=orange if n<=index else stroke)
    im.save(path)

def render(brief,output,model):
    from piper import PiperVoice
    validate(brief);output.mkdir(parents=True,exist_ok=True)
    voice=PiperVoice.load(str(model));chunks=[];cursor=0;sample_rate=None;audio_parts=[];scenes=[]
    for scene_index,scene in enumerate(brief['scenes']):
        image=output/f'scene-{scene_index:02}.png';card(scene,scene_index,len(brief['scenes']),brief,image)
        start=cursor
        for chunk_index,text in enumerate(scene['chunks']):
            wav=output/f'voice-{scene_index:02}-{chunk_index:02}.wav'
            with wave.open(str(wav),'wb') as out:voice.synthesize_wav(text,out)
            with wave.open(str(wav),'rb') as stream:
                if stream.getsampwidth()!=2 or stream.getnchannels()!=1:raise ValueError('Expected mono PCM16 speech')
                if sample_rate is not None and stream.getframerate()!=sample_rate:raise ValueError('Inconsistent voice sample rate')
                sample_rate=stream.getframerate();samples=stream.readframes(stream.getnframes());duration=stream.getnframes()/sample_rate
            pause=.12;audio_parts.append(samples+b'\0\0'*round(pause*sample_rate))
            chunks.append({'start':cursor,'end':cursor+duration,'text':text});cursor+=duration+pause
        scenes.append({'file':image.name,'duration':cursor-start})
    if not 20<=cursor<=90:raise ValueError('Video must be between 20 and 90 seconds')
    with wave.open(str(output/'narration.wav'),'wb') as out:
        out.setnchannels(1);out.setsampwidth(2);out.setframerate(sample_rate);out.writeframes(b''.join(audio_parts))
    srt='\n\n'.join(f"{i+1}\n{timestamp(c['start'])} --> {timestamp(c['end'])}\n{c['text']}" for i,c in enumerate(chunks))+'\n'
    (output/'subtitles.srt').write_text(srt)
    header='[Script Info]\nScriptType: v4.00+\nPlayResX: 1080\nPlayResY: 1920\nWrapStyle: 0\n\n[V4+ Styles]\nFormat: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding\nStyle: Default,Arial,48,&H00FFFFFF,&H00FFFFFF,&HCC111820,&HCC111820,0,0,0,0,100,100,0,0,3,13,0,2,100,180,460,1\n\n[Events]\nFormat: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text\n'
    events=[]
    for c in chunks:
        text=c['text'].replace('\\','').replace('{','').replace('}','').replace('\n',' ')
        events.append(f"Dialogue: 0,{timestamp(c['start'],True)},{timestamp(c['end'],True)},Default,,0,0,0,,{text}")
    (output/'captions.ass').write_text(header+'\n'.join(events)+'\n')
    concat='ffconcat version 1.0\n'+''.join(f"file '{s['file']}'\nduration {s['duration']:.6f}\n" for s in scenes)+f"file '{scenes[-1]['file']}'\n"
    (output/'scenes.ffconcat').write_text(concat)
    vf="fps=30,zoompan=z='1.005+0.003*sin(on/100)':d=1:s=1080x1920:fps=30,subtitles=captions.ass,format=yuv420p"
    subprocess.run(['ffmpeg','-hide_banner','-loglevel','error','-y','-f','concat','-safe','0','-i','scenes.ffconcat','-i','narration.wav','-vf',vf,'-af','loudnorm=I=-16:TP=-1.5:LRA=9','-t',f'{cursor:.6f}','-c:v','libx264','-preset','veryfast','-crf','21','-c:a','aac','-b:a','160k','-ar','48000','-movflags','+faststart','video.mp4'],cwd=output,check=True,timeout=300)
    subprocess.run(['ffmpeg','-hide_banner','-loglevel','error','-y','-ss','1','-i','video.mp4','-frames:v','1','cover.jpg'],cwd=output,check=True,timeout=30)
    (output/'caption.txt').write_text(brief['caption']+'\n')
    digest=hashlib.sha256((output/'video.mp4').read_bytes()).hexdigest()
    manifest={'post_id':brief['post_id'],'account':brief['account'],'duration_seconds':round(cursor,2),'dimensions':[1080,1920],'fps':30,'voice_model':model.name,'synthetic_voice':True,'sources':brief['sources'],'article_url':brief['article_url'],'status':'ready_for_review','published':False,'sha256':digest,'caption_chunks':len(chunks),'music':None}
    (output/'manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2));print(json.dumps(manifest,ensure_ascii=False));return manifest

def enqueue(root,post,config):
    from runtime import read,write,now
    if post['status']!='publish':raise ValueError('Video drafts require a published article')
    state=Path(config['state_dir']).expanduser();state.mkdir(parents=True,exist_ok=True)
    queue_path=state/'queue.json';queue=read(queue_path,{'jobs':{}});key=str(post['id'])
    brief_path=root/'private'/f"video-brief-{post['id']}.json"
    output=Path(config['output_dir']).expanduser()/f"{post['id']}-{re.sub('[^a-zA-Z0-9_-]','-',post.get('slug','article'))}"
    if not brief_path.exists():
        queue['jobs'][key]={'post_id':post['id'],'status':'needs_brief','article_url':post['link'],'updated_at':now().isoformat()};write(queue_path,queue);return queue['jobs'][key]
    try:
        brief=validate(read(brief_path));digest=hashlib.sha256(brief_path.read_bytes()).hexdigest()
        if brief['post_id']!=post['id'] or brief.get('article_url')!=post['link']:raise ValueError('Brief belongs to a different article')
    except (ValueError,TypeError,KeyError):
        queue['jobs'][key]={'post_id':post['id'],'status':'failed','error':'InvalidBrief','updated_at':now().isoformat(),'published':False};write(queue_path,queue);return queue['jobs'][key]
    previous=queue['jobs'].get(key,{})
    if previous.get('status')=='ready_for_review' and previous.get('brief_sha256')==digest and (output/'video.mp4').is_file() and hashlib.sha256((output/'video.mp4').read_bytes()).hexdigest()==previous.get('video_sha256'):return previous
    job={'post_id':post['id'],'article_url':post['link'],'status':'rendering','brief_sha256':digest,'updated_at':now().isoformat(),'output':str(output),'published':False}
    queue['jobs'][key]=job;write(queue_path,queue)
    process=None
    try:
        with (state/f"render-{key}.log").open('a') as log:
            os.chmod(log.name,0o600)
            process=subprocess.Popen([str(Path(config['python']).expanduser()),str(Path(__file__).resolve()),'--brief',str(brief_path),'--output',str(output),'--model',str(Path(config['model']).expanduser())],stdout=log,stderr=log,start_new_session=True)
            process.wait(timeout=360)
        if process.returncode:raise RuntimeError('Local renderer failed')
        manifest=read(output/'manifest.json')
        if not manifest or manifest['post_id']!=post['id'] or manifest.get('published') is not False:raise RuntimeError('Render not verified')
        job.update(status='ready_for_review',duration_seconds=manifest['duration_seconds'],video_sha256=manifest['sha256'],finished_at=now().isoformat())
    except Exception as error:
        if process and process.poll() is None:
            os.killpg(process.pid,signal.SIGTERM)
            try:process.wait(timeout=10)
            except subprocess.TimeoutExpired:os.killpg(process.pid,signal.SIGKILL);process.wait()
        job.update(status='failed',error=type(error).__name__,finished_at=now().isoformat())
    write(queue_path,queue);return job

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--brief',type=Path,required=True);p.add_argument('--output',type=Path,required=True);p.add_argument('--model',type=Path,required=True);a=p.parse_args()
    render(json.loads(a.brief.read_text()),a.output.resolve(),a.model.resolve())
