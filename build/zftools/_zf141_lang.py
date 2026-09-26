# -*- coding: utf-8 -*-
r"""_zf141_lang.py —— 四语言加 **4 个键**（三件工具名 + 一句共用的 Shift 说明）。

用户原话：「还有几个星璨钢的工具你自己写一下呗」+「配方就是原版工具一样」。
三件新工具各有一个名字键；技能只有一条「与夜同频：夜晚采掘与攻击不消耗耐久」，
三把共用 ⇒ **只加一个说明键**，不复制三份（§11.4）。

键数：483 → **487**（4 个 × 四语言）。
⚠ 键数是**活体数字**，全工程有二十多份常驻门按源码文本钉着它 ⇒ 改完必须跑
  `_zf141_gatefix.py` 跟平（与 ZF139 同一套做法）。

四个键的值（四语言都写全；日语沿用既有的「星燦鋼」写法，俄语沿用「звёздной стали」）：
  item.potato_s_t.star_steel_sword      星璨钢剑 / Star Steel Sword / 星燦鋼の剣 / Меч из звёздной стали
  item.potato_s_t.star_steel_pickaxe    星璨钢镐 / Star Steel Pickaxe / 星燦鋼のツルハシ / Кирка из звёздной стали
  item.potato_s_t.star_steel_hoe        星璨钢锄 / Star Steel Hoe / 星燦鋼のクワ / Мотыга из звёздной стали
  tooltip.potato_s_t.star_steel_tool.1  夜晚采掘与攻击不消耗耐久。1192 耐久，挖掘等级钻石（三把共用）

跑法：python build\zftools\_zf141_lang.py
"""
import io
import json
import os
import sys

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

LANG = r"E:\PotatoST\src\main\resources\assets\potato_s_t\lang"
KEYS_EXPECT = 487
KEYS_BEFORE = 483

# 名字键：插在斧子名那一行**之后**
NAME_ROWS = {
    "zh_cn": [
        u'  "item.potato_s_t.star_steel_sword": "星璨钢剑",',
        u'  "item.potato_s_t.star_steel_pickaxe": "星璨钢镐",',
        u'  "item.potato_s_t.star_steel_hoe": "星璨钢锄",',
    ],
    "en_us": [
        u'  "item.potato_s_t.star_steel_sword": "Star Steel Sword",',
        u'  "item.potato_s_t.star_steel_pickaxe": "Star Steel Pickaxe",',
        u'  "item.potato_s_t.star_steel_hoe": "Star Steel Hoe",',
    ],
    "ja_jp": [
        u'  "item.potato_s_t.star_steel_sword": "星燦鋼の剣",',
        u'  "item.potato_s_t.star_steel_pickaxe": "星燦鋼のツルハシ",',
        u'  "item.potato_s_t.star_steel_hoe": "星燦鋼のクワ",',
    ],
    "ru_ru": [
        u'  "item.potato_s_t.star_steel_sword": "Меч из звёздной стали",',
        u'  "item.potato_s_t.star_steel_pickaxe": "Кирка из звёздной стали",',
        u'  "item.potato_s_t.star_steel_hoe": "Мотыга из звёздной стали",',
    ],
}

# 说明键：插在斧子说明第 3 行**之后**（与斧子那三行挨着，一眼能看出是同一条技能）
TIP_ROW = {
    "zh_cn": u'  "tooltip.potato_s_t.star_steel_tool.1": '
              u'"夜晚采掘与攻击不消耗耐久。1192 耐久，挖掘等级钻石",',
    "en_us": u'  "tooltip.potato_s_t.star_steel_tool.1": '
              u'"No durability loss from mining or attacking at night. '
              u'1192 durability, diamond mining level",',
    "ja_jp": u'  "tooltip.potato_s_t.star_steel_tool.1": '
              u'"夜間は採掘と攻撃で耐久を消費しない。耐久 1192、採掘レベルはダイヤ相当",',
    "ru_ru": u'  "tooltip.potato_s_t.star_steel_tool.1": '
              u'"Ночью добыча и атаки не расходуют прочность. '
              u'Прочность 1192, уровень добычи — алмазный",',
}

ANCHOR_NAME = u'"item.potato_s_t.star_steel_axe":'
ANCHOR_TIP = u'"tooltip.potato_s_t.star_steel_axe.3":'

