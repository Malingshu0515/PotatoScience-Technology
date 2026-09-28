# -*- coding: utf-8 -*-
u"""_zf149_pre.py —— ZF149 动手前备份（§10：第一个字节改动之前先备份）。

本轮是**打包轮**：把手册装进 `release\\PotatoST-0.12.jar`。要备的改前件：
  · `release\\PotatoST-0.12.jar` + 它的 `.sha1`（**被替换的那一份**，必须先留档）
  · `build\\libs\\potato_s_t-0.12.jar`（改前那一次的产物）
  · 三份文档（档案 / 交接 / 英文公告）
  · 本轮可能要跟平的门（成品哈希 / 键数 / 路径写死的那批 `_zf*_verify.py`）
  · `gradle.properties`（版本号，打包前后都要对得上）

落到 `C:\\PotatoST救援\\zf149_pre\\`，逐份核 sha1 + 回读。
跑法：python build\\zftools\\_zf149_pre.py
"""
import hashlib
import io
import os
import shutil
import sys

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding=u"utf-8", errors=u"replace")

PROJ = r"E:\PotatoST"
DST = r"C:\PotatoST救援\zf149_pre"
ZT = os.path.join(PROJ, "build", "zftools")

EXPLICIT = [
    r"gradle.properties",
    r"release\PotatoST-0.12.jar",
    r"release\PotatoST-0.12.jar.sha1",
    r"build\libs\potato_s_t-0.12.jar",
    r"docs\开发档案.md",
    r"docs\多会话协作交接.md",
    r"docs\UpdateAnnouncement_EN.md",
]


def want(fn):
    if fn.startswith(u"_zf149_"):
        return False
    return fn.endswith(u"_verify.py") and fn.startswith(u"_zf")


def sha(p):
    h = hashlib.sha1()
    with open(p, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 16), b""):
            h.update(chunk)
    return h.hexdigest()


def main():
    items = list(EXPLICIT)
    for fn in sorted(os.listdir(ZT)):
        if want(fn):
            items.append(os.path.join(u"build", u"zftools", fn))
    items = sorted(set(items))

    if not os.path.isdir(DST):
        os.makedirs(DST)
    fails, total = [], 0
    for rel in items:
        src = os.path.join(PROJ, rel)
        if not os.path.isfile(src):
            fails.append(u"改前件不在：%s" % rel)
            continue
        dst = os.path.join(DST, rel)
        d = os.path.dirname(dst)
        if not os.path.isdir(d):
            os.makedirs(d)
        shutil.copy2(src, dst)
        a, b = sha(src), sha(dst)
        if a != b:
            fails.append(u"%s 回读不一致" % rel)
            continue
        total += 1
    print(u"备份根：%s" % DST)
    print(u"备份成功 %d 份" % total)
    for rel in items:
        p = os.path.join(DST, rel)
        if os.path.isfile(p):
            print(u"   %-46s %10d B  %s" % (rel, os.path.getsize(p), sha(p)[:12]))
    print(u"")
    print(u"失败 = %d" % len(fails))
    for f in fails:
        print(u"  !! " + f)
    return 1 if fails else 0


if __name__ == u"__main__":
    sys.exit(main())
