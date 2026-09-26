# -*- coding: utf-8 -*-
u"""_zf124_retarget.py —— ZF124：把**被本轮改动作废的两处判据**改准（不是放宽）

1. `_zf70_verify.py` 里根成就那条 `title_zh=u"新的开始！"`
   —— 那是"中文标题逐字等于用户原话"的判据（ZF70 立的）。用户 ZF124 亲自把标题改成了
   `PotatoS&T` ⇒ 判据的目标值跟着换。**判据本身没放宽**（仍然是"逐字等于表里那一个值"）。
   ⚠ 表里另外两条（更强劲的电源 / 入门清洁能源）一个字都不动。

2. `docs\\UpdateAnnouncement_EN.md` 的**成就树那一段**（第 233 行）
   —— 那是"当前状态"的树（玩家照着看流程），根的名字跟着改。
   ⚠ 下面第 269 行那条是 **ZF107 那轮的 changelog 记录**，属于历史，**不改**（改了就是篡改当时发生的事）。

跑法：
    python build\\zftools\\_zf124_retarget.py            # 只校验
    python build\\zftools\\_zf124_retarget.py --write    # 落盘
"""
import io
import os
import sys

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

ROOT = r"E:\PotatoST"
ZT = os.path.join(ROOT, "build", "zftools")
DOC_EN = os.path.join(ROOT, r"docs\UpdateAnnouncement_EN.md")

Z70_OLD = u'''         requirements=[["got"]],
         title_zh=u"新的开始！",'''
Z70_NEW = u'''         requirements=[["got"]],
         # ⚠ ZF124 retarget：用户把根成就的标题改成了 PotatoS&T（成就界面里那个页签的名字）
         #   ⇒ 目标值跟着换。判据没放宽：仍然是"中文标题逐字等于这里写的这一个值"。
         title_zh=u"PotatoS&T",'''

EN_OLD = u'''A New Beginning!        obtain a Micro Crusher'''
EN_NEW = u'''PotatoS&T                obtain a Micro Crusher'''

EDITS = [(os.path.join(ZT, u"_zf70_verify.py"), Z70_OLD, Z70_NEW, u"_zf70_verify 的 title_zh"),
         (DOC_EN, EN_OLD, EN_NEW, u"英文公告的成就树根节点")]


def read(p):
    return io.open(p, encoding="utf-8").read()


def write(p, text):
    io.open(p, "w", encoding="utf-8", newline=u"\n").write(text)


def main(argv):
    do_write = "--write" in argv
    fails, done, cache = [], 0, {}
    for path, old, new, label in EDITS:
        if path not in cache:
            cache[path] = read(path)
        txt = cache[path]
        if new.strip()[:40] in txt and old not in txt:
            print(u"  [跳过] %-28s（幂等）" % label)
            done += 1
            continue
        n = txt.count(old)
        if n != 1:
            fails.append(u"%s 的锚点命中 %d 次（应为 1）" % (label, n))
            continue
        cache[path] = txt.replace(old, new, 1)
        print(u"  [改]   %-28s %s" % (label, os.path.basename(path)))
        done += 1
    if fails:
        print(u"")
        print(u"锚点对不上，**一个字节都没写**：")
        for f in fails:
            print(u"  !! " + f)
        return 1
    if do_write:
        for p, txt in cache.items():
            write(p, txt)
        print(u"\n落盘：%d 个文件" % len(cache))
    else:
        print(u"\n（只校验，没落盘；加 --write 才写）")
    print(u"通过 = %d   失败 = 0" % done)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
