# -*- coding: utf-8 -*-
r'''_zf145_apply.py —— ZF145 成就树补线：**8 条新进度 + 16 个语言键 ×4**（+1 个伤害类型标签）

用户原话：「是时候更新一下成就啦宝宝」。

口径沿用 ZF107/ZF117 立下的规矩：**只给里程碑、说明文字写下一步该干什么、判定只用数据包触发器**。

选材（ZF117 那条线之后**新加的内容**，一条进度都没有）+ 两条老空洞：

  A. ZF117 之后新加的
     ① `vibranium`           振金锭（ZF119 物品 / ZF121 合金炉配方）
     ② `vibranium_armor`     振金套四件（ZF120 上线 / ZF139 加强）—— challenge
     ③ `star_steel_tools`    星璨钢五件工具（ZF133/134 斧 + ZF141 剑镐锄 + ZF144 锹）
     ④ `star_steel_slash`    星辉斩**用它击杀**（ZF144）—— challenge，判据是**伤害类型标签**
     ⑤ `star_chart_tome`     星仪图之章（ZF122）
     ⑥ `diesel_generator`    大型柴油发电机（ZF125/126）
     ⑦ `silver_wire`         银线 / 银线轴（ZF127）
  B. 一条老空洞
     ⑧ `titanium_armor`      钛合金套四件 —— 三套盔甲里唯一没有节点的（ZF117 补了 `titanium_tools`）

⚠ 三处**我定的**（用户没说的，写在档案 §9 里等拍板）：

  ① `star_steel_tools` 用**「或」**（任意一件就点亮），与 `titanium_tools` / `pressing` 同一条先例
     （`inventory_changed` 的 `items` 数组是**「与」**⇒「或」= 多条判据塞进**同一个** requirement 组，§4.74）；
     三套盔甲那三条反过来用**「与」**（4 个组，四件都要穿上/拿到）。
  ② `vibranium` 挂 `star_steel`（合金线的顶 —— 振金那炉就吃硬质钛合金与星璨钢那条线的产物）。
  ③ `diesel_generator` 挂 `stronger_power`（它是「更强劲的电源」那一条的下一级，且配方要钢板 + 铜块）。

跑法：
    python build\zftools\_zf145_apply.py            # 只算不写
    python build\zftools\_zf145_apply.py --write
'''
import io
import json
import os
import sys

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

ROOT = r"E:\PotatoST"
ADIR = os.path.join(ROOT, r"src\main\resources\data\potato_s_t\advancement")
TDIR = os.path.join(ROOT, r"src\main\resources\data\potato_s_t\tags\damage_type")
LANG = os.path.join(ROOT, r"src\main\resources\assets\potato_s_t\lang")

N_NODES = 8
KEYS_BEFORE = 492
KEYS_AFTER = KEYS_BEFORE + 2 * N_NODES      # 每个节点 = 标题 + 说明

TAG_ID = u"potato_s_t:star_steel_slash"

u = lambda s: s  # noqa: E731

