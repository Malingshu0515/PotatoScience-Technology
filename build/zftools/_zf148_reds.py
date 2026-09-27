# -*- coding: utf-8 -*-
u'''_zf148_reds.py —— ZF148：把红门的**全部**失败行原样抓下来，用来判定「是不是我弄红的」。

只读：逐份跑门，抓 stdout 里所有失败行（不截断），写 `_zf148_reds.txt`。
判据：失败行里点到的东西属于本轮新增的（`guide` / `手册` / 71 个新键 / 配方 +1），
      就是**我**弄红的；点到贴图、tooltip 数字、老 sha1、JEI 分类数……的是**先前就红**的。

跑法：python build\zftools\_zf148_reds.py
'''
import io
import os
import subprocess
import sys

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding=u"utf-8", errors="replace")
ZT = r"E:\PotatoST\build\zftools"
OUT = os.path.join(ZT, u"_zf148_reds.txt")

NAMES = [u"_zf70_verify.py", u"_zf71_verify.py", u"_zf73_repro.py", u"_zf73_verify.py",
         u"_zf75_verify.py", u"_zf78_verify.py", u"_zf79_verify.py", u"_zf80_verify.py",
         u"_zf81_verify.py", u"_zf82_verify.py", u"_zf89_verify.py", u"_zf90_verify.py",
         u"_zf91_verify.py", u"_zf92_verify.py", u"_zf93_verify.py", u"_zf95_verify.py",
         u"_zf96_verify.py", u"_zf97_verify.py", u"_zf98_verify.py", u"_zf100_verify.py",
         u"_zf101_verify.py", u"_zf102_verify.py", u"_zf107_verify.py", u"_zf109_verify.py",
         u"_zf111_verify.py", u"_zf112_verify.py", u"_zf117_verify.py", u"_zf118_verify.py",
         u"_zf119_verify.py", u"_zf121_verify.py", u"_zf124_verify.py", u"_zf125_verify.py",
         u"_zf126_verify.py", u"_zf127_verify.py", u"_zf128_verify.py", u"_zf133_verify.py",
         u"_zf139_verify.py", u"_zf141_verify.py", u"_zf145_verify.py"]

lines = []


def say(s):
    lines.append(s)
    print(s)


for n in NAMES:
    p = os.path.join(ZT, n)
    if not os.path.exists(p):
        say(u"---- %s：不在盘上 ----" % n)
        continue
    try:
        r = subprocess.run([sys.executable, p], stdout=subprocess.PIPE,
                           stderr=subprocess.STDOUT, timeout=300)
        out = r.stdout.decode(u"utf-8", "replace")
        rc = r.returncode
    except subprocess.TimeoutExpired:
        say(u"---- %s：超时 ----" % n)
        continue
    if rc == 0:
        say(u"---- %s：绿 ----" % n)
        continue
    say(u"==================== %s（退出码 %d） ====================" % (n, rc))
    for l in out.split(u"\n"):
        s = l.strip()
        if s.startswith(u"!!") or s.startswith(u"[FAIL]") or u"[FAIL]" in s:
            say(u"   " + s[:400])
        elif s.startswith(u"- ") and (u"—" in s or u"缺" in s or u"实际" in s or u"期望" in s):
            say(u"   " + s[:400])
    say(u"")

io.open(OUT, "w", encoding="utf-8", newline=u"\n").write(u"\n".join(lines) + u"\n")
print(u"（已写 %s）" % OUT)
