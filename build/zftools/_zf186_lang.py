# -*- coding: utf-8 -*-
u"""_zf186_lang.py —— ZF186 五语种文案（配置界面 + 引力装置动态 tooltip）。

干跑：python build\\zftools\\_zf186_lang.py
落盘：python build\\zftools\\_zf186_lang.py --write

为什么要这么写：
  · 本工程五份 lang 必须**键齐**（LangCheck 那类常驻门看的是键集合）⇒ 新键一次补齐 5 语种；
  · 写之前先做**原样回环自证**：把读进来的 dict 按「ensure_ascii=False + indent=2 + 尾换行」
    重新 dump 一遍，必须与原文件**逐字节相同** —— 不同就说明格式口径不对，直接判失败、不写盘
    （否则一次写盘会把 655 个键的排版全搅乱，diff 变成一锅粥）；
  · 只动两类东西：新增这份 KEYS，以及对 `tooltip.potato_s_t.gravity_device` 里那个
    「25」的数字词做**一次**定点替换（用户把默认蓄力时长改成 30 秒，静态文案不能还说 25）。
"""
import io
import json
import os
import sys

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding=u"utf-8", errors="replace")

ROOT = r"E:\PotatoST"
LANG = os.path.join(ROOT, "src", "main", "resources", "assets", "potato_s_t", "lang")
FILES = [u"zh_cn.json", u"en_us.json", u"lzh.json", u"ja_jp.json", u"ru_ru.json"]

