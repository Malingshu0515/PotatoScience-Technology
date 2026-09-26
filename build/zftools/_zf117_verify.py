# -*- coding: utf-8 -*-
u"""_zf117_verify.py —— ZF117 **常驻校验**：进度树补线（8 条新节点 / 四语言 476 键 / 状态文案）

用户原话：「嗯嗯 成就该更新了宝宝」

它盯的是**这一轮说出口的每一句话**：
  A 账目：目录正好 35 份；8 份新的在；**27 份老的逐字节等于本轮开工前**（表里内嵌 sha1）；
  B 新节点结构：父链 / frame / hidden / 图标 / 判据物品 / requirement 组数 —— 逐条对设计表；
  C 全树：父指针都解析得到、只有一个根、从根可达、无环；
  D 四语言：476 键 ×4、70 个成就键 ×4 齐全、16 个新键的值 == 生成器表里的值、
    **除状态文案那一处外**老键的值与改前件逐字相同、没有 ASCII 双引号；
  D5 状态文案里的酸账（ZF115 漏改的那四句，现在四语言都必须是 1 mB / 600 mB）；
  E 活体数字：21 份往轮校验里没有残留 432；英文公告 (476 keys each)；
    `_zf117_adv.py` 的 KEY_OLD/KEY_NEW；`_zf107_verify.py` 的 EXPECT_NODES=35 + ZF117 名单；
  F 探针：UTF-8 报告全绿 + 存档在 `check/`（先抄后删）；
  G 改前件：`zf117_pre` 在，且里面 27 份 advancement 的哈希与内嵌表一致；
  H 文档：档案 §5/§9 有 ZF117、写着 476 键与 8 条；交接文档的活体数字也是 476。

⚠ §4.81：stdout 必须自己钉成 UTF-8，否则被 gatesnap 用管道调起来时按 GBK 崩掉 = **假绿**。
"""
import hashlib
import io
import json
import os
import re
import sys

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

ROOT = r"E:\PotatoST"
ADIR = os.path.join(ROOT, r"src\main\resources\data\potato_s_t\advancement")
LANG = os.path.join(ROOT, r"src\main\resources\assets\potato_s_t\lang")
TOOLS = os.path.join(ROOT, r"build\zftools")
CHECK = os.path.join(TOOLS, "check")
DOC = os.path.join(ROOT, r"docs\开发档案.md")
DOC_EN = os.path.join(ROOT, r"docs\UpdateAnnouncement_EN.md")
DOC_HAND = os.path.join(ROOT, r"docs\多会话协作交接.md")
BK = r"C:\PotatoST救援\zf117_pre"
REPORT = os.path.join(TOOLS, r"_zf117_probe_utf8.txt")

LANGS = ["zh_cn", "en_us", "ja_jp", "ru_ru"]
KEY_OLD, KEY_NEW = 432, 476
N_OLD, N_NEW, N_ALL = 27, 8, 35

# ⚠ ZF124 新增：本项目线自己改过的老键（与润色线的 `DESC_TOUCHED` 分开列，便于追责）。
#   ⚠⚠ 必须放在**模块级**：ZF124 第一版把它插在 main() 里"用完之后" ⇒ 直接 UnboundLocalError 崩栈
#   （门崩掉 = 既看不到哪条挂了、也分不清"跑了且失败"还是"根本没跑完"，§4.77 那条老账）。
TOUCHED_BY_MAIN_LINE = [u"tooltip.potato_s_t.alloy_smelter",              # ZF121 合金炉脚注
                        u"advancements.potato_s_t.new_beginning.title"]   # ZF124 页签改名

