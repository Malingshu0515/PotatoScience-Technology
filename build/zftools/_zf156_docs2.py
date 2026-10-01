# -*- coding: utf-8 -*-
u"""_zf156_docs2.py —— ZF156 文档补笔（幂等，默认 dry-run）：

  ① 档案 §4.164 追加 ⑥~⑪ 六条**本轮现场踩出来的**判据/工具雷；
  ② 档案 §5 的 ZF156 行补上"成品重打"那一笔 + 坏字符修复。

跑法：python build\\zftools\\_zf156_docs2.py [--write]
"""
import io
import os
import sys

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding=u"utf-8", errors=u"replace")

ROOT = r"E:\PotatoST"
DOC = os.path.join(ROOT, "docs", u"开发档案.md")
notes, fails, plan = [], [], []

ADD4 = u"""
**⑥ 探针报告里的判定行**没有** `[A156] ` 前缀** —— 那个前缀只打在 stdout 上（§4.50 那套）。
我的解析器第一版按 `\\[A156\\]\\s+\\[OK\\]\\s+A2` 去 match，于是**探针全绿而门全红**。
是**活体反证脚本**先咬出来的（它报"上刀后 A2 没红"，而我明明看到报告里 A2 红了）——
门与解析器的判据也要被刀咬过。现在一律按 `^\\s*\\[OK\\]\\s+A2\\b` 匹配。

**⑦ 反证刀的锚点必须跟着文件的换行符走。**
`TerminalBlockEntity.java` 是 **CRLF**（本工程少数几份；`.gitattributes` 是 `* -text`，git 不会替你转），
而刀脚本用 `newline=""` 读进来、锚点却按 `\\n` 写死 ⇒ K1 直接"命中 0 次"，脚本把它记成"没咬住"。
修法：读一次文件判定换行，再把锚点里的 `\\n` 全部换成它（本轮 11/11 把刀自此全中）。

**⑧ 判据要判「代码行」，不能纯 `in`。**
K3/K4/K6 第一版只是把那一行**注释掉**（`// other.removeConnection(...)`）——
字面量还在文件里，`in` 判据照样绿 ⇒「刀咬不住」。
现在有了 `code_has()`：跳过整行注释 / 块注释行，且 needle 前面出现过 `//` 也不算。
（这不是把判据放松，是**把判据修成它本来想说的意思**：这行代码在不在。）

**⑨ 同一份文件的多处替换，不能"各自基于原文排队、最后一起写"。**
`_zf156_retarget.py` 第一版就是这么写的：`_zf149_verify.py` 有三个替换，
每个都基于**同一份原文**算出结果，最后按顺序写 ⇒ **只有最后一次生效**，
docstring 与 `JAR` 两处改动当场蒸发（打包自证时才暴露）。
修法：一份文件只读一次、在同一份 text 上依次替换、最后写一次。

**⑩ 上一轮留下的文档可能带着「被吃掉的字符」。**
交接 §1 的成品行在 HEAD（`57423ee`）里就是坏的：反引号变成了 `\\`、开头那对
`` `r `` 被当转义吃掉（`release` 成了 `elease`）—— 大概率是某次用会解释反引号的通道写 markdown。
本轮按**整行重写**修好（顺手换成 0.13 的哈希/体积），并把"旧行是坏字符行"打进 notes。
教训：往 markdown 里写反引号，别走会解释反引号的通道（PowerShell 双引号串里的 `` ` `` 是转义符）。

**⑪「本轮号 = 全文最大」这种判据活不过下一轮。**
ZF155 的常驻门 E2 写的是"4.163 = 全文最大且唯一"；本轮加了 §4.164 之后它**必红**——
可 4.163 本身没有任何问题。已改成"本轮号**唯一** + 把'它之后新增的号'打出来当情报"：
真实意图是**防撞号**，不是"我这轮永远是最后一轮"。
"""

ADD5_OLD = u"| 见 §9 ｜ 见 §4.164 |\n"
ADD5_NEW = (u"⑥ **重打成品**：`release\\PotatoST-0.13.jar` = **5,865,661 字节 / "
            u"sha1 `9be8488c877baf445ae68a2d0ed385b338503b1f`**（0.13 第一次打包；"
            u"旧的 0.12 那份 `36fbc383…` 留在盘上不动）。`_zf149_jar.py` 26/0、`_zf149_verify.py` 28/0、"
            u"`_zf156_jarcheck.py` ALL OK、`_zf155_jarcheck.py` ALL OK。"
            u"⑦ ⚠ **顺手修了上一轮的一处坏字符**：交接 §1 成品行在 HEAD 里反引号已被吃成 `\\`"
            u"（`release` 写成 `elease`）—— 整行重写修好（§4.164⑩）。"
            u"⑧ ⚠ **判据跟平**：`_zf73/_zf78/_zf79_verify.py` 的 `mod_version`（0.12 → 0.13，其中 "
            u"`_zf78` 那条本来就自相矛盾）+ `_zf149_verify.py` 的成品靶子/成品名/`build\\libs` 名 + "
            u"`_zf149_jar.py` 的默认 jar 与 `mods.toml` 版本断言 + `_zf155_jarcheck.py` 的 jar 名 + "
            u"`_zf155_verify.py` 的 E2（「最大」改成「唯一」，§4.164⑪）；`_zf152_plates_gate.py` **一个字没动**、仍然全过 "
            u"| 见 §9 ｜ 见 §4.164 |\n")


def main(argv):
    write = u"--write" in argv
    doc = io.open(DOC, encoding="utf-8", newline=u"").read()

    anchor = u"**⑤ 判据修正二：格式门（无 BOM / 纯 LF）只对本轮动过的文件判。**"
    if ADD4.strip().split(u"\n")[0] in doc:
        notes.append(u"  [跳过] §4.164 的 ⑥~⑪（已经在，幂等）")
    elif anchor in doc:
        i = doc.find(anchor)
        j = doc.find(u"\n\n", i)
        doc = doc[:j] + u"\n" + ADD4 + doc[j:]
        notes.append(u"  [改] §4.164 追加 ⑥~⑪")
    else:
        fails.append(u"§4.164 的 ⑤ 那段锚点没找到")

    if u"⑥ **重打成品**" in doc:
        notes.append(u"  [跳过] §5 行尾的成品那一笔（已经在，幂等）")
    elif doc.count(ADD5_OLD) == 1:
        doc = doc.replace(ADD5_OLD, ADD5_NEW, 1)
        notes.append(u"  [改] §5 的 ZF156 行补 ⑥⑦⑧ 三笔")
    else:
        fails.append(u"§5 行尾锚点命中 %d 次" % doc.count(ADD5_OLD))

    plan.append((DOC, doc))
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
