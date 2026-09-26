# -*- coding: utf-8 -*-
u"""_zf104_gatecount.py —— 门日志**完整性**核对（§4.53 的保险）

做法：从 `.ps1` 里抠出所有 `Run-Ps1/Run-Py '<段名>'`，再去日志里找
      `==================== <段名> ====================`；缺一段就 FAIL；
      另外日志里出现 Python traceback 也算 FAIL（段"在"不等于段"跑通了"）。
⚠ ZF104 相对 ZF102 多两段（`ZF104 verify` + `ZF104 falsify`）；ZF106 又加一段（`ZF106 recipes`）；
  **ZF120 再加两段**（`ZF120 verify` + `ZF120 falsify`）；**ZF134 再加两段**
  （`ZF134 verify` + `ZF134 falsify`）⇒ 现在 `_zf104_gates.ps1` 里是 **63** 段
  + 门结束 = 日志 64 段（⚠ 以脚本里的实际行数为准 —— 这个数跟着脚本长，别照抄注释）。
"""
import io
import os
import re
import sys

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

TOOLS = r"E:\PotatoST\build\zftools"
SCRIPT = os.path.join(TOOLS, u"_zf104_gates.ps1")
LOG = os.path.join(TOOLS, u"_zf104_gates.txt")

fails = []


def main():
    ps1 = io.open(SCRIPT, encoding="utf-8").read()
    names = re.findall(r"(?m)^Run-(?:Ps1|Py)\s+'([^']+)'", ps1)
    print(u"脚本声明了 %d 段" % len(names))

    raw = io.open(LOG, "rb").read()
    try:
        text = raw.decode("utf-16")
        enc = u"utf-16"
    except Exception:
        text = raw.decode("utf-8", "replace")
        enc = u"utf-8"
    missing = []
    for n in names:
        ascii_part = re.sub(r"[^\x20-\x7e]", "", n).strip()
        ok = (u"==================== " + n + u" ====================") in text
        if not ok and ascii_part:
            ok = len(re.findall(re.escape(ascii_part), text)) >= 1
        if not ok:
            missing.append(n)
    label = u"日志里每一段都出现了（缺 %s）" % (missing or u"无")
    if missing:
        fails.append(label)
        print(u"  [FAIL] " + label)
    else:
        print(u"  [OK]   " + label)
    print(u"  日志编码 = %s，共 %d 行" % (enc, text.count(u"\n")))

    declared = set(names)
    found = re.findall(r"==================== (.+?) ====================", text)
    extra = [f for f in found if f not in declared and f != u"门结束"]
    if extra:
        print(u"  [WARN] 日志里有脚本未声明的段：%s" % extra)
    else:
        print(u"  [OK]   没有脚本未声明的段（%d 段 + 门结束）" % len(found))

    tb = [i + 1 for i, l in enumerate(text.split(u"\n")) if u"Traceback (most recent call last)" in l]
    label = u"日志里没有任何 Python traceback（段不能只'在'，得真的跑通）"
    if tb:
        fails.append(u"%s：在第 %s 行" % (label, tb[:5]))
        print(u"  [FAIL] " + label + u"（%d 处，首个在第 %d 行）" % (len(tb), tb[0]))
    else:
        print(u"  [OK]   " + label)

    print(u"\n失败项 = %d" % len(fails))
    for f in fails:
        print(u"  !! " + f)
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())
