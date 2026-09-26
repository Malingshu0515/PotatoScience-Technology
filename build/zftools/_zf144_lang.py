# -*- coding: utf-8 -*-
r'''_zf144_lang.py —— 四语言加 **5 个键**（锹名 + 剑的三行说明 + 剑气死亡文案）。

用户原话：「锹现在放用户素材了 然后剑你看看能不能再加个特殊技能」。
  · 锹：只要一个名字键（技能与镐/锄共用 `tooltip.potato_s_t.star_steel_tool.1`）；
  · 剑：加了第二个技能 ⇒ 它**不再共用**那一句，改用自己的一组三行
    （`tooltip.potato_s_t.star_steel_sword.1~3`）；
  · 剑气用的是**本工程第二个自定义伤害类型** ⇒ 多一个死亡文案键
    `death.attack.potato_s_t.star_steel_slash`。

键数：487 → **492**（5 个 × 四语言）。
⚠ 键数是活体数字，全工程二十多份常驻门按源码文本钉着它 ⇒ 改完必须跑
  `_zf144_gatefix.py` 跟平。

跑法：python build\zftools\_zf144_lang.py
'''
import io
import json
import os
import sys

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

LANG = r"E:\PotatoST\src\main\resources\assets\potato_s_t\lang"
KEYS_BEFORE = 487
KEYS_AFTER = 492

# ---- 锚点：插在哪一行之后 ----
ANCHOR_HOE = u'"item.potato_s_t.star_steel_hoe":'          # 锹名插在锄名之后
ANCHOR_TIP = u'"tooltip.potato_s_t.star_steel_tool.1":'    # 剑那三行插在共用那句之后
ANCHOR_DEATH = u'"death.attack.potato_s_t.vibranium_reflect":'  # 死亡文案插在振金那条之后

ROWS = {
    "zh_cn": {
        "shovel": u'  "item.potato_s_t.star_steel_shovel": "星璨钢锹",',
        "tips": [
            u'  "tooltip.potato_s_t.star_steel_sword.1": '
            u'"夜晚采掘与攻击不消耗耐久。1192 耐久，挖掘等级钻石",',
            u'  "tooltip.potato_s_t.star_steel_sword.2": '
            u'"Shift + 右键：扣 100 点耐久，朝面向斩出一道 8 格长的星辉剑气（15 秒冷却）",',
            u'  "tooltip.potato_s_t.star_steel_sword.3": '
            u'"剑气贯穿沿途的所有敌人，各受 12 点伤害，并被星辉照亮 5 秒",',
        ],
        "death": u'  "death.attack.potato_s_t.star_steel_slash": "%1$s被星光贯穿",',
    },
    "en_us": {
        "shovel": u'  "item.potato_s_t.star_steel_shovel": "Star Steel Shovel",',
        "tips": [
            u'  "tooltip.potato_s_t.star_steel_sword.1": '
            u'"No durability loss from mining or attacking at night. '
            u'1192 durability, diamond mining level",',
            u'  "tooltip.potato_s_t.star_steel_sword.2": '
            u'"Shift + right-click: costs 100 durability to send an 8-block starlight slash '
            u'along your facing (15 s cooldown)",',
            u'  "tooltip.potato_s_t.star_steel_sword.3": '
            u'"The slash pierces every enemy along its path for 12 damage and lights them up '
            u'for 5 s",',
        ],
        "death": u'  "death.attack.potato_s_t.star_steel_slash": "%1$s was pierced by starlight",',
    },
    "ja_jp": {
        "shovel": u'  "item.potato_s_t.star_steel_shovel": "星燦鋼のシャベル",',
        "tips": [
            u'  "tooltip.potato_s_t.star_steel_sword.1": '
            u'"夜間は採掘と攻撃で耐久を消費しない。耐久 1192、採掘レベルはダイヤ相当",',
            u'  "tooltip.potato_s_t.star_steel_sword.2": '
            u'"Shift + 右クリック：耐久を 100 消費し、向いている方向へ長さ 8 ブロックの'
            u'星輝斬を放つ（クールダウン 15 秒）",',
            u'  "tooltip.potato_s_t.star_steel_sword.3": '
            u'"斬撃は進路上のすべての敵を貫き、それぞれに 12 のダメージを与え、'
            u'5 秒間発光させる",',
        ],
        "death": u'  "death.attack.potato_s_t.star_steel_slash": "%1$sは星光に貫かれた",',
    },
    "ru_ru": {
        "shovel": u'  "item.potato_s_t.star_steel_shovel": "Лопата из звёздной стали",',
        "tips": [
            u'  "tooltip.potato_s_t.star_steel_sword.1": '
            u'"Ночью добыча и атаки не расходуют прочность. '
            u'Прочность 1192, уровень добычи — алмазный",',
            u'  "tooltip.potato_s_t.star_steel_sword.2": '
            u'"Shift + ПКМ: расходует 100 прочности и посылает звёздный разрез длиной '
            u'8 блоков по направлению взгляда (перезарядка 15 с)",',
            u'  "tooltip.potato_s_t.star_steel_sword.3": '
            u'"Разрез пробивает всех врагов на пути, нанося каждому 12 урона '
            u'и подсвечивая их на 5 с",',
        ],
        "death": u'  "death.attack.potato_s_t.star_steel_slash": '
                 u'"%1$s пронзён звёздным светом",',
    },
}

