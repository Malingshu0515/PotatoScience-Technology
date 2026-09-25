# -*- coding: utf-8 -*-
u"""_zf78_voidfix.py —— 把发布脚本的 VOID 指到最新成品（下次重打包时作废的就是它）

⚠ 为什么单独一个脚本：我上一版想用 `python -c` 内联改，PowerShell 把里面的引号搅坏了
（`SyntaxError: unterminated string literal`）—— 老规矩：**别用内联 python 带引号干活，写文件**。
"""
import io
import os
import sys

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

P = r"E:\PotatoST\build\zftools\_zf78_publish.py"
OLD = 'VOID = "9fd7340f0d776a540e1935b2536c08ea03474c75"'
NEW = 'VOID = "bafa7853364ae22ff8f1e5e2b62aad085ed40dbb"'


def main():
    t = io.open(P, encoding="utf-8").read()
    if NEW in t:
        print(u"  [SKIP] VOID 已经是最新的（幂等）")
        return 0
    if t.count(OLD) != 1:
        print(u"  [FAIL] 锚点命中 %d 次（必须 1 次）" % t.count(OLD))
        return 1
    io.open(P, "w", encoding="utf-8", newline=u"\n").write(t.replace(OLD, NEW, 1))
    print(u"  [OK]   VOID → bafa7853…（本轮第三次的成品）")
    return 0


if __name__ == "__main__":
    sys.exit(main())
