"""Landscape explanatory guides with original diagrams and uninterrupted narration."""
import argparse,hashlib,json,math,subprocess,wave
from pathlib import Path
from video_finish import master,verify_mastering,VOICE_ENCODE_FILTER
W,H,FPS=1920,1080,30
WHITE='#fafafa';MUTED='#bdbdbd';PANEL='#242424';BG='#111111';ACCENT='#ff966f'

def expected_route(rule,enabled,paused=False):
    if rule not in ['on','off','default']:raise ValueError('Unsupported website rule')
    if paused:return 'Sin VPN'
    return 'VPN' if rule=='on' or rule=='default' and enabled else 'Sin VPN'

def canvas(brief,scene,index,local_time,logo):
    from PIL import Image,ImageDraw,ImageFont
    image=Image.new('RGB',(W,H),BG);d=ImageDraw.Draw(image)
    d.polygon([(1500,0),(1920,0),(1920,1080),(1800,1080)],fill='#191919')
    regular='/System/Library/Fonts/Supplemental/Arial.ttf';bold='/System/Library/Fonts/Supplemental/Arial Bold.ttf'
    font=lambda size,b=False:ImageFont.truetype(bold if b else regular,size)
    def text(value,x,y,size=42,color=WHITE,b=False):d.text((x,y),value,font=font(size,b),fill=color)
    def wrapped(value,x,y,width,size=40,color=WHITE,b=False):
        lines=[]
        for word in value.split():
            if lines and d.textlength(lines[-1]+' '+word,font=font(size,b))<=width:lines[-1]+=' '+word
            else:lines.append(word)
        for n,line in enumerate(lines):text(line,x,y+n*(size+12),size,color,b)
    def box(x,y,width,height,title,body='',active=False):
        d.rounded_rectangle((x,y,x+width,y+height),radius=24,fill=PANEL,outline=WHITE if active else '#505050',width=3 if active else 2)
        wrapped(title,x+26,y+24,width-52,39,b=True)
        if body:wrapped(body,x+26,y+92,width-52,33,MUTED)
    def arrow(x1,y,x2,active=False):
        d.line((x1,y,x2,y),fill=WHITE if active else '#707070',width=5);d.polygon([(x2,y),(x2-18,y-13),(x2-18,y+13)],fill=WHITE)
        phase=(local_time%2)/2;dot=x1+(x2-x1)*phase;d.ellipse((dot-7,y-7,dot+7,y+7),fill=WHITE)
    text('DATOGEDON  /  GUÍAS PRÁCTICAS',86,48,25,MUTED,True)
    image.paste(logo,(1760,34),logo)
    wrapped(scene['headline'],86,110,1550,68,b=True)
    text(scene['subtitle'],90,208,35,MUTED)
    pulse=int(local_time//3)
    visual=scene['visual']
    if visual=='routing':
        box(110,420,380,220,'Firefox','Una regla para cada sitio',True)
        arrow(510,480,930,True);arrow(510,650,930)
        box(960,370,760,180,'Sitio A · Siempre activada','Ruta esperada: VPN',pulse%2==0)
        box(960,590,760,180,'Sitio B · Siempre desactivada','Ruta esperada: sin VPN',pulse%2==1)
        text('El interruptor general no sustituye una regla específica.',115,860,39)
    elif visual=='checklist':
        for n,(title,body) in enumerate([('1 · Escritorio','Firefox 161 o posterior'),('2 · Cuenta Mozilla','Sesión iniciada'),('3 · Disponibilidad','Región y despliegue gradual')]):box(95+n*590,410,555,280,title,body,pulse%3==n)
        text('La disponibilidad se comprueba en la ayuda de Mozilla.',100,800,38,MUTED)
    elif visual=='scope':
        box(100,375,420,175,'Firefox','Tráfico del navegador',pulse%2==0);arrow(540,460,1020,True);box(1050,375,680,175,'VPN integrada','Ruta del navegador')
        box(100,640,420,175,'Otra aplicación','Conexión independiente',pulse%2==1);arrow(540,725,1020);box(1050,640,680,175,'No queda cubierta','por activar la VPN de Firefox')
    elif visual=='steps':
        labels=['Menú','Ajustes','Privacidad y seguridad','VPN','Reglas']
        for n,label in enumerate(labels):
            x=95+n*350;box(x,350,320,120,label,active=pulse%5==n)
            if n<4:arrow(x+323,410,x+344)
        box(100,570,790,235,'1 · Añade una web','La regla corresponde al sitio completo',pulse%2==0)
        box(940,570,790,235,'2 · Elige su regla','Siempre activada / siempre desactivada',pulse%2==1)
        text('En inglés: Manage VPN rules → Set rule',105,870,36,MUTED)
    elif visual=='matrix':
        columns=[130,650,1200]
        for x,label in zip(columns,['Interruptor general','Regla del sitio','Ruta esperada']):text(label,x,325,37,MUTED,True)
        rows=[(False,'on'),(False,'off'),(False,'default'),(True,'on'),(True,'off'),(True,'default')]
        names={'on':'Siempre activada','off':'Siempre desactivada','default':'Sin regla'}
        for n,(enabled,rule) in enumerate(rows):
            y=398+n*76
            if pulse%6==n:d.rounded_rectangle((95,y-10,1740,y+60),radius=12,fill='#303030')
            for x,value in zip(columns,['Encendido' if enabled else 'Apagado',names[rule],expected_route(rule,enabled)]):text(value,x,y,36,b=n==pulse%6)
        text('Los servicios esenciales de Mozilla tienen excepciones de conexión.',130,890,28,MUTED)
    elif visual=='verify':
        for n,(title,body) in enumerate([('Sitio','Dirección que estás visitando'),('Regla','Preferencia que guardaste'),('Panel','Estado que se aplica ahora')]):box(95+n*590,390,555,270,title,body,pulse%3==n)
        box(100,760,1630,135,'Cambia una sola variable y vuelve a comprobar.','',True)
    elif visual=='paused':
        box(105,345,1630,165,'Si eliges continuar sin VPN…','Las reglas quedan pausadas, incluidas las de siempre activada.',True)
        for n,label in enumerate(['Sitio A','Sitio B','Sitio C']):
            x=105+n*555;box(x,585,520,180,label,expected_route('on',True,True),pulse%3==n)
        text('Reactivar / reiniciar → comprobar de nuevo el panel',110,850,38,ACCENT,True)
    elif visual=='diagnose':
        for n,(title,body) in enumerate([('Versión y cuenta','Actualización e inicio de sesión'),('Región y despliegue','Revisar disponibilidad actual'),('Equipo administrado','Revisar políticas aplicadas')]):box(95+n*590,390,555,260,title,body,pulse%3==n)
        text('about:policies',110,765,62,b=True);text('Identifica la causa antes de cambiar opciones.',110,850,38,MUTED)
    else:
        for n,label in enumerate(['Sitio correcto','Regla visible','Estado sin pausa']):box(110,350+n*160,1600,125,label,active=pulse%3==n)
    text('Esquemas: Datogedon · Fuente: documentación de Mozilla',90,975,25,MUTED)
    text(f'{index+1:02d} / {len(brief["scenes"]):02d}',1690,975,25,MUTED)
    return image

def render(brief,output,branding):
    from PIL import Image,ImageDraw,ImageFont,ImageOps
    publication=output/'youtube-publication.json'
    if publication.exists() and json.loads(publication.read_text()).get('status')=='published':raise ValueError('Published guide master is immutable; use a separate revision directory')
    data=json.loads((output/'segments.json').read_text());duration=data['duration'];segments=data['segments']
    if not 120<=duration<=900:raise ValueError('An extended guide must contain 2–15 minutes of real narration')
    with wave.open(str(output/'narration.wav'),'rb') as stream:
        if abs(stream.getnframes()/stream.getframerate()-duration)>.01:raise ValueError('Narration timeline mismatch')
    logo=Image.open(branding['logo_path']).convert('RGBA');logo=ImageOps.contain(logo,(100,100),Image.Resampling.LANCZOS)
    audio=master(output/'narration.wav',output/'narration-mastered.wav')
    count=round(duration*FPS)
    command=['ffmpeg','-v','error','-y','-f','rawvideo','-pixel_format','rgb24','-video_size',f'{W}x{H}','-framerate',str(FPS),'-i','pipe:0','-i','narration-mastered.wav','-frames:v',str(count),'-c:v','libx264','-preset','veryfast','-crf','21','-pix_fmt','yuv420p','-af',VOICE_ENCODE_FILTER,'-c:a','aac','-b:a','160k','-ar','48000','-movflags','+faststart','video.mp4']
    process=subprocess.Popen(command,cwd=output,stdin=subprocess.PIPE,stderr=subprocess.PIPE)
    scene_starts={};scene_ends={}
    for segment in segments:
        scene_starts.setdefault(segment['scene_index'],segment['start']);scene_ends[segment['scene_index']]=segment['start']+segment['duration']+.15
    ordered=list(scene_starts);scene_index=0;intro_at=min(6.5,segments[0]['duration']*.4)
    try:
        previous_key=None;pixels=None
        for frame_index in range(count):
            t=frame_index/FPS
            while scene_index+1<len(ordered) and t>=scene_starts[scene_index+1]:scene_index+=1
            local=t-scene_starts[scene_index]
            key=(scene_index,round(local*10))
            if key!=previous_key:
                image=canvas(brief,brief['scenes'][scene_index],scene_index,local,logo)
                if intro_at<=t<intro_at+1 or t>=duration-4:
                    d=ImageDraw.Draw(image);d.rounded_rectangle((460,310,1460,800),radius=34,fill=BG,outline='#707070',width=2)
                    big=ImageOps.contain(Image.open(branding['logo_path']).convert('RGBA'),(270,270),Image.Resampling.LANCZOS);image.paste(big,(825,345),big)
                    font=ImageFont.truetype('/System/Library/Fonts/Supplemental/Arial Bold.ttf',54)
                    label='Comparte · @datogedon' if t>=duration-4 else 'Guías prácticas'
                    d.text(((W-d.textlength(label,font=font))/2,665),label,font=font,fill=WHITE)
                pixels=image.tobytes();previous_key=key
            process.stdin.write(pixels)
        process.stdin.close();process.stdin=None;_,error=process.communicate(timeout=120)
        if process.returncode:raise RuntimeError(error.decode()[-1000:])
    except BaseException:process.kill();process.wait();raise
    audio=verify_mastering(audio,output/'video.mp4')
    result=subprocess.run(['ffprobe','-v','error','-select_streams','v:0','-show_entries','stream=nb_frames,width,height,r_frame_rate,duration','-of','json',str(output/'video.mp4')],check=True,capture_output=True,text=True)
    stream=json.loads(result.stdout)['streams'][0]
    if int(stream['nb_frames'])!=count or (stream['width'],stream['height'])!=(W,H):raise ValueError('Extended video format mismatch')
    chapters=[]
    for index,start in scene_starts.items():
        seconds=int(start);chapters.append(f'{seconds//60:02d}:{seconds%60:02d} '+brief['scenes'][index]['headline'])
    description='Firefox 161 permite definir qué webs usan la VPN integrada. Esta guía explica las reglas, su prioridad frente al interruptor general y qué comprobar cuando la conexión falla o no aparece la función.\n\nNarración con voz sintética. Diagramas originales basados en documentación de Mozilla; las rutas muestran el resultado esperado de cada configuración.\n\nArtículo: '+brief['article_url']+'\n\nCapítulos\n'+'\n'.join(chapters)+'\n\nFuentes oficiales\n'+'\n'.join(brief['sources'])+'\n\n#Firefox #VPN #Privacidad #Tecnologia\n'
    (output/'description.txt').write_text(description);(output/'chapters.txt').write_text('\n'.join(chapters)+'\n')
    thumb=Image.new('RGB',(1280,720),BG);d=ImageDraw.Draw(thumb)
    bold='/System/Library/Fonts/Supplemental/Arial Bold.ttf'
    for label,y,size,color in [('FIREFOX',70,54,MUTED),('VPN POR',200,112,WHITE),('SITIO',325,112,WHITE),('Reglas y excepciones',510,42,MUTED)]:d.text((70,y),label,font=ImageFont.truetype(bold,size),fill=color)
    for y,label in [(240,'Siempre ON'),(420,'Siempre OFF')]:
        d.rounded_rectangle((850,y,1220,y+125),radius=20,fill=PANEL,outline='#707070',width=2);d.text((875,y+39),label,font=ImageFont.truetype(bold,40),fill=WHITE)
    thumb.paste(logo,(1110,52),logo);thumb.save(output/'cover.jpg',quality=91,optimize=True)
    manifest={'post_id':brief['post_id'],'format':'extended','title':brief['title'],'account':'@datogedon','dimensions':[W,H],'fps':FPS,'duration_seconds':duration,'frames':count,'status':'ready_for_review','published':False,'sha256':hashlib.sha256((output/'video.mp4').read_bytes()).hexdigest(),'narration_continuous':True,'music':False,'visuals':'original_explanatory_diagrams','live_network_test':False,'captions':'transcript supplied; use native automatic synchronization','sources':brief['sources'],'chapters':chapters,'audio_mastering':audio['encoded_aac']}
    (output/'manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2));(output/'audio-mastering.json').write_text(json.dumps(audio,indent=2));print(json.dumps(manifest,ensure_ascii=False))
if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--brief',type=Path,required=True);p.add_argument('--output',type=Path,required=True);p.add_argument('--branding',type=Path,required=True);a=p.parse_args();render(json.loads(a.brief.read_text()),a.output,json.loads(a.branding.read_text()))
