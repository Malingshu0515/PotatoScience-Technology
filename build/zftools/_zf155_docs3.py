# -*- coding: utf-8 -*-
u"""_zf155_docs3.py —— 档案 §5 的 ZF155 行里补上活体键数（`_zf139_verify.py` 会查这一条）。

判据原文：`check(u"594 键" in doc or u"594 键 × 4" in doc, u"档案里写着键数 594")`
—— 键数跟平到 594 之后，**档案里也得有这个数**（活体数字纪律）。

跑法：python build\\zftools\\_zf155_docs3.py [--write]
"""
import io
import os
import sys

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

ROOT = r"E:\PotatoST"
DOC = os.path.join(ROOT, "docs", "开发档案.md")
OLD = u"① 新增物品 `potato_s_t:universal_upgrade_template`（原版 `SmithingTemplateItem` 子类，"
NEW = (u"① 新增物品 `potato_s_t:universal_upgrade_template`（原版 `SmithingTemplateItem` 子类，"
       u"四语言键数随之 **587 → 594 键**、lzh 589 → **596**，")


def main(argv):
    write = u"--write" in argv
    text = io.open(DOC, encoding="utf-8", newline="").read()
    if u"594 键" in text:
        print(u"  [跳过] 档案里已经有「594 键」（幂等）")
        return 0
    if text.count(OLD) != 1:
        print(u"!! 锚点命中 %d 次" % text.count(OLD))
        return 1
    print(u"待插入：%s" % NEW[:80])
    if not write:
        print(u"（没加 --write，只算不写）")
        return 0
    io.open(DOC, u"w", encoding="utf-8", newline=u"").write(text.replace(OLD, NEW, 1))
    print(u"已落盘")
    return 0


if __name__ == u"__main__":
    sys.exit(main(sys.argv[1:]))
