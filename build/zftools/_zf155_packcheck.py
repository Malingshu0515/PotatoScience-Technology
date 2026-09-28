# -*- coding: utf-8 -*-
u"""_zf155_packcheck.py —— 打包前看盘：语言键数现在是多少、别人在途改了什么（只读）。"""
import io
import json
import os
import subprocess
import sys

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

ROOT = r"E:\PotatoST"
GIT = r"C:\Program Files\Git\cmd\git.exe"
LANG = os.path.join(ROOT, "src", "main", "resources", "assets", "potato_s_t", "lang")

print(u"== 语言键数（盘上现在） ==")
for fn in sorted(os.listdir(LANG)):
    n = len(json.loads(io.open(os.path.join(LANG, fn), encoding="utf-8").read()))
    print(u"   %-12s %4d 键" % (fn, n))

print(u"\n== 五份 lang 相对 HEAD 的改动（只看键的增删） ==")
for fn in sorted(os.listdir(LANG)):
    p = u"src/main/resources/assets/potato_s_t/lang/" + fn
    r = subprocess.run([GIT, u"-c", u"core.quotepath=false", u"diff", u"--", p], cwd=ROOT,
                       stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    out = r.stdout.decode(u"utf-8", "replace")
    add = [l for l in out.split(u"\n") if l.startswith(u"+ ") and u":" in l]
    rem = [l for l in out.split(u"\n") if l.startswith(u"- ") and u":" in l]
    print(u"   %-12s +%d 行 / -%d 行" % (fn, len(add), len(rem)))
    for l in (add[:3] + rem[:2]):
        print(u"        " + l.strip()[:120])

print(u"\n== src 里在途改动的**非资源**部分 ==")
r = subprocess.run([GIT, u"-c", u"core.quotepath=false", u"diff", u"--stat", u"--",
                    u"src/main/java"], cwd=ROOT, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
print(r.stdout.decode(u"utf-8", "replace").strip() or u"   （没有）")
