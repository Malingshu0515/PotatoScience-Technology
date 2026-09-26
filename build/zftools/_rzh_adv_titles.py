# -*- coding: utf-8 -*-
r"""_rzh_adv_titles.py —— 成就标题改名：把「就是物品名」的 10 条换成"看得出这是个成就"的说法。

用户原话：「你看看能不能再优化一下成就翻译（进度名称 别单单是获得的物品名称了
          内容不想改可以不改）」+「从今往后你不只是润色 可以自由发挥」。

筛法：标题与**物品/方块显示名逐字相同**的一共 12 条，其中
  · `acid`（酸性反应室）/ `combustion`（燃烧反应室）虽同名，但"做出这台机器"本身就是里程碑，
    **保留**；
  · `hard_alloy` / `light_alloy` / `stable_block` / `lithium_battery` 是**关键材料**的专属名，
    本来就没有更贴切的说法，**保留**；
  · 其余 **10 条**改成动词化的成就名（与 `磨成粉`/`压成板`/`接电`/`钢铁是这样炼成的` 同一路数）。

只改 `advancements.potato_s_t.<id>.title` 的**值**，键一个不动（键数不变）。
"""
import io
import json
import sys

LANG = u"src/main/resources/assets/potato_s_t/lang/%s.json"
LOCALES = [u"zh_cn", u"en_us", u"ja_jp", u"ru_ru"]

NEW = {
    u"electrolyzer": {
        u"zh_cn": u"把水拆开",
        u"en_us": u"Split the Water",
        u"ja_jp": u"水を分解しよう",
        u"ru_ru": u"Разложите воду",
    },
    u"distillation": {
        u"zh_cn": u"把原油拆成五份",
        u"en_us": u"Five From One",
        u"ja_jp": u"原油を五つに分けよう",
        u"ru_ru": u"Пять из одного",
    },
    u"alloy_smelter": {
        u"zh_cn": u"配出一炉合金",
        u"en_us": u"Stoke the Alloy Line",
        u"ja_jp": u"合金を一炉どうぞ",
        u"ru_ru": u"Сплавы в одной печи",
    },
    u"blast_furnace": {
        u"zh_cn": u"砌一座高炉",
        u"en_us": u"Raise a Blast Furnace",
        u"ja_jp": u"高炉を建てよう",
        u"ru_ru": u"Постройте домну",
    },
    u"starfall": {
        u"zh_cn": u"召唤一颗星星",
        u"en_us": u"Call Down a Star",
        u"ja_jp": u"星を呼び下ろす",
        u"ru_ru": u"Позовите звезду",
    },
    u"salt": {
        u"zh_cn": u"向大海要盐",
        u"en_us": u"Salt From the Sea",
        u"ja_jp": u"海から塩を",
        u"ru_ru": u"Соль из моря",
    },
    u"star_steel": {
        u"zh_cn": u"炼出星璨钢",
        u"en_us": u"Forge the Star Steel",
        u"ja_jp": u"星燦鋼を鍛えよう",
        u"ru_ru": u"Выкуйте звёздную сталь",
    },
    u"oil_pump": {
        u"zh_cn": u"向海要油",
        u"en_us": u"Oil From Beneath the Sea",
        u"ja_jp": u"海の底から油を",
        u"ru_ru": u"Нефть из-под моря",
    },
    u"capacitor": {
        u"zh_cn": u"攒出一颗电容",
        u"en_us": u"Build a Capacitor",
        u"ja_jp": u"コンデンサを作ろう",
        u"ru_ru": u"Соберите конденсатор",
    },
    u"sulfur": {
        u"zh_cn": u"从沥青里掏出硫",
        u"en_us": u"Sulfur Out of Bitumen",
        u"ja_jp": u"瀝青から硫黄を",
        u"ru_ru": u"Сера из битума",
    },
}

fails = []
raw = {loc: io.open(LANG % loc, encoding=u"utf-8", newline=u"").read() for loc in LOCALES}

# ---- 写前断言 1：新标题不得与任何物品/方块显示名或别的成就标题重名 ----
for loc in LOCALES:
    data = json.loads(raw[loc])
    items = set(v for k, v in data.items()
                if k.startswith((u"item.", u"block.", u"fluid.", u"fluid_type.")))
    titles = dict((k, v) for k, v in data.items()
                  if k.startswith(u"advancements.") and k.endswith(u".title"))
    for nid, table in NEW.items():
        t = table[loc]
        if t in items:
            fails.append(u"%s / %s：新标题「%s」与物品名重名" % (loc, nid, t))
        for k2, v2 in titles.items():
            if v2 == t and k2 != u"advancements.potato_s_t.%s.title" % nid:
                fails.append(u"%s / %s：新标题「%s」与 %s 重名" % (loc, nid, t, k2))

plan = []
for loc in LOCALES:
    for nid, table in NEW.items():
        key = json.dumps(u"advancements.potato_s_t.%s.title" % nid, ensure_ascii=False)
        # ⚠⚠ 必须按**行首键**定位（`    "key":`）。
        #    第一版用裸 `find('"key"')` —— 而这些成就标题**与物品名同名**，
        #    `"advancements...starfall.title"` 在文件里首次出现的位置落在**物品行之后**，
        #    于是它取到的是**物品名的值**、把物品名改成了成就名（20 个键被误伤，
        #    已由 `_rzh_restore20.py` 恢复）。前车之鉴：`find_block` 也栽在同一件事上。
        anchor = u'    ' + key + u':'
        if raw[loc].count(anchor) != 1:
            fails.append(u"%s / %s：行首键出现 %d 次" % (loc, nid, raw[loc].count(anchor)))
            continue
        i = raw[loc].find(anchor)
        c = i + len(anchor)
        j = raw[loc].index(u'"', c)
        k = j + 1
        while True:
            if raw[loc][k] == u"\\":
                k += 2
                continue
            if raw[loc][k] == u'"':
                break
            k += 1
        old_lit, new_lit = raw[loc][j:k + 1], json.dumps(table[loc], ensure_ascii=False)
        if old_lit == new_lit:
            continue
        # 键值配对自检：取到的字面量必须**真的等于该键解析出来的值**
        if json.loads(old_lit) != json.loads(raw[loc])[u"advancements.potato_s_t.%s.title" % nid]:
            fails.append(u"%s / %s：取到的字面量与键的值不符" % (loc, nid))
            continue
        plan.append((loc, old_lit, new_lit, nid, json.loads(old_lit), table[loc]))

if fails:
    print(u"写前自检挂了，没落盘：")
    for f in fails:
        print(u"  !! " + f)
    sys.exit(1)

print(u"%-8s %-22s %s" % (u"语言", u"节点", u"改前 → 改后"))
for loc in LOCALES:
    text = raw[loc]
    for (l, old_lit, new_lit, nid, old, new) in [p for p in plan if p[0] == loc]:
        text = text.replace(old_lit, new_lit, 1)
        print(u"%-8s %-22s %s → %s" % (loc, nid, old, new))
    if text != raw[loc]:
        assert len(json.loads(text)) == len(json.loads(raw[loc])), u"键数变了"
        io.open(LANG % loc, u"w", encoding=u"utf-8", newline=u"").write(text)

print(u"\n合计改了 %d 处（%d 个节点 × %d 语言）" % (len(plan), len(NEW), len(LOCALES)))
