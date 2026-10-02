# -*- coding: utf-8 -*-
"""ZF139 取证（三）：DamageSource 构造/死亡文案、LivingEntity.hurt 的真实顺序、摔落链路、注册表取值方式。只读。"""
import io, re, zipfile

SRC = r"E:\PotatoST\build\neoForm\neoFormJoined1.21.1-20240808.144430\sources.jar"
z = zipfile.ZipFile(SRC)
OUT = []

def dump(path, patterns=(), head=0, ctx=14):
    s = z.read(path).decode("utf-8")
    OUT.append("=" * 25 + " " + path + " " + "=" * 25)
    lines = s.split("\n")
    if head:
        for i, l in enumerate(lines[:head]):
            OUT.append("%4d %s" % (i + 1, l))
    for pat in patterns:
        for i, l in enumerate(lines):
            if re.search(pat, l):
                lo, hi = max(0, i - 3), min(len(lines), i + ctx)
                OUT.append("---- /%s/ @%d ----" % (pat, i + 1))
                for k in range(lo, hi):
                    OUT.append("%4d %s" % (k + 1, lines[k]))
    OUT.append("")

dump("net/minecraft/world/damagesource/DamageSource.java",
     [r"public DamageSource\(", r"public Component getLocalizedDeathMessage",
      r"public boolean is\(", r"death\.attack"])
dump("net/minecraft/world/damagesource/DamageSources.java",
     [r"class DamageSources", r"public DamageSources\(", r"private final RegistryAccess",
      r"public DamageSource playerAttack", r"public DamageSource mobAttack", r"generic\(\)"],
     head=40)
dump("net/minecraft/world/entity/LivingEntity.java",
     [r"public boolean hurt\(DamageSource", r"public int invulnerableTime", r"protected void actuallyHurt",
      r"public boolean causeFallDamage", r"public void knockback\("],
     ctx=40)
dump("net/minecraft/core/RegistryAccess.java", [r"registryOrThrow", r"lookupOrThrow", r"registry\("], ctx=6)
dump("net/minecraft/world/level/Level.java", [r"registryAccess"], ctx=4)
dump("net/minecraft/world/entity/Entity.java", [r"public boolean causeFallDamage", r"protected void checkFallDamage"], ctx=30)

txt = "\n".join(OUT)
io.open(r"E:\PotatoST\build\zftools\_zf139_src3.txt", "w", encoding="utf-8").write(txt + "\n")
print("ok -> _zf139_src3.txt (%d lines)" % len(OUT))
