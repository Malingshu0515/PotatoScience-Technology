# -*- coding: utf-8 -*-
u"""_zf120_lang.py —— 振金套的 5 个语言键（四语言一起加）

键（每语言各 5 个，插在 `item.potato_s_t.star_steel_boots` 那一行**后面**，
与另外两套的盔甲名字排在一起）：
    item.potato_s_t.vibranium_helmet / chestplate / leggings / boots
    tooltip.potato_s_t.vibranium_set        （Shift 说明：三条套装效果）

为什么要脚本而不是手改：
  ① 四份文件是 449 键的 JSON，手改一次要精确复现"2 空格缩进 + 冒号后 2 空格 + LF"这套格式，
     错一处 JsonCheck 才发现；脚本里的写出口径与 `_zf103_lang.py` 那批完全一致。
  ② 脚本顺手核对"改前 449 → 改后 454"、"四份文件的**键集合**完全一致"
     （少一种语言就是玩家切语言后看到原始 key）。
  ③ 幂等：重复跑不会写第二遍（第二次会报"已经在了"并退出 0 失败）。

跑法：
    python build/zftools/_zf120_lang.py            # 只校验
    python build/zftools/_zf120_lang.py --write
"""
import io
import json
import os
import sys

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

PROJ = r"E:\PotatoST"
LANG = os.path.join(PROJ, "src", "main", "resources", "assets", "potato_s_t", "lang")

ANCHOR = u'  "item.potato_s_t.star_steel_boots":'

# 每种语言 5 个键，顺序固定（写出去的行序也一样）
KEYS = [u"item.potato_s_t.vibranium_helmet",
        u"item.potato_s_t.vibranium_chestplate",
        u"item.potato_s_t.vibranium_leggings",
        u"item.potato_s_t.vibranium_boots",
        u"tooltip.potato_s_t.vibranium_set"]

TEXT = {
    u"zh_cn.json": [
        u"振金头盔",
        u"振金胸甲",
        u"振金护腿",
        u"振金靴子",
        u"振金套：全套无限耐久（永不消耗）、附魔权重 2（全游戏最低，附魔台很难刷出好东西）、自带附魔光效。"
        u"\\n基础数据与下界合金一致：护甲值 头 3 / 胸 8 / 腿 6 / 靴 3，盔甲韧性 +3，击退抗性 +0.1。"
        u"\\n穿满四件：免疫弹射物伤害，并把射来的弹射物沿原路弹回去（速度减半）；爆炸伤害减半；"
        u"免疫任何击退（含爆炸击退）。"
        u"\\n贴图暂时借用原版铁套。",
    ],
    u"en_us.json": [
        u"Vibranium Helmet",
        u"Vibranium Chestplate",
        u"Vibranium Leggings",
        u"Vibranium Boots",
        u"Vibranium set: unbreakable (durability is never spent), enchantment weight 2 - the lowest in the game, "
        u"so the enchanting table rarely offers anything good - and a built-in enchantment glint."
        u"\\nBase stats match netherite: armour 3 helmet / 8 chestplate / 6 leggings / 3 boots, "
        u"armour toughness +3, knockback resistance +0.1."
        u"\\nWith all four pieces: immune to projectile damage, and incoming projectiles are sent straight back "
        u"the way they came (at half speed); explosion damage is halved; immune to all knockback, "
        u"explosion knockback included."
        u"\\nTextures currently borrow the vanilla iron set.",
    ],
    u"ja_jp.json": [
        u"ヴィブラニウムのヘルメット",
        u"ヴィブラニウムのチェストプレート",
        u"ヴィブラニウムのレギンス",
        u"ヴィブラニウムのブーツ",
        u"ヴィブラニウムセット：4 部位すべてが耐久無限（消費されません）。エンチャント適性は 2 で全ゲーム中最低"
        u"（エンチャント台では良いものがなかなか出ません）。最初からエンチャントの輝き付き。"
        u"\\n基本性能はネザライトと同じ：防具値はヘルメット 3 / チェストプレート 8 / レギンス 6 / ブーツ 3、"
        u"防具強度 +3、ノックバック耐性 +0.1。"
        u"\\n4 部位そろうと：投射物ダメージを無効化し、飛んできた投射物はそのままの軌道で跳ね返します（速度は半分）。"
        u"爆発ダメージは半分。あらゆるノックバック（爆発によるものを含む）を無効化。"
        u"\\nテクスチャは暫定でバニラの鉄装備を借用。",
    ],
    u"ru_ru.json": [
        u"Шлем из вибраниума",
        u"Нагрудник из вибраниума",
        u"Поножи из вибраниума",
        u"Ботинки из вибраниума",
        u"Набор вибраниума: полная неубиваемость (прочность не расходуется), вес зачарования 2 — самый низкий в игре, "
        u"поэтому стол зачаровывания редко предложит что-то стоящее; есть собственное сияние зачарования."
        u"\\nБазовые характеристики как у незерита: броня — шлем 3 / нагрудник 8 / поножи 6 / ботинки 3, "
        u"прочность брони +3, сопротивление отбрасыванию +0.1."
        u"\\nВ полном наборе: иммунитет к урону от снарядов, а сами снаряды отлетают обратно тем же путём "
        u"(на половинной скорости); урон от взрывов уменьшен вдвое; полный иммунитет к отбрасыванию, "
        u"включая отбрасывание взрывом."
        u"\\nТекстуры пока заимствованы у ванильного железного набора.",
    ],
}

