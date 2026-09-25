# -*- coding: utf-8 -*-
u"""_zf81_publish.py —— ZF81 出成品（作废 ZF80 那版 `c43c3468…`）+ 填文档占位 + 把 ZF80 条目的"成品"降格

照老规矩（§5 ZF63 教训）：**先核对旧哈希，再动文件**；不对就一个字节都不动。
"""
import hashlib
import io
import os
import shutil
import sys
import zipfile

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

ROOT = r"E:\PotatoST"
SRC = os.path.join(ROOT, "build", "libs", "potato_s_t-0.11.jar")
DST = os.path.join(ROOT, "release", "PotatoST-0.11.jar")
SHA = DST + ".sha1"
PUB = os.path.join(ROOT, "build", "zftools", "_zf81_publish.py")
DOC = os.path.join(ROOT, "docs", u"开发档案.md")
VOID = "257ff4b79635f7764bd241d1e7fc17d387188efe"
fails = []


def sha1(p):
    return hashlib.sha1(open(p, "rb").read()).hexdigest()


def patch(path, old, new, label, expect=1):
    t = io.open(path, encoding="utf-8").read()
    hits = t.count(old)
    if hits != expect:
        fails.append(u"%s：锚点命中 %d 次（必须 %d 次）" % (label, hits, expect))
        return
    io.open(path, "w", encoding="utf-8", newline=u"\n").write(t.replace(old, new, 1))
    print(u"  [OK]   %s" % label)


def main():
    old = sha1(DST) if os.path.exists(DST) else u"(缺)"
    if old != VOID:
        fails.append(u"当前成品 %s ≠ 预期要作废的 %s" % (old, VOID))
    if not os.path.exists(SRC):
        fails.append(u"没有构建产物 %s" % SRC)
    new = sha1(SRC) if os.path.exists(SRC) else u"(缺)"
    size = os.path.getsize(SRC) if os.path.exists(SRC) else 0
    entries = 0
    bad = []
    if os.path.exists(SRC):
        with zipfile.ZipFile(SRC) as zf:
            names = zf.namelist()
            entries = len(names)
            bad = [n for n in names if "Check" in n.split("/")[-1] and n.endswith(".class")]
    if bad:
        fails.append(u"成品里带探针：%s" % bad)
    if new == old:
        fails.append(u"新旧哈希相同 ⇒ 源码没变？")

    if fails:
        print(u"  [FAIL] 以上 %d 条没过 ⇒ 一个字节都不动" % len(fails))
        for f in fails:
            print(u"    !! " + f)
        return 1

    shutil.copy2(SRC, DST)
    io.open(SHA, "w", encoding="ascii", newline=u"\n").write(new + u"\n")
    print(u"① 已发布 release\\PotatoST-0.11.jar = %s（%d B / %d 条目）" % (new, size, entries))
    print(u"   作废 %s（ZF80）" % VOID[:8])

    patch(DOC, u"__NEWSHA__", new, u"§9 ZF81 条目：成品哈希填实")
    patch(DOC, u"__NEWSIZE__", str(size), u"§9 ZF81 条目：字节数填实")
    patch(DOC, u"__NEWENTRIES__", str(entries), u"§9 ZF81 条目：条目数填实")
    patch(DOC, u"**成品**：`release\\PotatoST-0.11.jar` = `%s`" % VOID,
          u"**当时的成品**：`release\\PotatoST-0.11.jar` = `%s`" % VOID,
          u"§9 ZF80 条目：成品 → 当时的成品")
    patch(PUB, u'VOID = "%s"' % VOID, u'VOID = "%s"' % new, u"发布脚本 VOID 跟到最新")

    print(u"\n失败项 = %d" % len(fails))
    for f in fails:
        print(u"  !! " + f)
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())