# 新键：key -> 5 语种的值
KEYS = {
    u"potato_s_t.configuration.title": {
        u"zh_cn": u"PotatoS&T 配置", u"en_us": u"PotatoS&T Configuration",
        u"lzh": u"PotatoS&T 設置", u"ja_jp": u"PotatoS&T 設定", u"ru_ru": u"Настройки PotatoS&T"},
    u"potato_s_t.configuration.section.potato.s.t.common.toml": {
        u"zh_cn": u"通用配置", u"en_us": u"Common configuration",
        u"lzh": u"通用設置", u"ja_jp": u"共通設定", u"ru_ru": u"Общие настройки"},
    u"potato_s_t.configuration.section.potato.s.t.common.toml.title": {
        u"zh_cn": u"PotatoS&T 通用配置", u"en_us": u"PotatoS&T common configuration",
        u"lzh": u"PotatoS&T 通用設置", u"ja_jp": u"PotatoS&T 共通設定",
        u"ru_ru": u"Общие настройки PotatoS&T"},
    # ── 三个分组标题（+ .button 是那一行的按钮文案）──
    u"potato_s_t.configuration.section.black_hole": {
        u"zh_cn": u"黑洞", u"en_us": u"Black hole", u"lzh": u"黑洞",
        u"ja_jp": u"ブラックホール", u"ru_ru": u"Чёрная дыра"},
    u"potato_s_t.configuration.section.black_hole.button": {
        u"zh_cn": u"黑洞", u"en_us": u"Black hole", u"lzh": u"黑洞",
        u"ja_jp": u"ブラックホール", u"ru_ru": u"Чёрная дыра"},
    u"potato_s_t.configuration.section.gravity_device": {
        u"zh_cn": u"引力装置", u"en_us": u"Gravity device", u"lzh": u"引力裝置",
        u"ja_jp": u"重力装置", u"ru_ru": u"Гравитационное устройство"},
    u"potato_s_t.configuration.section.gravity_device.button": {
        u"zh_cn": u"引力装置", u"en_us": u"Gravity device", u"lzh": u"引力裝置",
        u"ja_jp": u"重力装置", u"ru_ru": u"Гравитационное устройство"},
    u"potato_s_t.configuration.section.lithium_battery": {
        u"zh_cn": u"锂电池", u"en_us": u"Lithium battery", u"lzh": u"鋰電池",
        u"ja_jp": u"リチウム電池", u"ru_ru": u"Литиевая батарея"},
    u"potato_s_t.configuration.section.lithium_battery.button": {
        u"zh_cn": u"锂电池", u"en_us": u"Lithium battery", u"lzh": u"鋰電池",
        u"ja_jp": u"リチウム電池", u"ru_ru": u"Литиевая батарея"},
    # ── 黑洞 6 项 ──
    u"potato_s_t.configuration.black_hole.one_shot": {
        u"zh_cn": u"黑洞一次性", u"en_us": u"One-shot black hole", u"lzh": u"黑洞一次性",
        u"ja_jp": u"ブラックホールは使い切り", u"ru_ru": u"Одноразовая чёрная дыра"},
    u"potato_s_t.configuration.black_hole.one_shot.tooltip": {
        u"zh_cn": u"开：放完黑洞装置当场损坏（老行为）。关：只把电力条抽干，装置留着 —— 充上电还能再放。",
        u"en_us": u"On: the device breaks after firing (the original behaviour). Off: only the energy bar is drained, so you can recharge and fire again.",
        u"lzh": u"開：放畢黑洞裝置當場損壞（舊行為）。關：只抽乾電力條，裝置留之 —— 充上電可再放。",
        u"ja_jp": u"オン：発射後に装置が壊れます（元の挙動）。オフ：電力バーを空にするだけで、装置は残ります。",
        u"ru_ru": u"Вкл: устройство ломается после выстрела (исходное поведение). Выкл: разряжается только энергия, устройство остаётся целым."},
    u"potato_s_t.configuration.black_hole.lifetime_seconds": {
        u"zh_cn": u"黑洞存活时长（秒）", u"en_us": u"Black hole lifetime (seconds)",
        u"lzh": u"黑洞存續時長（息）", u"ja_jp": u"ブラックホールの寿命（秒）",
        u"ru_ru": u"Время жизни чёрной дыры (с)"},
    u"potato_s_t.configuration.black_hole.lifetime_seconds.tooltip": {
        u"zh_cn": u"黑洞存在多少秒（5~120，默认 20）。越长吸得越多，也越吃性能。",
        u"en_us": u"How long a black hole lives (5-120, default 20). Longer pulls more blocks and costs more performance.",
        u"lzh": u"黑洞存幾息（5~120，默 20）。愈長吸愈多，亦愈費機能。",
        u"ja_jp": u"ブラックホールが存在する秒数（5~120、既定 20）。長いほど多く吸い込み、負荷も増えます。",
        u"ru_ru": u"Сколько секунд живёт чёрная дыра (5-120, по умолчанию 20). Дольше — больше блоков и больше нагрузки."},
    u"potato_s_t.configuration.black_hole.max_blocks": {
        u"zh_cn": u"单次搬运上限", u"en_us": u"Blocks moved per black hole",
        u"lzh": u"單次搬運上限", u"ja_jp": u"1 回の移動ブロック上限",
        u"ru_ru": u"Лимит перемещённых блоков"},
    u"potato_s_t.configuration.black_hole.max_blocks.tooltip": {
        u"zh_cn": u"一个黑洞最多搬走多少方块（100~5000，默认 1500）。",
        u"en_us": u"How many blocks one black hole may move (100-5000, default 1500).",
        u"lzh": u"一黑洞至多搬走幾塊（100~5000，默 1500）。",
        u"ja_jp": u"1 つのブラックホールが動かせるブロック数の上限（100~5000、既定 1500）。",
        u"ru_ru": u"Сколько блоков может переместить одна чёрная дыра (100-5000, по умолчанию 1500)."},
    u"potato_s_t.configuration.black_hole.scan_radius_blocks": {
        u"zh_cn": u"扫描半径（格）", u"en_us": u"Scan radius (blocks)",
        u"lzh": u"掃描半徑（格）", u"ja_jp": u"走査半径（ブロック）",
        u"ru_ru": u"Радиус поиска (блоки)"},
    u"potato_s_t.configuration.black_hole.scan_radius_blocks.tooltip": {
        u"zh_cn": u"以黑洞为中心、各轴 ±N 格（8~80，默认 40 = 5×5×5 区块）。每加一格，扫描体积是三次方地涨 —— 调大之前先想想 TPS。",
        u"en_us": u"Each axis spans +/- N blocks around the hole (8-80, default 40 = 5x5x5 chunks). The scanned volume grows cubically — mind your TPS.",
        u"lzh": u"以黑洞為心、各軸 ±N 格（8~80，默 40 = 5×5×5 區塊）。每加一格，所掃體積以三方增 —— 調大前先念 TPS。",
        u"ja_jp": u"ブラックホールを中心に各軸 ±N ブロック（8~80、既定 40 = 5×5×5 チャンク）。体積は三乗で増えるので負荷に注意。",
        u"ru_ru": u"По +/- N блоков на каждую ось вокруг дыры (8-80, по умолчанию 40 = 5x5x5 чанков). Объём растёт кубически — следите за TPS."},
    u"potato_s_t.configuration.black_hole.pull_entities": {
        u"zh_cn": u"吸引生物", u"en_us": u"Pull entities", u"lzh": u"吸引生物",
        u"ja_jp": u"エンティティを引き寄せる", u"ru_ru": u"Притягивать сущностей"},
    u"potato_s_t.configuration.black_hole.pull_entities.tooltip": {
        u"zh_cn": u"是否把生物（含玩家）拉向奇点，默认开。关掉只吸方块。",
        u"en_us": u"Whether living entities (players included) are dragged towards the singularity. Off means blocks only.",
        u"lzh": u"是否拉生物（含玩家）向奇點，默開。關之則只吸方塊。",
        u"ja_jp": u"生物（プレイヤー含む）を特異点へ引き寄せるか（既定オン）。オフならブロックのみ。",
        u"ru_ru": u"Притягивать ли существ (включая игроков) к сингулярности. Выкл — только блоки."},
    u"potato_s_t.configuration.black_hole.void_damage": {
        u"zh_cn": u"视界虚空伤害", u"en_us": u"Void damage at the horizon",
        u"lzh": u"視界虛空傷害", u"ja_jp": u"地平面のヴォイドダメージ",
        u"ru_ru": u"Урон пустоты у горизонта"},
    u"potato_s_t.configuration.black_hole.void_damage.tooltip": {
        u"zh_cn": u"生物进到视界半径（6 格）内是否持续吃虚空伤害，默认开。关掉只是「拉过来」，不掉血。",
        u"en_us": u"Whether entities inside the event horizon (6 blocks) keep taking void damage. Off only pulls them.",
        u"lzh": u"生物入視界半徑（6 格）內是否續吃虛空傷害，默開。關之只「拉來」，不掉血。",
        u"ja_jp": u"地平面（6 ブロック）内のエンティティがヴォイドダメージを受け続けるか（既定オン）。",
        u"ru_ru": u"Получают ли сущности внутри горизонта событий (6 блоков) урон пустоты. Выкл — только притягивание."},
    # ── 引力装置 2 项 ──
    u"potato_s_t.configuration.gravity_device.charge_seconds": {
        u"zh_cn": u"蓄力时长（秒）", u"en_us": u"Charge-up time (seconds)",
        u"lzh": u"蓄力時長（息）", u"ja_jp": u"チャージ時間（秒）",
        u"ru_ru": u"Время зарядки (с)"},
    u"potato_s_t.configuration.gravity_device.charge_seconds.tooltip": {
        u"zh_cn": u"长按右键多久放出黑洞（5~60，默认 30）。",
        u"en_us": u"How long you hold right-click before the black hole appears (5-60, default 30).",
        u"lzh": u"長按右鍵幾息放黑洞（5~60，默 30）。",
        u"ja_jp": u"右クリック長押しでブラックホールが出るまでの秒数（5~60、既定 30）。",
        u"ru_ru": u"Сколько держать ПКМ до появления чёрной дыры (5-60, по умолчанию 30)."},
    u"potato_s_t.configuration.gravity_device.capacity_fe": {
        u"zh_cn": u"储能上限（FE）", u"en_us": u"Energy buffer (FE)",
        u"lzh": u"儲能上限（FE）", u"ja_jp": u"蓄電容量（FE）",
        u"ru_ru": u"Буфер энергии (FE)"},
    u"potato_s_t.configuration.gravity_device.capacity_fe.tooltip": {
        u"zh_cn": u"引力装置能存多少电（1,000,000~64,000,000，默认 8,000,000）。改小之后已经充进去的电按新上限算。",
        u"en_us": u"How much energy the device holds (1,000,000-64,000,000, default 8,000,000).",
        u"lzh": u"引力裝置能存幾電（1,000,000~64,000,000，默 8,000,000）。",
        u"ja_jp": u"重力装置が蓄えられる電力（1,000,000~64,000,000、既定 8,000,000）。",
        u"ru_ru": u"Сколько энергии вмещает устройство (1 000 000-64 000 000, по умолчанию 8 000 000)."},
    # ── 锂电池 3 项 ──
    u"potato_s_t.configuration.lithium_battery.per_block_fe": {
        u"zh_cn": u"单块容量（FE）", u"en_us": u"Capacity per block (FE)",
        u"lzh": u"單塊容量（FE）", u"ja_jp": u"1 ブロックあたりの容量（FE）",
        u"ru_ru": u"Ёмкость на блок (FE)"},
    u"potato_s_t.configuration.lithium_battery.per_block_fe.tooltip": {
        u"zh_cn": u"每块锂电池存多少电（1,000,000~20,000,000，默认 4,000,000）；多方块总容量 = 块数 × 本值。",
        u"en_us": u"Capacity of each battery block (1,000,000-20,000,000, default 4,000,000); total = blocks x this value.",
        u"lzh": u"每塊鋰電池存幾電（1,000,000~20,000,000，默 4,000,000）；多方塊總量 = 塊數 × 此值。",
        u"ja_jp": u"リチウム電池 1 ブロックの容量（1,000,000~20,000,000、既定 4,000,000）。総容量 = ブロック数 × この値。",
        u"ru_ru": u"Ёмкость одного блока батареи (1 000 000-20 000 000, по умолчанию 4 000 000); всего = блоков x это значение."},
    u"potato_s_t.configuration.lithium_battery.transfer_rate_fe": {
        u"zh_cn": u"每面速率（FE/t）", u"en_us": u"Transfer rate per side (FE/t)",
        u"lzh": u"每面速率（FE/t）", u"ja_jp": u"面あたりの転送速度（FE/t）",
        u"ru_ru": u"Скорость передачи (FE/t)"},
    u"potato_s_t.configuration.lithium_battery.transfer_rate_fe.tooltip": {
        u"zh_cn": u"每个面每 tick 最多进出多少电（1,024~1,048,576，默认 65,536）。",
        u"en_us": u"Maximum energy in or out per side per tick (1,024-1,048,576, default 65,536).",
        u"lzh": u"每面每 tick 至多進出幾電（1,024~1,048,576，默 65,536）。",
        u"ja_jp": u"1 面あたり 1 tick の最大入出力（1,024~1,048,576、既定 65,536）。",
        u"ru_ru": u"Максимум энергии на грань за тик (1 024-1 048 576, по умолчанию 65 536)."},
    u"potato_s_t.configuration.lithium_battery.max_size_blocks": {
        u"zh_cn": u"多方块块数上限", u"en_us": u"Max blocks per multiblock",
        u"lzh": u"多方塊塊數上限", u"ja_jp": u"マルチブロックの最大数",
        u"ru_ru": u"Максимум блоков в мультиблоке"},
    u"potato_s_t.configuration.lithium_battery.max_size_blocks.tooltip": {
        u"zh_cn": u"一座电池最多拼几块（27~800，默认 800）。",
        u"en_us": u"Maximum blocks in one battery multiblock (27-800, default 800).",
        u"lzh": u"一電池至多拼幾塊（27~800，默 800）。",
        u"ja_jp": u"1 つの電池マルチブロックの最大ブロック数（27~800、既定 800）。",
        u"ru_ru": u"Максимум блоков в одной батарее (27-800, по умолчанию 800)."},
    # ── 引力装置物品 tooltip 的动态两行（ZF186：数字不再写死）──
    u"tooltip.potato_s_t.gravity_device.stats": {
        u"zh_cn": u"按当前配置：容量 %s FE、蓄力 %s 秒",
        u"en_us": u"From the config: %s FE buffer, %s s charge-up",
        u"lzh": u"按今之設置：儲能 %s FE、蓄力 %s 息",
        u"ja_jp": u"現在の設定：容量 %s FE、チャージ %s 秒",
        u"ru_ru": u"По настройкам: %s FE, зарядка %s с"},
    u"tooltip.potato_s_t.gravity_device.one_shot.on": {
        u"zh_cn": u"一次性：放完就损坏（可在配置里关掉）",
        u"en_us": u"Single use: breaks after firing (can be turned off in the config)",
        u"lzh": u"一次性：放畢即壞（可於設置關之）",
        u"ja_jp": u"使い切り：発射後に壊れる（設定で変更可）",
        u"ru_ru": u"Одноразовое: ломается после выстрела (можно отключить в настройках)"},
    u"tooltip.potato_s_t.gravity_device.one_shot.off": {
        u"zh_cn": u"可重复使用：只抽干电力，装置不坏",
        u"en_us": u"Reusable: only the energy is drained, the device survives",
        u"lzh": u"可重複使用：只抽乾電力，裝置不壞",
        u"ja_jp": u"再利用可：電力だけ消費し、装置は壊れない",
        u"ru_ru": u"Многоразовое: тратится только энергия, устройство цело"},
}

