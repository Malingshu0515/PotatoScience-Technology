# -*- coding: utf-8 -*-
"""_zf142_gates.py —— ZF140 的九道门（§11.1，一道都不能跳）

⚠ **必须用 scriptblock 方式调 PowerShell 脚本**（这三个 .ps1 自己头部就写了原因）：
    $sb = [scriptblock]::Create([IO.File]::ReadAllText('<路径>', [Text.Encoding]::UTF8)); & $sb
  为什么不能用 `powershell -File`：本机是 **Windows PowerShell 5.1 + 中文 GBK 代码页**，
  而这些 .ps1 是**无 BOM 的 UTF-8** ⇒ 5.1 按 ANSI 读源码 ⇒ 中文与 `}` 一起被解码坏掉，
  报的却是"缺少右花括号"这种**指向错误方向的**语法错。
  ⇒ 档案 §4.119：**"门报语法错"先怀疑调用方式，别急着改门。**

跑法：python build\\zftools\\_zf142_gates.py
"""
import io
import os
import subprocess
import sys

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
ROOT = r"E:\PotatoST"
T = os.path.join(ROOT, "build", "zftools")
OUT = os.path.join(T, "_zf142_gates.txt")


def ps(script, extra=""):
    """按脚本自己文档里的方式跑（UTF-8 读源码 + scriptblock）。"""
    code = ("$ErrorActionPreference='Continue';"
            "$sb = [scriptblock]::Create([IO.File]::ReadAllText('%s', [Text.Encoding]::UTF8)); "
            "& $sb %s" % (script, extra))
    return ["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass", "-Command", code]


GATES = [
    ("① Audit.ps1", ps(os.path.join(T, "Audit.ps1"))),
    ("② LangCheck.ps1", ps(os.path.join(T, "LangCheck.ps1"))),
    ("③ RecipeCheck.ps1 -All", ps(os.path.join(T, "RecipeCheck.ps1"), "-All")),
    ("④ ModelCheck.py", [sys.executable, os.path.join(T, "ModelCheck.py")]),
    ("⑤ JsonCheck.py", [sys.executable, os.path.join(T, "JsonCheck.py"),
                        os.path.join(ROOT, "src", "main", "resources")]),
    ("⑥ SoundCheck.py", [sys.executable, os.path.join(T, "SoundCheck.py")]),
    ("⑦ TextureCheck.py", [sys.executable, os.path.join(T, "TextureCheck.py")]),
    ("⑧ ToolLint.py", [sys.executable, os.path.join(T, "ToolLint.py")]),
]

buf = []
env = dict(os.environ, PYTHONIOENCODING="utf-8")
for name, cmd in GATES:
    r = subprocess.run(cmd, capture_output=True, cwd=ROOT, env=env)
    out = r.stdout.decode("utf-8", "replace") + r.stderr.decode("utf-8", "replace")
    tail = [l for l in out.strip().split("\n") if l.strip()][-8:]
    buf.append("=== %s (exit %d) ===" % (name, r.returncode))
    buf.extend(tail)
    print("=== %s (exit %d) ===" % (name, r.returncode))
    for l in tail:
        print("   " + l.strip()[:170])

buf.append("=== ⑨ GroupEnergyCheck.java ===")
g = os.path.join(T, "check", "GroupEnergyCheck.java")
print("=== ⑨ GroupEnergyCheck.java ===")
if os.path.isfile(g):
    print("   在盘上：%s（这道门要真服务端，按 §11.1 由 runServer 那一路覆盖）" % g)
    buf.append("在盘上：%s" % g)
else:
    print("   ⚠ 不在 check\\ 下")
    buf.append("不在 check\\ 下")

io.open(OUT, "w", encoding="utf-8", newline="\n").write("\n".join(buf) + "\n")
print("\n九道门输出存档：%s" % OUT)
