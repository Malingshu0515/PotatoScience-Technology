# -*- coding: utf-8 -*-
u"""_zf139_lang.py —— ZF139 的四语言改动（482 → **483** 键）

两件事，一次做完：
  ① **改值**：`tooltip.potato_s_t.vibranium_set` —— 把新加的三条效果写进去
     （常驻抗性 I / 免疫摔落 / 10% 反伤 + 死亡文案）；
  ② **加键**：`death.attack.potato_s_t.vibranium_reflect` —— 反伤致死那条死亡文案。
     值里的 `%1$s` 是**死掉的那个人**（= 先动手的那位），见 `ModVibraniumSet` 类注释第八节。

插键位置：紧挨在 `tooltip.potato_s_t.vibranium_set` **前面**（四语言同一个锚点），
这样振金那一簇键仍然连在一起；`_zf109_verify.py` 那条"四语言键序逐位相同"也才不会被搅乱。

⚠ 本脚本**不碰** `_rzh_armor_tips.py`（润色线的装备说明生成器）——
它那份底稿是 ZF133 之前的，谁再跑它都会把这四条新说明打回原样。
本轮在交接 §6 点名了这条，不去动别人线上的文件。

跑法：
    python build\\zftools\\_zf139_lang.py
"""
import io
import json
import sys

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

LANG = u"src/main/resources/assets/potato_s_t/lang/%s.json"
LOCALES = [u"zh_cn", u"en_us", u"ja_jp", u"ru_ru"]
OLD_KEYS, NEW_KEYS = 482, 483

TOOLTIP_KEY = u"tooltip.potato_s_t.vibranium_set"
DEATH_KEY = u"death.attack.potato_s_t.vibranium_reflect"
ANCHOR = u'  "%s":' % TOOLTIP_KEY

NEW_TOOLTIP = {
    u"zh_cn":
        u"振金套：全套无限耐久、附魔权重 2（全游戏最低，附魔台很难刷出好东西）、自带附魔光效。\n"
        u"穿满四件：抗性提升 I 常驻（不挑昼夜与维度）、免疫摔落伤害；免疫弹射物伤害，来弹沿原路弹回"
        u"（速度减半）；爆炸伤害减半；免疫任何击退。\n"
        u"挨打时有 10% 概率把这一击的伤害原样还给攻击者 —— 被这一下打死的人，死因写的是「踢到了铁板」。\n"
        u"（贴图暂时借用原版铁套）",
    u"en_us":
        u"Vibranium set: unbreakable, enchantment weight 2 - the lowest in the game, so the enchanting "
        u"table rarely offers anything good - and a built-in glint.\n"
        u"All four pieces: Resistance I at all times (any hour, any dimension) and immunity to fall damage; "
        u"immune to projectiles (incoming ones bounce back at half speed); explosion damage halved; immune to "
        u"all knockback.\n"
        u"10% of the hits you take are returned in full to whoever dealt them - anyone killed by that gets "
        u"kicked a steel plate as their death message.\n"
        u"(Textures currently borrow the vanilla iron set)",
    u"ja_jp":
        u"ヴィブラニウムセット：4 部位すべて耐久無限。エンチャント適性は 2 で全ゲーム中最低"
        u"（エンチャント台では良いものがなかなか出ません）。最初からエンチャントの輝き付き。\n"
        u"4 部位そろうと：耐性 I が常時付与（昼夜・次元を問わず）、落下ダメージ無効。投射物ダメージを"
        u"無効化し、飛んできた投射物は速度半分で跳ね返ります。爆発ダメージは半分。あらゆるノックバックを無効化。\n"
        u"被弾時に 10% の確率でその一撃のダメージをそのまま攻撃者へ返します。これで死んだ相手の死因は"
        u"「鉄板を蹴った」になります。\n"
        u"（テクスチャは暫定でバニラの鉄装備を借用）",
    u"ru_ru":
        u"Набор вибраниума: все четыре части неразрушимы, вес зачарования 2 — самый низкий в игре, "
        u"поэтому стол зачаровывания редко предложит что-то стоящее; есть собственное сияние.\n"
        u"В полном наборе: постоянное Сопротивление I (в любое время суток и в любом измерении) и иммунитет "
        u"к урону от падения; иммунитет к снарядам (летящие в вас отскакивают обратно на половинной "
        u"скорости); урон от взрывов вдвое меньше; полный иммунитет к отбрасыванию.\n"
        u"С вероятностью 10% полученный удар возвращается нападающему целиком — убитый этим получает "
        u"причину смерти «пнул стальную плиту».\n"
        u"(Текстуры пока заимствованы у ванильного железного набора)",
}

