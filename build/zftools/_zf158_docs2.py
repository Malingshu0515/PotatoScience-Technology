# -*- coding: utf-8 -*-
u"""_zf158_docs2.py —— ZF158 文档第二笔（幂等，默认 dry-run）：

  ① 档案 §4.166 追加 ⑤：重打成品时顺带发现的两件事 ——
     · 这一版 jar 还带上了**另一条线在途的贴图**（4 张钛合金护甲图 + 重画的热力金属图）；
     · 表里管着的 8 份"粒/锭"配方在盘上但**没进 git**（ZF150 在途）。
  ② 档案 §5 的 ZF158 行补 ④⑤ 两笔（成品与全门快照对照）。

跑法：python build\\zftools\\_zf158_docs2.py [--write]
"""
import io
import os
import sys

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding=u"utf-8", errors="replace")

ROOT = r"E:\PotatoST"
DOC = os.path.join(ROOT, "docs", u"开发档案.md")
notes, fails = [], []

ADD4 = u"""
**⑤ 重打成品时顺带对出来的两件事（都记成账，不当没看见）。**
  · **这一版 jar 里还有另一条线在途的贴图**：拿新旧两份 jar 逐条目比对，
    多出来的是 4 张钛合金护甲图（`titanium_alloy_{helmet,chestplate,leggings,boots}.png`，
    共 ~11.9 KB）+ 4 个对应模型改指新图，另外 `thermal_metal.png` 由 728 B 换成 3080 B（重画）。
    那是另一条线（`_zf157_*`，贴图轮）**还没提交**的活；jar 是从工作树打的，所以照样打进去了。
    本轮**没有**提交它们（只提交自己点名的路径）。
  · **表里管着的 8 份"粒/锭"配方在盘上有、git 里没有**（`{aluminum,cobalt,nickel,silver}_{nugget,ingot_from_nuggets}.json`）
    —— ZF150 那条线的在途产物。本轮 `--write` 重出后与盘上逐字节相同（等于顺带证明它们没漂），
    但**没把它们带上车**（本轮的改动不依赖它们；上一轮带 ZF152 那 15 份是因为我的配方直接引用它们）。
"""

ADD5_OLD = (u"③ 验收：跟平后 `--write` 重出，**除 `thermal_metal.json` 一份不动**（= 表与盘的机器证明）；"
            u"`_zf45_recipes.py` 校验模式 47 条 0 失败；常驻 `_zf158_verify.py`（A 图纸 7 项 / B 表 5 项 / C 旁证 2 项 / "
            u"D 文档与成品）**全绿**，其中 B5 是「把生成器复制到临时夹重出一遍、与盘逐字节相同」。（详见 §4.166）"
            u" | 见 §9 ｜ 见 §4.166 |\n")
ADD5_NEW = (u"③ 验收：跟平后 `--write` 重出，**除 `thermal_metal.json` 一份不动**（= 表与盘的机器证明）；"
            u"`_zf45_recipes.py` 校验模式 47 条 0 失败；常驻 `_zf158_verify.py`（A 图纸 7 项 / B 表 5 项 / C 旁证 2 项 / "
            u"D 文档与成品）**20 项 0 失败**，其中 B5 是「把生成器复制到临时夹重出一遍、与盘逐字节相同」。（详见 §4.166）"
            u"④ **重打成品**：`release\\PotatoST-0.13.jar` = **5,881,011 字节 / sha1 "
            u"`c7dcd4306a9b6ef25d8d54a61d77a1b36e6c9498`**；"
            u"`_zf149_jar.py` 26/0、`_zf149_verify.py` 28/0、`_zf156_jarcheck.py` ALL OK、`_zf155_jarcheck.py` ALL OK。"
            u"⚠ 这一版**还带上了另一条线在途的贴图**（4 张钛合金护甲图 + 重画的热力金属图）—— 见 §4.166⑤。"
            u"⑤ 全门快照（`_zf158_gatediff.py` 对 ZF156 那份）：**绿 23 → 24**（多的那条就是本轮新写的 "
            u"`_zf158_verify.py`）、**红 45 → 45**（一条没多、一条没少；45 条全是历次并行留下的老账）"
            u" | 见 §9 ｜ 见 §4.166 |\n")


def main(argv):
    write = u"--write" in argv
    doc = io.open(DOC, encoding="utf-8", newline=u"").read()

    anchor = u"**④ 附带发现（不是本轮的账，记在这儿给后面的人）**："
    if u"**⑤ 重打成品时顺带对出来的两件事" in doc:
        notes.append(u"  [跳过] §4.166 ⑤（已经在，幂等）")
    elif anchor in doc:
        j = doc.find(u"\n\n", doc.find(anchor))
        doc = doc[:j] + u"\n" + ADD4 + doc[j:]
        notes.append(u"  [改] §4.166 追加 ⑤")
    else:
        fails.append(u"§4.166 ④ 锚点没找到")

    if u"**5,881,011 字节 / sha1" in doc:
        notes.append(u"  [跳过] §5 行的 ④⑤（已经在，幂等）")
    elif doc.count(ADD5_OLD) == 1:
        doc = doc.replace(ADD5_OLD, ADD5_NEW, 1)
        notes.append(u"  [改] §5 行补 ④⑤")
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