fails, notes = [], []


def main():
    for loc in ("zh_cn", "en_us", "ja_jp", "ru_ru"):
        path = os.path.join(LANG, loc + ".json")
        text = io.open(path, encoding="utf-8", newline="").read()
        nl = u"\r\n" if u"\r\n" in text else u"\n"
        lines = text.split(nl)
        before = json.loads(text)
        if len(before) != KEYS_BEFORE:
            fails.append(u"%s 加之前是 %d 键，期望 %d ⇒ 停手（别人可能刚改过）"
                         % (loc, len(before), KEYS_BEFORE))
            continue

        idx = {}
        for key, anchor in (("hoe", ANCHOR_HOE), ("tip", ANCHOR_TIP), ("death", ANCHOR_DEATH)):
            hit = [i for i, l in enumerate(lines) if anchor in l]
            if len(hit) != 1:
                fails.append(u"%s 的锚点 %s 命中 %d 行（应为 1）" % (loc, anchor, len(hit)))
            else:
                idx[key] = hit[0]
        if len(idx) != 3:
            continue

        out = list(lines)
        # 从后往前插，下标才不会漂
        for key, block in (("death", [ROWS[loc]["death"]]),
                           ("tip", ROWS[loc]["tips"]),
                           ("hoe", [ROWS[loc]["shovel"]])):
            i = idx[key]
            out[i + 1:i + 1] = block
        new_text = nl.join(out)

        after = json.loads(new_text)
        if len(after) != KEYS_AFTER:
            fails.append(u"%s 加完是 %d 键，期望 %d" % (loc, len(after), KEYS_AFTER))
            continue
        if set(before) - set(after):
            fails.append(u"%s 有键丢了：%s" % (loc, sorted(set(before) - set(after))[:3]))
            continue
        changed = [k for k in before if before[k] != after[k]]
        if changed:
            fails.append(u"%s 有旧键被改了值：%s" % (loc, changed[:3]))
            continue
        io.open(path, "w", encoding="utf-8", newline="").write(new_text)
        back = json.loads(io.open(path, encoding="utf-8").read())
        if back != after:
            fails.append(u"%s 回读与写入不一致" % loc)
            continue
        notes.append(u"  %-6s %d → %d 键（新增 5，旧值一个没动，换行 %s）"
                     % (loc, len(before), len(back), u"CRLF" if nl == u"\r\n" else u"LF"))

    print(u"四语言加键：")
    for n in notes:
        print(n)

    docs = {}
    for loc in ("zh_cn", "en_us", "ja_jp", "ru_ru"):
        docs[loc] = json.load(io.open(os.path.join(LANG, loc + ".json"), encoding="utf-8"))
    base = set(docs["zh_cn"])
    for loc, d in docs.items():
        if set(d) != base:
            fails.append(u"%s 的键集与 zh_cn 不一致" % loc)
    print(u"")
    print(u"  四份键数：%s" % {loc: len(d) for loc, d in docs.items()})
    NEW = ["item.potato_s_t.star_steel_shovel",
           "tooltip.potato_s_t.star_steel_sword.1", "tooltip.potato_s_t.star_steel_sword.2",
           "tooltip.potato_s_t.star_steel_sword.3",
           "death.attack.potato_s_t.star_steel_slash"]
    print(u"  五个新键四语言都在：%s"
          % all(all(k in d for k in NEW) for d in docs.values()))
    print(u"")
    print(u"失败项 = %d" % len(fails))
    for f in fails:
        print(u"  !! " + f)
    return 1 if fails else 0


if __name__ == u"__main__":
    sys.exit(main())
