# -*- coding: utf-8 -*-
"""_zf137_rewrite.py —— ZF137：把套装说明改成**文案**，别写成开发笔记

用户原话：「像这种介绍其实没必要这么啰嗦 尤其是暂用原版贴图...死亡后显示 这种给"我"
而不是玩家看的 可以改掉 换成高大上一点的科幻浪漫一点的介绍 不要太俗」

## 要删的（给"我"看的，不是给玩家看的）

1. `（贴图暂时借用原版铁套）` —— **开发笔记**。玩家不需要知道我还没画完贴图；
   这种东西该留在 `docs/贴图清单.md` 的「待画」表里，那里本来就是它的家。
2. `被这一下打死的人，死因写的是「踢到了铁板」` —— **讲实现**。玩家该看到的是
   "这一击被原样还了回去"，不是"我给它挂了个自定义伤害类型"。

## 要改的（俗 → 科幻浪漫，但不堆辞藻）

| 键 | 改前 | 改后 |
|---|---|---|
| `tooltip.*.star_steel_set` | 罗列 + "多件也只有 I" 这种括号补丁 | 拟作**与夜同频**的叙述，数值一个不少 |
| `tooltip.*.vibranium_set` | 同上 + 两处开发笔记 | 拟作**承受与归还**的叙述，数值一个不少 |
| `death.attack.*.vibranium_reflect` | `%1$s踢到了铁板`（俗） | `%1$s被自己的攻击原样奉还`（贴机制、不俗） |

## 铁律（脚本自己断言，不靠人眼）

  · **键集合四语言必须一致**（只改值，不动键）；
  · **格式占位符签名必须一致**（`%1$s` 不能丢、不能多）；
  · 除 `%s` 外的**数值 token 必须原样保留**（伤害/秒数/半径……一个都不许改）——
    这是文案重写，不是数值改动；
  · 改完回读，逐键比对"该在的数值还在不在"。
"""
import io
import json
import os
import re
import sys

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

LANGDIR = r"E:\PotatoST\src\main\resources\assets\potato_s_t\lang"
PRE = r"E:\PotatoST\build\zftools\zf137_pre"
LANGS = ["zh_cn", "en_us", "ja_jp", "ru_ru"]

