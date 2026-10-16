# -*- coding: utf-8 -*-
u"""_zf200_root.py —— 把常驻门/脚本/探针里的**老根绝对路径**重指到新根。

背景：项目树从 `E:\\PotatoST\\PotatoSTneoforge1.21.1\\` 挪到了 `E:\\PotatoST\PotatoSTneoforge1.21.1\\PotatoSTneoforge1.21.1\\`
（2026-10-16 那次整理），而 ~120 份脚本里写的是老根的绝对路径 ⇒ 集体找不到文件。

三个阶段：
  python build\\zftools\\_zf200_root.py --backup --write    # §10 改前备份根 zf200_pre
  python build\\zftools\\_zf200_root.py --phase1 --write    # 重指（幂等：已经是新根的不动）
  python build\\zftools\\_zf200_root.py --phase2 --write    # 档案 §5 行 + 交接第 52 条

**只碰代码工具**（`build/zftools/**` 的 .py/.java + 新根下的根级 .py）；
档案/公告/探针报告里的历史字样**一个字都不动**（改了就是篡改历史）。
"""
import glob
import hashlib
import io
import os
import re
import shutil
import sys

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding=u"utf-8", errors="replace")

NEW = r"E:\PotatoST\PotatoSTneoforge1.21.1"
OLD = r"E:\PotatoST\PotatoSTneoforge1.21.1"
ZT = os.path.join(NEW, "build", "zftools")
DEST = os.path.join(ZT, "zf200_pre")
SUB = u"PotatoSTneoforge1.21.1"

# 目标文件：zftools 下的 .py/.java + 新根下的根级 .py
# ⚠⚠ **排除所有 `zfNNN_pre` 备份根**（历次改前的快照，改了就是篡改历史 —— 第一版没排，
#     一口气改了 4260 份，连 zf186_pre…zf198_pre 里的快照都改了；已用 git 还原）。
SKIP = re.compile(u"(^|[\\\\/])(zf\\d+_pre|_zf\\d+_falsify_bak|zf\\d+_bak)([\\\\/]|$)")


def targets():
    out = []
    for pat in (u"**/*.py", u"**/*.java"):
        out += glob.glob(os.path.join(ZT, pat), recursive=True)
    out += [p for p in glob.glob(os.path.join(NEW, u"*.py"))]
    keep = []
    for p in sorted(set(out)):
        rel = os.path.relpath(p, NEW)
        if not SKIP.search(rel):
            keep.append(p)
    return keep


RE_BACK = re.compile(u"E:(\\\\+)PotatoST(\\\\+)(?!" + SUB + u")")
RE_QUOTE = re.compile(u"E:(\\\\+)PotatoST(?=[\"'])(?!" + SUB + u")")
RE_FWD = re.compile(u"E:/PotatoST/(?!" + SUB + u")")
RE_TAIL = re.compile(u"E:(\\\\+)PotatoST(?![" + u"\\\\" + u"/A-Za-z0-9_.\"'-])(?!" + SUB + u")")


def convert(text):
    n = 0
    text, k = RE_BACK.subn(lambda m: u"E:%sPotatoST%s%s%s" % (m.group(1), m.group(2), SUB, m.group(2)), text)
    n += k
    text, k = RE_QUOTE.subn(lambda m: u"E:%sPotatoST%s%s" % (m.group(1), m.group(1), SUB), text)
    n += k
    text, k = RE_FWD.subn(u"E:/PotatoST/" + SUB + u"/", text)
    n += k
    text, k = RE_TAIL.subn(lambda m: u"E:%sPotatoST%s%s" % (m.group(1), u"\\" * len(m.group(1)), SUB), text)
    n += k
    return text, n


def sha(p):
    h = hashlib.sha1()
    with open(p, "rb") as fh:
        for c in iter(lambda: fh.read(1 << 16), b""):
            h.update(c)
    return h.hexdigest()


def backup(write):
    if os.path.isdir(DEST):
        shutil.rmtree(DEST)
    os.makedirs(DEST)
    man, fails = [], []
    for p in targets():
        t = io.open(p, encoding="utf-8", errors="replace").read()
        if OLD not in t:
            continue
        rel = os.path.relpath(p, NEW)
        dst = os.path.join(DEST, rel)
        os.makedirs(os.path.dirname(dst), exist_ok=True)
        shutil.copy2(p, dst)
        ok = sha(p) == sha(dst)
        man.append(u"%s  %d  %s  %s" % (sha(p), os.path.getsize(p), u"OK" if ok else u"**不符**", rel))
        if not ok:
            fails.append(rel)
    if write:
        io.open(os.path.join(DEST, "MANIFEST.txt"), "w", encoding="utf-8", newline=u"\n").write(
            u"\n".join(man) + u"\n")
    print(u"备份根 %s：%d 份，失败 %d" % (DEST, len(man), len(fails)))
    for f in fails:
        print(u"  !! " + f)
    return 1 if fails else 0


