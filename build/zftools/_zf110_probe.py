import io, os, hashlib, zlib, struct
from PIL import Image

cands = [
 r"E:\PotatoST\build\用户素材\油桶.jpg",
 r"E:\PotatoST\build\用户素材\星璨钢头盔.png",
 r"E:\PotatoST\build\用户素材\碳酸锂.png",
 r"E:\PotatoST\build\用户素材\氯化钠.png",
 r"E:\硫_001.png",
]
out=[]
for p in cands:
    if not os.path.exists(p):
        out.append("MISSING "+p); continue
    b=open(p,'rb').read()
    sha1=hashlib.sha1(b).hexdigest()
    sig=b[:12]
    kind = "PNG" if b[:8]==b'\x89PNG\r\n\x1a\n' else ("JPEG" if b[:2]==b'\xff\xd8' else ("WEBP" if b[8:12]==b'WEBP' else "UNKNOWN"))
    try:
        im=Image.open(io.BytesIO(b))
        im.load()
        mode=im.mode
        size=im.size
        # alpha stats
        al=[]
        if mode in ('RGBA','LA','P'):
            rgba=im.convert('RGBA')
            a=rgba.getchannel('A')
            px=list(a.getdata())
            opaque=sum(1 for v in px if v==255)
            trans=sum(1 for v in px if v==0)
            semi=len(px)-opaque-trans
            al=[opaque,trans,semi]
            rgb=rgba.convert('RGB')
        else:
            rgb=im.convert('RGB')
        cols=rgb.getcolors(maxcolors=100000)
        ncol=len(cols) if cols else -1
        mean=tuple(round(sum(c[i]*n for n,c in cols)/sum(n for n,c in cols)) for i in range(3)) if cols else None
        out.append("="*70)
        out.append("PATH  %s"%p)
        out.append("  bytes=%d sha1=%s"%(len(b),sha1))
        out.append("  magic=%s  realformat=%s  mode=%s  size=%sx%s  colors=%d  meanRGB=%s"%(
            sig[:8].hex(),kind,mode,size[0],size[1],ncol,mean))
        if al: out.append("  alpha: opaque=%d transparent=%d semi=%d (total=%d)"%(al[0],al[1],al[2],sum(al)))
        else: out.append("  alpha: NONE (no alpha channel)")
    except Exception as e:
        out.append("="*70); out.append("PATH  %s"%p); out.append("  ERROR %r"%(e,))
rep="\n".join(out)
open(r"E:\PotatoST\build\zftools\_zf110_probe.txt","w",encoding="utf-8").write(rep)
print(rep)
