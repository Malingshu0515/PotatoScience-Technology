# -*- coding: utf-8 -*-
u"""_zf151_synchash.py —— 把「当前成品哈希」同步进文档（幂等）。

为什么单独一个小脚本：**哈希随重打走**，而这棵树里别的线会重打成品。
判据与落点分得很清楚：
  · **历史**（档案 §9 的 ZF149 小节、§5 表格、公告末尾那几条）—— 记的是**当时那一版**，不许改；
  · **活体**（交接 §1 的「已发布成品」行、公告 Download 段）—— 必须等于 `release\\*.sha1` 里那个。

跑法：python build\\zftools\\_zf151_synchash.py [--write]
"""
import hashlib
import io
import os
import re
import sys

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding=u"utf-8", errors="replace")

ROOT = r"E:\PotatoST"
JAR = os.path.join(ROOT, "release", u"PotatoST-0.12.jar")
HAND = os.path.join(ROOT, "docs", u"多会话协作交接.md")
ANN = os.path.join(ROOT, "docs", u"UpdateAnnouncement_EN.md")


def main(argv):
    write = u"--write" in argv
    cur = hashlib.sha1(open(JAR, "rb").read()).hexdigest()
    size = os.path.getsize(JAR)
    print(u"当前成品：%s（%s B）" % (cur, format(size, u",")))
    plan, notes = [], []

    hand = io.open(HAND, encoding=u"utf-8", newline=u"").read()
    m = re.search(u"\\| \\*\\*已发布成品\\*\\* \\|[^\\n]*", hand)
    if not m:
        print(u"!! 交接 §1 找不到「已发布成品」行")
        return 1
    row = m.group(0)
    if cur in row:
        notes.append(u"  [跳过] 交接 §1 成品行已经是当前哈希")
    else:
        new_row = (u"| **已发布成品** | `release\\PotatoST-0.12.jar` = `" + cur + u"`（"
                   + format(size, u",") + u" B，**最新一次重打**：含 ZF148 手册 / ZF149 打包 / "
                   u"**ZF151 挖掘口径修复** / ZF150 金属粒 / ZF153 振金剑）⚠ 哈希**随重打走** —— "
                   u"活体那一处（本行 + 公告 Download 段）必须等于 `release\\PotatoST-0.12.jar.sha1`，"
                   u"历史那些（档案 §9 / §5 / 公告末尾）记的是当时那一版，**不许改**（§4.159 三处联动） |")
        plan.append((HAND, hand, hand.replace(row, new_row, 1)))
        notes.append(u"  [改] 交接 §1 成品行 → %s" % cur[:12])

    ann = io.open(ANN, encoding=u"utf-8", newline=u"").read()
    a2 = re.sub(u"(`release/PotatoST-0\\.12\\.jar`\\*\\* — )[0-9,]+ bytes, sha1 `[0-9a-f]+`",
                lambda mm: mm.group(1) + format(size, u",") + u" bytes, sha1 `" + cur + u"`",
                ann, count=1)
    a2 = re.sub(u"(- sha1 `)[0-9a-f]{40}(` — `)[0-9,]+( bytes)",
                lambda mm: mm.group(1) + cur + mm.group(2) + format(size, u",") + mm.group(3),
                a2, count=1)
    if a2 != ann:
        plan.append((ANN, ann, a2))
        notes.append(u"  [改] 公告 Download 段 + ZF149 那条 → %s（%s B）" % (cur[:12], format(size, u",")))
    else:
        notes.append(u"  [跳过] 公告里已经是当前哈希（或格式没匹配上）")

    print(u"\n".join(notes))
    print(u"计划写盘 %d 份" % len(plan))
    if not write:
        print(u"（没加 --write，只算不写）")
        return 0
    for p, old, new in plan:
        io.open(p, u"w", encoding=u"utf-8", newline=u"").write(new)
        assert io.open(p, encoding=u"utf-8", newline=u"").read() == new, p
    print(u"已写盘 %d 份" % len(plan))
    return 0


if __name__ == u"__main__":
    sys.exit(main(sys.argv[1:]))
