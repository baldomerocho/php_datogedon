"""Short, staggered entrances and data emphasis; settled cards remain readable."""
import math,subprocess

PROFILE={'name':'editorial-entrances-v1','fps':30,'settled_after_seconds':1.05,
         'title_seconds':0.32,'panel_seconds':0.38,'music':False}

def progress(time,delay,duration):
    if duration<=0:raise ValueError('Animation duration must be positive')
    value=max(0.0,min(1.0,(time-delay)/duration))
    return 1-(1-value)**3

def layers(image,visual,brand=False):
    from PIL import Image,ImageDraw
    background=Image.new('RGB',image.size,'#111820');draw=ImageDraw.Draw(background)
    draw.polygon([(730,0),(1080,0),(1080,1920),(940,1920)],fill='#19252e')
    base=image.copy();items=[]
    def take(box,delay=0,duration=.32,shift=28,pulse=False,rounded=0):
        crop=image.crop(box).convert('RGBA')
        if rounded:
            mask=Image.new('L',crop.size);ImageDraw.Draw(mask).rounded_rectangle((0,0,crop.width-1,crop.height-1),radius=rounded,fill=255);crop.putalpha(mask)
        base.paste(background.crop(box),box[:2]);items.append((crop,box[:2],delay,duration,shift,pulse))
    if brand:
        take((150,330,811,991),duration=.24,shift=24,rounded=34)
        take((70,1020,890,1320),delay=.10,duration=.28,shift=22)
        return base,items
    take((80,250,890,560),duration=.32,shift=30)
    take((90,620,881,1071),delay=.08,duration=.38,shift=36,rounded=30)
    panel,position,delay,duration,shift,pulse=items.pop()
    boxes=[]
    if visual=='metric':boxes=[((110,670,860,831),.22,True)]
    elif visual=='comparison':boxes=[((125,645,860,810),.18,False),((125,840,860,1005),.34,False)]
    elif visual=='parallel':boxes=[((135+c*178,755,281+c*178,923),.18+c*.11,False) for c in range(4)]
    elif visual=='context':boxes=[((130,760+n*87,840,835+n*87),.16+n*.12,False) for n in range(3)]
    elif visual=='question':boxes=[((110,875,860,975),.24,True)]
    accents=[]
    for box,lag,pop in boxes:
        accent=image.crop(box).convert('RGBA')
        local=(box[0]-90,box[1]-620,box[2]-90,box[3]-620)
        ImageDraw.Draw(panel).rectangle(local,fill='#202e38')
        accents.append((accent,box[:2],lag,.38,18,pop))
    items.append((panel,position,delay,duration,shift,pulse));items.extend(accents)
    return base,items

def frame(base,items,time):
    from PIL import Image
    result=base.copy()
    for tile,(x,y),delay,duration,shift,pulse in items:
        p=progress(time,delay,duration)
        if p<=0:continue
        opacity=min(1,max(0,(time-delay)/.16))
        scale=1.0
        if pulse:
            raw=max(0,min(1,(time-delay)/.65))
            scale=.94+.06*progress(time,delay,.30)+.035*math.sin(math.pi*raw)
        if abs(scale-1)>.001:
            resized=tile.resize((round(tile.width*scale),round(tile.height*scale)),Image.Resampling.BICUBIC)
        else:resized=tile
        if opacity<1:
            resized=resized.copy();resized.putalpha(resized.getchannel('A').point(lambda a:round(a*opacity)))
        position=(round(x+(tile.width-resized.width)/2),round(y+shift*(1-p)+(tile.height-resized.height)/2))
        result.paste(resized,position,resized)
    return result

def encode(output,scenes,visuals):
    from PIL import Image
    count=sum(s['frame_count'] for s in scenes)
    command=['ffmpeg','-hide_banner','-loglevel','error','-y','-f','rawvideo','-pixel_format','rgb24',
             '-video_size','1080x1920','-framerate','30','-i','pipe:0','-i','narration-mastered.wav',
             '-vf','subtitles=captions.ass,format=yuv420p','-frames:v',str(count),
             '-c:v','libx264','-preset','veryfast','-crf','21','-c:a','aac','-b:a','160k',
             '-ar','48000','-movflags','+faststart','video.mp4']
    process=subprocess.Popen(command,cwd=output,stdin=subprocess.PIPE,stderr=subprocess.PIPE)
    try:
        for scene in scenes:
            with Image.open(output/scene['file']) as source:image=source.convert('RGB')
            base,items=layers(image,visuals.get(scene['file']),scene['kind'] in ('intro','outro'))
            settled=image.tobytes()
            for index in range(scene['frame_count']):
                time=index/30
                pixels=frame(base,items,time).tobytes() if time<PROFILE['settled_after_seconds'] else settled
                process.stdin.write(pixels)
        process.stdin.close();process.stdin=None
        _,error=process.communicate(timeout=120)
        if process.returncode:raise RuntimeError('Animated video encoding failed: '+error.decode()[-1500:])
    except BaseException:
        process.kill();process.wait();raise
    return PROFILE
