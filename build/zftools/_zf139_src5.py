# -*- coding: utf-8 -*-
"""ZF139 取证（五）：LivingEvent.getEntity 的返回类型、Registry.getHolderOrThrow。只读。"""
import io, re, zipfile

MC = r"E:\PotatoST\build\neoForm\neoFormJoined1.21.1-20240808.144430\sources.jar"
NF = r"E:\gradle-home\caches\modules-2\files-2.1\net.neoforged\neoforge\21.1.235\4566e557485e2cf5843d29a9c44795f5f731d36d\neoforge-21.1.235-sources.jar"
z1, z2 = zipfile.ZipFile(MC), zipfile.ZipFile(NF)
OUT = []

s = z2.read("net/neoforged/neoforge/event/entity/living/LivingEvent.java").decode("utf-8")
OUT.append("=== LivingEvent.java ===")
OUT.append(s[s.find("public abstract class LivingEvent"):])

s2 = z1.read("net/minecraft/core/Registry.java").decode("utf-8")
OUT.append("=== Registry.getHolderOrThrow ===")
for m in re.finditer(r"[^\n]*getHolderOrThrow[^\n]*", s2):
    OUT.append(m.group(0).strip())

s3 = z1.read("net/minecraft/core/WritableRegistry.java").decode("utf-8") if "net/minecraft/core/WritableRegistry.java" in z1.namelist() else ""
OUT.append("=== DefaultedRegistry/Registry 里 getHolder 家族 ===")
for m in re.finditer(r"[^\n]*getHolder[^\n]*", s2):
    OUT.append(m.group(0).strip())

txt = "\n".join(OUT)
io.open(r"E:\PotatoST\build\zftools\_zf139_src5.txt", "w", encoding="utf-8").write(txt + "\n")
print("ok")
