"""Reusable logo bumpers and measured, voice-only mobile mastering."""
import hashlib,json,math,re,subprocess
from pathlib import Path
PREPROCESS='highpass=f=70,acompressor=threshold=0.125:ratio=1.8:attack=15:release=130:makeup=1:knee=2.828'
TARGET={'integrated_lufs':-16.0,'true_peak_dbtp':-1.5,'loudness_range_lu':7.0}

def branding_spec(config):
    if not config or not config.get('enabled'):return {'enabled':False}
    path=Path(config['logo_path']).expanduser()
    if not path.is_file():raise ValueError('Brand logo is unavailable; copy it outside protected Downloads')
    if float(config.get('intro_seconds',1))!=1:raise ValueError('The intro must be exactly one second')
    outro=float(config.get('outro_seconds',3))
    if not 1<=outro<=6:raise ValueError('Outro must last 1–6 seconds over the existing final narration')
    return {**config,'logo_path':str(path),'logo_sha256':hashlib.sha256(path.read_bytes()).hexdigest(),'intro_seconds':1.0,'outro_seconds':outro}

def brand_card(config,brief,path,outro=False):
    from PIL import Image,ImageDraw,ImageFont,ImageOps
    image=Image.new('RGB',(1080,1920),'#111820');draw=ImageDraw.Draw(image)
    draw.polygon([(730,0),(1080,0),(1080,1920),(940,1920)],fill='#19252e')
    draw.rounded_rectangle((150,330,810,990),radius=34,fill='white')
    logo=Image.open(config['logo_path']).convert('RGBA');logo=ImageOps.contain(logo,(610,610),Image.Resampling.LANCZOS)
    image.paste(logo,(480-logo.width//2,660-logo.height//2),logo)
    font_path='/System/Library/Fonts/Supplemental/Arial Bold.ttf'
    text='Comparte' if outro else brief.get('series_title',config.get('intro_title','Noticias de tecnología'))
    font=ImageFont.truetype(font_path,108 if outro else 76)
    lines=[]
    for word in text.split():
        if lines and draw.textlength(lines[-1]+' '+word,font=font)<=790:lines[-1]+=' '+word
        else:lines.append(word)
    if len(lines)>2 or any(draw.textlength(line,font=font)>790 for line in lines):raise ValueError('Brand title overflows safe area')
    for n,line in enumerate(lines):draw.text((480-draw.textlength(line,font=font)/2,1090+n*94),line,font=font,fill='#fff8ed')
    draw.line((300,1028,660,1028),fill='#ff966f',width=5)
    image.save(path)

def outro_timeline(scenes,config):
    timeline=[dict(scene) for scene in scenes]
    if config.get('enabled'):
        remaining=min(config['outro_seconds'],sum(s['duration'] for s in timeline if s['kind']=='body'));seconds=remaining
        while remaining>1e-9 and timeline and timeline[-1]['kind']=='body':
            last=timeline.pop();take=min(remaining,last['duration']);remaining-=take
            if last['duration']-take>1e-9:timeline.append({**last,'duration':last['duration']-take})
        timeline.append({'file':'outro.png','duration':seconds,'kind':'outro'})
    cursor=0;frames=0
    for scene in timeline:
        cursor+=scene['duration'];end=round(cursor*30)
        scene['start_frame']=frames;scene['frame_count']=end-frames;scene['start']=frames/30;scene['video_duration']=scene['frame_count']/30
        frames=end
    return timeline

def parse_measurements(stderr):
    blocks=re.findall(r'\{\s*"input_i".*?\}',stderr,re.S)
    if not blocks:raise RuntimeError('FFmpeg loudness measurements missing')
    data=json.loads(blocks[-1]);result={k:float(data[k]) for k in ['input_i','input_tp','input_lra','input_thresh','target_offset']}
    if not all(math.isfinite(v) for v in result.values()):raise RuntimeError('Invalid or silent audio measurement')
    return result

def measure(path,preprocess=''):
    chain=(preprocess+',' if preprocess else '')+'loudnorm=I=-16:TP=-1.5:LRA=7:print_format=json'
    result=subprocess.run(['ffmpeg','-hide_banner','-nostats','-i',str(path),'-af',chain,'-f','null','-'],capture_output=True,text=True,check=True,timeout=60)
    return parse_measurements(result.stderr)

def master(source,target):
    measured=measure(source,PREPROCESS)
    chain=PREPROCESS+(',loudnorm=I=-16:TP=-1.5:LRA=7:measured_I={input_i}:measured_TP={input_tp}:measured_LRA={input_lra}:measured_thresh={input_thresh}:offset={target_offset}:linear=true:print_format=json'.format(**measured))
    subprocess.run(['ffmpeg','-hide_banner','-loglevel','error','-y','-i',str(source),'-af',chain,'-ar','48000','-ac','1','-c:a','pcm_s16le',str(target)],capture_output=True,check=True,timeout=60)
    return {'target':TARGET,'processing':{'high_pass_hz':70,'compressor_ratio':1.8,'two_pass_normalization':True,'music':False},'preprocessed_input':measured,'mastered_wav':measure(target)}

def verify_mastering(report,encoded):
    encoded_measurement=measure(encoded);report['encoded_aac']=encoded_measurement
    if abs(encoded_measurement['input_i']-TARGET['integrated_lufs'])>1.0:raise RuntimeError('Encoded voice is outside the loudness target')
    if encoded_measurement['input_tp']>-1.0:raise RuntimeError('Encoded audio needs more peak headroom')
    return report


def verify_frames(video,expected_frames):
    result=subprocess.run(['ffprobe','-v','error','-select_streams','v:0','-show_entries','stream=nb_frames,width,height,r_frame_rate,duration','-of','json',str(video)],capture_output=True,text=True,check=True,timeout=30)
    stream=json.loads(result.stdout)['streams'][0]
    if int(stream.get('nb_frames',0))!=expected_frames or stream.get('width')!=1080 or stream.get('height')!=1920 or stream.get('r_frame_rate')!='30/1':raise RuntimeError('Encoded video is truncated or has an unexpected format')
    return {'frames':int(stream['nb_frames']),'duration_seconds':float(stream['duration']),'fps':stream['r_frame_rate']}
