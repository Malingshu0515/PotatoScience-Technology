# -*- coding: utf-8 -*-
u"""_zf89_publish.py —— ZF89 出成品（作废 ZF88 那版 `f86c569c…`）+ 把 §9 的占位填实

照老规矩（§5 ZF63 教训）：**先核对旧哈希、再核对新产物内容，全过了才动文件**；
任何一条不过就一个字节都不动。
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
PUB = os.path.join(ROOT, "build", "zftools", "_zf89_publish.py")
DOC = os.path.join(ROOT, "docs", u"开发档案.md")
TEXB = os.path.join(ROOT, r"src\main\resources\assets\potato_s_t\textures\block")
VOID = "05895f2d72a0f363bf1b311ff231d9c75f313aa4"
ENTRIES = [(u"gasoline_still.png",), (u"gasoline_flow.png",),
           (u"naphtha_still.png",), (u"naphtha_flow.png",),
           (u"electric_blast_furnace.png",)]
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
        new, size, entries = u"(缺)", 0, 0
    else:
        new = sha1(SRC)
        size = os.path.getsize(SRC)
        with zipfile.ZipFile(SRC) as zf:
            names = zf.namelist()
            entries = len(names)
            bad = [n for n in names if "Check" in n.split("/")[-1] and n.endswith(".class")]
            if bad:
                fails.append(u"成品里带探针：%s" % bad)
            for (nm,) in ENTRIES:
                entry = u"assets/potato_s_t/textures/block/" + nm
                disk = os.path.join(TEXB, nm)
                if entry not in names:
                    fails.append(u"成品里没有 %s" % entry)
                elif zf.read(entry) != open(disk, "rb").read():
                    fails.append(u"成品里的 %s 与盘上不一致" % nm)
                else:
                    print(u"  [OK]   成品里的 %s 与盘上一致" % nm)
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
    print(u"   作废 %s（ZF88）" % VOID[:8])

    patch(DOC, u"__ZF89_SHA1__", new, u"§9 ZF89 条目：成品哈希填实")
    patch(DOC, u"__ZF89_BYTES__", str(size), u"§9 ZF89 条目：字节数填实")
    patch(DOC, u"__ZF89_ENTRIES__", str(entries), u"§9 ZF89 条目：条目数填实")
    patch(DOC, u"**成品**：`release\\PotatoST-0.11.jar` = `%s`" % VOID,
          u"**当时的成品**：`release\\PotatoST-0.11.jar` = `%s`" % VOID,
          u"§9 ZF88 条目：成品 → 当时的成品")
    patch(PUB, u'VOID = "%s"' % VOID, u'VOID = "%s"' % new, u"发布脚本 VOID 跟到最新")

    print(u"\n失败项 = %d" % len(fails))
    for f in fails:
        print(u"  !! " + f)
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())
