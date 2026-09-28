# -*- coding: utf-8 -*-
u"""把 ①② 两道门的**失败行**原样落成 UTF-8（GBK 控制台看不见中文，只能落盘再读）。"""
import io
import os
import subprocess
import sys

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
ROOT = r"E:\PotatoST"
T = os.path.join(ROOT, "build", "zftools")


def run(name):
    code = ("$ErrorActionPreference='Continue';"
            "$sb = [scriptblock]::Create([IO.File]::ReadAllText('%s', [Text.Encoding]::UTF8)); "
            "& $sb" % os.path.join(T, name))
    r = subprocess.run(["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass",
                        "-Command", code], capture_output=True, cwd=ROOT,
                       env=dict(os.environ, PYTHONIOENCODING="utf-8"))
    return r.stdout.decode("utf-8", "replace") + r.stderr.decode("utf-8", "replace")


buf = []
for name in (u"Audit.ps1", u"LangCheck.ps1"):
    out = run(name)
    buf.append(u"================ %s ================" % name)
    for line in out.split(u"\n"):
        if any(k in line for k in (u"FAIL", u"失败", u"结论", u"键数", u"多 2", u"缺 ")):
            buf.append(u"  " + line.rstrip()[:200])
    buf.append(u"")
io.open(os.path.join(T, u"_zf153_gates_red.txt"), "w", encoding="utf-8",
        newline=u"\n").write(u"\n".join(buf) + u"\n")
print(u"写出 _zf153_gates_red.txt（%d 行）" % len(buf))
