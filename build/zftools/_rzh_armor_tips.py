# -*- coding: utf-8 -*-
r"""_rzh_armor_tips.py —— 装备类说明润色：去掉流水账，只留玩家真需要知道的。

用户原话：「你主要润色一下装备的介绍 尤其是钛合金这种 只写个附魔权重就行了
          耐久和修复材料完全没必要写上去 太罗嗦了」

改动（三条套装说明 × 四语言，只动 tooltip 的值，键一个不动）：
  · `titanium_alloy_set` 117 → 32：**删掉逐件耐久与护甲值、删掉修理材料**，只留附魔权重。
  · `vibranium_set`      174 → 137：删掉"基础数据与下界合金一致"那串逐件数值（下界合金是常识），
                          保留「无限耐久」——`_zf120_verify.py` 硬性要求这句在（用户原话）。
  · `star_steel_set`     294 → 228：**删掉修理材料**；保留「伤害吸收是周期性一次性护盾、
                          不提前补满」——那是用户特意要求的平衡说明（原话「护盾不要立马就恢复」），
                          不是啰嗦，不许删。

同步：`_zf120_lang.py`（振金的生成器）里振金那条也一起改，否则重跑会把文案打回。
"""
import io
import json
import sys

LANG = u"src/main/resources/assets/potato_s_t/lang/%s.json"
GEN = u"build/zftools/_zf120_lang.py"
LOCALES = [u"zh_cn", u"en_us", u"ja_jp", u"ru_ru"]
ARGS = {u"zh_cn": u"zh", u"en_us": u"en", u"ja_jp": u"ja", u"ru_ru": u"ru"}

NEW = {
    u"titanium_alloy_set": {
        u"zh_cn": u"钛合金套：附魔权重 25（金是 22）。比金更吃附魔台，也更扛打",
        u"en_us": u"Titanium Alloy set: enchantment weight 25 (gold is 22) - it takes enchantments better than gold, and takes hits better too",
        u"ja_jp": u"チタン合金セット：エンチャント適性 25（金は 22）。金よりエンチャントが乗り、打たれ強い",
        u"ru_ru": u"Титановый набор: вес зачарования 25 (у золота 22) — зачарования ложатся лучше, чем на золото, и держит удар крепче",
    },
    u"vibranium_set": {
        u"zh_cn": u"振金套：全套无限耐久、附魔权重 2（全游戏最低，附魔台很难刷出好东西）、自带附魔光效。\n"
                  u"穿满四件：免疫弹射物伤害，来弹沿原路弹回（速度减半）；爆炸伤害减半；免疫任何击退。\n"
                  u"（贴图暂时借用原版铁套）",
        u"en_us": u"Vibranium set: unbreakable, enchantment weight 2 - the lowest in the game, so the enchanting table "
                  u"rarely offers anything good - and a built-in glint.\n"
                  u"All four pieces: immune to projectiles (incoming ones bounce back at half speed); explosion damage "
                  u"halved; immune to all knockback.\n"
                  u"(Textures currently borrow the vanilla iron set)",
        u"ja_jp": u"ヴィブラニウムセット：4 部位すべて耐久無限。エンチャント適性は 2 で全ゲーム中最低"
                  u"（エンチャント台では良いものがなかなか出ません）。最初からエンチャントの輝き付き。\n"
                  u"4 部位そろうと：投射物ダメージを無効化し、飛んできた投射物は速度半分で跳ね返ります。"
                  u"爆発ダメージは半分。あらゆるノックバックを無効化。\n"
                  u"（テクスチャは暫定でバニラの鉄装備を借用）",
        u"ru_ru": u"Набор вибраниума: все четыре части неразрушимы, вес зачарования 2 — самый низкий в игре, поэтому стол "
                  u"зачаровывания редко предложит что-то стоящее; есть собственное сияние.\n"
                  u"В полном наборе: иммунитет к снарядам (летящие в вас отскакивают обратно на половинной скорости); "
                  u"урон от взрывов вдвое меньше; полный иммунитет к отбрасыванию.\n"
                  u"(Текстуры пока заимствованы у ванильного железного набора)",
    },
    u"star_steel_set": {
        u"zh_cn": u"星璨钢套：每件在夜晚获得抗性提升 I（多件也只有 I），夜晚装备耐久不消耗。\n"
                  u"穿满四件：末地永不掉耐久；主世界夜晚得力量 I、抗性提升 II，每 45 秒给 10 秒伤害吸收 III；"
                  u"末地得生命恢复 I、抗性提升 III、力量 II，每 15 秒给 12 秒伤害吸收 VI。\n"
                  u"伤害吸收是周期性一次性护盾：一轮走完（或被打空）才给下一轮，不提前补满。\n"
                  u"受虚空伤害时传送到 20×20 内最近的方块上（先给缓降、清空坠落距离）；找不到方块就与附近生物换位",
        u"en_us": u"Star Steel set: every piece grants Resistance I at night (more pieces still only I), and gear worn at "
                  u"night takes no durability damage.\n"
                  u"All four pieces: no durability loss in the End; Overworld at night - Strength I, Resistance II, "
                  u"Absorption III for 10 s every 45 s; the End - Regeneration I, Resistance III, Strength II, Absorption "
                  u"VI for 12 s every 15 s.\n"
                  u"The Absorption is a one-shot shield on a timer: no refill until the current one runs out or is knocked "
                  u"empty.\n"
                  u"Void damage teleports you to the nearest block within 20x20 (you land safely); with no block at all, it "
                  u"swaps you with a nearby mob",
        u"ja_jp": u"星燦鋼セット：各部位は夜になると耐性 I を得ます（何枚重ねても I のまま）。夜間は装備の耐久を消費しません。\n"
                  u"4 部位そろうと：エンドでは耐久が一切減らず、主世界の夜は力 I・耐性 II、45 秒ごとに 10 秒間の衝撃吸収 III。"
                  u"エンドでは再生 I・耐性 III・力 II、15 秒ごとに 12 秒間の衝撃吸収 VI。\n"
                  u"衝撃吸収は時間制の一度きりシールドで、今回分が切れるか削り切られるまで次は補充されません。\n"
                  u"ヴォイドダメージを受けると 20×20 内の最も近いブロックへ転送されます（安全に着地）。"
                  u"ブロックが無ければ近くのモブと場所を交換します",
        u"ru_ru": u"Набор звёздной стали: каждая часть даёт ночью Сопротивление I (сколько бы частей ни было — всё равно I), "
                  u"а ночью снаряжение не расходует прочность.\n"
                  u"В полном наборе: в Крае прочность не тратится вовсе; Верхний мир ночью — Сила I, Сопротивление II, "
                  u"Поглощение III на 10 с каждые 45 с; Край — Регенерация I, Сопротивление III, Сила II, Поглощение VI "
                  u"на 12 с каждые 15 с.\n"
                  u"Поглощение — одноразовый щит на таймере: пополнения нет, пока текущий не истечёт или не будет выбит.\n"
                  u"Урон от пустоты переносит вас на ближайший блок в пределах 20×20 (с безопасным приземлением); если "
                  u"блоков нет, вы меняетесь местами с ближайшим мобом",
    },
}

