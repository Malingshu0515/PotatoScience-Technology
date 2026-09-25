# -*- coding: utf-8 -*-
u"""_zf82_gatecount.py —— 门日志**完整性**核对：日志里必须出现脚本声明的每一段

为什么要有这个（ZF81 踩的坑，见档案 §4.53）：
  本轮的 `_zf82_gates.ps1` 是拿 ZF80 那份用 PowerShell 字符串替换生成的，
  结果 **6 个 `Run-` 行被并进了注释里** —— ToolLint / RecipeCheck / JsonCheck /
  ZF75 / ZF78 / ZF80 verify 与 falsify **根本没跑**，可日志看上去仍然"结论: 通过"。
  ⇒ 光看"有没有 FAIL"不够，必须核对"该跑的段数对不对"。

做法：从 `.ps1` 里抠出所有 `Run-Ps1/Run-Py '<段名>'`，再去日志里找
      `==================== <段名> ====================`；缺一段就报 FAIL。
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
SCRIPT = os.path.join(TOOLS, u"_zf82_gates.ps1")
LOG = os.path.join(TOOLS, u"_zf82_gates.txt")

fails = []


def main():
    ps1 = io.open(SCRIPT, encoding="utf-8").read()
    names = re.findall(r"(?m)^Run-(?:Ps1|Py)\s+'([^']+)'", ps1)
    print(u"脚本声明了 %d 段：%s" % (len(names), u" / ".join(names)))

    raw = io.open(LOG, "rb").read()
    try:
        text = raw.decode("utf-16")
        enc = u"utf-16"
    except Exception:
        text = raw.decode("utf-8", "replace")
        enc = u"utf-8"
    # 中文段名在日志里可能是"UTF-8 被当 GBK 转了一手"的乱码，所以只认 ASCII 主干；
    # 全 ASCII 的段名（Audit.ps1 / ToolLint.py / falsify…）一比一，中文段名退化成"包含 ASCII 部分"
    missing = []
    for n in names:
        ascii_part = re.sub(r"[^\x20-\x7e]", "", n).strip()
        ok = (u"==================== " + n + u" ====================") in text
        if not ok and ascii_part:
            ok = len(re.findall(re.escape(ascii_part), text)) >= 1
        if not ok:
            missing.append(n)
    eq_label = u"日志里每一段都出现了（缺 %s）" % (missing or u"无")
    if missing:
        fails.append(eq_label)
        print(u"  [FAIL] " + eq_label)
    else:
        print(u"  [OK]   " + eq_label)
    print(u"  日志编码 = %s，共 %d 行" % (enc, text.count(u"\n")))

    # 反向：不许有"跑了但脚本里没声明"的段落（防手工改过脚本/日志对不上）
    declared = set(names)
    found = re.findall(r"==================== (.+?) ====================", text)
    extra = [f for f in found if f not in declared and f != u"门结束"]
    if extra:
        print(u"  [WARN] 日志里有脚本未声明的段：%s" % extra)
    else:
        print(u"  [OK]   没有脚本未声明的段（%d 段 + 门结束）" % len(found))

    print(u"\n失败项 = %d" % len(fails))
    for f in fails:
        print(u"  !! " + f)
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())