BEFORE = 449          # 改前每份的键数（活体数字：写完变 454）
AFTER = 454

fails = []


def check(label, ok, extra=u""):
    if ok:
        print(u"  [OK]   " + label)
    else:
        fails.append(label)
        print(u"  [FAIL] " + label + (u"　" + extra if extra else u""))
    return ok


def read(name):
    path = os.path.join(LANG, name)
    return io.open(path, encoding="utf-8").read()


def main(argv):
    write = u"--write" in argv
    print(u"=========== ZF120 语言键：振金套 5 个 × 4 语言 ===========")

    for name in sorted(TEXT):
        text = read(name)
        raw = io.open(os.path.join(LANG, name), "rb").read()
        check(u"%s 无 BOM" % name, not raw.startswith(b"\xef\xbb\xbf"))
        check(u"%s 全是 LF（没有 CR）" % name, b"\r" not in raw)

        lines = text.split(u"\n")
        hits = [i for i, l in enumerate(lines) if l.startswith(ANCHOR)]
        if not check(u"%s 锚点行唯一（star_steel_boots）" % name, len(hits) == 1,
                     u"命中 %d 次" % len(hits)):
            continue
        at = hits[0]

        obj = json.loads(text)
        already = [k for k in KEYS if k in obj]
        if already:
            # ⚠ 幂等：这一段必须在"改前 449 键"那条**前面**。
            #   第一版把顺序写反了 ⇒ 第二次跑时键数已经是 454，"改前 449"当场报 4 条 FAIL，
            #   而这一轮的东西看起来"已经写好了"—— 假红灯比没检查更坏（§4.53 的兄弟）。
            check(u"%s 已经有全部 %d 个振金键（重复跑 ⇒ 跳过）" % (name, len(KEYS)),
                  len(already) == len(KEYS), u"只找到 %d 个：%s" % (len(already), already))
            check(u"%s 键数 = %d" % (name, AFTER), len(obj) == AFTER, u"实际 %d" % len(obj))
            continue
        check(u"%s 改前 %d 键" % (name, BEFORE), len(obj) == BEFORE, u"实际 %d" % len(obj))

        # 「1 空格 + 1 空行」的插法：直接接在锚点行后面，保持文件原有的紧凑风格
        new_lines = []
        for i, l in enumerate(lines):
            new_lines.append(l)
            if i == at:
                for k, v in zip(KEYS, TEXT[name]):
                    new_lines.append(u'  "%s":  "%s",' % (k, v))
        out = u"\n".join(new_lines)

        # 先自己验一遍：解析得开、键数对、值一字不差
        back = json.loads(out)
        if not check(u"%s 写出去能解析回来" % name, isinstance(back, dict)):
            continue
        check(u"%s 改后 %d 键" % (name, AFTER), len(back) == AFTER, u"实际 %d" % len(back))
        bad = [k for k, v in zip(KEYS, TEXT[name]) if back.get(k) != v.replace(u"\\n", u"\n")]
        check(u"%s 五个键的值与表一致" % name, not bad, u"不一致：%s" % bad)

        if write:
            with io.open(os.path.join(LANG, name), "w", encoding="utf-8", newline=u"\n") as f:
                f.write(out)
            print(u"  [写出] %s" % name)

    # 四份文件的键集合必须完全一致（少一种语言 = 玩家切语言看到原始 key）
    sets = {}
    for name in sorted(TEXT):
        o = json.loads(read(name))
        sets[name] = set(o.keys())
    base = sets[sorted(TEXT)[0]]
    for name in sorted(TEXT):
        miss = sorted(base - sets[name])
        more = sorted(sets[name] - base)
        check(u"%s 与 %s 的键集合一致（缺 %d / 多 %d）"
              % (name, sorted(TEXT)[0], len(miss), len(more)),
              not miss and not more,
              u"缺 %s 多 %s" % (miss[:3], more[:3]))

    print(u"")
    print(u"失败项 = %d" % len(fails))
    for f in fails:
        print(u"  !! " + f)
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