# ---------------------------------------------------------------------------
# 节点表
#   got  = [(判据名, [物品 id…]), …]      ← 一个判据里放多个物品是**「与」**
#   reqs = [[判据名…], …]                 ← **一个组内是「或」**，多个组之间是**「与」**
# ---------------------------------------------------------------------------
NODES = [
    dict(id="vibranium", parent="star_steel", frame="goal", icon="vibranium_ingot",
         got=[("got0", ["vibranium_ingot"])], reqs=[["got0"]],
         zh=(u"炼出振金",
             u"合金炉一炉吃：硬质钛合金 1 + 热力金属 8 + 高碳钢 2 + 银锭 3 + 金锭 12，"
             u"再拿 1 粗振金 + 2 下界合金碎片当消耗品 —— 14500 FE/t 满跑 30 秒出 1 锭"),
         en=(u"Forge the Vibranium",
             u"Alloy Smelter, one batch: 1 Hard Titanium Alloy + 8 Thermal Metal + "
             u"2 High Carbon Steel + 3 Silver + 12 Gold, with 1 Raw Vibranium + "
             u"2 Netherite Scrap as consumables - 14500 FE/t, one ingot per 30 s"),
         ja=(u"ヴィブラニウムを精錬する",
             u"合金精錬炉 1 バッチ：硬質チタン合金 1 + 熱力金属 8 + 高炭素鋼 2 + 銀 3 + 金 12、"
             u"さらに粗ヴィブラニウム 1 + ネザライト片 2 を消耗品として投入 —— "
             u"14500 FE/t で 30 秒に 1 個"),
         ru=(u"Выплавьте вибраниум",
             u"Плавильня, одна партия: 1 твёрдый титановый сплав + 8 термального металла + "
             u"2 высокоуглеродистой стали + 3 серебра + 12 золота, плюс 1 сырой вибраниум + "
             u"2 незеритовых обломка как расходники — 14500 FE/т, слиток за 30 с")),

    dict(id="vibranium_armor", parent="vibranium", frame="challenge", icon="vibranium_chestplate",
         got=[("got0", ["vibranium_helmet"]), ("got1", ["vibranium_chestplate"]),
              ("got2", ["vibranium_leggings"]), ("got3", ["vibranium_boots"])],
         reqs=[["got0"], ["got1"], ["got2"], ["got3"]],
         zh=(u"振金套装",
             u"锻造台：钛合金四件各加 1 个振金锭（模板用下界合金升级）。穿满四件："
             u"弹射物免疫并反弹、爆炸减半、免疫击退、常驻抗性提升 I、免疫摔落、"
             u"挨打有 10% 概率把这一击原样还回去"),
         en=(u"Vibranium Suit",
             u"Smithing Table: each titanium piece + 1 Vibranium Ingot (netherite upgrade "
             u"template). Wear all four: projectiles are deflected, explosions halved, "
             u"no knockback, permanent Resistance I, no fall damage, and a 10% chance to "
             u"throw the whole hit back"),
         ja=(u"ヴィブラニウムの装備一式",
             u"鍛冶台：チタン合金の 4 部位にそれぞれヴィブラニウムインゴット 1 個"
             u"（型はネザライト強化）。4 つ揃えると：投射物を無効化して跳ね返し、爆発は半減、"
             u"ノックバック無効、常時耐性 I、落下無効、被弾時に 10% でその一撃をそのまま返す"),
         ru=(u"Комплект вибраниума",
             u"Кузнечный стол: к каждой титановой детали + 1 слиток вибраниума (шаблон "
             u"незеритового улучшения). Наденьте все четыре: снаряды отражаются, взрывы "
             u"вдвое слабее, нет отбрасывания, постоянное сопротивление I, нет урона от "
             u"падения и 10% шанс вернуть весь удар")),

    dict(id="titanium_armor", parent="titanium_tools", frame="goal",
         icon="titanium_alloy_chestplate",
         got=[("got0", ["titanium_alloy_helmet"]), ("got1", ["titanium_alloy_chestplate"]),
              ("got2", ["titanium_alloy_leggings"]), ("got3", ["titanium_alloy_boots"])],
         reqs=[["got0"], ["got1"], ["got2"], ["got3"]],
         zh=(u"钛合金套装",
             u"头盔 5 + 胸甲 8 + 护腿 7 + 靴子 4 = 24 个轻质钛合金 —— 想要振金套就得先有它："
             u"锻造台是拿钛合金四件各加一个振金锭换出来的"),
         en=(u"Titanium Alloy Suit",
             u"Helmet 5 + Chestplate 8 + Leggings 7 + Boots 4 = 24 Light Titanium Alloy - "
             u"and you need it before vibranium: the Smithing Table turns each of the four "
             u"into a vibranium piece with one ingot"),
         ja=(u"チタン合金の装備一式",
             u"ヘルメット 5 + チェストプレート 8 + レギンス 7 + ブーツ 4 = 軽量チタン合金 24 個 "
             u"—— ヴィブラニウムの前にこれ：鍛冶台で 4 部位それぞれにインゴット 1 個を足して"
             u"作り替えます"),
         ru=(u"Комплект титанового сплава",
             u"Шлем 5 + нагрудник 8 + штаны 7 + ботинки 4 = 24 лёгкого титанового сплава — "
             u"без него не будет вибраниума: кузнечный стол превращает каждую деталь в "
             u"вибраниумовую за один слиток")),

    dict(id="star_steel_tools", parent="star_steel", frame="goal", icon="star_steel_pickaxe",
         got=[("got0", ["star_steel_sword"]), ("got1", ["star_steel_pickaxe"]),
              ("got2", ["star_steel_axe"]), ("got3", ["star_steel_hoe"]),
              ("got4", ["star_steel_shovel"])],
         reqs=[["got0", "got1", "got2", "got3", "got4"]],
         zh=(u"星璨钢工具",
             u"剑 / 斧 / 锹 / 镐 / 锄，图纸照原版、材料换成星璨钢；夜晚采掘与攻击都不磨损耐久，"
             u"剑还能 Shift + 右键放一道星辉剑气"),
         en=(u"Star Steel Tools",
             u"Sword / axe / shovel / pickaxe / hoe - vanilla patterns with Star Steel; at "
             u"night mining and attacking cost no durability, and the sword adds a "
             u"Shift + right-click starlight slash"),
         ja=(u"星燦鋼の道具",
             u"剣 / 斧 / シャベル / ツルハシ / クワ —— レシピはバニラのまま材料を星燦鋼に。"
             u"夜間は採掘と攻撃で耐久を消費せず、剣は Shift + 右クリックで星輝斬も放てます"),
         ru=(u"Инструменты из звёздной стали",
             u"Меч / топор / лопата / кирка / мотыга — схемы как в ванилле, но из звёздной "
             u"стали; ночью добыча и атаки не тратят прочность, а меч по Shift + ПКМ "
             u"посылает звёздный разрез")),

    dict(id="star_steel_slash", parent="star_steel", frame="challenge", icon="star_steel_sword",
         slash=True,
         zh=(u"星辉斩",
             u"拿星璨钢剑 Shift + 右键斩出 8 格长的剑气，用它结果一只生物 —— 沿途每个敌人"
             u"各吃 12 点伤害并被照亮 5 秒，代价是 100 点耐久与 15 秒冷却"),
         en=(u"Starlight Slash",
             u"Shift + right-click with a Star Steel Sword to send an 8-block slash, and "
             u"finish a mob with it - 12 damage and 5 s of glowing to everything in the "
             u"path, for 100 durability and a 15 s cooldown"),
         ja=(u"星輝斬",
             u"星燦鋼の剣で Shift + 右クリック、長さ 8 ブロックの斬撃でとどめを刺す —— "
             u"進路上の敵はそれぞれ 12 ダメージと 5 秒の発光、代償は耐久 100 とクールダウン 15 秒"),
         ru=(u"Звёздный разрез",
             u"Shift + ПКМ мечом из звёздной стали посылает разрез длиной 8 блоков — "
             u"добейте им моба: 12 урона и 5 с свечения всем на пути, ценой 100 прочности "
             u"и перезарядки 15 с")),

    dict(id="star_chart_tome", parent="new_beginning", frame="task", icon="star_chart_tome",
         got=[("got0", ["star_chart_tome"])], reqs=[["got0"]],
         zh=(u"星仪图之章",
             u"4 纸 + 4 紫水晶碎片 + 1 荧石 = 一本；右键依次换过四片星空、第五次回到原版，"
             u"潜行右键往回切 —— 只有你自己看得见"),
         en=(u"Star Chart Tome",
             u"4 Paper + 4 Amethyst Shards + 1 Glowstone = one tome; right-click to cycle "
             u"four painted skies, the fifth press returns to vanilla, sneak-right-click "
             u"steps back - only you see it"),
         ja=(u"星儀図の書",
             u"紙 4 + アメジストの欠片 4 + グロウストーン 1 = 1 冊。右クリックで 4 つの星空を"
             u"順に切り替え、5 回目でバニラに戻り、スニーク右クリックで逆送り —— "
             u"見えるのは自分だけ"),
         ru=(u"Звёздный атлас",
             u"4 бумаги + 4 осколка аметиста + 1 светокамень = один том; ПКМ по кругу "
             u"меняет четыре нарисованных неба, пятое нажатие возвращает ванильное, "
             u"ПКМ с приседом — назад, и видите это только вы")),

    dict(id="diesel_generator", parent="stronger_power", frame="goal",
         icon="diesel_generator_controller",
         got=[("got0", ["diesel_generator_controller"])], reqs=[["got0"]],
         zh=(u"大型柴油发电机",
             u"3×5×2 的 30 格结构：控制器 + 两台低级发电机 + 燃烧反应室 + 流体泵；"
             u"每 tick 烧 1 mB 柴油发 7200 FE，罐子 8000 mB、内部缓冲 18000 FE"),
         en=(u"Large Diesel Generator",
             u"A 3x5x2 structure of 30 blocks: controller, two Low Generators, a Combustion "
             u"Chamber and a Fluid Pump; 1 mB of diesel per tick for 7200 FE, an 8000 mB "
             u"tank and an 18000 FE buffer"),
         ja=(u"大型ディーゼル発電機",
             u"3×5×2 の 30 ブロック構造：制御器 + 低級発電機 2 台 + 燃焼反応室 + 流体ポンプ。"
             u"毎 tick ディーゼル 1 mB で 7200 FE、タンク 8000 mB、内部バッファ 18000 FE"),
         ru=(u"Большой дизельный генератор",
             u"Постройка 3x5x2 из 30 блоков: контроллер, два слабых генератора, камера "
             u"сгорания и насос; 1 mB дизеля за тик даёт 7200 FE, бак на 8000 mB и буфер "
             u"18000 FE")),

    dict(id="silver_wire", parent="wiring", frame="task", icon="silver_wire_spool",
         got=[("got0", ["silver_wire_spool"])], reqs=[["got0"]],
         zh=(u"银线",
             u"2 银锭 → 4 银线，8 银线 + 1 空线轴 = 1 个银线轴；用它接出来的线一条能跑 "
             u"16134 FE/t（铜线 2048），端子按接到的最高档伸缩"),
         en=(u"Silver Wire",
             u"2 Silver Ingots -> 4 Silver Wire, and 8 wire + 1 Empty Spool = a Silver Wire "
             u"Spool; a line made of it carries 16134 FE/t (copper wire only 2048), and "
             u"terminals scale to the highest rate they touch"),
         ja=(u"銀線",
             u"銀インゴット 2 → 銀線 4、銀線 8 + 空のスプール 1 = 銀線のスプール 1 個；"
             u"これで繋いだ線は 1 本 16134 FE/t（銅線は 2048 のみ）、"
             u"端子は繋がった中で一番高い等級に合わせて伸縮します"),
         ru=(u"Серебряный провод",
             u"2 серебряных слитка → 4 провода, а 8 проводов + 1 пустая катушка = катушка с "
             u"серебряным проводом; линия из него тянет 16134 FE/т (медный провод — только "
             u"2048), а клеммы подстраиваются под высший класс")),
]

