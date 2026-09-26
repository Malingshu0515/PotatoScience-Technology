# -*- coding: utf-8 -*-
r"""_rzh_lzh_fix.py —— 文言文包的**跨片术语收口**。

三份译稿是并行产出的：第 1 片译物品名、第 2 片译 tooltip/GUI、第 3 片译成就。
片内自洽，**合起来**才暴露「同一个东西两个名字」。这个脚本只做这一件事：

    把"正文里对不上物品名的写法"改成物品名那份的写法。

改哪些、不改哪些，逐条都要有理由：

  ✔ 改：胄/鎧/靴/鍁 —— 第 1 片按**原版 lzh** 的先例取的（原版就是 鐵胄/鐵鎧/鐵護腿/
        鐵鞾/鐵鍁），正文却写「頭盔/胸甲/靴子/鍬」。同一个东西两个名字，收口。
  ✔ 改：鋰電池原件 → 鋰電池元件 —— 中文原文本轮就把「原件」纠正成了「元件」
        （电子件才叫元件），文言文正文里的三处是照**旧**中文译的。
  ✔ 改：三元聚合物鋰電池 → 鋰電池 —— 方块显示名是「鋰電池」，正文却用全称。
  ✔ 改：扳手 → 扳鉗、碳粉 → 印墨 —— 同上，正文用的是中文原文的旧名字。
  ✔ 改：冶煉爐 → 合金爐 —— `gui.potato_s_t.alloy_smelter.name` 是**界面里显示的机器名**，
        必须与方块显示名一致。
  ✘ 不改：「熱金」—— 那是**图纸里的图例简写**（图例本身写明「熱力金屬」，格子放不下）；
        蓝图 ASCII 逐字照抄，名实已在图例里交代清楚。
  ✘ 不改：「柴油 / 汽油 / 海鹽 / 合金爐」在正文里的短名 —— 它们与显示名**同形**，
        不算两个名字（前缀表里列出来的那些是量词/语境差异，不是术语冲突）。

用法：`python build/zftools/_rzh_lzh_fix.py`
"""
from __future__ import print_function
import io
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
LZH = os.path.join(ROOT, u"src", u"main", u"resources", u"assets", u"potato_s_t",
                   u"lang", u"lzh.json")

# (旧写法, 新写法, 最少命中数, 只在这几个键里改 —— 空 = 全域)
FIXES = [
    # ---- 装备与工具：对齐第 1 片按原版 lzh 取的写法 ----
    (u"頭盔", u"胄", 2, []),
    (u"胸甲", u"鎧", 2, []),
    (u"靴子", u"靴", 2, []),
    # ⚠ 工具那条正文写的是「劍 / 斧 / 鍬 / 鎬 / 鋤」；物品名是「星璨鋼鍁」。
    #   只改这一处，且**只在工具那条正文里**改 —— 「鍬」在别处没出现过，
    #   但为了不给日后留"全域替换"的隐患，仍然限定在这个键。
    (u"鍬", u"鍁", 1, [u"advancements.potato_s_t.star_steel_tools.description"]),

    # ---- 本轮中文纠正过的词，文言文正文还是照旧译的 ----
    # 中文：「锂电池原件」→「锂电池元件」（电子件是元件）；文言文正文三处没跟上
    (u"鋰電池原件", u"鋰電池元件", 3, []),
    # 方块显示名是「鋰電池」；正文里两处用了全称
    (u"三元聚合物鋰電池", u"鋰電池", 2, []),

    # ---- 正文用了中文原文的旧名字 ----
    (u"扳手", u"扳鉗", 1, []),
    # ⚠⚠ 这一条**必须限键**。第一版写了全域替换，结果把**物品名**也换了：
    #    `item.potato_s_t.carbon` 的值是「碳粉」（煅烧出来的碳），而
    #    `item.potato_s_t.toner` 才是「墨粉」→「印墨」。全域替换把前者的
    #    内部子串也改成了「印墨」，碳粉和墨粉成了同一个名字。
    #    教训：**替换词若是另一个词的真子串，就必须限键**，并且事后逐条复读。
    (u"碳粉", u"印墨", 3, [
        u"tooltip.potato_s_t.electric_blast_furnace",
        u"advancements.potato_s_t.crushing.description",
        u"advancements.potato_s_t.steel.description",
    ]),

    # ---- ⚠⚠ 这里**故意没有**"把界面里的「冶煉爐」改成「合金爐」"这一条 ----
    #   我一开始写了它，理由想错了：`gui.alloy_smelter.name` 显示的是**整台成型
    #   机器**的名字，对应方块 `alloy_smelter_part`（中文原文就叫「合金冶炼炉」），
    #   不是主控（`alloy_smelter` = 「合金炉主控」）、也不是接线口。
    #   中文原文三条界面写的全是「合金冶炼炉」—— 本来就自洽，
    #   我那一条真是"没事找事"，还顺手把方块名改成了「合金合金爐」。
    #   ⇒ 这三条与方块名对齐即可，由下面的 POINT_FIX 一并收口。

    # ---- 一处漏网的旧称谓 ----
    # star_steel_set 的正文写「盔亦照及形貌之外」，而物品名是「胄」。
    # 前面把「頭盔」收口了，这个单字「盔」没被覆盖到 —— 一致性扫描换了一组
    # 关键词之后才露出来（所以扫描表要覆盖"短名/单字"这一档）。
    (u"盔亦照及", u"胄亦照及", 1, []),
]

