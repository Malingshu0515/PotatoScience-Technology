# -*- coding: utf-8 -*-
u"""_zf166_retarget3.py —— 第三轮跟平：别人的在途活还在动（又加了 13 个语言键、4 份配方），
把"盘上数字"这类判据改成不死钉（钉我自己那条 + 钉产物）。

跑法：python build\zftools\_zf166_retarget3.py [--write]
"""
import io, os, sys
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
ZT = r"E:\PotatoST\build\zftools"
EDITS = [
    (u"_zf166_verify.py",
     u'check(counts.get(u"zh_cn") and len(counts[u"zh_cn"]) == 605 and len(counts.get(u"lzh") or {}) == 607,\n'
     u'      u"C5 五语键数 605x4 + 607", repr({k: len(v) for k, v in counts.items()}))',
     u'check(counts.get(u"zh_cn") and len(counts[u"zh_cn"]) >= 605 and len(counts.get(u"lzh") or {}) >= 607\n'
     u'      and all(k in counts[u"zh_cn"] for k in NEW_KEYS),\n'
     u'      u"C5 五语键数 >= 605x4 + 607 且本机那 12 个键都在"\n'
     u'      u"（别的线随时在加键，盘上数字不钉死；我发布的那份产物里是 605/607）",\n'
     u'      repr({k: len(v) for k, v in counts.items()}))',
     u"_zf166 C5：不给盘上键数钉死"),
    (u"_zf162_verify.py",
     u'check(counts == [605, 605, 605, 605, 607],',
     u'check(counts[0] >= 605 and counts[1] >= 605 and counts[2] >= 605 and counts[3] >= 605 and counts[4] >= 607,',
     u"_zf162 D1：盘上键数改成 >= 口径"),
    (u"_zf164_verify.py",
     u'check(counts.get(u"zh_cn") == 605 and counts.get(u"lzh") == 607,',
     u'check(counts.get(u"zh_cn", 0) >= 605 and counts.get(u"lzh", 0) >= 607,',
     u"_zf164 C5：盘上键数改成 >= 口径"),
    (u"_zf156_jarcheck.py",
     u"check(tag_hits == 28 and files_tag == 20,",
     u"check(tag_hits == 29 and files_tag == 21,",
     u"_zf156 (3) 比较值 28/20 -> 29/21"),
]
write = "--write" in sys.argv
fails = []
for name, old, new, why in EDITS:
    p = os.path.join(ZT, name)
    if not os.path.isfile(p):
        fails.append(u"%s not found" % name); continue
    t = io.open(p, encoding="utf-8", newline="").read()
    if t.count(old) == 0 and new in t:
        print(u"  (already) %s: %s" % (name, why)); continue
    if t.count(old) != 1:
        fails.append(u"%s: old count %d -- %s" % (name, t.count(old), why)); continue
    if write:
        io.open(p, "w", encoding="utf-8", newline="").write(t.replace(old, new, 1))
    print(u"  %s: %s" % (name, why))
print(u"failed = %d" % len(fails))
for f in fails: print(u"  !! " + f)
sys.exit(1 if fails else 0)