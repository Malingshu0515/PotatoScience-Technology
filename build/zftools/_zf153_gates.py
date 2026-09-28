# -*- coding: utf-8 -*-
u"""_zf153_gates.py —— ZF153 的九道门（§11.1，一道都不能跳）

⚠ **必须用 scriptblock 方式调 PowerShell 脚本**（三个 .ps1 自己头部就写了原因）：
    $sb = [scriptblock]::Create([IO.File]::ReadAllText('<路径>', [Text.Encoding]::UTF8)); & $sb
  为什么不能用 `powershell -File`：本机是 **Windows PowerShell 5.1 + 中文 GBK 代码页**，
  而这些 .ps1 是**无 BOM 的 UTF-8** ⇒ 5.1 按 ANSI 读源码 ⇒ 中文与 `}` 一起被解码坏掉，
  报的却是"缺少右花括号"这种**指向错误方向的**语法错（§4.119：先怀疑调用方式）。

红了的门**逐条归因**：本轮只碰了"物品 + 贴图/模型/语言 + 一批写死键数的门 + 文档"，
所以凡是红的都要能说清"是不是我的"—— 说不清就不算过（ZF146 的同一套口径）。

跑法：python build\\zftools\\_zf153_gates.py
"""
import io
import os
import subprocess
import sys

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

ROOT = r"E:\PotatoST"
T = os.path.join(ROOT, "build", "zftools")
OUT = os.path.join(T, "_zf153_gates.txt")


def ps(script, extra=""):
    code = ("$ErrorActionPreference='Continue';"
            "$sb = [scriptblock]::Create([IO.File]::ReadAllText('%s', [Text.Encoding]::UTF8)); "
            "& $sb %s" % (script, extra))
    return ["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass", "-Command", code]


GATES = [
    (u"① Audit.ps1", ps(os.path.join(T, "Audit.ps1"))),
    (u"② LangCheck.ps1", ps(os.path.join(T, "LangCheck.ps1"))),
    (u"③ RecipeCheck.ps1 -All", ps(os.path.join(T, "RecipeCheck.ps1"), "-All")),
    (u"④ ModelCheck.py", [sys.executable, os.path.join(T, "ModelCheck.py")]),
    (u"⑤ JsonCheck.py", [sys.executable, os.path.join(T, "JsonCheck.py"),
                         os.path.join(ROOT, "src", "main", "resources")]),
    (u"⑥ SoundCheck.py", [sys.executable, os.path.join(T, "SoundCheck.py")]),
    (u"⑦ TextureCheck.py", [sys.executable, os.path.join(T, "TextureCheck.py")]),
    (u"⑧ ToolLint.py", [sys.executable, os.path.join(T, "ToolLint.py")]),
]

buf = []
env = dict(os.environ, PYTHONIOENCODING="utf-8")
for name, cmd in GATES:
    r = subprocess.run(cmd, capture_output=True, cwd=ROOT, env=env)
    out = r.stdout.decode("utf-8", "replace") + r.stderr.decode("utf-8", "replace")
    # 红的行要看得见：优先抓失败/警告那几行，没有再退回末尾
    hits = [l for l in out.split(u"\n")
            if any(k in l for k in (u"FAIL", u"失败", u"警告", u"WARN", u"!!", u"违规"))]
    tail = hits[-8:] if hits else [l for l in out.strip().split(u"\n") if l.strip()][-6:]
    buf.append(u"=== %s (exit %d) ===" % (name, r.returncode))
    buf.extend(tail)
    print(u"=== %s (exit %d) ===" % (name, r.returncode))
    for l in tail:
        print(u"   " + l.strip()[:170])

buf.append(u"=== ⑨ GroupEnergyCheck.java ===")
g = os.path.join(T, "check", "GroupEnergyCheck.java")
print(u"=== ⑨ GroupEnergyCheck.java ===")
if os.path.isfile(g):
    print(u"   在盘上：%s（这道门要真服务端，按 §11.1 由 runServer 那一路覆盖 —— "
          u"本轮的 `Zf153Check` 那趟就是那一路）" % g)
    buf.append(u"在盘上：%s（由本轮 runServer 探针那一趟覆盖）" % g)
else:
    print(u"   ⚠ 不在 check\\ 下")
    buf.append(u"不在 check\\ 下")

io.open(OUT, "w", encoding="utf-8", newline=u"\n").write(u"\n".join(buf) + u"\n")
print(u"\n九道门输出存档：%s" % OUT)
