# -*- coding: utf-8 -*-
u"""_zf86_counts.py —— ZF86 的活体数字：借原版贴图的模型 11 → 8

（ZF86 把 氯化钠 / 电容 / 碳酸锂 三件从"借原版贴图"改成自家贴图，所以这个数掉到 8。
 英文公告里那句 "11 models still do this" 与 `_zf71_verify.py` 的期望都要跟着改。）
"""
import io
import os
import sys

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

ROOT = r"E:\PotatoST"
fails = []


def patch(rel, old, new, label, expect=1):
    p = os.path.join(ROOT, rel)
    t = io.open(p, encoding="utf-8").read()
    n = t.count(old)
    if n != expect:
        fails.append(u"%s：锚点命中 %d 次（期望 %d）" % (label, n, expect))
        return
    io.open(p, "w", encoding="utf-8", newline=u"\n").write(t.replace(old, new, expect))
    print(u"  [OK]   %s" % label)


def main():
    patch(r"docs\UpdateAnnouncement_EN.md", u"11 models still do this", u"8 models still do this",
          u"公告 11 → 8")
    patch(r"build\zftools\_zf71_verify.py",
          u'check(n_draw == 11 and u"11 models still do this" in doc,',
          u'check(n_draw == 8 and u"8 models still do this" in doc,',
          u"活体校验 11 → 8")
    print(u"\n失败项 = %d" % len(fails))
    for f in fails:
        print(u"  !! " + f)
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())
