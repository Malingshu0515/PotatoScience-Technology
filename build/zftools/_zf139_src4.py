# -*- coding: utf-8 -*-
"""ZF139 取证（四）：DamageType/DamageEffects 的 JSON 结构、hurt 里无敌帧的位置、CommonHooks.onLivingFall。只读。"""
import io, re, zipfile

MC = r"E:\PotatoST\build\neoForm\neoFormJoined1.21.1-20240808.144430\sources.jar"
NF = r"E:\gradle-home\caches\modules-2\files-2.1\net.neoforged\neoforge\21.1.235\4566e557485e2cf5843d29a9c44795f5f731d36d\neoforge-21.1.235-sources.jar"
z1, z2 = zipfile.ZipFile(MC), zipfile.ZipFile(NF)
OUT = []

def raw(z, path, label):
    OUT.append("=" * 25 + " " + label + " " + "=" * 25)
    OUT.append(z.read(path).decode("utf-8"))
    OUT.append("")

raw(z1, "net/minecraft/world/damagesource/DamageType.java", "vanilla DamageType.java")
raw(z1, "net/minecraft/world/damagesource/DamageEffects.java", "vanilla DamageEffects.java")

s = z1.read("net/minecraft/world/entity/LivingEntity.java").decode("utf-8").split("\n")
OUT.append("=" * 25 + " LivingEntity.hurt 1180-1245 " + "=" * 25)
for k in range(1179, 1245):
    OUT.append("%4d %s" % (k + 1, s[k]))
OUT.append("")

s2 = z2.read("net/neoforged/neoforge/common/CommonHooks.java").decode("utf-8").split("\n")
for pat in [r"onLivingFall", r"onLivingKnockBack"]:
    for i, l in enumerate(s2):
        if re.search(pat, l):
            OUT.append("---- CommonHooks /%s/ @%d ----" % (pat, i + 1))
            OUT.extend(s2[max(0, i - 6):i + 16])
            OUT.append("")

txt = "\n".join(OUT)
io.open(r"E:\PotatoST\build\zftools\_zf139_src4.txt", "w", encoding="utf-8").write(txt + "\n")
print("ok -> _zf139_src4.txt (%d lines)" % len(OUT))
