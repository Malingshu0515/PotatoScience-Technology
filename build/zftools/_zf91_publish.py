# -*- coding: utf-8 -*-
u"""_zf91_publish.py —— ZF91 出成品（作废 ZF90 那版 `f7b77eab…`）+ 把 §9 的占位填实

照老规矩（§5 ZF63 教训）：**先核对旧哈希、再核对新产物内容，全过了才动文件**。
⚠ §4.59 ④ 的两条硬化：① "成品 → 当时的成品"那句重命名用**独立的 `PREV_ROUND_SHA`**（不自更新）；
② 三个占位补丁允许"已经被填过"（幂等，重跑不会把新成品标错）。
"""
import hashlib
import io
import os
import re
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
PUB = os.path.join(ROOT, "build", "zftools", "_zf91_publish.py")
DOC = os.path.join(ROOT, "docs", u"开发档案.md")
MB = os.path.join(ROOT, r"src\main\resources\assets\potato_s_t\models\block")
VOID = "43e23e9a8d651bb17630b1e7fdfed59f939f21ec"
PREV_ROUND_SHA = "f7b77eab8fef1acef7722e8f5fb8a09178a74392"
FACINGS = ("north", "south", "east", "west")
fails = []


def sha1(p):
    return hashlib.sha1(open(p, "rb").read()).hexdigest()


def patch(path, old, new, label, expect=1, optional=False):
    t = io.open(path, encoding="utf-8").read()
    hits = t.count(old)
    if hits != expect:
        if optional and hits == 0:
            print(u"  [SKIP] %s（锚点已不在 = 之前填过了，幂等放行）" % label)
            return
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
        print(u"  [FAIL] 缺构建产物 ⇒ 一个字节都不动")
        return 1
    new = sha1(SRC)
    size = os.path.getsize(SRC)
    with zipfile.ZipFile(SRC) as zf:
        names = zf.namelist()
        entries = len(names)
        bad = [n for n in names if "Check" in n.split("/")[-1] and n.endswith(".class")]
        if bad:
            fails.append(u"成品里带探针：%s" % bad)
        evil = [n for n in names
                if (n.startswith(u"assets/") or n.startswith(u"data/"))
                and not re.fullmatch(u"[a-z0-9/._-]+", n)]
        if evil:
            fails.append(u"成品里有非 ASCII 条目：%s" % evil)
        else:
            print(u"  [OK]   assets/ 与 data/ 的条目名全合法")
        for f in FACINGS:
            e = u"assets/potato_s_t/models/block/electric_blast_furnace_%s.obj" % f
            disk = os.path.join(MB, u"electric_blast_furnace_%s.obj" % f)
            if e not in names:
                fails.append(u"成品里没有 %s" % e)
            elif zf.read(e) != open(disk, "rb").read():
                fails.append(u"成品里的 %s.obj 与盘上不一致" % f)
            else:
                print(u"  [OK]   成品里的 %s.obj 与盘上一致（%d 字节）" % (f, zf.getinfo(e).file_size))
        e = u"assets/potato_s_t/textures/block/electric_blast_furnace.png"
        if e not in names or zf.read(e) != open(
                os.path.join(ROOT, r"src\main\resources\assets\potato_s_t\textures\block\electric_blast_furnace.png"),
                "rb").read():
            fails.append(u"成品里的高炉贴图与盘上不一致")
        else:
            print(u"  [OK]   成品里的高炉贴图与盘上一致（未动）")
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
    print(u"   作废 %s（ZF90）" % VOID[:8])

    patch(DOC, u"__ZF91_SHA1__", new, u"§9 ZF91 条目：成品哈希填实", optional=True)
    patch(DOC, u"__ZF91_BYTES__", str(size), u"§9 ZF91 条目：字节数填实", optional=True)
    patch(DOC, u"__ZF91_ENTRIES__", str(entries), u"§9 ZF91 条目：条目数填实", optional=True)
    patch(DOC, u"**成品**：`release\\PotatoST-0.11.jar` = `%s`" % PREV_ROUND_SHA,
          u"**当时的成品**：`release\\PotatoST-0.11.jar` = `%s`" % PREV_ROUND_SHA,
          u"§9 ZF90 条目：成品 → 当时的成品", optional=True)
    patch(PUB, u'VOID = "%s"' % VOID, u'VOID = "%s"' % new, u"发布脚本 VOID 跟到最新")

    print(u"\n失败项 = %d" % len(fails))
    for f in fails:
        print(u"  !! " + f)
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())
