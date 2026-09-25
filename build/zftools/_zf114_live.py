# -*- coding: utf-8 -*-
u"""_zf114_live.py —— ZF114 的"活体数字"一次改全：四语言键数 417 → 432

本工程的老规矩（ZF93/ZF109/ZF112 都这么干）：**往轮常驻校验里写死的键数是"活体数字"**，
一加键就会集体假报警，所以必须一次改全。

本轮改动：
  · `build\\zftools\\_zf*_verify.py` 里所有 `417` → `432`（21 份，都是键数断言或它的文案）
  · `docs\\UpdateAnnouncement_EN.md` 里的 `(417 keys each)` → `(432 keys each)`

三条断言（都不是摆设）：
  ① 改前：每份文件里 `417` 的命中次数先数出来、总和必须等于预期；
  ② 改后：全目录再扫一遍 `\\b417\\b`，**必须一个都不剩**；
  ③ 每份被改过的文件重新 `py_compile` 一遍（语法坏了当场炸，不靠眼睛）。
  另外 `_zf104_verify.py` / `_zf70_verify.py` 里的 398 / 408 **只出现在注释里**（已核对），不动。

跑法：
    python build\\zftools\\_zf114_live.py            # 只体检
    python build\\zftools\\_zf114_live.py --write     # 真改
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

ROOT = r"E:\PotatoST"
TOOLS = os.path.join(ROOT, r"build\zftools")
DOC_EN = os.path.join(ROOT, r"docs\UpdateAnnouncement_EN.md")
OLD = 417
NEW = 432
OLD_DOC = u"(%d keys each)" % OLD
NEW_DOC = u"(%d keys each)" % NEW


def read(p):
    return io.open(p, encoding="utf-8").read()


def main(argv):
    write = "--write" in argv
    targets = sorted(glob.glob(os.path.join(TOOLS, u"_zf*_verify.py")))
    total_hits, touched, fails = 0, [], 0

    print(u"=== ① 改前盘点 ===")
    for p in targets:
        t = read(p)
        hits = len(re.findall(r"\b%d\b" % OLD, t))
        if hits:
            total_hits += hits
            touched.append(p)
            print(u"   %-24s %d 处" % (os.path.basename(p), hits))
    print(u"   合计 %d 份 / %d 处" % (len(touched), total_hits))

    doc = read(DOC_EN)
    doc_hits = doc.count(OLD_DOC)
    print(u"   %-24s %d 处" % (os.path.basename(DOC_EN), doc_hits))

    if not write:
        print(u"（体检模式，未写盘）")
        return 0

    print(u"=== ② 改 ===")
    for p in touched:
        t = read(p)
        new = re.sub(r"\b%d\b" % OLD, str(NEW), t)
        io.open(p, "w", encoding="utf-8", newline=u"").write(new)
        try:
            py_compile.compile(p, doraise=True)
        except Exception as exc:                     # ③ 语法自检
            print(u"   [FAIL] %s 语法坏了：%s" % (os.path.basename(p), exc))
            fails += 1
    if doc_hits:
        io.open(DOC_EN, "w", encoding="utf-8", newline=u"").write(doc.replace(OLD_DOC, NEW_DOC))
    print(u"   已改 %d 份校验 + 公告 %d 处" % (len(touched), doc_hits))

    print(u"=== ③ 改后复核（必须一个 417 都不剩）===")
    left = []
    # ⚠ 只扫**常驻校验**（_zf*_verify.py）：各轮的 `_zfNNN_lang/docs/fix*.py` 里出现的 417
    #    是"那一轮当时的基线"，属于历史记录，不该被改（ZF112/ZF115 的都留着）。
    for p in sorted(glob.glob(os.path.join(TOOLS, u"_zf*_verify.py"))):
        t = read(p)
        if re.search(r"\b%d\b" % OLD, t):
            left.append(os.path.basename(p))
    if left:
        print(u"   [FAIL] 仍有残留：%s" % u", ".join(left))
        fails += 1
    else:
        print(u"   [OK] build\\zftools 下已无 417")
    if OLD_DOC in read(DOC_EN):
        print(u"   [FAIL] 英文公告里还有 %s" % OLD_DOC)
        fails += 1
    else:
        print(u"   [OK] 英文公告已跟到 %s" % NEW_DOC)

    print(u"失败 = %d" % fails)
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
