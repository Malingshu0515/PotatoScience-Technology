# -*- coding: utf-8 -*-
"""ZF139 取证：① 从 client-extra.jar 里掏出原版 damage_type 的 JSON 样例；
② 从 neoforge jar 里 javap 出伤亡事件 / DamageContainer 的真签名。只读。"""
import io, json, os, re, subprocess, sys, zipfile, glob

OUT = []
def w(s=""):
    OUT.append(s)

# ---------- ① 原版 damage_type 样例 ----------
ce = glob.glob(r"E:\gradle-home\caches\ng_execute\*\client-extra.jar")
w("client-extra.jar: %r" % ce)
if ce:
    z = zipfile.ZipFile(ce[0])
    names = [n for n in z.namelist() if "/damage_type/" in n]
    w("原版 damage_type 共 %d 个" % len(names))
    for want in ["thorns.json", "generic.json", "player_attack.json", "mob_attack.json",
                 "cactus.json", "fall.json", "explosion.player.json", "arrow.json",
                 "magic.json", "indirect_magic.json", "out_of_world.json", "sonic_boom.json",
                 "sting.json", "wither.json"]:
        hit = [n for n in names if n.endswith("/" + want)]
        if hit:
            w("--- %s ---" % want)
            w(z.read(hit[0]).decode("utf-8"))

# ---------- ② neoforge 事件签名 ----------
jar = None
for p in glob.glob(r"E:\gradle-home\caches\modules-2\files-2.1\net.neoforged\neoforge\21.1.235\*\*.jar"):
    if "sources" not in p and "javadoc" not in p:
        jar = p
w()
w("neoforge jar: %r" % jar)

CLS = [
    "net.neoforged.neoforge.event.entity.living.LivingDamageEvent",
    "net.neoforged.neoforge.event.entity.living.LivingDamageEvent$Pre",
    "net.neoforged.neoforge.event.entity.living.LivingDamageEvent$Post",
    "net.neoforged.neoforge.event.entity.living.LivingIncomingDamageEvent",
    "net.neoforged.neoforge.common.damagesource.DamageContainer",
    "net.neoforged.neoforge.event.entity.living.LivingEvent$LivingTickEvent",
    "net.neoforged.neoforge.event.entity.living.LivingFallEvent",
    "net.neoforged.neoforge.event.entity.living.LivingKnockBackEvent",
]
javap = os.path.join(os.environ.get("JAVA_HOME", r"C:\Program Files\Java\jdk-21"), "bin", "javap.exe")
if not os.path.exists(javap):
    javap = "javap"
for c in CLS:
    r = subprocess.run([javap, "-cp", jar, c], capture_output=True, text=True, encoding="utf-8", errors="replace")
    w("=== %s ===" % c)
    w(r.stdout.strip() or r.stderr.strip())
    w()

txt = "\n".join(OUT)
io.open(r"E:\PotatoST\build\zftools\_zf139_src.txt", "w", encoding="utf-8").write(txt + "\n")
print("ok -> _zf139_src.txt  (%d lines)" % len(OUT))