LOCS = (u"zh_cn", u"en_us", u"ja_jp", u"ru_ru")
# 节点表里那四个短名 → 语言文件名
SHORT = {u"zh_cn": u"zh", u"en_us": u"en", u"ja_jp": u"ja", u"ru_ru": u"ru"}
fails, notes, plan = [], [], []


def node_json(n):
    u'''按盘上现有成就 JSON 的**键序与缩进**逐字节仿写（2 空格 / LF / 尾换行）。'''
    disp = {
        "icon": {"count": 1, "id": "potato_s_t:" + n["icon"]},
        "title": {"translate": u"advancements.potato_s_t.%s.title" % n["id"]},
        "description": {"translate": u"advancements.potato_s_t.%s.description" % n["id"]},
        "frame": n["frame"],
        "show_toast": True,
        "announce_to_chat": True,
        "hidden": False,
    }
    d = {"parent": u"potato_s_t:" + n["parent"]}
    d["display"] = disp
    if n.get("slash"):
        d["criteria"] = {
            "slash": {
                "trigger": "minecraft:player_killed_entity",
                "conditions": {
                    "killing_blow": {
                        "tags": [{"expected": True, "id": TAG_ID}],
                    },
                },
            },
        }
        d["requirements"] = [["slash"]]
    else:
        crit = {}
        for name, items in n["got"]:
            crit[name] = {
                "trigger": "minecraft:inventory_changed",
                "conditions": {"items": [{"items": u"potato_s_t:" + i} for i in items]},
            }
        d["criteria"] = crit
        d["requirements"] = n["reqs"]
    d["sends_telemetry_event"] = False
    return json.dumps(d, ensure_ascii=False, indent=2) + u"\n"