fails = []

# ---- 写前断言：两条"用户特意要求的说明"不许丢 ----
if u"无限耐久" not in NEW[u"vibranium_set"][u"zh_cn"]:
    fails.append(u"振金说明丢了「无限耐久」（_zf120_verify.py 硬性要求）")
if u"不提前补满" not in NEW[u"star_steel_set"][u"zh_cn"] and u"不会提前补满" not in NEW[u"star_steel_set"][u"zh_cn"]:
    fails.append(u"星璨钢说明丢了「伤害吸收不提前补满」（用户原话要求）")
for nid, table in NEW.items():
    if u"修理材料" in table[u"zh_cn"] or u"Repair material" in table[u"en_us"]:
        fails.append(u"%s：还留着修理材料" % nid)

raw, plan = {}, []
for loc in LOCALES:
    raw[loc] = io.open(LANG % loc, encoding=u"utf-8", newline=u"").read()
for loc in LOCALES:
    for nid, table in NEW.items():
        key = u'"tooltip.potato_s_t.%s"' % nid
        i = raw[loc].find(key)
        if i < 0:
            fails.append(u"%s / %s：找不到键" % (loc, nid))
            continue
        c = raw[loc].index(u":", i)
        j = raw[loc].index(u'"', c + 1)
        k = j + 1
        while True:
            if raw[loc][k] == u"\\":
                k += 2
                continue
            if raw[loc][k] == u'"':
                break
            k += 1
        old_lit = raw[loc][j:k + 1]
        new_lit = json.dumps(table[loc], ensure_ascii=False)
        if old_lit == new_lit:
            continue
        if raw[loc].count(old_lit) != 1:
            fails.append(u"%s / %s：老值出现 %d 次" % (loc, nid, raw[loc].count(old_lit)))
            continue
        plan.append((loc, old_lit, new_lit, nid, len(json.loads(old_lit)), len(table[loc])))

if fails:
    print(u"写前自检挂了，没落盘：")
    for f in fails:
        print(u"  !! " + f)
    sys.exit(1)

print(u"%-8s %-22s %s" % (u"语言", u"键", u"字数 老 → 新"))
for loc in LOCALES:
    text = raw[loc]
    for (l, old_lit, new_lit, nid, lo, ln) in [p for p in plan if p[0] == loc]:
        text = text.replace(old_lit, new_lit, 1)
        print(u"%-8s %-22s %3d → %3d" % (loc, nid, lo, ln))
    if text != raw[loc]:
        assert len(json.loads(text)) == len(json.loads(raw[loc])), u"键数变了"
        io.open(LANG % loc, u"w", encoding=u"utf-8", newline=u"").write(text)

# ---- 振金的生成器 `_zf120_lang.py` 另行同步（见 `_rzh_sync_armor_gen.py`）----
print(u"\n合计改了 %d 处（振金生成器 %s 待另同步）" % (len(plan), GEN))
