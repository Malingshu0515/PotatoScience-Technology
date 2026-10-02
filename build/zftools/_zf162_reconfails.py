# -*- coding: utf-8 -*-
u"""_zf162_reconfails.py —— ZF162 跟平侦察：把相关门**这一次**失败的断言原文全打出来（只读）。

跑法：python build\\zftools\\_zf162_reconfails.py
输出：build\\zftools\\_zf162_reconfails.txt
"""
import io
import os
import subprocess
import sys

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding=u"utf-8", errors="replace")

ZT = r"E:\PotatoST\build\zftools"
NAMES = [u"_zf71_verify.py", u"_zf73_verify.py", u"_zf79_verify.py", u"_zf80_verify.py",
         u"_zf93_verify.py", u"_zf98_verify.py", u"_zf100_verify.py", u"_zf102_verify.py",
         u"_zf103_verify.py", u"_zf107_verify.py", u"_zf109_verify.py", u"_zf114_verify.py",
         u"_zf117_verify.py", u"_zf122_verify.py", u"_zf126_verify.py", u"_zf127_verify.py",
         u"_zf128_verify.py", u"_zf134_verify.py", u"_zf139_verify.py", u"_zf145_verify.py",
         u"_zf146_verify.py", u"_zf148_verify.py", u"_zf150_verify.py", u"_zf153_verify.py",
         u"_zf155_verify.py", u"_zf156_verify.py", u"_zf158_verify.py"]
KEY = (u"594", u"596", u"wrench", u"electric_blast_furnace", u"FluidContainerItem",
       u"mayPlace", u"isItemValid", u"UNSUPPORTED", u"关卡", u"判据顺序", u"crafting_shaped",
       u"plates", u"icon", u"图标", u"键")

lines = []
for n in NAMES:
    p = os.path.join(ZT, n)
    if not os.path.isfile(p):
        lines.append(u"== %s：不在盘上" % n)
        continue
    r = subprocess.run([sys.executable, p], stdout=subprocess.PIPE, stderr=subprocess.STDOUT, timeout=300)
    out = r.stdout.decode("utf-8", "replace")
    fails = [l.strip() for l in out.split(u"\n") if l.strip().startswith(u"[FAIL]")]
    if not fails:
        fails = [l.strip() for l in out.split(u"\n") if l.strip().startswith(u"!!")]
    hits = [f for f in fails if any(k in f for k in KEY)]
    lines.append(u"== %s（rc=%d，失败 %d 条，命中 %d 条）" % (n, r.returncode, len(fails), len(hits)))
    for h in hits:
        lines.append(u"    " + h)
    lines.append(u"")

io.open(os.path.join(ZT, u"_zf162_reconfails.txt"), "w", encoding="utf-8", newline=u"\n").write(
    u"\n".join(lines) + u"\n")
print(u"已写 _zf162_reconfails.txt（%d 行）" % len(lines))