fails, notes = [], []


def main():
    for loc in ("zh_cn", "en_us", "ja_jp", "ru_ru"):
        path = os.path.join(LANG, loc + ".json")
        text = io.open(path, encoding="utf-8", newline="").read()
        # ⚠ 换行风格照原文件（本工程这些 lang 是 LF；照抄文件自己的才不会整份重写 diff）
        nl = u"\r\n" if u"\r\n" in text else u"\n"
        lines = text.split(nl)

        before = json.loads(text)
        if len(before) != KEYS_BEFORE:
            fails.append(u"%s 加之前是 %d 键，期望 %d ⇒ 停手（别人可能刚改过）"
                         % (loc, len(before), KEYS_BEFORE))
            continue

        # 每个锚点必须**恰好命中一行**
        for anchor, label in ((ANCHOR_NAME, u"斧子名"), (ANCHOR_TIP, u"斧子说明第 3 行")):
            hit = [i for i, l in enumerate(lines) if anchor in l]
            if len(hit) != 1:
                fails.append(u"%s 的锚点「%s」命中 %d 行（应为 1）" % (loc, label, len(hit)))

        idx_name = [i for i, l in enumerate(lines) if ANCHOR_NAME in l]
        idx_tip = [i for i, l in enumerate(lines) if ANCHOR_TIP in l]
        if len(idx_name) != 1 or len(idx_tip) != 1:
            continue

        # 先插靠后的那个，下标才不会漂
        # ⚠ 锚点是用列表推导找的 ⇒ 拿到的是**列表**，取 [0] 再用（第一版忘了，当场 TypeError）
        i_tip = idx_tip[0]
        i_name = idx_name[0]
        out = list(lines)
        out[i_tip + 1:i_tip + 1] = [TIP_ROW[loc]]
        out[i_name + 1:i_name + 1] = NAME_ROWS[loc]
        new_text = nl.join(out)

        after = json.loads(new_text)
        if len(after) != KEYS_EXPECT:
            fails.append(u"%s 加完是 %d 键，期望 %d" % (loc, len(after), KEYS_EXPECT))
            continue
        missing = set(before) - set(after)
        if missing:
            fails.append(u"%s 有键丢了：%s" % (loc, sorted(missing)[:3]))
            continue
        changed = [k for k in before if before[k] != after[k]]
        if changed:
            fails.append(u"%s 有旧键被改了值：%s" % (loc, changed[:3]))
            continue

        io.open(path, "w", encoding="utf-8", newline="").write(new_text)
        # 回读核对（写完再读一遍，不信 write 的返回值）
        back = json.loads(io.open(path, encoding="utf-8").read())
        if back != after:
            fails.append(u"%s 回读与写入不一致" % loc)
            continue
        notes.append(u"  %-6s %d → %d 键（新增 4，快捷键的值一个没动，换行 %s）"
                     % (loc, len(before), len(back), u"CRLF" if nl == u"\r\n" else u"LF"))

    print(u"四语言加键：")
    for n in notes:
        print(n)

    # ---- 全局核对：四份键集必须逐字一致 ----
    docs = {}
    for loc in ("zh_cn", "en_us", "ja_jp", "ru_ru"):
        docs[loc] = json.load(io.open(os.path.join(LANG, loc + ".json"), encoding="utf-8"))
    sets = {loc: set(d) for loc, d in docs.items()}
    base = sets["zh_cn"]
    for loc, s in sets.items():
        if s != base:
            fails.append(u"%s 的键集与 zh_cn 不一致（多 %s / 少 %s）"
                         % (loc, sorted(s - base)[:3], sorted(base - s)[:3]))
    print(u"")
    print(u"  四份键数：%s" % {loc: len(d) for loc, d in docs.items()})
    print(u"  新键四语言都在：%s"
          % all(all(k in d for k in (
              u"item.potato_s_t.star_steel_sword",
              u"item.potato_s_t.star_steel_pickaxe",
              u"item.potato_s_t.star_steel_hoe",
              u"tooltip.potato_s_t.star_steel_tool.1")) for d in docs.values()))

    print(u"")
    print(u"失败项 = %d" % len(fails))
    for f in fails:
        print(u"  !! " + f)
    return 1 if fails else 0


if __name__ == u"__main__":
    sys.exit(main())