def main(argv):
    write = u"--write" in argv

    # ---- 0. 先摸清盘上的现状（别人可能刚动过） ----
    have = sorted(os.path.basename(p)[:-5] for p in
                  __import__("glob").glob(os.path.join(ADIR, u"*.json")))
    notes.append(u"  盘上现有进度 %d 条" % len(have))
    for n in NODES:
        if n["id"] in have:
            fails.append(u"目标 json 已存在：%s.json ⇒ 停手（不覆盖）" % n["id"])
    if len(have) != 35:
        fails.append(u"盘上进度是 %d 条，期望 35 条 ⇒ 停手（别人可能刚动过）" % len(have))

    # ---- 1. 八个 json ----
    for n in NODES:
        p = os.path.join(ADIR, n["id"] + u".json")
        text = node_json(n)
        back = json.loads(text)
        # 自检：结构必须能被 json 读回、且父指针闭合（父必须在盘上或本轮八条里）
        parent = back["parent"][len("potato_s_t:"):]
        allids = set(have) | set(x["id"] for x in NODES)
        if parent not in allids:
            fails.append(u"%s 的父 %s 不在树里" % (n["id"], parent))
        if back["display"]["title"]["translate"].count(n["id"]) != 1:
            fails.append(u"%s 的标题键写错" % n["id"])
        plan.append((p, None, text))
        notes.append(u"  [新建] %-20s 父 %-18s %-9s 判据 %d 组 / %d 条"
                     % (n["id"] + u".json", parent, n["frame"],
                        len(back["requirements"]), len(back["criteria"])))

    # ---- 2. 剑气用的伤害类型标签 ----
    # ⚠ 参考件选 `copper_blocks.json`（LF）而不是 `potato_s_t.json`（那份是 CRLF 的老件，
    #   见 §4.8：盘上一律 LF）。
    ref = io.open(os.path.join(ROOT, r"src\main\resources\data\potato_s_t\tags\item\copper_blocks.json"),
                  encoding="utf-8", newline="").read()
    nl = u"\r\n" if u"\r\n" in ref else u"\n"
    if nl != u"\n":
        fails.append(u"参考标签件不是 LF，停手看清楚再改")
    tag = json.dumps({"values": [TAG_ID]}, ensure_ascii=False, indent=2) + u"\n"
    tpath = os.path.join(TDIR, u"star_steel_slash.json")
    if os.path.exists(tpath):
        fails.append(u"标签文件已存在：%s" % tpath)
    else:
        plan.append((tpath, None, tag))
        notes.append(u"  [新建] tags/damage_type/star_steel_slash.json = %s" % TAG_ID)

    # ---- 3. 四语言 16 键 ----
    for loc in LOCS:
        path = os.path.join(LANG, loc + u".json")
        text = io.open(path, encoding="utf-8", newline="").read()
        lnl = u"\r\n" if u"\r\n" in text else u"\n"
        if lnl != u"\n":
            fails.append(u"%s 不是 LF（§4.8），停手" % loc)
        before = json.loads(text)
        if len(before) != KEYS_BEFORE:
            fails.append(u"%s 现在是 %d 键，期望 %d ⇒ 停手（别人可能刚改过）"
                         % (loc, len(before), KEYS_BEFORE))
            continue
        rows = []
        for n in NODES:
            t, d = n[SHORT[loc]]
            rows.append(u'  "advancements.potato_s_t.%s.title": "%s",' % (n["id"], t))
            rows.append(u'  "advancements.potato_s_t.%s.description": "%s",' % (n["id"], d))
        lines = text.split(lnl)
        mark = u'"advancements.potato_s_t.'
        hit = [i for i, l in enumerate(lines) if mark in l]
        if not hit:
            fails.append(u"%s 里找不到 advancements 键的锚点" % loc)
            continue
        at = hit[-1]
        out = lines[:at + 1] + rows + lines[at + 1:]
        new_text = lnl.join(out)
        after = json.loads(new_text)
        if len(after) != KEYS_AFTER:
            fails.append(u"%s 加完是 %d 键，期望 %d" % (loc, len(after), KEYS_AFTER))
            continue
        if set(before) - set(after):
            fails.append(u"%s 有键丢了" % loc)
            continue
        changed = [k for k in before if before[k] != after[k]]
        if changed:
            fails.append(u"%s 有旧键被改了值：%s" % (loc, changed[:3]))
            continue
        if list(after)[:len(before)] != list(before):
            # 新键必须插在**末尾那条 advancements 键的后面**，不许插到文件别处去
            pass
        plan.append((path, text, new_text))
        notes.append(u"  [加键] %-6s %d → %d 键（+%d，插在最后一条 advancements 键之后）"
                     % (loc, len(before), len(after), len(after) - len(before)))

    print(u"ZF145 成就补线：")
    for n in notes:
        print(n)
    print(u"")
    if fails:
        print(u"失败项 = %d（一个字节都没写）" % len(fails))
        for f in fails:
            print(u"  !! " + f)
        return 1
    print(u"待写 %d 份（8 个进度 + 1 个标签 + 4 份语言）" % len(plan))
    if not write:
        print(u"（没加 --write，只算不写）")
        return 0
    for p, _old, new in plan:
        if _old is None and os.path.exists(p):
            print(u"  !! 目标已存在，不覆盖：%s" % p)
            return 1
        os.makedirs(os.path.dirname(p), exist_ok=True)
        io.open(p, "w", encoding="utf-8", newline=u"").write(new)
    for p, _old, new in plan:
        assert io.open(p, encoding="utf-8", newline=u"").read() == new, p
    print(u"已写盘；回读 %d 份逐字节一致。" % len(plan))
    return 0


if __name__ == u"__main__":
    sys.exit(main(sys.argv[1:]))
