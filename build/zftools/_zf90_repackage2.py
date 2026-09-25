# -*- coding: utf-8 -*-
u"""_zf90_repackage2.py —— ZF90 第二次重打包（作废 c625f20c…，并写清两版中间产物的作废原因）

为什么再打一次：新加的"成品里 assets/ 与 data/ 的条目名必须全合法"这条断言抓到
`assets/potato_s_t/textures/block/电力高炉.原名件` —— ZF79 把用户原图留在资源目录里，
从那时起一直被打进 jar。`_zf90_preserve_ebf.py` 已把它按 §4.24 挪到 `build/用户素材/`
并记进来源凭据 ⇒ 这里重打包一次，把这个条目从成品里去掉。

照老规矩：先核对旧哈希、再核新产物的内容（含"没有非 ASCII 条目"），全过了才动文件。
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
DOC = os.path.join(ROOT, "docs", u"开发档案.md")
VOID = "c625f20c17d5efa7c846d609600f6cdec1d14b71"
fails = []


def sha1(p):
    return hashlib.sha1(open(p, "rb").read()).hexdigest()


def main():
    old = sha1(DST) if os.path.exists(DST) else u"(缺)"
    if old != VOID:
        fails.append(u"当前成品 %s ≠ 预期要作废的 %s" % (old, VOID))
    if not os.path.exists(SRC):
        fails.append(u"没有构建产物 %s" % SRC)
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
            fails.append(u"成品里仍有非 ASCII 条目：%s" % evil)
        else:
            print(u"  [OK]   assets/ 与 data/ 的条目名全合法（没有 .原名件 了）")
        if u"assets/potato_s_t/textures/block/electric_blast_furnace.png" not in names:
            fails.append(u"成品里的电力高炉贴图不见了")
        else:
            print(u"  [OK]   电力高炉贴图仍在（%d 字节）"
                  % zf.getinfo(u"assets/potato_s_t/textures/block/electric_blast_furnace.png").file_size)
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
    print(u"   作废 %s（本轮中间版：夹带 .原名件）" % VOID[:8])

    t = io.open(DOC, encoding="utf-8").read()
    anchor = u"**成品**：`release\\PotatoST-0.11.jar` = `%s`（2347320 B / 799 条目）" % VOID
    if t.count(anchor) != 1:
        fails.append(u"§9 ZF90「**成品**」行锚点命中 %d 次" % t.count(anchor))
    else:
        io.open(DOC, "w", encoding="utf-8", newline=u"\n").write(
            t.replace(anchor, u"**成品**：`release\\PotatoST-0.11.jar` = `%s`（%d B / %d 条目）"
                      % (new, size, entries), 1))
        print(u"  [OK]   §9 ZF90「**成品**」行改成新哈希/字节数/条目数")

    print(u"\n失败项 = %d" % len(fails))
    for f in fails:
        print(u"  !! " + f)
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())