# 老键的定点追加：静态 tooltip 里原来**没写蓄力时长**（只写了一次性 / 8M FE / 副手 / Shift+左键），
# 所以不是"改数字"而是"补一句" —— 补上「长按右键 30 秒」以及"这些都能在配置里改"。
# ⚠ 锚点必须**恰好不存在于现值**（追加不是替换）；现值非空也要自检。
APPEND = {
    u"zh_cn.json": (u"tooltip.potato_s_t.gravity_device",
                    u"；长按右键蓄力 30 秒放黑洞（蓄力时长/储能/是否一次性都能在配置里改）"),
    u"en_us.json": (u"tooltip.potato_s_t.gravity_device",
                    u"; hold right-click for 30 s to fire (charge time, buffer and single-use are configurable)"),
    u"ja_jp.json": (u"tooltip.potato_s_t.gravity_device",
                    u"。右クリック長押し 30 秒で発射（チャージ時間・容量・使い切りは設定で変更可）"),
    u"ru_ru.json": (u"tooltip.potato_s_t.gravity_device",
                    u"; удерживайте ПКМ 30 с для выстрела (время зарядки, буфер и одноразовость настраиваются)"),
    u"lzh.json": (u"tooltip.potato_s_t.gravity_device",
                  u"；長按右鍵三十息而放黑洞（蓄力時長／儲能／是否一次性皆可於設置改之）"),
}