# ---------------------------------------------------------------------------
# 定点替换：`(键, 旧子串, 新子串)` —— 只改这一个键里的这一段。
#
# ⚠ 第一版这里写的是**整值**（`(键, 旧整值, 新整值)`），结果 `status` 那条因为
#   我把整串凭记忆写错（把「储能 %s / %s FE」写成了「已激活」的截断）而拒绝执行。
#   **手抄长句等于再打错一次**。改成按子串定位：既不容易写错，报错时也只说这一小段。
# ---------------------------------------------------------------------------
POINT_FIX = [
    (u"item.potato_s_t.carbon", u"印墨", u"碳粉"),
    (u"block.potato_s_t.alloy_smelter_part", u"合金合金爐", u"合金冶煉爐"),
    # ⚠ 同一次误伤在**界面三条**里留下了尾巴：那三条在"限键"之前就被改过。
    #   限键修的是将来，修不了已经落盘的 —— 所以按同一个"叠字"子串把它们一起收掉。
    (u"gui.potato_s_t.alloy_smelter.formed", u"合金合金爐", u"合金冶煉爐"),
    (u"gui.potato_s_t.alloy_smelter.name", u"合金合金爐", u"合金冶煉爐"),
    (u"gui.potato_s_t.alloy_smelter.status", u"合金合金爐", u"合金冶煉爐"),
]

FORBIDDEN = [
    (u"鋰電池原件", u"还有旧词「鋰電池原件」（物品名是「鋰電池元件」）"),
    (u"三元聚合物鋰電池", u"还有显示名之外的全称「三元聚合物鋰電池」"),
    (u"頭盔", u"还有「頭盔」（物品名是「胄」）"),
    (u"胸甲", u"还有「胸甲」（物品名是「鎧」）"),
    (u"靴子", u"还有「靴子」（物品名是「靴」）"),
    # ⚠ 这里**不能**写「冶煉爐」——「合金冶煉爐」本来就是这个方块的正名，
    #   那样写会把正确的名字判成错的。要防的是**叠字**：替换误伤把
    #   「合金冶煉爐」变成了「合金合金爐」。
    (u"合金合金爐", u"还有叠字「合金合金爐」（替换误伤）"),
]

# 界面里显示的机器名必须与方块名一致：这三条**恰好**是「合金爐」
GUI_MUST = [u"gui.potato_s_t.alloy_smelter.formed",
            u"gui.potato_s_t.alloy_smelter.name",
            u"gui.potato_s_t.alloy_smelter.status"]