# ---------------------------------------------------------------- 新文案
NEW = {
    # 星璨钢套
    "tooltip.potato_s_t.star_steel_set": {
        "zh_cn": (u"星璨钢套：与夜同频。\n"
                  u"夜幕落下时，每一件都获得抗性提升 I；此时装备不磨损，头盔还会点亮相貌之外的视野"
                  u"——夜视 I，每次 4 秒，戴着便一直续。\n"
                  u"四件共振，才是它真正的形态：末地之中永不磨损；主世界的夜里得力量 I 与抗性提升 II，"
                  u"每 45 秒降下一层 10 秒的伤害吸收 III；到了末地，则得生命恢复 I、抗性提升 III、力量 II，"
                  u"每 15 秒降下一层 12 秒的伤害吸收 VI。\n"
                  u"那层吸收是周期性的护盾：一轮耗尽或被打空，才会有下一轮。\n"
                  u"虚空也夺不走你 —— 它会在 20×20 内为你寻一处落脚的方块，先托住你、再抹去坠落；"
                  u"若四下无物，便与附近的生物交换位置。"),
        "en_us": (u"Star Steel set: in tune with the night.\n"
                  u"When darkness falls, every piece grants Resistance I; the gear does not wear, "
                  u"and the helmet opens a sight beyond sight - Night Vision I, 4 s at a time, "
                  u"renewed for as long as it is worn.\n"
                  u"All four in resonance reveal its true form: no wear in the End; in the Overworld "
                  u"at night, Strength I and Resistance II, with Absorption III descending for 10 s "
                  u"every 45 s; in the End, Regeneration I, Resistance III and Strength II, with "
                  u"Absorption VI for 12 s every 15 s.\n"
                  u"That ward is a cyclic shield: the next one comes only once the current one is "
                  u"spent or struck empty.\n"
                  u"The void cannot take you either - it finds you solid ground within 20x20, "
                  u"catching you first and erasing the fall; where nothing stands, it trades your "
                  u"place with a creature nearby."),
        "ja_jp": (u"星燦鋼セット：夜と共鳴する。\n"
                  u"闇が下りると各部位が耐性 I を得て、装備は摩耗しない。ヘルメットはさらに"
                  u"視界の外を照らす――暗視 I、1 回 4 秒、装着している限り途切れず更新される。\n"
                  u"4 部位が共振して初めて本来の姿になる：エンドでは摩耗せず、主世界の夜は力 I と耐性 II、"
                  u"45 秒ごとに 10 秒の衝撃吸収 III が降りる。エンドでは再生 I・耐性 III・力 II、"
                  u"15 秒ごとに 12 秒の衝撃吸収 VI。\n"
                  u"その障りは周期の盾――今の一枚を使い切るか打ち砕かれるまで、次は来ない。\n"
                  u"ヴォイドもあなたを奪えない――20×20 内に足場を見つけ、まず受け止めてから落下を消す。"
                  u"何も無ければ、近くの生物と場所を交換する。"),
        "ru_ru": (u"Набор звёздной стали: в лад с ночью.\n"
                  u"С наступлением тьмы каждая часть даёт Сопротивление I, снаряжение не изнашивается, "
                  u"а шлем открывает зрение за пределами зрения — Ночное зрение I, по 4 с, "
                  u"продлевается, пока он надет.\n"
                  u"Все четыре в резонансе являют истинную форму: в Крае износ исчезает; в Верхнем мире "
                  u"ночью — Сила I и Сопротивление II, каждые 45 с нисходит Поглощение III на 10 с; "
                  u"в Крае — Регенерация I, Сопротивление III и Сила II, Поглощение VI на 12 с каждые 15 с.\n"
                  u"Этот щит цикличен: следующий придёт лишь тогда, когда нынешний исчерпан или пробит.\n"
                  u"И пустота вас не заберёт — она найдёт опору в пределах 20×20, сначала подхватит, "
                  u"а после сотрёт падение; где опоры нет — обменяет вас местами с ближним существом."),
    },
    # 振金套
    "tooltip.potato_s_t.vibranium_set": {
        "zh_cn": (u"振金套：不朽之躯。\n"
                  u"全套无限耐久，自带附魔辉光。它几乎不与附魔台共鸣（附魔权重 2，全游戏最低）——"
                  u"它不需要被修饰。\n"
                  u"四件同在时：抗性提升 I 常驻，不分昼夜与维度；摔落伤害免疫；弹射物伤害免疫，"
                  u"飞来的箭矢以半速沿原路退回；爆炸伤害减半；一切击退免疫。\n"
                  u"每一次承受，都有 10% 的几率被原样奉还 —— 那副躯体从不索取，只是把力道还回去。"),
        "en_us": (u"Vibranium set: a body that does not yield.\n"
                  u"Unbreakable, with a glint of its own. It scarcely answers the enchanting table "
                  u"(enchantment weight 2, the lowest in the game) - it needs no adornment.\n"
                  u"With all four: Resistance I at all times, in any hour and any dimension; "
                  u"immunity to fall damage; projectiles do nothing, and what flies at you returns "
                  u"along its own path at half speed; explosions are halved; knockback does not exist.\n"
                  u"And for every blow taken, there is a 10% chance it is given back exactly as it "
                  u"came - the body never takes; it only returns."),
        "ja_jp": (u"ヴィブラニウムセット：朽ちぬ身体。\n"
                  u"4 部位すべて耐久無限、自前のエンチャントの輝きを纏う。エンチャント台とはほとんど"
                  u"共鳴しない（エンチャント適性 2、全ゲーム中最低）――飾られる必要がないのだ。\n"
                  u"4 部位がそろうと：耐性 I が常時、昼夜も次元も問わない。落下ダメージ無効。"
                  u"投射物ダメージ無効、飛来する弾は半速で来た道を戻る。爆発ダメージは半分。"
                  u"あらゆるノックバックを無効化。\n"
                  u"受け止めるたび、10% の確率でその一撃はあるがまま返される――この身体は奪わず、"
                  u"ただ返すだけ。"),
        "ru_ru": (u"Набор вибраниума: тело, что не уступает.\n"
                  u"Неразрушим, с собственным сиянием. Он едва откликается столу зачаровывания "
                  u"(вес зачарования 2, самый низкий в игре) — ему не нужны украшения.\n"
                  u"Все четыре вместе: Сопротивление I постоянно, в любой час и любом измерении; "
                  u"иммунитет к урону от падения; снаряды не вредят, а летящее в вас возвращается "
                  u"своим же путём на половинной скорости; взрывы вдвое слабее; отбрасывания нет.\n"
                  u"И за каждый принятый удар есть 10% шанс вернуть его в точности таким, каким он пришёл — "
                  u"тело не отнимает, оно лишь возвращает."),
    },
    # 钛合金套：改掉那句自嘲（也与 §4 那条"文案别自嘲"一致）
    "tooltip.potato_s_t.titanium_alloy_set": {
        "zh_cn": (u"钛合金套：坚韧与附魔的平衡。\n"
                  u"附魔权重 25（金为 22）—— 比金更受附魔台青睐，也比金更扛得住。"),
        "en_us": (u"Titanium Alloy set: a balance of temper and enchantment.\n"
                  u"Enchantment weight 25 (gold is 22) - it answers the enchanting table more "
                  u"readily than gold, and endures more besides."),
        "ja_jp": (u"チタン合金セット：靭さとエンチャントの均衡。\n"
                  u"エンチャント適性 25（金は 22）――金よりエンチャント台に応え、金より耐える。"),
        "ru_ru": (u"Титановый набор: равновесие закалки и зачарования.\n"
                  u"Вес зачарования 25 (у золота 22) — стол зачаровывания отвечает охотнее, "
                  u"чем золоту, и держит удар крепче."),
    },
    # 死亡文案
    "death.attack.potato_s_t.vibranium_reflect": {
        "zh_cn": u"%1$s被自己的攻击原样奉还",
        "en_us": u"%1$s was answered in kind",
        "ja_jp": u"%1$sは己の一撃をそのまま返された",
        "ru_ru": u"%1$s получил ответ тем же",
    },
}