NEW_DEATH = {
    u"zh_cn": u"%1$s踢到了铁板",
    u"en_us": u"%1$s kicked a steel plate",
    u"ja_jp": u"%1$sは鉄板を蹴った",
    u"ru_ru": u"%1$s пнул стальную плиту",
}


def scan_literal(text, key_anchor):
    u"""从 `"key":  "值"` 里把**值的 JSON 字面量**（含两端引号）原样抠出来。"""
    i = text.find(key_anchor)
    if i < 0:
        return None, -1
    c = text.index(u":", i)
    j = text.index(u'"', c + 1)
    k = j + 1
    while True:
        if text[k] == u"\\":
            k += 2
            continue
        if text[k] == u'"':
            break
        k += 1
    return text[j:k + 1], i


def main():
    print(u"")
    print(u"%-8s %-10s %-22s %s" % (u"语言", u"键数", u"说明字数 老 → 新", u"新键"))
    fails = []
    plan = []          # (loc, path, 新文本, 老字数, 新字数) —— **全部算完再落盘**
    for loc in LOCALES:
        path = LANG % loc
        raw = io.open(path, encoding=u"utf-8", newline=u"").read()
        old_obj = json.loads(raw)
        if len(old_obj) != OLD_KEYS:
            fails.append(u"%s：改前是 %d 键，期望 %d" % (loc, len(old_obj), OLD_KEYS))
            continue
        if raw.count(ANCHOR) != 1:
            fails.append(u"%s：锚点出现 %d 次" % (loc, raw.count(ANCHOR)))
            continue
        old_lit, _i = scan_literal(raw, ANCHOR)
        if old_lit is None:
            fails.append(u"%s：抠不出老字面量" % loc)
            continue
        if raw.count(old_lit) != 1:
            fails.append(u"%s：老值出现 %d 次" % (loc, raw.count(old_lit)))
            continue
        old_len = len(json.loads(old_lit))
        new_lit = json.dumps(NEW_TOOLTIP[loc], ensure_ascii=False)
        text = raw.replace(old_lit, new_lit, 1)
        # 插键：就插在说明那一行前面
        ins = u'  "%s":  %s,\n' % (DEATH_KEY, json.dumps(NEW_DEATH[loc], ensure_ascii=False))
        text = text.replace(ANCHOR, ins + ANCHOR, 1)

        new_obj = json.loads(text)
        if len(new_obj) != NEW_KEYS:
            fails.append(u"%s：改完是 %d 键，期望 %d" % (loc, len(new_obj), NEW_KEYS))
            continue
        ok_order = list(old_obj.keys())
        ok_order.insert(ok_order.index(TOOLTIP_KEY), DEATH_KEY)
        if list(new_obj.keys()) != ok_order:
            fails.append(u"%s：键序变了（除插入那一个键之外）" % loc)
            continue
        for k in old_obj:
            if k == TOOLTIP_KEY:
                continue
            if new_obj[k] != old_obj[k]:
                fails.append(u"%s：%s 的值被动到了" % (loc, k))
                break
        plan.append((loc, path, text, old_len, len(NEW_TOOLTIP[loc])))

    if fails:
        print(u"写前自检挂了，**一个字节都没落盘**：")
        for f in fails:
            print(u"  !! " + f)
        return 1

    for loc, path, text, old_len, new_len in plan:
        io.open(path, u"w", encoding=u"utf-8", newline=u"").write(text)
        print(u"%-8s %d → %d   %-22s %s" % (loc, OLD_KEYS, NEW_KEYS,
                                            u"%d → %d 字" % (old_len, new_len),
                                            u"+1（%s）" % NEW_DEATH[loc][:14]))
    print(u"")
    # ---- 回读 ----
    for loc in LOCALES:
        obj = json.loads(io.open(LANG % loc, encoding=u"utf-8", newline=u"").read())
        assert len(obj) == NEW_KEYS, loc
        assert obj[DEATH_KEY] == NEW_DEATH[loc], loc
        assert obj[TOOLTIP_KEY] == NEW_TOOLTIP[loc], loc
    print(u"回读：四语言各 %d 键，新键与两条新说明逐字一致" % NEW_KEYS)
    print(u"失败项 = 0")
    return 0


if __name__ == u"__main__":
    sys.exit(main())
