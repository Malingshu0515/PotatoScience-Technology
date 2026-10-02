# -*- coding: utf-8 -*-
# _zf131_prov.py —— 把柴油发电机音频登进 build/用户素材/_来源凭据.json
import hashlib
import io
import json
import os
import sys

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
USERART = r"E:\PotatoST\build\用户素材"
PROV = os.path.join(USERART, "_来源凭据.json")
SRC = os.path.join(USERART, u"柴油发电机工作.mp3")
KEY = u"柴油发电机工作.mp3"

raw = io.open(PROV, encoding="utf-8").read()
prov = json.loads(raw)
before = len(prov)

if KEY in prov:
    print(u"  [幂等] 已在凭据里")
else:
    blob = open(SRC, "rb").read()
    prov[KEY] = {
        u"原名": u"柴油发电机工作.mp3",
        "sha1": hashlib.sha1(blob).hexdigest(),
        "bytes": len(blob),
        u"说明": (u"用户 ZF131 给的大型柴油发电机工作音频（44100 Hz / 单声道 / 10.81 s / RMS 0.1464）"
                 u"⇒ 用 build/zftools/MakeSfx.py 转成 "
                 u"sounds/diesel_generator_running.ogg"
                 u"（--loop --start 0.086 --end 10.550 --crossfade 300 --target-rms 0.10；"
                 u"成品单声道 10.16 s / RMS 0.0981 / 接缝样本差 0.0136 / 末→首电平差 3.13%）"),
    }
    io.open(PROV, "w", encoding="utf-8", newline="\n").write(
        json.dumps(prov, indent=2, ensure_ascii=False) + "\n")
    print(u"  [OK] 登记 %s  %d B  sha1 %s"
          % (KEY, len(blob), hashlib.sha1(blob).hexdigest()[:12]))

back = json.loads(io.open(PROV, encoding="utf-8").read())
print(u"\n  凭据条目 %d -> %d" % (before, len(back)))
ok = KEY in back
print(u"  %s 回读：在" % (u"[OK]" if ok else u"[!!]"))
print(u"  %s 老条目未丢" % (u"[OK]" if all(k in back for k in
      ("oil_bucket.jpg", "star_steel_helmet.png", "silver_wire.png")) else u"[!!]"))
sys.exit(0 if ok else 1)
