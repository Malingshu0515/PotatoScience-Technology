# -*- coding: utf-8 -*-
r"""_rzh_fix_pass2.py —— 第二轮收口：把**两块真正的配方表**也交给 JEI。

第一轮（`_rzh_adv_trim.py`）清的是成就里的配方表；这一轮清 tooltip 里的，
判据完全一样，但**只动两块**，因为全库扫描（`_rzh_ledger_sweep.py`）显示
其余命中都不是流水账：

  · 图纸坐标（`1 3 1 ｜ 2 1 2`）、层高规则（`2×2 最高 6 层…`）、
    机器的独有规格（`8000 mB 柴油罐`、`16134 FE/t`）—— 那些是**玩家就要在
    这一屏读到的东西**，搬去 JEI 反而读不到。扫描命中不等于流水账。
  · 同一行里同一个数字出现两次，多数是"输入量 = 输出量"（`100 mB 水 → 100 mB 硫酸`），
    那是配方的**结构**，不是冗余。

真正该动的两类：
  1. `tooltip.potato_s_t.acidic_reaction_chamber` 里用 ①②③ 列出的**四条配方**
     —— 它自己的 GUI 有一套 `recipe.info.N` 逐条显示，JEI 也有；
  2. `tooltip.potato_s_t.alloy_smelter` 结尾那段**四条配方**的原料罗列。

⚠ 旧值从盘上读（`_rzh_lzh` 那套教训：手抄长句 = 再打错一次）。这里用
   "只给旧串的一个**唯一锚**、由脚本自己在值里定位并整段替换"的写法。

用法：`python build/zftools/_rzh_fix_pass2.py`
"""
from __future__ import print_function
import io
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
LANGDIR = os.path.join(ROOT, u"src", u"main", u"resources", u"assets", u"potato_s_t", u"lang")
LOCALES = [u"zh_cn", u"en_us", u"ja_jp", u"ru_ru"]

# 每条 = (语言, 键, 要删掉的锚（必须唯一出现）, 说明)
# ⚠ 锚是**整行**（含换行符），删掉整行；这样不会留下悬空的标点。
DROP_LINES = [
    # —— 酸性反应室：三条配方行（GUI 与 JEI 都有）——
    (u"zh_cn", u"tooltip.potato_s_t.acidic_reaction_chamber",
     u"用按钮选配方：① 10 mB 二氧化碳 + 1 mB 水 → 1 mB 碳酸　② 1 mB 氧气 + 1 mB 氨气 → 1 mB 硝酸\n"),
    (u"zh_cn", u"tooltip.potato_s_t.acidic_reaction_chamber",
     u"③ 10 个硫 + 100 mB 水 → 100 mB 硫酸（一批 5 秒，材料到最后一刻才扣）\n"),
    (u"en_us", u"tooltip.potato_s_t.acidic_reaction_chamber",
     u"Pick a recipe with the buttons: (1) 10 mB Carbon Dioxide + 1 mB Water -> 1 mB Carbonic Acid  (2) 1 mB Oxygen + 1 mB Ammonia -> 1 mB Nitric Acid\n"),
    (u"en_us", u"tooltip.potato_s_t.acidic_reaction_chamber",
     u"(3) 10 Sulfur + 100 mB Water -> 100 mB Sulfuric Acid (one batch takes 5 seconds, and the materials are only consumed at the very end)\n"),
    (u"ja_jp", u"tooltip.potato_s_t.acidic_reaction_chamber",
     u"ボタンでレシピを選びます：① 二酸化炭素 10 mB + 水 1 mB → 炭酸 1 mB　② 酸素 1 mB + アンモニア 1 mB → 硝酸 1 mB\n"),
    (u"ja_jp", u"tooltip.potato_s_t.acidic_reaction_chamber",
     u"③ 硫黄 10 個 + 水 100 mB → 硫酸 100 mB（1 バッチ 5 秒、材料は最後の瞬間にだけ消費されます）\n"),
    (u"ru_ru", u"tooltip.potato_s_t.acidic_reaction_chamber",
     u"Рецепт выбирается кнопками: (1) 10 mB углекислого газа + 1 mB воды → 1 mB угольной кислоты　(2) 1 mB кислорода + 1 mB аммиака → 1 mB азотной кислоты\n"),
    (u"ru_ru", u"tooltip.potato_s_t.acidic_reaction_chamber",
     u"(3) 10 серы + 100 mB воды → 100 mB серной кислоты (партия за 5 секунд, материалы списываются в самый последний момент)\n"),
]

# 整段替换：`(语言, 键, 旧尾段锚, 新尾段)` —— 用于合金炉那条（配方罗列在句末）
TAIL_SWAP = [
    (u"zh_cn", u"tooltip.potato_s_t.alloy_smelter",
     u"。配方四条：", u"。四条配方见 JEI；"),
]