# 数值 token：除 %s/%1$s 外的数字与单位，必须原样保留
NUM = re.compile(r"\d+(?:\.\d+)?")
PH = re.compile(r"%\d+\$s|%s")


def main():
    os.makedirs(PRE, exist_ok=True)
    data = {}
    for lg in LANGS:
        p = os.path.join(LANGDIR, lg + ".json")
        raw = io.open(p, "rb").read()
        io.open(os.path.join(PRE, lg + ".json"), "wb").write(raw)   # 备份
        data[lg] = json.loads(raw.decode("utf-8"))
        print(u"  备份并读入 %s.json（%d 字节）" % (lg, len(raw)))

    # 基线：键集合一致
    base = set(data["zh_cn"])
    for lg in LANGS:
        if set(data[lg]) != base:
            print(u"  !! %s 键集合与 zh_cn 不一致，停手" % lg)
            return 1
    print(u"  [OK] 四语言键集合一致（各 %d 键）" % len(base))

    fails = []
    print(u"\n== 逐键替换 + 断言 ==")
    for key, per_lang in NEW.items():
        if key not in base:
            fails.append(u"键不存在：%s" % key)
            print(u"  !! 键不存在 %s" % key)
            continue
        # 旧值（用来核数值 token）
        for lg in LANGS:
            old = data[lg][key]
            new = per_lang[lg]
            # 占位符签名必须一致
            if sorted(PH.findall(old)) != sorted(PH.findall(new)):
                fails.append(u"%s[%s] 占位符不一致：%s -> %s"
                             % (key, lg, PH.findall(old), PH.findall(new)))
            # 数值 token 必须全在（death 文案没有数值）
            miss = [n for n in NUM.findall(old) if n not in NUM.findall(new)]
            if miss:
                fails.append(u"%s[%s] 丢了数值 %s" % (key, lg, miss))
            data[lg][key] = new
        print(u"  [重写] %s" % key)
        print(u"         zh: %s" % per_lang["zh_cn"].replace(u"\n", u" ⏎ ")[:88])

    if fails:
        print(u"\n断言未过，**没有写盘**：")
        for f in fails:
            print(u"  !! " + f)
        return 1

    print(u"\n== 写盘 + 回读 ==")
    for lg in LANGS:
        p = os.path.join(LANGDIR, lg + ".json")
        io.open(p, "w", encoding="utf-8", newline="\n").write(
            json.dumps(data[lg], indent=2, ensure_ascii=False) + "\n")
        back = json.loads(io.open(p, encoding="utf-8").read())
        if set(back) != base:
            fails.append(u"%s 写回后键集合变了" % lg)
        for key in NEW:
            if back[key] != NEW[key][lg]:
                fails.append(u"%s[%s] 写回后与预期不符" % (key, lg))
        print(u"  [OK] %s.json 键 %d，四组文案已核" % (lg, len(back)))

    # 顺带确认"开发者笔记"真的没了
    joined = u"\n".join(data[lg][k] for lg in LANGS for k in NEW)
    for bad in (u"暂时借用", u"贴图暂", u"踢到了铁板", u"Textures currently borrow",
                u"テクスチャは暫定", u"заимствованы у ванильного", u"kicked a steel plate",
                u"鉄板を蹴った", u"пнул стальную плиту"):
        if bad in joined:
            fails.append(u"开发笔记残留：%s" % bad)
    if not any(u"开发笔记残留" in f for f in fails):
        print(u"  [OK] 四语言里的开发笔记与俗套死亡文案已全部清除")

    print(u"\n失败项 = %d" % len(fails))
    for f in fails:
        print(u"  !! " + f)
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())
