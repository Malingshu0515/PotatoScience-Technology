# -*- coding: utf-8 -*-
u"""_zf155_status.py —— 提交前点一遍：语言键数（别人有没有又加键）+ 我这条线该提交哪些路径。"""
import io
import json
import os
import subprocess
import sys

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

ROOT = r"E:\PotatoST"
GIT = r"C:\Program Files\Git\cmd\git.exe"
LANG = os.path.join(ROOT, "src", "main", "resources", "assets", "potato_s_t", "lang")

print(u"== 语言键数（活体） ==")
for fn in sorted(os.listdir(LANG)):
    raw = io.open(os.path.join(LANG, fn), "rb").read()
    print(u"   %-12s %4d 键" % (fn, len(json.loads(raw.decode("utf-8")))))

print(u"\n== git status（只看我要动的那些前缀） ==")
r = subprocess.run([GIT, "-c", "core.quotepath=false", "status", "--porcelain"],
                   cwd=ROOT, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
out = r.stdout.decode("utf-8", "replace")
mine = (u"src/main/java/com/potatost/mod/", u"src/main/resources/", u"docs/",
        u"build/zftools/_zf155", u"build/zftools/_zf149", u"build/zftools/check/")
for line in out.split(u"\n"):
    if any(m in line for m in mine):
        print(u"   " + line)
