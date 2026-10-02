# -*- coding: utf-8 -*-
"""ZF139 取证（二）：从 neoforge sources.jar 里读伤亡事件 / DamageContainer / 击退事件的源码。只读。"""
import io, re, zipfile, glob

SRC = r"E:\gradle-home\caches\modules-2\files-2.1\net.neoforged\neoforge\21.1.235\4566e557485e2cf5843d29a9c44795f5f731d36d\neoforge-21.1.235-sources.jar"
z = zipfile.ZipFile(SRC)
names = z.namelist()
OUT = []

WANT = [
    "net/neoforged/neoforge/event/entity/living/LivingDamageEvent.java",
    "net/neoforged/neoforge/event/entity/living/LivingIncomingDamageEvent.java",
    "net/neoforged/neoforge/common/damagesource/DamageContainer.java",
    "net/neoforged/neoforge/event/entity/living/LivingFallEvent.java",
]
for w in WANT:
    hit = [n for n in names if n.endswith(w)]
    OUT.append("=" * 20 + " " + w + " " + "=" * 20)
    if not hit:
        OUT.append("!! 找不到")
        continue
    s = z.read(hit[0]).decode("utf-8")
    # 只留 public/protected 成员与类头，去掉大段注释
    OUT.append(s)
    OUT.append("")

# 找 LivingEvent 里的 LivingTickEvent
hit = [n for n in names if n.endswith("event/entity/living/LivingEvent.java")]
if hit:
    s = z.read(hit[0]).decode("utf-8")
    i = s.find("LivingTickEvent")
    OUT.append("=" * 20 + " LivingEvent.LivingTickEvent " + "=" * 20)
    OUT.append(s[max(0, i - 400):i + 900])

txt = "\n".join(OUT)
io.open(r"E:\PotatoST\build\zftools\_zf139_src2.txt", "w", encoding="utf-8").write(txt + "\n")
print("ok -> _zf139_src2.txt (%d lines)" % len(OUT))
