# -*- coding: utf-8 -*-
u"""_zf79_publish.py —— ZF79 出成品（作废 ZF78 的 `330ea020…`）+ 把文档里的哈希填实

照老规矩（§5 的 ZF63 教训）：**先核对旧哈希，再动文件**；不对就一个字节都不动。
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
PUB = os.path.join(ROOT, "build", "zftools", "_zf79_publish.py")
DOC = os.path.join(ROOT, "docs", u"开发档案.md")
VOID = "6b49d491aa61d43d60bea87c965344fcee6aa8ac"
fails = []


def sha1(p):
    return hashlib.sha1(open(p, "rb").read()).hexdigest()


def patch(path, old, new, label):
    t = io.open(path, encoding="utf-8").read()
    hits = t.count(old)
    if hits != 1:
        fails.append(u"%s：锚点命中 %d 次（必须 1 次）" % (label, hits))
        return
    io.open(path, "w", encoding="utf-8", newline=u"\n").write(t.replace(old, new, 1))
    print(u"  [OK]   %s" % label)


def main():
    old = sha1(DST) if os.path.exists(DST) else u"(缺)"
    if old != VOID:
        fails.append(u"当前成品 %s ≠ 预期要作废的 %s" % (old, VOID))
    if not os.path.exists(SRC):
        fails.append(u"没有构建产物")
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
    print(u"   作废 %s（ZF78 第五次）" % VOID[:8])

    patch(PUB, u'VOID = "%s"' % VOID, u'VOID = "%s"' % new, u"发布脚本 VOID 跟到最新")
    patch(DOC, u"（成品 `release\\PotatoST-0.11.jar` = `__NEWSHA__`）。要看的：",
          u"（成品 `release\\PotatoST-0.11.jar` = `%s`，%d B / %d 条目；"
          u"同版本重打包 ⇒ 上一版 `330ea020…` 作废）。要看的：" % (new, size, entries),
          u"§9 ZF79 条目填上真实哈希")
    patch(DOC, u"（成品 `release\\PotatoST-0.11.jar` = `2bf27d2cf68a51e2721901af8805c6a8cf1273ed`",
          u"（**当时**的成品 = `2bf27d2c…`；**当前成品见 ZF79 那条**",
          u"§9 ZF78 条目：把过期的「成品」改成「当时的成品」")

    print(u"\n失败项 = %d" % len(fails))
    for f in fails:
        print(u"  !! " + f)
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())
