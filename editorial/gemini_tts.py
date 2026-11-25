"""Gemini speech with private keys, content cache and quota-only paid fallback."""
import base64,hashlib,io,json,os,re,tempfile,time,wave
from pathlib import Path
from urllib.error import HTTPError,URLError
from urllib.request import Request,build_opener,HTTPRedirectHandler
ENDPOINT='https://generativelanguage.googleapis.com/v1beta/interactions'
DEFAULT_MODEL='gemini-3.8-flash-tts'
DEFAULT_VOICE='Algieba'
DEFAULT_STYLE='Español latinoamericano, acento mexicano neutro. Voz cálida, cercana y segura de divulgador tecnológico. Ritmo conversacional ágil, pausas naturales. Sin tono robótico, de anuncio ni dramatización. Lee únicamente el texto indicado.'
class SpeechError(RuntimeError):
    def __init__(self,status,code='REQUEST_FAILED',retry_after=None):
        self.status=status;self.code=code;self.retry_after=retry_after
        super().__init__(f'Gemini speech failed: HTTP {status}, {code}')
class NoRedirect(HTTPRedirectHandler):
    def redirect_request(self,*args,**kwargs):return None

def credentials(path):
    path=Path(path).expanduser()
    if path.stat().st_mode&0o077:raise SpeechError(0,'PRIVATE_ENV_PERMISSIONS')
    values={}
    for line in path.read_text().splitlines():
        line=line.strip().removeprefix('export ')
        if line and not line.startswith('#') and '=' in line:
            key,value=line.split('=',1);values[key.strip()]=value.strip().strip('\"\'')
    if not values.get('PUBLIC_APIKEY'):raise SpeechError(0,'PRIMARY_KEY_MISSING')
    return values

def atomic(path,data):
    path=Path(path);path.parent.mkdir(parents=True,exist_ok=True,mode=0o700)
    fd,temp=tempfile.mkstemp(dir=path.parent)
    try:
        os.fchmod(fd,0o600)
        with os.fdopen(fd,'wb') as out:out.write(data)
        os.replace(temp,path)
    finally:
        if os.path.exists(temp):os.unlink(temp)

def request(payload,key):
    req=Request(ENDPOINT,data=json.dumps(payload,ensure_ascii=False).encode(),headers={'Content-Type':'application/json','x-goog-api-key':key,'User-Agent':'DatogedonSpeech/2.0'})
    try:
        with build_opener(NoRedirect).open(req,timeout=100) as response:return json.load(response)
    except HTTPError as error:
        retry=None
        try:
            problem=json.load(error).get('error',{})
            for detail in problem.get('details',[]):
                if detail.get('@type','').endswith('RetryInfo'):
                    value=str(detail.get('retryDelay',''))
                    if re.fullmatch(r'[0-9.]+s',value):retry=float(value[:-1])
        except (ValueError,TypeError):pass
        # Never propagate the provider body: it may include credential or project data.
        raise SpeechError(error.code,'QUOTA_EXHAUSTED' if error.code==429 else 'REQUEST_REJECTED',retry) from None
    except (URLError,TimeoutError,ValueError):
        # Outcome may be uncertain: do not duplicate potentially billable generation.
        raise SpeechError(0,'TRANSPORT_OR_RESPONSE_ERROR') from None

def decode_audio(response):
    outputs=[]
    for step in response.get('steps',[]):
        if step.get('type')=='model_output':
            outputs.extend(c for c in step.get('content',[]) if c.get('type')=='audio')
    if not outputs:raise SpeechError(200,'NO_AUDIO')
    try:
        data=base64.b64decode(outputs[-1]['data'],validate=True)
        with wave.open(io.BytesIO(data),'rb') as audio:
            if audio.getnchannels()!=1 or audio.getsampwidth()!=2 or audio.getnframes()==0:raise ValueError()
    except (KeyError,ValueError,wave.Error,EOFError):raise SpeechError(200,'INVALID_WAV') from None
    return data

class GeminiSpeech:
    def __init__(self,config):
        self.config=config;self.model=config.get('model',DEFAULT_MODEL);self.voice=config.get('voice',DEFAULT_VOICE);self.style=config.get('style',DEFAULT_STYLE)
        if self.model not in ['gemini-3.8-flash-tts','gemini-3.8-flash-lite-tts']:raise SpeechError(0,'UNSUPPORTED_TTS_MODEL')
        self.keys=credentials(config['env_file']);self.cache=Path(config['cache_dir']).expanduser();self.cache.mkdir(parents=True,exist_ok=True,mode=0o700)
        self.primary_exhausted=False;self.calls=[]
    def synthesize(self,text,target):
        payload={'model':self.model,'input':[{'type':'user_input','content':[{'type':'text','text':text,'annotations':[{'type':'speech_metadata','style':self.style}]}]}],'response_format':{'type':'audio','mime_type':'audio/wav'},'generation_config':{'speech_config':[{'voice':self.voice}]}}
        fingerprint=hashlib.sha256(json.dumps(payload,sort_keys=True,ensure_ascii=False).encode()).hexdigest();cached=self.cache/(fingerprint+'.wav');meta=self.cache/(fingerprint+'.json')
        if cached.is_file() and meta.is_file():
            info=json.loads(meta.read_text());data=cached.read_bytes()
            if hashlib.sha256(data).hexdigest()==info.get('sha256'):
                atomic(target,data);self.calls.append({'cache_hit':True,'credential_slot':info['credential_slot']});return
        def generate(slot):
            key=self.keys.get(slot)
            if not key:raise SpeechError(0,'PAID_KEY_MISSING' if slot=='APIKEY' else 'PRIMARY_KEY_MISSING')
            return request(payload,key)
        slot='APIKEY' if self.primary_exhausted else 'PUBLIC_APIKEY'
        try:response=generate(slot)
        except SpeechError as error:
            if slot!='PUBLIC_APIKEY' or error.status!=429:raise
            if error.retry_after is not None and 0<error.retry_after<=20:
                time.sleep(error.retry_after)
                try:response=generate(slot)
                except SpeechError as second:
                    if second.status!=429:raise
                    response=None
            else:response=None
            if response is None:
                if self.keys.get('APIKEY')==self.keys['PUBLIC_APIKEY']:raise SpeechError(429,'FALLBACK_KEY_NOT_DISTINCT') from None
                self.primary_exhausted=True;slot='APIKEY';response=generate(slot)
        data=decode_audio(response);atomic(target,data);atomic(cached,data)
        info={'model':self.model,'voice':self.voice,'credential_slot':slot,'sha256':hashlib.sha256(data).hexdigest(),'usage':{k:v for k,v in response.get('usage',{}).items() if isinstance(v,(int,float))}}
        atomic(meta,json.dumps(info,ensure_ascii=False,indent=2).encode());self.calls.append({'cache_hit':False,**info})
    def report(self):
        return {'provider':'gemini','model':self.model,'voice':self.voice,'requests':sum(not c['cache_hit'] for c in self.calls),'cache_hits':sum(c['cache_hit'] for c in self.calls),'paid_fallback_used':any(not c['cache_hit'] and c['credential_slot']=='APIKEY' for c in self.calls),'credentials_used':sorted({c['credential_slot'] for c in self.calls if not c['cache_hit']}),'calls':self.calls}
