"""Public-source visual assets, isolated from private activity/session data."""
import hashlib,struct
from pathlib import Path
from urllib.parse import urlsplit

EVIDENCE_ROOT=Path.home()/'claude-activity-audit/videos/evidence'

def asset(data,brief,cover=False):
    path=Path(data.get('asset','')).expanduser().resolve()
    if not path.is_relative_to(EVIDENCE_ROOT.resolve()) or not path.is_file():
        raise ValueError('Visual asset must be inside the public evidence directory')
    if path.stat().st_size>8*1024*1024:raise ValueError('Visual asset too large')
    raw=path.read_bytes()
    if len(raw)>8*1024*1024 or raw[:8]!=b'\x89PNG\r\n\x1a\n' or len(raw)<33:
        raise ValueError('Use a bounded PNG visual asset')
    width,height=struct.unpack('>II',raw[16:24])
    if width<240 or height<80 or width*height>16_000_000:
        raise ValueError('Visual asset dimensions are unsuitable')
    if hashlib.sha256(raw).hexdigest()!=data.get('sha256'):
        raise ValueError('Visual asset changed after review')
    source=data.get('source_url','');url=urlsplit(source)
    if url.scheme!='https' or not url.hostname or url.username or url.password:
        raise ValueError('Public visual source required')
    if cover:
        if url.hostname!=urlsplit(brief.get('article_url','')).hostname:
            raise ValueError('Article cover must come from the article website')
    elif source not in [*brief.get('sources',[]),brief.get('article_url')]:
        raise ValueError('Visual source must be cited in the article brief')
    if not isinstance(data.get('credit'),str) or not 1<=len(data['credit'])<=65:
        raise ValueError('Short visible visual credit required')
    return path

def cache_cover(media,state,post_id):
    """Fetch only the already-published article's own featured image."""
    from urllib.request import Request,urlopen
    from PIL import Image
    import io
    url=media.get('source_url','');parts=urlsplit(url)
    if parts.scheme!='https' or parts.hostname!='datogedon.com' or not parts.path.startswith('/wp-content/uploads/'):
        raise ValueError('Expected the published Datogedon cover')
    with urlopen(Request(url,headers={'User-Agent':'Mozilla/5.0 DatogedonEditorial'}),timeout=30) as response:
        if urlsplit(response.geturl()).hostname!=parts.hostname:raise ValueError('Unexpected cover redirect')
        raw=response.read(8*1024*1024+1)
    if len(raw)>8*1024*1024:raise ValueError('Article cover too large')
    # Pillow lives in the rendering environment, not necessarily the scheduler.
    with Image.open(io.BytesIO(raw)) as image:
        if image.width*image.height>16_000_000:raise ValueError('Article cover too large')
        target=Path(state)/'evidence'/f'{post_id}-article-cover.png';target.parent.mkdir(parents=True,exist_ok=True)
        image.convert('RGB').save(target)
    return {'asset':str(target),'sha256':hashlib.sha256(target.read_bytes()).hexdigest(),
            'source_url':url,'credit':'Datogedon','kind':'article_cover'}

def vertical_cover(brief,target):
    """Keep the full landscape cover inside a vertical, branded composition."""
    from PIL import Image,ImageDraw,ImageFont,ImageOps,ImageFilter,ImageEnhance
    source=asset(brief['article_cover'],brief,cover=True)
    with Image.open(source) as image:
        image=image.convert('RGB');background=ImageEnhance.Brightness(ImageOps.fit(image,(1080,1920)).convert('L').filter(ImageFilter.GaussianBlur(48))).enhance(.20).convert('RGB')
        foreground=ImageOps.contain(image,(920,560))
        background.paste(foreground,((1080-foreground.width)//2,810+(560-foreground.height)//2))
    draw=ImageDraw.Draw(background)
    regular='/System/Library/Fonts/Supplemental/Arial.ttf';bold='/System/Library/Fonts/Supplemental/Arial Bold.ttf'
    draw.text((80,390),'DATOGEDON',font=ImageFont.truetype(bold,38),fill='#fafafa')
    draw.text((80,450),brief['topic_label'],font=ImageFont.truetype(regular,28),fill='#bdbdbd')
    title=brief.get('cover_title') or brief['scenes'][0]['headline'];size=64
    while True:
        font=ImageFont.truetype(bold,size);lines=[]
        for word in title.split():
            if lines and draw.textlength(lines[-1]+' '+word,font=font)<=920:lines[-1]+=' '+word
            else:lines.append(word)
        if len(lines)<=3 and all(draw.textlength(line,font=font)<=920 for line in lines):break
        size-=2
        if size<32:raise ValueError('Cover headline too long')
    for i,line in enumerate(lines):draw.text((80,575+i*(size+12)),line,font=font,fill='#fafafa')
    draw.text((80,1430),brief.get('series_title','Datogedon'),font=ImageFont.truetype(regular,30),fill='#bdbdbd')
    background.save(target,quality=94)
