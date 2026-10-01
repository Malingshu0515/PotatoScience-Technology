# -*- coding: utf-8 -*-
u"""_zf156_docs3.py —— ZF156 文档第三笔（幂等，默认 dry-run）：

  ① 档案 §4.164 追加 ⑫：判据跟平要分清"谁的账"（`_zf148_verify.py` 的 F5/F6 是本轮跟平的，
     E7 是别人 9/28 改短文案留下的）；
  ② 档案 §5 的 ZF156 行 ⑧ 那笔补上"全门快照对照"的结论与 `_zf148_verify.py` 的归属。

跑法：python build\\zftools\\_zf156_docs3.py [--write]
"""
import io
import os
import sys

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding=u"utf-8", errors=u"replace")

ROOT = r"E:\PotatoST"
DOC = os.path.join(ROOT, "docs", u"开发档案.md")
notes, fails = [], []

ADD4 = u"""
**⑫ 判据跟平时要分清「谁的账」——同一次快照里的红可能各有主人。**
本轮的 `_zf148_verify.py`（ZF148 手册门）开工前是绿的，收工时红，于是"新增的红"看起来像我的账。
打开一看是两笔：
  · **F5/F6 是本轮的**：判据写的是 `t.find("getBoolean(GIVEN_TAG)") < t.find("getBookStack(BOOK_ID)")`
    这种"某段字面量在文件里的先后"。本轮把标记搬进附件、判据抽成 `shouldGive()` 之后，
    字面量换了位置（人读行为一个字没变）⇒ 按**调用先后**重写判据（查过再取书、取到书且非空才打标记），
    强度没降；
  · **E7 是别人的**：五份 lang 里 `message.potato_s_t.guide_book.received` 的值被**另一条线**
    在 2026-09-28 15:17 改短了（`git diff` 里那五份 lang 本轮开工前就是 M 状态；
    同一份文案的生成器表没同步）⇒ 该门红在"值 vs 表不一致"，**不是本轮弄的，也没替别人改**。
全门快照对照（`_zf156_gatediff.py` 比 `_zf155_gatesnap.txt` 与 `_zf156_gatesnap.txt`）：
绿 23 / 红 44 → 绿 23 / 红 45，**唯一新增的红是 `_zf148_verify.py`，且它红在 E7**；
其余 44 条是历次并行留下的老账（本轮一条都没多）。
教训：把"新增的红"一条条打开看**归属**，别一口气算到自己头上（§4.147 同族）。
"""

ADD5_OLD = (u"`_zf155_verify.py` 的 E2（「最大」改成「唯一」，§4.164⑪）；`_zf152_plates_gate.py` **一个字没动**、仍然全过 "
            u"| 见 §9 ｜ 见 §4.164 |\n")
ADD5_NEW = (u"`_zf155_verify.py` 的 E2（「最大」改成「唯一」，§4.164⑪）、`_zf148_verify.py` 的 F5/F6"
            u"（GuideBook 重构后按语义重写）；`_zf152_plates_gate.py` **一个字没动**、仍然全过。"
            u"⑨ **全门快照对照**（`_zf156_gatediff.py`）：绿 23 / 红 44 → **绿 23 / 红 45**，"
            u"唯一新增的红是 `_zf148_verify.py`，而它红在 **E7** —— "
            u"另一条线 2026-09-28 15:17 改短了五语的 `message.potato_s_t.guide_book.received`、"
            u"没同步生成器表（本轮开工前那五份 lang 就是 M 状态，本轮一个字节没碰 lang）"
            u"| 见 §9 ｜ 见 §4.164 |\n")


def main(argv):
    write = u"--write" in argv
    doc = io.open(DOC, encoding="utf-8", newline=u"").read()

    anchor = u"**⑪「本轮号 = 全文最大」这种判据活不过下一轮。**"
    if u"**⑫ 判据跟平时要分清" in doc:
        notes.append(u"  [跳过] §4.164 ⑫（已经在，幂等）")
    elif anchor in doc:
        j = doc.find(u"\n\n", doc.find(anchor))
        doc = doc[:j] + u"\n" + ADD4 + doc[j:]
        notes.append(u"  [改] §4.164 追加 ⑫")
    else:
        fails.append(u"§4.164 ⑪ 锚点没找到")

    if u"⑨ **全门快照对照**" in doc:
        notes.append(u"  [跳过] §5 行的 ⑨（已经在，幂等）")
    elif doc.count(ADD5_OLD) == 1:
        doc = doc.replace(ADD5_OLD, ADD5_NEW, 1)
        notes.append(u"  [改] §5 行补 ⑨（全门快照对照）")
    else:
        fails.append(u"§5 行尾锚点命中 %d 次" % doc.count(ADD5_OLD))

    print(u"\n".join(notes))
    print(u"失败项 = %d" % len(fails))
    for f in fails:
        print(u"  !! " + f)
    if fails or not write:
        if not write:
            print(u"（没加 --write，只算不写）")
        return 1 if fails else 0
    io.open(DOC, u"w", encoding="utf-8", newline=u"").write(doc)
    print(u"  已写 docs\\开发档案.md")
    return 0


if __name__ == u"__main__":
    sys.exit(main(sys.argv[1:]))