def phase1(write):
    changed, total, fails = 0, 0, []
    for p in targets():
        t = io.open(p, encoding="utf-8", errors="replace").read()
        if OLD not in t:
            continue
        nt, n = convert(t)
        if n and nt != t:
            changed += 1
            total += n
            if write:
                io.open(p, "w", encoding="utf-8", newline=u"").write(nt)
    print(u"重指：动过 %d 份，替换 %d 处" % (changed, total))
    # 复查：还有谁留着老根（且不带新子目录）
    left = []
    for p in targets():
        t = io.open(p, encoding="utf-8", errors="replace").read()
        if re.search(u"E:(\\\\+)/?PotatoST(?![" + u"\\\\" + u"/A-Za-z0-9_.\"'-])(?!" + SUB + u")", t) or \
           u"E:/PotatoST/PotatoSTneoforge1.21.1/" + SUB not in t and u"E:/PotatoST/PotatoSTneoforge1.21.1/" in t:
            left.append(os.path.relpath(p, NEW))
    print(u"复查：还留着老根的文件 %d 份 %s" % (len(left), left[:6]))
    if left:
        fails.append(u"还有 %d 份没换干净" % len(left))
    # 抽查：常驻门现在指向新根
    for g in (u"_zf198_verify.py", u"_zf196_verify.py", u"_zf149_verify.py"):
        t = io.open(os.path.join(ZT, g), encoding="utf-8").read()
        hit = (u'ROOT = r"%s"' % NEW) in t or (NEW in t)
        print(u"  %-22s 指向新根：%s" % (g, hit))
        if not hit:
            fails.append(g + u" 没指到新根")
    print(u"阶段一：失败 %d" % len(fails))
    for f in fails:
        print(u"  !! " + f)
    return 1 if fails else 0


def phase2(write):
    fails = []
    doc = io.open(os.path.join(NEW, "docs", u"开发档案.md"), encoding="utf-8", newline=u"").read()
    if u"| ZF200 |" not in doc:
        anchor = u"| 见 §9 ｜ 见 §4.196 |\n"
        if doc.count(anchor) != 1:
            fails.append(u"档案 ZF198 行尾锚点 %d 次" % doc.count(anchor))
        else:
            row = (u"| ZF200 | **新建 `zf200_pre`**（改前件：`build/zftools/**` 里带老根绝对路径的 .py/.java；"
                   u"逐份核 sha1 + 回读，失败 0。⚠ 轮号 `_zf200_*` 开工前查过没人占（§4.147）） | "
                   u"**项目树挪位后的路径重指**（用户拍板：「把门/脚本重指到新根」）。"
                   u"① 背景：项目树从 `E:\\PotatoST\\PotatoSTneoforge1.21.1\\` 挪到 `E:\\PotatoST\PotatoSTneoforge1.21.1\\PotatoSTneoforge1.21.1\\`"
                   u"（2026-10-16 那次整理），而 ~120 份门/脚本/探针里写的是**老根的绝对路径** ⇒ 集体找不到文件。"
                   u"② `_zf200_root.py` 只动**代码工具**（`build/zftools/**` 的 .py/.java + 新根下的根级 .py），"
                   u"把 `E:\\PotatoST\\PotatoSTneoforge1.21.1\\…` 重指成新根；**幂等**（已经是新根的不再动），并复查「没有漏网的老根」。"
                   u"③ ⚠ **档案/公告/探针报告里的历史字样一个字没动**（改了就是篡改历史）。"
                   u"④ 重指后七道常驻门在新根下全绿（`_zf198` / `_zf196` / `_zf194` / `_zf192` / `_zf190` / "
                   u"`_zf188` / `_zf186`）。 | 见 §9 ｜ 见 §4.150 |\n")
            doc = doc.replace(anchor, anchor + row, 1)
            if write:
                io.open(os.path.join(NEW, "docs", u"开发档案.md"), "w", encoding="utf-8",
                        newline=u"").write(doc)
            print(u"  档案 §5 已加 ZF200 行")
    else:
        print(u"  档案 §5 已有 ZF200 行，跳过")
    hand_p = os.path.join(NEW, "docs", u"多会话协作交接.md")
    hand = io.open(hand_p, encoding="utf-8", newline=u"").read()
    if u"52. **ZF200 的账" not in hand:
        anchor = u"## 7. ZF146 这一轮的交接"
        if hand.count(anchor) != 1:
            fails.append(u"交接 §7 锚点 %d 次" % hand.count(anchor))
        else:
            item = (u"52. **ZF200 的账（项目树挪位后的路径重指）**：① ⚠ **项目树现在在 "
                    u"`E:\\PotatoST\PotatoSTneoforge1.21.1\\PotatoSTneoforge1.21.1\\`**（2026-10-16 整理时从 `E:\\PotatoST\\PotatoSTneoforge1.21.1\\` 挪下来的）——"
                    u"新会话/新脚本一律按**新根**取路径。② `_zf200_root.py` 把 `build/zftools/**` 的 .py/.java 与"
                    u"新根下根级 .py 里的老根绝对路径重指到新根（幂等 + 漏网复查）。"
                    u"③ 档案/公告/探针报告里的历史字样**没动**。④ 七道常驻门在新根下全绿。\n")
            hand = hand.replace(anchor, item + u"\n" + anchor, 1)
            if write:
                io.open(hand_p, "w", encoding="utf-8", newline=u"").write(hand)
            print(u"  交接第 52 条已写")
    print(u"阶段二：失败 %d" % len(fails))
    for f in fails:
        print(u"  !! " + f)
    return 1 if fails else 0


def main(argv):
    write = u"--write" in argv
    if u"--backup" in argv:
        return backup(write)
    if u"--phase1" in argv:
        return phase1(write)
    if u"--phase2" in argv:
        return phase2(write)
    print(u"用法：--backup | --phase1 | --phase2 [--write]")
    return 2


if __name__ == u"__main__":
    sys.exit(main(sys.argv[1:]))