def main():
    raw = io.open(LZH, u"rb").read()
    text = raw.decode(u"utf-8")
    data = json.loads(text)
    lines = text.split(u"\n")

    # 行首键名 -> 行号
    index = {}
    for n, line in enumerate(lines):
        s = line.lstrip()
        if s.startswith(u'"'):
            end = s.find(u'":')
            if end > 0:
                index[s[1:end]] = n

    total = 0
    for old, new, need, only in FIXES:
        hits = 0
        for k, v in data.items():
            if only and k not in only:
                continue
            hits += v.count(old)
        if hits == 0:
            continue                       # 幂等：已经改过
        if hits < need:
            raise SystemExit(u"[拒绝] 「%s」只命中 %d 次，至少要有 %d 次"
                             % (old, hits, need))
        for k, v in list(data.items()):
            if only and k not in only:
                continue
            if old not in v:
                continue
            nv = v.replace(old, new)
            data[k] = nv
            lines[index[k]] = u'  %s: %s,' % (
                json.dumps(k, ensure_ascii=False), json.dumps(nv, ensure_ascii=False))
            total += 1
        print(u"「%s」-> 「%s」：命中 %d 次%s"
              % (old, new, hits, (u"（限 %d 个键）" % len(only)) if only else u""))

    if total == 0:
        print(u"没有要改的（幂等）")
    else:
        out = u"\n".join(lines)
        if u"\r" in out:
            raise SystemExit(u"[拒绝] 出现了 CR —— 必须是纯 LF")
        json.loads(out)                    # 写前先确认还是合法 JSON
        io.open(LZH, u"w", encoding=u"utf-8", newline=u"\n").write(out)
        print(u"\n改了 %d 个键" % total)

    # ---- 定点替换（修替换误伤）----
    for key, old, new in POINT_FIX:
        cur = data.get(key)
        if cur is None:
            raise SystemExit(u"[拒绝] 定点替换：盘上没有键 %s" % key)
        if old not in cur:
            if new in cur:
                continue                   # 幂等：已经换过了
            raise SystemExit(u"[拒绝] 定点替换 %s：值里既没有 %r，也没有 %r\n   %r"
                             % (key, old, new, cur))
        data[key] = cur.replace(old, new)
        lines[index[key]] = u'  %s: %s,' % (
            json.dumps(key, ensure_ascii=False),
            json.dumps(data[key], ensure_ascii=False))
        print(u"定点替换 %s：%r -> %r" % (key, old, new))
    if POINT_FIX:
        io.open(LZH, u"w", encoding=u"utf-8", newline=u"\n").write(u"\n".join(lines))

    # 复读 + 禁用词
    print(u"\n===== 写后复读 =====")
    data2 = json.load(io.open(LZH, encoding=u"utf-8"))
    print(u"键数 %d（原 %d）  %s" % (len(data2), len(data),
                                    u"OK" if len(data2) == len(data) else u"变了！"))
    bad = 0
    for needle, why in FORBIDDEN:
        hits = [k for k, v in data2.items() if needle in v]
        if hits:
            bad += 1
            print(u"[错] %s" % why)
            for k in hits[:4]:
                print(u"     %s" % k)
        else:
            print(u"OK   %s 里已经没有「%s」" % (u"lzh", needle))

    # 误伤复检：碳粉（carbon）与墨粉（toner）必须是两个名字
    c, t = data2.get(u"item.potato_s_t.carbon"), data2.get(u"item.potato_s_t.toner")
    if c == t:
        bad += 1
        print(u"[错] 碳粉与墨粉同名了：两件都是 %r —— 替换误伤" % c)
    else:
        print(u"OK   碳粉 %r / 墨粉 %r 是两个名字" % (c, t))

    # 界面名与方块名一致：这三条显示的是**整台机器**，名字 = `alloy_smelter_part`
    # 的显示名「合金冶煉爐」（中文原文即「合金冶炼炉」）。
    for k in GUI_MUST:
        v = data2.get(k)
        if u"合金冶煉爐" not in v:
            bad += 1
            print(u"[错] %s 里没有「合金冶煉爐」：%r" % (k, v))
        else:
            print(u"OK   %s 与方块名一致（合金冶煉爐）" % k.split(u".")[-1])

    print(u"\n%s" % (u"全部通过" if bad == 0 else u"有 %d 处问题" % bad))
    return 1 if bad else 0


if __name__ == u"__main__":
    sys.exit(main())