def load(loc):
    p = os.path.join(LANGDIR, loc + u".json")
    with io.open(p, encoding=u"utf-8", newline=u"") as f:
        text = f.read()
    return p, text, json.loads(text)


def line_index(text):
    idx = {}
    for n, line in enumerate(text.split(u"\n")):
        s = line.lstrip()
        if s.startswith(u'"'):
            end = s.find(u'":')
            if end >= 0:
                idx[s[1:end]] = n
    return idx


def main():
    # ---- 阶段 1：校验 ----
    plans = {}
    for loc, key, anchor in DROP_LINES:
        plans.setdefault(loc, []).append((key, anchor))
    for loc, key, anchor, _newtail in TAIL_SWAP:
        plans.setdefault(loc, []).append((key, None))

    data = {}
    for loc in sorted(plans):
        path, text, d = load(loc)
        data[loc] = (path, text, d)

    # 先看"配方表还在不在"——已删过就跳过（幂等）
    todo = {}
    for loc, items in sorted(plans.items()):
        path, text, d = data[loc]
        drops = []
        for key, anchor in items:
            if anchor is None:
                continue
            v = d.get(key, u"")
            if anchor not in v:
                print(u"[跳过] %s %s：锚已不在（可能已经删过）" % (loc, key))
                continue
            if v.count(anchor) != 1:
                raise SystemExit(u"[拒绝] %s %s：锚出现 %d 次，不唯一"
                                 % (loc, key, v.count(anchor)))
            drops.append((key, anchor))
        if drops:
            todo[loc] = drops
    print(u"待删行：%s" % {k: len(v) for k, v in todo.items()})

    # ---- 阶段 2：落盘 ----
    for loc, drops in sorted(todo.items()):
        path, text, d = load(loc)
        lines = text.split(u"\n")
        idx = line_index(text)
        per_key = {}
        for key, anchor in drops:
            per_key.setdefault(key, []).append(anchor)
        for key, anchors in per_key.items():
            v = json.loads(json.dumps(d[key]))
            for a in anchors:
                v = v.replace(a, u"")
            d[key] = v
            lines[idx[key]] = u'  %s: %s,' % (json.dumps(key, ensure_ascii=False),
                                              json.dumps(v, ensure_ascii=False))
        out = u"\n".join(lines)
        if u"\r" in out:
            raise SystemExit(u"[拒绝] %s 出现 CR" % loc)
        json.loads(out)
        io.open(path, u"w", encoding=u"utf-8", newline=u"\n").write(out)
        print(u"%-6s 删了 %d 个键里的配方行" % (loc, len(per_key)))

    # ---- 阶段 3：合金炉尾段 ----
    for loc, key, anchor, newtail in TAIL_SWAP:
        path, text, d = load(loc)
        v = d.get(key, u"")
        if anchor not in v:
            print(u"[跳过] %s %s：尾段锚已不在" % (loc, key))
            continue
        if v.count(anchor) != 1:
            raise SystemExit(u"[拒绝] %s %s：尾锚不唯一" % (loc, key))
        head, _, tail = v.partition(anchor)
        # 尾段以「）」或「)」结尾 —— 保留它，中间那段配方罗列换掉
        keep = u"）" if tail.endswith(u"）") else (u")" if tail.endswith(u")") else u"")
        lines = text.split(u"\n")
        idx = line_index(text)
        nv = head + newtail + keep
        d[key] = nv
        lines[idx[key]] = u'  %s: %s,' % (json.dumps(key, ensure_ascii=False),
                                          json.dumps(nv, ensure_ascii=False))
        out = u"\n".join(lines)
        json.loads(out)
        io.open(path, u"w", encoding=u"utf-8", newline=u"\n").write(out)
        print(u"%-6s %s 尾段已换成「%s」" % (loc, key, newtail))

    # ---- 复读 ----
    print(u"\n===== 写后复读 =====")
    bad = 0
    for loc in sorted(plans):
        path, text, d = load(loc)
        for key in set(k for k, _ in plans[loc]):
            v = d.get(key, u"")
            for needle in (u"①", u"(1) ", u"配方四条：", u"recipes: (1)"):
                if needle in v:
                    bad += 1
                    print(u"[错] %s %s 里还有 %r" % (loc, key, needle))
            if u"\n\n" in v or v.endswith(u"\n"):
                bad += 1
                print(u"[错] %s %s 出现了空行/尾换行" % (loc, key))
    print(u"复读 %s" % (u"干净" if bad == 0 else u"%d 处问题" % bad))

    # ---- 结构 ----
    sets = dict((l, set(load(l)[2])) for l in LOCALES)
    base = sets[u"zh_cn"]
    for l in LOCALES:
        if sets[l] != base:
            bad += 1
            print(u"[错] %s 键集与 zh_cn 不一致" % l)
    print(u"四语键集 %s（各 %d）" % (u"一致" if bad == 0 else u"有问题", len(base)))
    return 1 if bad else 0


if __name__ == u"__main__":
    sys.exit(main())
