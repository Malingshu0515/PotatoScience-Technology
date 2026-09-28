# -*- coding: utf-8 -*-
u"""_zf155_docs2.py —— 把"打包 + 跟平 + 门阵"这三笔实测账补进档案 §6 第 31 条（幂等）。

跑法：python build\\zftools\\_zf155_docs2.py [--write]
"""
import io
import os
import sys

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

ROOT = r"E:\PotatoST"
HAND = os.path.join(ROOT, "docs", "多会话协作交接.md")

ANCHOR = (u"    ④ ⚠ **本轮顺手纠了 ZF151 的一笔账**：那轮的探针挂载块把前导空行吃掉了，摘完 `PotatoST.java`\n"
          u"    比改前**多 2 行空白**，它当时记成\"别人这几分钟改的\"——其实是锚点的必然产物。本轮把 `\\n\\n`\n"
          u"    放进锚点，摘完与改前件**逐字节相同**（§4.163⑤）。")
ADD = (u"\n    ⑤ **打包**：`release/PotatoST-0.12.jar` 重打为 `b02fe30cd8aa7f9c135310439d227fed1dbbc87f`\n"
       u"    （5,863,907 B）；`_zf149_jar.py` 内部审计 **26/0 绿**（91 配方 / 594x4 + 596 键）、\n"
       u"    `_zf149_verify.py` **28/0 绿**；§4.159 三处联动（`_zf149_verify.py` 的 WANT_SHA/WANT_SIZE、\n"
       u"    公告三处 Download 提法 + 「359 classes / 91 recipes」那一句、交接 §1 成品行）全部跟平。\n"
       u"    ⑥ **活体数字跟平**：通用模板 +7 键 × 5 份 ⇒ 四语言 **587 → 594**、lzh **589 → 596**；\n"
       u"    36 份写死旧键数的门由 `_zf155_retarget.py` 跟平（只动数字、历史叙述与别的量一律不碰），\n"
       u"    另有 **3 处「比较字面量写在下一行」**的漏网由 `_zf155_retarget2.py` 补刀\n"
       u"    （`_zf73`/`_zf78`/`_zf79`）——补完之后 `_zf78` 回到 164/12、`_zf79` 回到 68/5，\n"
       u"    与 ZF148 快照里的**既有红数一模一样**（即：本轮没有把它们变得更红）。\n"
       u"    ⑦ **门阵快照**：`_zf155_gatesnap.txt`（名单比上轮多 6 道：ZF150 / ZF153 / ZF155 / ZF137 /\n"
       u"    ZF140 / ZF117_audit）。红的那批逐条看过：全是**历史遗留**（老门钉着当年那份 jar/键数/配方数，\n"
       u"    例如 `_zf93` 期望 487 键、`_zf95`/`_zf100` 期望 51 条定形配方、`_zf91` 钉着更老的成品哈希），\n"
       u"    **由本轮引入的新红 = 0**。")


def main(argv):
    write = u"--write" in argv
    text = io.open(HAND, encoding="utf-8", newline="").read()
    if u"b02fe30cd8aa7f9c135310439d227fed1dbbc87f" in text and u"由本轮引入的新红 = 0" in text:
        print(u"  [跳过] 已经补过（幂等）")
        return 0
    if text.count(ANCHOR) != 1:
        print(u"!! 锚点命中 %d 次" % text.count(ANCHOR))
        return 1
    print(u"待插入 %d 字节" % len(ADD.encode("utf-8")))
    if not write:
        print(u"（没加 --write，只算不写）")
        return 0
    io.open(HAND, u"w", encoding="utf-8", newline=u"").write(text.replace(ANCHOR, ANCHOR + ADD, 1))
    print(u"已落盘")
    return 0


if __name__ == u"__main__":
    sys.exit(main(sys.argv[1:]))
