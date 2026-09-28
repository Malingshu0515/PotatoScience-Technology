# -*- coding: utf-8 -*-
u"""_zf153_lang.py —— 振金剑的五语言键（0.12 ZF153）

加 7 个键 × 5 份语言：
    item.potato_s_t.vibranium_sword        物品名
    tooltip.potato_s_t.vibranium_sword.1   数值（无法破坏 / 24 伤害 / 1.4 攻速 / 附魔权重 1）
    tooltip.potato_s_t.vibranium_sword.2   手持免疫（凋零 / 缓慢 / 挖掘疲劳）
    tooltip.potato_s_t.vibranium_sword.3   招式（Shift+右键猛击地面 / 6x6 击飞 / n+12 / 失明 4s / 缓慢 4s / 冷却 6s）

纪律：
  ① **键集合五份必须完全一致**（zh/en/ja/ru 四份 + lzh；lzh 另有 language.name/region 两键，
     所以它是 585 而不是 583 —— 这是它一直以来的样子，不是本轮加的）。
  ② **先证明我的写回器与盘上格式逐字节一致**（拿原文件 parse→dump 比一遍），
     再动手插键；否则一插就会把整份文件的排版/转义洗一遍，别人的 diff 就废了。
  ③ 插键位置照现有**分组**（不是字典序）：物品名跟在 `vibranium_ingot` 后面，
     三行说明跟在 `star_steel_sword.3` 后面（那一段就是工具说明区）。
  ④ 文案口径照盘上同类：工具说明是**陈述事实**（「夜晚采掘与攻击不消耗耐久。1192 耐久…」），
     不是套装那种抒情文案（ZF137 用户对"套装说明"的要求）；lzh 用文言（「夜則採掘…」）。

跑法：python build\\zftools\\_zf153_lang.py
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
CODES = [u"zh_cn", u"en_us", u"ja_jp", u"ru_ru", u"lzh"]

ITEM_KEY = u"item.potato_s_t.vibranium_sword"
TIP = [u"tooltip.potato_s_t.vibranium_sword.%d" % i for i in (1, 2, 3)]
NEW_KEYS = [ITEM_KEY] + TIP

# 插在哪：物品名插在它后面 / 三行说明插在它后面
AFTER_ITEM = u"item.potato_s_t.vibranium_ingot"
AFTER_TIP = u"tooltip.potato_s_t.star_steel_sword.3"

VALUES = {
    u"zh_cn": {
        ITEM_KEY: u"振金剑",
        TIP[0]: u"无法破坏。攻击伤害 24，攻速 1.4，几乎不与附魔台共鸣（附魔权重 1）",
        TIP[1]: u"拿在手里：免疫凋零、缓慢与挖掘疲劳 —— 那三样落不到你身上",
        TIP[2]: u"Shift + 右键猛击地面：6x6 内的所有生物（除你）被击飞，"
                 u"各受你基础伤害 + 12 点伤害，失明 4 秒、缓慢 4 秒。冷却 6 秒",
    },
    u"en_us": {
        ITEM_KEY: u"Vibranium Sword",
        TIP[0]: u"Unbreakable. 24 attack damage, 1.4 attacks per second, "
                 u"and it scarcely answers the enchanting table (enchantment weight 1)",
        TIP[1]: u"While held: immunity to Wither, Slowness and Mining Fatigue - "
                 u"none of the three can touch you",
        TIP[2]: u"Shift + right-click to slam the ground: every creature within 6x6 "
                 u"(except you) is launched, takes your base damage + 12, and is blinded "
                 u"and slowed for 4 s. 6 s cooldown",
    },
    u"ja_jp": {
        ITEM_KEY: u"ヴィブラニウムの剣",
        TIP[0]: u"壊れない。攻撃力 24、毎秒 1.4 回、エンチャントのつきは極めて悪い（エンチャント値 1）",
        TIP[1]: u"手持ちの間：衰弱・移動速度低下・採掘速度低下を無効化 —— その三つは君に届かない",
        TIP[2]: u"Shift + 右クリックで地面を叩きつける：6x6 内の自分以外の全生物を打ち上げ、"
                 u"基礎攻撃力 + 12 のダメージと 4 秒の盲目・4 秒の移動速度低下を与える。クールダウン 6 秒",
    },
    u"ru_ru": {
        ITEM_KEY: u"Меч из вибраниума",
        TIP[0]: u"Неразрушимый. 24 урона, 1.4 удара в секунду, "
                 u"и он почти не отвечает столу зачарований (вес зачарования 1)",
        TIP[1]: u"В руке: иммунитет к иссушению, замедлению и усталости - "
                 u"ни одно из трёх до вас не дотянется",
        TIP[2]: u"Shift + ПКМ — удар по земле: всех существ в области 6x6, кроме вас, "
                 u"подбрасывает, они получают ваш базовый урон + 12, слепоту и замедление "
                 u"на 4 с. Перезарядка 6 с",
    },
    u"lzh": {
        ITEM_KEY: u"振金劍",
        TIP[0]: u"不可毀。傷二十四，每秒一四，幾不與附魔臺相應（附魔權重 一）",
        TIP[1]: u"執於手者，凋零、遲緩、掘疲皆不能加",
        TIP[2]: u"Shift + 右鍵猛擊於地：六乘六之內，除己以外諸生皆被擊飛，"
                 u"各受汝基礎之傷 + 十二 點，失明四秒、遲緩四秒。冷卻六秒",
    },
}

fails, notes = [], []


def check(label, ok, detail=u""):
    print(u"  [%s] %s%s" % (u"OK" if ok else u"!!", label, (u"   " + detail) if detail else u""))
    if not ok:
        fails.append(label + (u" | " + detail if detail else u""))
    return ok


def load(code):
    p = os.path.join(LANG, code + u".json")
    raw = io.open(p, encoding="utf-8").read()
    return p, raw, json.loads(raw)


def dump(d):
    return json.dumps(d, ensure_ascii=False, indent=2) + u"\n"


def insert_after(d, anchor, pairs):
    """把 pairs（[(key, value)]）插在 anchor 这个键**后面**，保持其余顺序不变。"""
    keys = list(d.keys())
    if anchor not in keys:
        raise KeyError(anchor)
    i = keys.index(anchor) + 1
    out = {}
    for k in keys[:i]:
        out[k] = d[k]
    for k, v in pairs:
        out[k] = v
    for k in keys[i:]:
        out[k] = d[k]
    return out


def main():
    # ---------- ① 写回器必须与盘上格式逐字节一致 ----------
    print(u"① 写回器自检（parse→dump 与盘上逐字节比）")
    for code in CODES:
        p, raw, d = load(code)
        if dump(d) == raw:
            print(u"      %-6s %5d 键  逐字节一致" % (code, len(d)))
        else:
            check(u"%s 的排版/转义写回后变了" % code, False,
                  u"长度 %d → %d（**拒绝改这份文件**）" % (len(raw), len(dump(d))))
    if fails:
        return 1

    # ---------- ② 插键 ----------
    print(u"\n② 插键（五份各 +%d）" % len(NEW_KEYS))
    counts = {}
    for code in CODES:
        p, raw, d = load(code)
        before = len(d)
        vals = VALUES[code]
        check(u"%s 的 %d 条新键文案齐全" % (code, len(NEW_KEYS)),
              all(k in vals for k in NEW_KEYS))
        # 幂等：已经有了而且值一样 ⇒ 跳过
        if all(d.get(k) == vals[k] for k in NEW_KEYS):
            notes.append(u"%s 已是目标状态（幂等重跑）" % code)
            counts[code] = before
            continue
        stale = [k for k in NEW_KEYS if k in d and d[k] != vals[k]]
        if stale:
            check(u"%s 里这些键已存在且值不同（拒绝覆盖）：%s" % (code, stale), False)
            continue
        new = insert_after(d, AFTER_ITEM, [(ITEM_KEY, vals[ITEM_KEY])])
        new = insert_after(new, AFTER_TIP, [(k, vals[k]) for k in TIP])
        io.open(p, "w", encoding="utf-8", newline=u"\n").write(dump(new))
        back = json.loads(io.open(p, encoding="utf-8").read())
        counts[code] = len(back)
        check(u"%s：%d → %d 键" % (code, before, len(back)), len(back) == before + len(NEW_KEYS))
        check(u"%s 回读：%d 条键值与文案全对" % (code, len(NEW_KEYS)),
              all(back.get(k) == vals[k] for k in NEW_KEYS))

    # ---------- ③ 键集合五份一致 ----------
    print(u"\n③ 键集合一致性")
    sets = {}
    for code in CODES:
        _p, _raw, d = load(code)
        sets[code] = set(d)
    four = [u"zh_cn", u"en_us", u"ja_jp", u"ru_ru"]
    check(u"zh/en/ja/ru 四份键集合完全相同",
          len(set(frozenset(sets[c]) for c in four)) == 1,
          u" / ".join(u"%s %d" % (c, len(sets[c])) for c in four))
    check(u"lzh 与四份的差集恰好是 language.name / language.region",
          sets[u"lzh"] - sets[u"zh_cn"] == {u"language.name", u"language.region"},
          str(sorted(sets[u"lzh"] - sets[u"zh_cn"])))
    check(u"lzh 不缺任何键", not (sets[u"zh_cn"] - sets[u"lzh"]),
          str(sorted(sets[u"zh_cn"] - sets[u"lzh"])))
    check(u"四份各 %d 键（583 + %d）" % (583 + len(NEW_KEYS), len(NEW_KEYS)),
          all(len(sets[c]) == 583 + len(NEW_KEYS) for c in four),
          str({c: len(sets[c]) for c in four}))
    check(u"lzh = 585 + %d = %d 键" % (len(NEW_KEYS), 585 + len(NEW_KEYS)),
          len(sets[u"lzh"]) == 585 + len(NEW_KEYS), str(len(sets[u"lzh"])))

    # ---------- ④ 打印新键 ----------
    print(u"\n④ 新键的五语言全文")
    for k in NEW_KEYS:
        print(u"  %s" % k)
        for code in CODES:
            _p, _raw, d = load(code)
            print(u"      %-6s %s" % (code, d.get(k)))
    check(u"每份的 7 条键都不是空串",
          all(load(c)[2].get(k) for c in CODES for k in NEW_KEYS))

    print(u"\n备注：")
    for n in notes:
        print(u"  - " + n)
    print(u"失败项 = %d" % len(fails))
    for f in fails:
        print(u"  !! " + f)
    return 1 if fails else 0


if __name__ == u"__main__":
    sys.exit(main())
