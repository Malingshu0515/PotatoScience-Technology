# -*- coding: utf-8 -*-
u"""_zf125_fixdocs.py —— 给 `_zf125_docs.py` 收尾：去掉 BOM + 最后那个 475 → 476

**为什么会有这一出**：我用 PowerShell 的 `(Get-Content -Raw) -replace ... | Set-Content -Encoding UTF8`
批量改数字 —— PowerShell 5.1 的 `-Encoding UTF8` 会**写 BOM**，而且漏了一处 `475 键`。
脚本文件带 BOM 不致命（Python 3 认），但本工程的脚本一律无 BOM，留着迟早让某道文本级检查咬人。

跑法：
    python build\\zftools\\_zf125_fixdocs.py
"""
import io
import os
import sys

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

P = r"E:\PotatoST\build\zftools\_zf125_docs.py"

notes, fails = [], []


def main():
    raw = open(P, "rb").read()
    had_bom = raw[:3] == b"\xef\xbb\xbf"
    text = raw.decode("utf-8-sig")
    if had_bom:
        notes.append(u"① 去掉 BOM")
    if u"475 键" in text:
        n = text.count(u"475 键")
        text = text.replace(u"475 键", u"476 键")
        notes.append(u"② 475 键 → 476 键（%d 处）" % n)
    text = text.replace(u"464 → 476", u"464 → 476")     # 幂等
    io.open(P, "w", encoding="utf-8", newline=u"").write(text)
    back = io.open(P, encoding="utf-8", newline=u"").read()
    if u"475" in back:
        fails.append(u"还有 475 残留")
    if open(P, "rb").read()[:3] == b"\xef\xbb\xbf":
        fails.append(u"BOM 还在")
    if not fails:
        notes.append(u"收尾完成：无 BOM、无 475（%d B）" % os.path.getsize(P))
    print(u"\n".join(u"  [OK] " + n for n in notes))
    print(u"失败项 = %d" % len(fails))
    for f in fails:
        print(u"  !! " + f)
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())
