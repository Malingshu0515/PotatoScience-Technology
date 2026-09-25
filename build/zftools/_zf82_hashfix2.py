# -*- coding: utf-8 -*-
u"""_zf82_hashfix2.py —— ZF82 同日第二次打包：把 §9 里那三个数换成新的，并写清上一版也作废

（第一次打包 `50f028f7…` 之后，门炸出 6 条 ⇒ 修完重打包 `8ba61f5d…`。
 占位符已经填过一次，所以这次是**改数**而不是填占位。）
"""
import hashlib
import io
import os
import sys

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

ROOT = r"E:\PotatoST"
DOC = os.path.join(ROOT, "docs", u"开发档案.md")
PUB = os.path.join(ROOT, "build", "zftools", "_zf82_publish.py")
JAR = os.path.join(ROOT, "release", "PotatoST-0.11.jar")
OLD = "50f028f7e4506d0e74386c19eb8054c280e55198"
fails = []


def main():
    raw = open(JAR, "rb").read()
    new = hashlib.sha1(raw).hexdigest()
    size = len(raw)
    import zipfile
    with zipfile.ZipFile(JAR) as zf:
        entries = len(zf.namelist())
    print(u"新成品 = %s（%d B / %d 条目）" % (new, size, entries))

    t = io.open(DOC, encoding="utf-8").read()
    if t.count(OLD) != 1:
        fails.append(u"§9 里那个旧哈希命中 %d 次（期望 1）" % t.count(OLD))
    else:
        t = t.replace(OLD, new, 1)
        print(u"  [OK]   §9 ZF82：哈希 %s… → %s…" % (OLD[:8], new[:8]))
    # 紧跟其后的字节数/条目数（第一次填的是 2352648 / 805）
    for old_v, new_v, label in [(u"2352648 B / 805 条目", u"%d B / %d 条目" % (size, entries),
                                 u"字节数/条目数")]:
        if t.count(old_v) != 1:
            fails.append(u"§9 里 %s 命中 %d 次" % (label, t.count(old_v)))
        else:
            t = t.replace(old_v, new_v, 1)
            print(u"  [OK]   §9 ZF82：%s → %s" % (old_v, new_v))
    note = u"（**同日按门里的 6 条修复重打包 ⇒ 第一版 `%s` 作废**）" % OLD[:8]
    if note not in t:
        anchor = u"**作废上一版 `257ff4b79635f7764bd241d1e7fc17d387188efe`**（ZF81）"
        if t.count(anchor) != 1:
            fails.append(u"§9 ZF82 作废行锚点命中 %d 次" % t.count(anchor))
        else:
            t = t.replace(anchor, anchor + u"\n" + note, 1)
            print(u"  [OK]   §9 ZF82：写清第一版也作废")
    io.open(DOC, "w", encoding="utf-8", newline=u"\n").write(t)

    p = io.open(PUB, encoding="utf-8").read()
    if p.count(u'VOID = "%s"' % OLD) == 1:
        io.open(PUB, "w", encoding="utf-8", newline=u"\n").write(
            p.replace(u'VOID = "%s"' % OLD, u'VOID = "%s"' % new, 1))
        print(u"  [OK]   发布脚本 VOID 跟到最新")
    else:
        fails.append(u"发布脚本里没找到 VOID = %s" % OLD)

    print(u"\n失败项 = %d" % len(fails))
    for f in fails:
        print(u"  !! " + f)
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())