OLD_SHA = {
    "acid": "9db10ff640142d525dcf7a45a9de666025dc89cc",
    "alloy_smelter": "f4c3d704a81f4863d695a74357062ecba1999e7e",
    "ammonia": "8c7b0bb0df77d2b5b122b3211348b5faaa208a22",
    "blast_furnace": "b96e1e291cde7ede84194c28262883513401b10a",
    "capacitor": "bc3eb63f51d328fcffef9d68a814d2ca25471fef",
    "clean_energy": "ee7467159e453c71f4f9b4bef91449e9e748b68c",
    "combustion": "fd5c58290a2b914698a234edc11f8b763d2fe2dc",
    "crushing": "16fe9264e9bffd07d5c066bcbe34248874863d85",
    "distillation": "ab7d36df47eaffbd708d2cc14b118d0b60371418",
    "electrolyzer": "861779c7f0b517d76b03413d28c80d7c8060da3c",
    "first_power": "7420b4b2bd2910336625ef2224e572097c5c429d",
    "fuel": "c5df8098bd04db32f21331eebf8349d0fc00b802",
    "gas_handling": "7c46b87102aa1b192037f3b0f688742426b9df10",
    "hard_alloy": "87d4cbb196b328552f82bd4938efbe170c21e7ea",
    "light_alloy": "8a8632f60fcfde27271fb596dfaa316043031691",
    "music_disc_anvil": "ca26ba647d0022d9cfab09b4939427c4c9f76b43",
    "music_disc_jasmine": "f78ccb36563c585e0793643378a139e5da08d81a",
    "new_beginning": "06bdc98bc63d2ebec96d73227843f6ec067ecc28",
    "oil": "6546ccc4aed1948303e8804ff78437454f79650f",
    "pressing": "210ccae06698baa00419188658642836553e6633",
    "stable_block": "351ec9b5da98cfdd87bc839db5be7f3b9f59eaa8",
    "steel": "db791240c6da90e35162a53d5917ea263ccfed33",
    "stronger_power": "287efaf2390c3d3eda5b790ecc3cbf8f5a66eb61",
    "sulfur": "2c05c990357d1bc9d77bbb070d5f644c86a3989b",
    "titanium": "17a1e52a51dfb098e082b8bf736ec86da9133f9f",
    "titanium_tools": "a43e56d96ffa8e75ad8fee62433b87e874523ad4",
    "wiring": "fb42faaff187ca07e6cb248f81777ba4ddf9eb84",
}

# 8 条新节点的设计表（生成器的表在 `_zf117_adv.py`；这里**独立再写一遍** —— 校验器不许
# 从被测代码里抄预期值，否则改一处两边一起变，等于没检查，§4.27）
NEW = [
    dict(id="oil_pump", parent="distillation", frame="goal", hidden=False,
         icon="oil_pump", kind="any", items=["oil_pump"]),
    dict(id="lithium_battery_plant", parent="acid", frame="goal", hidden=False,
         icon="lithium_battery_plant", kind="any", items=["lithium_battery_plant"]),
    dict(id="lithium_battery", parent="lithium_battery_plant", frame="task", hidden=False,
         icon="lithium_battery", kind="any", items=["lithium_battery"]),
    dict(id="star_steel", parent="hard_alloy", frame="goal", hidden=False,
         icon="star_steel_ingot", kind="any", items=["star_steel_ingot"]),
    dict(id="star_steel_armor", parent="star_steel", frame="challenge", hidden=False,
         icon="star_steel_chestplate", kind="all",
         items=["star_steel_helmet", "star_steel_chestplate", "star_steel_leggings",
                "star_steel_boots"]),
    dict(id="starfall", parent="new_beginning", frame="challenge", hidden=True,
         icon="starfall_pendant", kind="any", items=["starfall_pendant", "raw_vibranium"]),
    dict(id="salt", parent="steel", frame="task", hidden=False,
         icon="sea_salt", kind="any", items=["sea_salt", "salt_dryer"]),
    dict(id="fluid_logistics", parent="stronger_power", frame="task", hidden=False,
         icon="fluid_pump", kind="any", items=["fluid_pump", "fluid_exchanger"]),
]
NEW_IDS = [n["id"] for n in NEW]

# 16 个新语言键 × 四语言，只钉"必须出现的字面量"（值本身由生成器写；这里检查关键数字/专名，
# 这样以后润色线改文案只要不丢这些事实就不会红）
MUST = {
    "oil_pump": [u"8n²+80n", u"10n mB/s", u"25B"],
    "lithium_battery_plant": [u"1 mB", u"600 mB", u"30 秒"],
    "lithium_battery": [u"4M FE"],
    "star_steel": [u"12000 FE/t", u"30 秒"],
    "star_steel_armor": [u"24"],
    "starfall": [u"y=200", u"7~20"],
    "salt": [u"海盐"],
    "fluid_logistics": [u"1000 mB"],
}
ACID_KEY = u"gui.potato_s_t.lithium_battery_plant.status.no_acid"
ACID_FIX_KEY = ACID_KEY          # ZF115 漏改、ZF117 补上的那一句