def dump(d, tail_nl):
    s = json.dumps(d, ensure_ascii=False, indent=2)
    return s + (u"\n" if tail_nl else u"")


def main(argv):
    write = u"--write" in argv
    verify = u"--verify" in argv
    fails = []
    loaded = {}
    for f in FILES:
        p = os.path.join(LANG, f)
        raw = io.open(p, encoding="utf-8", newline=u"").read()
        d = json.loads(raw)
        tail_nl = raw.endswith(u"\n")
        style_ok = (dump(d, tail_nl) == raw)
        print(u"%-12s 键 %d  尾换行 %s  回环自证 %s" % (f, len(d), tail_nl, u"OK" if style_ok else u"**不符**"))
        if not style_ok:
            fails.append(u"%s：原样回环自证不符（格式口径不对，拒绝写盘）" % f)
        loaded[f] = (d, tail_nl, raw)
        # 缺键 / 缺语种自检
        for k, m in KEYS.items():
            if f[:-5] not in m:
                fails.append(u"%s：KEYS[%s] 没有 %s 的值" % (f, k, f[:-5]))

    if verify:
        # 只看"写完之后对不对"：新键齐 + 追加语恰好一次 + 五份键集合一致
        for f, (d, tail_nl, raw) in loaded.items():
            lang = f[:-5]
            for k, m in KEYS.items():
                if k not in d:
                    fails.append(u"%s：缺 %s" % (f, k))
                elif d[k] != m[lang]:
                    fails.append(u"%s：%s 的值与表不符" % (f, k))
            key, suffix = APPEND[f]
            n = d.get(key, u"").count(suffix)
            print(u"  追加语 %-14s 命中 %d 次" % (suffix[:14], n))
            if n != 1:
                fails.append(u"%s：追加语命中 %d 次（要求 1）" % (f, n))
        sets = {f: set(loaded[f][0]) for f in FILES}
        base = sets[u"zh_cn.json"]
        allowed = {u"language.name", u"language.region"}
        for f in FILES:
            miss = base - sets[f]
            extra = sets[f] - base - allowed
            if miss or extra:
                fails.append(u"%s 与 zh_cn 键集合不一致：缺 %s / 多 %s"
                             % (f, sorted(miss)[:4], sorted(extra)[:4]))
        print(u"五份键数：%s" % u"、".join(u"%s=%d" % (f, len(sets[f])) for f in FILES))
        print(u"模式：复验 ｜ 失败 = %d" % len(fails))
        for x in fails:
            print(u"  !! " + x)
        return 1 if fails else 0

    # 定点追加能不能命中（现值必须非空，且追加语还没在里面）
    hits = {}
    for f, (d, tail_nl, raw) in loaded.items():
        key, suffix = APPEND[f]
        cur = d.get(key)
        if not cur:
            fails.append(u"%s：找不到（或为空）%s" % (f, key))
            continue
        n = cur.count(suffix)
        hits[f] = n
        if n != 0:
            fails.append(u"%s：追加语已经在里面了（重复追加？）" % f)
        print(u"  追加锚点现值（前 60 字）：%s" % cur[:60].replace(u"\n", u" "))

    if fails:
        print(u"干跑就红了 ⇒ 不写盘。失败 = %d" % len(fails))
        for x in fails:
            print(u"  !! " + x)
        return 1

    for f in FILES:
        d, tail_nl, raw = loaded[f]
        lang = f[:-5]
        key, suffix = APPEND[f]
        d[key] = d[key] + suffix
        added = 0
        for k, m in KEYS.items():
            if k in d:
                if d[k] != m[lang]:
                    fails.append(u"%s：%s 已存在且值不同（不覆盖别人写的）" % (f, k))
                continue
            d[k] = m[lang]
            added += 1
        print(u"%-12s 新增 %d 键 ⇒ %d 键" % (f, added, len(d)))
        if write and not fails:
            io.open(os.path.join(LANG, f), "w", encoding="utf-8", newline=u"").write(dump(d, tail_nl))

    # 写后自证：①五份键集合一致（除 lzh 多 language.* 那两个）②新键都在 ③老键一个没丢
    if write:
        if fails:
            print(u"有失败 ⇒ 不写盘")
            for x in fails:
                print(u"  !! " + x)
            return 1
        sets = {}
        for f in FILES:
            p = os.path.join(LANG, f)
            d = json.loads(io.open(p, encoding="utf-8").read())
            sets[f] = set(d)
            for k in KEYS:
                if k not in d:
                    fails.append(u"%s 写后缺 %s" % (f, k))
            for k, v in loaded[f][0].items():
                if k not in d:
                    fails.append(u"%s 写后丢了老键 %s" % (f, k))
                elif k not in KEYS and d[k] != v:
                    fails.append(u"%s 写后老键 %s 的值变了" % (f, k))
        base = sets[u"zh_cn.json"] | {u"language.name", u"language.region"}
        for f in FILES:
            diff = sets[f] ^ base
            if diff:
                fails.append(u"%s 与 zh_cn 键集合不一致：%s" % (f, sorted(diff)[:6]))
        print(u"五份键数：%s" % u"、".join(u"%s=%d" % (f, len(sets[f])) for f in FILES))

    print(u"模式：%s ｜ 失败 = %d" % (u"落盘" if write else u"干跑", len(fails)))
    for x in fails:
        print(u"  !! " + x)
    return 1 if fails else 0


if __name__ == u"__main__":
    sys.exit(main(sys.argv[1:]))
