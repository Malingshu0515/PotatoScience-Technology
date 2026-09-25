# -*- coding: utf-8 -*-
u"""_zf122_live.py —— ZF122 的活体数字：四语言键数 454 → 464

（键数一直在涨：ZF114 后是 432，之后别轮加到 454；本轮 +10 = 464。）
改两处：所有 `_zf*_verify.py` 里的 454，以及英文公告的 `(454 keys each)`。
照 §4.53：改前数命中、改后核无残留、每份重新 py_compile。

跑法：python build\\zftools\\_zf122_live.py [--write]
"""
import glob
import io
import os
import py_compile
import re
import sys

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

TOOLS = r"E:\PotatoST\build\zftools"
DOC_EN = r"E:\PotatoST\docs\UpdateAnnouncement_EN.md"
OLD, NEW = 454, 464


def read(p):
    return io.open(p, encoding="utf-8", errors="replace").read()


def main(argv):
    write = "--write" in argv
    touched, total = [], 0
    for p in sorted(glob.glob(os.path.join(TOOLS, u"_zf*_verify.py"))):
        n = len(re.findall(r"\b%d\b" % OLD, read(p)))
        if n:
            touched.append((p, n))
            total += n
    doc = read(DOC_EN)
    doc_hits = doc.count(u"(%d keys each)" % OLD)
    print(u"   改前：%d 份校验 / %d 处；英文公告 %d 处" % (len(touched), total, doc_hits))
    if not write:
        print(u"（体检模式，未写盘）")
        return 0
    fails = 0
    for p, _n in touched:
        io.open(p, "w", encoding="utf-8", newline=u"").write(re.sub(r"\b%d\b" % OLD, str(NEW), read(p)))
        try:
            py_compile.compile(p, doraise=True)
        except Exception as exc:
            print(u"   [FAIL] %s 语法坏了：%s" % (os.path.basename(p), exc))
            fails += 1
    if doc_hits:
        io.open(DOC_EN, "w", encoding="utf-8", newline=u"").write(
            doc.replace(u"(%d keys each)" % OLD, u"(%d keys each)" % NEW))
    left = [os.path.basename(p) for p in sorted(glob.glob(os.path.join(TOOLS, u"_zf*_verify.py")))
            if re.search(r"\b%d\b" % OLD, read(p))]
    if left:
        print(u"   [FAIL] 仍有残留：%s" % u", ".join(left))
        fails += 1
    if u"(%d keys each)" % OLD in read(DOC_EN):
        print(u"   [FAIL] 英文公告没跟上")
        fails += 1
    print(u"   已改 %d 份 + 公告；残留检查 %s" % (len(touched), u"通过" if not fails else u"失败"))
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