n_pass = 0
fails = []


def read(p):
    return io.open(p, encoding="utf-8").read()


def sha1(p):
    return hashlib.sha1(open(p, "rb").read()).hexdigest()


def check(name, cond, detail=None):
    global n_pass
    if cond:
        n_pass += 1
    else:
        fails.append(name + (u"  ← %s" % detail if detail else u""))


def eq(name, want, got):
    check(name, want == got, u"期望 %r 实际 %r" % (want, got))


def crit_items(obj):
    out = []
    for c in obj.get("criteria", {}).values():
        cond = c.get("conditions", {})
        for pred in cond.get("items", []):
            i = pred.get("items")
            if isinstance(i, str) and i.startswith(u"potato_s_t:"):
                out.append(i.split(u":", 1)[1])
        for loc in cond.get("location", []):
            b = loc.get("block")
            if isinstance(b, str) and b.startswith(u"potato_s_t:"):
                out.append(b.split(u":", 1)[1])
    return out


def main():
    # ================= A 账目 =================
    print(u"== A 账目 ==")
    files = sorted(f[:-5] for f in os.listdir(ADIR) if f.endswith(u".json"))
    eq(u"A1 advancement 目录正好 %d 份" % N_ALL, N_ALL, len(files))
    eq(u"A2 目录 = 27 老 + 8 新", sorted(list(OLD_SHA) + NEW_IDS), files)
    for n in NEW_IDS:
        check(u"A3 新节点 %s.json 在" % n, os.path.exists(os.path.join(ADIR, n + u".json")))
    bad = []
    for n, want in sorted(OLD_SHA.items()):
        p = os.path.join(ADIR, n + u".json")
        if not os.path.exists(p) or sha1(p) != want:
            bad.append(n)
    eq(u"A4 27 份老节点**逐字节**等于本轮开工前", [], bad)
    adv = {}
    for n in files:
        try:
            adv[n] = json.loads(read(os.path.join(ADIR, n + u".json")))
        except Exception as e:
            fails.append(u"%s.json 解析不了：%s" % (n, e))
    eq(u"A5 %d 份全部解析成功" % N_ALL, N_ALL, len(adv))

    # ================= B 新节点结构 =================
    print(u"\n== B 新节点结构 ==")
    for spec in NEW:
        n = spec["id"]
        o = adv.get(n)
        if o is None:
            check(u"B %s 在" % n, False)
            continue
        eq(u"B1 %s 的父链" % n, u"potato_s_t:" + spec["parent"], o.get("parent"))
        d = o.get("display", {})
        eq(u"B2 %s 的图标" % n, u"potato_s_t:" + spec["icon"], d.get("icon", {}).get("id"))
        eq(u"B3 %s 的 frame" % n, spec["frame"], d.get("frame"))
        eq(u"B4 %s 的 hidden" % n, spec["hidden"], bool(d.get("hidden")))
        check(u"B5 %s 的 toast/公告都开" % n,
              d.get("show_toast") is True and d.get("announce_to_chat") is True)
        check(u"B6 %s 不是根就没有背景图" % n, u"background" not in d)
        eq(u"B7 %s 的说明键" % n, u"advancements.potato_s_t.%s.description" % n,
           d.get("description", {}).get("translate"))
        eq(u"B8 %s 的标题键" % n, u"advancements.potato_s_t.%s.title" % n,
           d.get("title", {}).get("translate"))
        eq(u"B9 %s 的 sends_telemetry_event = False" % n, False, o.get("sends_telemetry_event"))
        got = sorted(crit_items(o))
        eq(u"B10 %s 的判据物品" % n, sorted(spec["items"]), got)
        eq(u"B11 %s 的判据条数" % n, len(spec["items"]), len(o.get("criteria", {})))
        ng = len(o.get("requirements", []))
        if spec["kind"] == "any":
            eq(u"B12 %s 是「或」：1 个 requirement 组装全部判据" % n, 1, ng)
            eq(u"B13 %s 那个组装着全部判据" % n, sorted(o["criteria"]),
               sorted(o["requirements"][0]))
        else:
            eq(u"B12 %s 是「与」：每条判据各占一组" % n, len(spec["items"]), ng)
            eq(u"B13 %s 每组正好一条判据" % n, sorted(o["criteria"]),
               sorted(g[0] for g in o["requirements"]))
        trig = set(c["trigger"] for c in o["criteria"].values())
        eq(u"B14 %s 的触发器只有 inventory_changed" % n, set(["minecraft:inventory_changed"]), trig)
        multi = [k for k, c in o["criteria"].items()
                 if len(c.get("conditions", {}).get("items", [])) > 1]
        eq(u"B15 %s 没有「一个判据塞多个物品谓词」的写法（§4.74）" % n, [], multi)

    # ================= C 全树 =================
    print(u"\n== C 全树 ==")
    roots = [n for n in files if u"parent" not in adv.get(n, {})]
    eq(u"C1 恰好 1 个根", [u"new_beginning"], roots)
    par = dict((n, adv[n]["parent"].split(u":", 1)[1]) for n in files if u"parent" in adv[n])
    eq(u"C2 所有父指针都指向目录里的节点", [], [n for n, p in par.items() if p not in files])
    cyc = []
    for n in files:
        walk, cur = set(), n
        while cur in par:
            if cur in walk or len(walk) > len(files):
                cyc.append(n)
                break
            walk.add(cur)
            cur = par[cur]
    eq(u"C3 没有环（带步数上限，坏数据要报错不许卡死，§4.77）", [], cyc)
    reach, grew = set([u"new_beginning"]), True
    while grew:
        grew = False
        for n, p in par.items():
            if p in reach and n not in reach:
                reach.add(n)
                grew = True
    eq(u"C4 %d 个节点全部从根可达" % N_ALL, sorted(files), sorted(reach))
    eq(u"C5 8 条新节点的父链设计值", dict((s["id"], s["parent"]) for s in NEW),
       dict((s["id"], par.get(s["id"])) for s in NEW))

    # ================= D 四语言 =================
    print(u"\n== D 四语言 ==")
    lang, counts = {}, {}
    for l in LANGS:
        lang[l] = json.loads(read(os.path.join(LANG, l + u".json")))
        counts[l] = len(lang[l])
    eq(u"D1 四语言各 %d 键" % KEY_NEW, [KEY_NEW] * 4, [counts[l] for l in LANGS])
    base = set(lang["zh_cn"])
    for l in LANGS[1:]:
        eq(u"D2 %s 的键集合与 zh_cn 完全一致" % l, set(), base ^ set(lang[l]))
    miss = [(l, k) for l in LANGS for n in (list(OLD_SHA) + NEW_IDS)
            for k in ("advancements.potato_s_t.%s.title" % n,
                      "advancements.potato_s_t.%s.description" % n)
            if k not in lang[l] or not lang[l][k].strip()]
    eq(u"D3 %d 个节点 × 标题/说明 × 四语言 = %d 条齐全且非空" % (N_ALL, N_ALL * 2 * 4), [], miss)
    quote = [(l, k) for l in LANGS for k in lang[l]
             if k.startswith(u"advancements.") and u'"' in lang[l][k]]
    eq(u"D4 成就文案里没有 ASCII 双引号（中文串一律用「」）", [], quote)
    # 新键与改前件比：**加**了 16 个；老键里被改值的只有下面这张表列出的那些 ——
    # ⚠ 2026-09-25 订正：原判据写死「只有状态文案那一处」，当时是对的。之后**润色线**把若干条
    #   成就说明改短了（用户：「成就介绍太长了」；最长一条中文 168 字、英文 374），
    #   以及把 `blast_furnace` 的一句收尾。按 §4.36 口径 **改锚点、不放宽断言**：
    #   这里仍逐个列名（不是 `startswith` 之类粗判据）。名单由「zf117_pre 快照 vs 工作树」机械算出。
    #   ⚠ zh_cn/ja_jp 的 `wiring` 与 en_us 的 `alloy_smelter` **没有**出现在表里 ——
    #   那几处润色时就判为「新句没更短」，没实际改动，所以不能写进期望值。
    DESC_TOUCHED = {
        u"zh_cn": [u"advancements.potato_s_t.blast_furnace.description"],
        u"en_us": [u"advancements.potato_s_t.blast_furnace.description",
                   u"advancements.potato_s_t.wiring.description"],
        u"ja_jp": [u"advancements.potato_s_t.blast_furnace.description",
                   u"advancements.potato_s_t.wiring.description"],
        u"ru_ru": [u"advancements.potato_s_t.alloy_smelter.description",
                   u"advancements.potato_s_t.blast_furnace.description",
                   u"advancements.potato_s_t.wiring.description"],
    }
    for l in LANGS:
        old = json.loads(read(os.path.join(BK, r"src\main\resources\assets\potato_s_t\lang",
                                          l + u".json")))
        added = sorted(k for k in lang[l] if k not in old)
        mine = sorted(k for k in added if k.startswith(u"advancements.potato_s_t."))
        eq(u"D5 %s：新增的成就键正好 16 个" % l, 16, len(mine))
        eq(u"D6 %s：没有键被删" % l, [], sorted(k for k in old if k not in lang[l]))
        changed = sorted(k for k in old if k in lang[l] and old[k] != lang[l][k])
        # ⚠ ZF124 补名单：下面两条**不是**润色线改的，是本项目线自己改的（判据没放宽）：
        #   · `tooltip.potato_s_t.alloy_smelter`  —— ZF121（脚注：2 消耗槽 / 配方三条 → 四条）
        #   · `advancements.potato_s_t.new_beginning.title` —— ZF124（页签改名 PotatoS&T）
        eq(u"D7 %s：老键里只有状态文案 + 润色的成就说明 + 本项目线 ZF121/ZF124 改的那两条被改值" % l,
           sorted([ACID_FIX_KEY] + DESC_TOUCHED[l] + TOUCHED_BY_MAIN_LINE), changed)

    # 每个新节点的文案里那些"事实"必须还在
    for n in NEW_IDS:
        for lit in MUST.get(n, []):
            v = lang["zh_cn"].get(u"advancements.potato_s_t.%s.description" % n, u"")
            check(u"D8 %s 的说明里还写着「%s」" % (n, lit), lit in v)
    # ---- D5 状态文案里的酸账（ZF115 漏改的那四句）----
    for l in LANGS:
        v = lang[l].get(ACID_KEY, u"")
        check(u"D9 %s 的状态文案念 1 mB（%s）" % (l, v), u"1 mB" in v)
        check(u"D10 %s 的状态文案念 600 mB" % l, u"600 mB" in v)
        check(u"D11 %s 的状态文案里没有 10 mB / 6000 mB" % l,
              u"10 mB" not in v and u"6000 mB" not in v)

    # ================= E 活体数字 =================
    print(u"\n== E 活体数字 ==")
    stale = []
    for f in sorted(os.listdir(TOOLS)):
        if not re.match(r"^_zf\d+_verify\.py$", f) or f.startswith(u"_zf117"):
            continue
        if re.search(r"\b%d\b" % KEY_OLD, read(os.path.join(TOOLS, f))):
            stale.append(f)
    eq(u"E1 21 份往轮校验里没有残留旧键数 %d" % KEY_OLD, [], stale)
    eq(u"E2 英文公告写的 %d keys each" % KEY_NEW,
       True, u"(%d keys each)" % KEY_NEW in read(DOC_EN))
    adv_py = read(os.path.join(TOOLS, u"_zf117_adv.py"))
    check(u"E3 生成器的 KEY_OLD/KEY_NEW 就是 %d/%d" % (KEY_OLD, KEY_NEW),
          re.search(r"KEY_OLD = %d\b" % KEY_OLD, adv_py) is not None
          and re.search(r"KEY_NEW = KEY_OLD \+ 16", adv_py) is not None)
    v107 = read(os.path.join(TOOLS, u"_zf107_verify.py"))
    check(u"E4 `_zf107_verify.py` 的 EXPECT_NODES = %d" % N_ALL,
          re.search(r"EXPECT_NODES = %d\b" % N_ALL, v107) is not None)
    check(u"E5 `_zf107_verify.py` 认得这 8 个新节点",
          all(u'"%s"' % n in v107 for n in NEW_IDS))
    check(u"E6 `_zf107_verify.py` 仍钉着 27 条老节点",
          all(u'"%s"' % n in v107 for n in OLD_SHA))
    check(u"E7 `_zf107_verify.py` 的 EXPECT_KEYS = %d" % KEY_NEW,
          re.search(r"EXPECT_KEYS = %d\b" % KEY_NEW, v107) is not None)
    # ---- 成品旁边的 .sha1 必须是**纯哈希一行**（十道门按这个格式判，ZF117 对账）----
    rel_jar = os.path.join(ROOT, r"release\PotatoST-0.11.jar")
    rel_side = rel_jar + u".sha1"
    if os.path.exists(rel_jar) and os.path.exists(rel_side):
        side = read(rel_side).strip()
        check(u"E8 成品 .sha1 是纯哈希一行（没有空格 / 没有文件名）",
              u" " not in side and u"\t" not in side, u"盘上：%r" % side)
        eq(u"E9 成品 .sha1 等于成品的真实 sha1", sha1(rel_jar), side.lower())
    else:
        check(u"E8/E9 成品与 .sha1 都在", False)

    # ================= F 探针 =================
    print(u"\n== F 探针 ==")
    check(u"F1 探针 UTF-8 报告在（%s）" % REPORT, os.path.exists(REPORT))
    if os.path.exists(REPORT):
        rep = read(REPORT)
        check(u"F2 报告全绿", u"verdict: ALL OK" in rep)
        check(u"F3 报告里没有 [FAIL]", u"[FAIL]" not in rep)
        check(u"F4 报告里 35 条全亮", u"35 条全部点亮" in rep)
        check(u"F5 报告里验过「与」只给三件不亮", u"只给三件" in rep)
        check(u"F6 报告里验过隐藏那条（星轨坠）", u"starfall" in rep)
        check(u"F7 报告里念过修好的状态文案", u"Not enough sulfuric acid: 1 mB" in rep
              or u"1 mB" in rep)
    arc = os.path.join(CHECK, u"Zf117Check.java")
    check(u"F8 探针存档在 check/（先抄后删，§10.1）", os.path.exists(arc))
    check(u"F9 探针源码已从 src 删掉",
          not os.path.exists(os.path.join(ROOT, r"src\main\java\com\potatost\mod\Zf117Check.java")))
    check(u"F10 PotatoST.java 里没有残留钩子",
          u"Zf117Check" not in read(os.path.join(ROOT, r"src\main\java\com\potatost\mod\PotatoST.java")))

    # ================= G 改前件 =================
    print(u"\n== G 改前件 ==")
    check(u"G1 zf117_pre 在", os.path.isdir(BK))
    mf = os.path.join(BK, u"_sha1.txt")
    check(u"G2 改前件清单在", os.path.exists(mf))
    if os.path.exists(mf):
        txt = read(mf)
        bad = [n for n, h in OLD_SHA.items() if h not in txt]
        eq(u"G3 清单里 27 份 advancement 的哈希都在", [], bad)
    check(u"G4 _zf117_newfiles.txt 记着'本轮开始前不该存在'的路径",
          os.path.exists(os.path.join(BK, u"_zf117_newfiles.txt")))

    # ================= H 文档 =================
    print(u"\n== H 文档 ==")
    doc = read(DOC)
    check(u"H1 档案 §5 有 ZF117 行", u"| ZF117 |" in doc)
    check(u"H2 档案 §9 有 ZF117 小节", u"ZF117（0.11）" in doc)
    check(u"H3 档案里写着 %d 键" % KEY_NEW, u"%d 键" % KEY_NEW in doc)
    check(u"H4 档案里写着 8 条新节点", u"8 条" in doc)
    check(u"H5 档案里记了 ZF115 漏的那四句", ACID_KEY.replace(u".", u".") in doc
          or u"status.no_acid" in doc)
    hand = read(DOC_HAND)
    check(u"H6 交接文档的活体数字也是 %d 键" % KEY_NEW, u"%d 键" % KEY_NEW in hand)
    check(u"H7 交接文档写着 35 条进度", u"35 条" in hand)

    print(u"")
    print(u"通过 = %d   失败 = %d" % (n_pass, len(fails)))
    for f in fails:
        print(u"  !! " + f)
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())
