# -*- coding: utf-8 -*-
u"""_zf118_verify.py —— ZF118 **常驻校验**：星轨坠的合成配方（+ 生成器表与盘对账）

用户原话：「星轨坠配方；中间一个下界之星 上下左右各一个星璨钢 四角放岩浆块」

它盯的是**这一轮说出口的每一句话**：
  A 配方本体：type / category / pattern / **按位置**的每一格 / 产物 / 与生成器表逐字节一致；
  B 全局账：60 份 / crafting_shaped 54；59 份旧配方逐字节等于改前件；没有第二条产出星轨坠的配方；
    **生成器表里每一条都与盘上 JSON 逐字节一致**（新常驻检查：以后谁手改 JSON 当场被抓）、
    目录里没有多出来的野文件；
  C 语言：四语言仍 492 键（加配方不该动文案）；星轨坠那条进度的关键事实还在；
  D 文档：档案 §5/§9、英文公告不再写 no recipe yet、交接文档的活体数字；
  E 探针：UTF-8 报告全绿 + 存档在 check/（先抄后删）+ src 无残留 + PotatoST 无钩子；
  F 改前件：zf118_pre 在，59 份旧配方的哈希都在清单里。

⚠ §4.81：stdout 必须自己钉成 UTF-8（被 gatesnap 用管道调起来时按 GBK 崩 = 假绿）。
⚠ §4.27：预期值**不抄被测代码** —— 图纸在这里独立再写一遍（pattern 与 key 的对应关系逐格核）。
"""
import hashlib
import importlib.util
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
RDIR = os.path.join(ROOT, r"src\main\resources\data\potato_s_t\recipe")
LANG = os.path.join(ROOT, r"src\main\resources\assets\potato_s_t\lang")
ADIR = os.path.join(ROOT, r"src\main\resources\data\potato_s_t\advancement")
TOOLS = os.path.join(ROOT, r"build\zftools")
CHECK = os.path.join(TOOLS, "check")
JAVA = os.path.join(ROOT, r"src\main\java\com\potatost\mod")
DOC = os.path.join(ROOT, r"docs\开发档案.md")
DOC_HAND = os.path.join(ROOT, r"docs\多会话协作交接.md")
DOC_EN = os.path.join(ROOT, r"docs\UpdateAnnouncement_EN.md")
GEN = os.path.join(TOOLS, r"_zf45_recipes.py")
BK = r"C:\PotatoST救援\zf118_pre"
BK_RDIR = os.path.join(BK, r"src\main\resources\data\potato_s_t\recipe")
REPORT = os.path.join(TOOLS, r"_zf118_probe_utf8.txt")

NAME = "starfall_pendant"
KEY_NEW = 492            # 四语言键数（ZF117 之后的活体数字；加配方不该动它）
N_RECIPE = 60            # 配方份数：ZF118 之前 59
N_SHAPED = 54            # 其中 crafting_shaped：ZF118 之前 53
N_TABLE = 31             # 生成器表条数：ZF118 之前 30

# 图纸（**独立再写一遍**，不抄 JSON 也不抄生成器表）
PATTERN = ["MSM", "SNS", "MSM"]
CELLS = {                # 位置 → 期望的物品 id
    (0, 0): "minecraft:magma_block", (0, 1): "potato_s_t:star_steel_ingot",
    (0, 2): "minecraft:magma_block",
    (1, 0): "potato_s_t:star_steel_ingot", (1, 1): "minecraft:nether_star",
    (1, 2): "potato_s_t:star_steel_ingot",
    (2, 0): "minecraft:magma_block", (2, 1): "potato_s_t:star_steel_ingot",
    (2, 2): "minecraft:magma_block",
}
RESULT = {"id": "potato_s_t:starfall_pendant", "count": 1}
VANILLA = ["minecraft:magma_block", "minecraft:nether_star"]

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


def load_gen():
    spec = importlib.util.spec_from_file_location("zf45_recipes", GEN)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def main():
    # ================= A 配方本体 =================
    print(u"== A 配方本体 ==")
    p = os.path.join(RDIR, NAME + ".json")
    check(u"A1 %s.json 在" % NAME, os.path.exists(p))
    if not os.path.exists(p):
        return report()
    raw = read(p)
    obj = json.loads(raw)
    eq(u"A2 type", "minecraft:crafting_shaped", obj.get("type"))
    eq(u"A3 category", "misc", obj.get("category"))
    eq(u"A4 pattern 逐格", PATTERN, obj.get("pattern"))
    key = {k: v.get("item") for k, v in obj.get("key", {}).items()}
    eq(u"A5 key 表正好三个字母", ["M", "N", "S"], sorted(key))
    eq(u"A6 M = 岩浆块", u"minecraft:magma_block", key.get("M"))
    eq(u"A7 N = 下界之星", u"minecraft:nether_star", key.get("N"))
    eq(u"A8 S = 星璨钢锭", u"potato_s_t:star_steel_ingot", key.get("S"))
    eq(u"A9 result", RESULT, obj.get("result"))
    # **按位置**逐格核（pattern × key → 每一格该是什么）——只核 key 表是核不出"哪格放哪"的
    for (r, c), want in sorted(CELLS.items()):
        ch = obj["pattern"][r][c]
        got = key.get(ch)
        check(u"A10 (%d,%d) 那格是 %s（现在 %s）" % (r, c, want, got), got == want)
    eq(u"A11 九格全被 pattern 用到", set(u"".join(PATTERN)), set(key))
    # 与生成器表逐字节一致
    gen = load_gen()
    entry = [r for r in gen.RECIPES if r["name"] == NAME]
    eq(u"A12 生成器表里有这一条", 1, len(entry))
    if entry:
        problems = []
        gname, gobj = gen.build(entry[0], problems)
        gtext = json.dumps(gobj, ensure_ascii=False, indent=2) + u"\n"
        eq(u"A13 表重跑 == 盘上 JSON（逐字节）", gtext, raw)
        check(u"A14 表重跑没有 problems", not problems, u"%s" % problems)
    ids = set()
    for fn in ("ModItems.java", "ModBlocks.java", "ModArmorItems.java", "PotatoSTOres.java"):
        fp = os.path.join(JAVA, fn)
        if os.path.exists(fp):
            ids |= set(re.findall(r'register\(\s*"([a-z0-9_]+)"', read(fp)))
    check(u"A15 产物 id 在本模组注册过（starfall_pendant）", u"starfall_pendant" in ids)
    vm = gen.vanilla_models()
    for vid in VANILLA:
        # vanilla_models() 返回的是**模型名**（不带命名空间）：assets/minecraft/models/item/<name>.json
        check(u"A16 原版 id 真实存在：%s" % vid, vid.split(u":", 1)[1] in vm)

    # ================= B 全局账 =================
    print(u"\n== B 全局账 ==")
    files = sorted(n for n in os.listdir(RDIR) if n.endswith(u".json"))
    eq(u"B1 配方份数 %d" % N_RECIPE, N_RECIPE, len(files))
    shaped = [n for n in files if json.loads(read(os.path.join(RDIR, n))).get("type")
              == "minecraft:crafting_shaped"]
    eq(u"B2 crafting_shaped %d 条" % N_SHAPED, N_SHAPED, len(shaped))
    # 59 份旧配方逐字节等于改前件
    missing_bk, changed = [], []
    for n in files:
        if n == NAME + ".json":
            continue
        bp = os.path.join(BK_RDIR, n)
        if not os.path.exists(bp):
            missing_bk.append(n)
        elif sha1(os.path.join(RDIR, n)) != sha1(bp):
            changed.append(n)
    eq(u"B3 改前件里 59 份旧配方都在", [], missing_bk)
    eq(u"B4 59 份旧配方逐字节未变（本轮只新增一份）", [], changed)
    if os.path.exists(os.path.join(BK, u"_sha1.txt")):
        mf = read(os.path.join(BK, u"_sha1.txt"))
        eq(u"B5 改前件清单里记着那 59 份的哈希",
           [], [n for n in files if n != NAME + ".json" and n not in mf])
    # 没有第二条配方产出星轨坠
    others = [n for n in files
              if n != NAME + ".json"
              and json.loads(read(os.path.join(RDIR, n))).get("result", {}).get("id")
              == RESULT["id"]]
    eq(u"B6 没有第二条配方产出星轨坠", [], others)
    # **生成器表 ↔ 盘**：整表逐条比（新常驻检查）
    gen = load_gen()
    eq(u"B7 生成器表条数 %d" % N_TABLE, N_TABLE, len(gen.RECIPES))
    bad = []
    for r in gen.RECIPES:
        problems = []
        gname, gobj = gen.build(r, problems)
        gtext = json.dumps(gobj, ensure_ascii=False, indent=2) + u"\n"
        fp = os.path.join(RDIR, gname + ".json")
        if not os.path.exists(fp):
            bad.append(gname + u"(缺)")
        elif read(fp) != gtext:
            bad.append(gname + u"(不一致)")
    eq(u"B8 生成器表里的每一条都与盘上 JSON 逐字节一致", [], bad)
    check(u"B9 生成器文件头那句「表里现在 N 条」与表一致",
          u"表里现在 %d 条" % len(gen.RECIPES) in read(GEN))
    check(u"B10 生成器表里也写了 ZF118 的来源与图纸注释",
          u"ZF118" in read(GEN) and u'pattern=["MSM", "SNS", "MSM"]' in read(GEN))

    # ================= C 语言 / 进度 =================
    print(u"\n== C 语言 / 进度 ==")
    counts = {}
    for l in ("zh_cn", "en_us", "ja_jp", "ru_ru"):
        counts[l] = len(json.loads(read(os.path.join(LANG, l + u".json"))))
    eq(u"C1 四语言仍各 %d 键（加配方不该动文案）" % KEY_NEW, [KEY_NEW] * 4,
       [counts[l] for l in ("zh_cn", "en_us", "ja_jp", "ru_ru")])
    st = json.loads(read(os.path.join(ADIR, "starfall.json")))
    check(u"C2 星轨坠那条进度还在、判据没被本轮动过",
          st["criteria"]["got0"]["conditions"]["items"][0]["items"]
          == u"potato_s_t:starfall_pendant")
    zh = json.loads(read(os.path.join(LANG, "zh_cn.json")))
    desc = zh.get(u"advancements.potato_s_t.starfall.description", u"")
    for lit in (u"y=200", u"7~20"):
        check(u"C3 那条进度的说明里还写着「%s」" % lit, lit in desc)

    # ================= D 文档 =================
    print(u"\n== D 文档 ==")
    doc = read(DOC)
    check(u"D1 档案 §5 有 ZF118 行", u"| ZF118 |" in doc)
    check(u"D2 档案 §9 有 ZF118 小节", u"ZF118（0.11）" in doc)
    check(u"D3 档案里写着这张图纸", u"MSM" in doc and u"下界之星" in doc)
    check(u"D4 档案里记了生成器表那条陈旧账", u"lithium_battery" in doc and u"手写" in doc)
    en = read(DOC_EN)
    check(u"D5 英文公告不再说星轨坠「no recipe yet」", u"pendant (no recipe yet)" not in en)
    check(u"D6 英文公告写了它的配方", u"Nether Star" in en or u"nether star" in en)
    hand = read(DOC_HAND)
    check(u"D7 交接文档的配方活体数字已到 %d 份 / %d 条" % (N_RECIPE, N_SHAPED),
          (u"%d 份" % N_RECIPE) in hand and (u"%d 条" % N_SHAPED) in hand)
    check(u"D8 交接文档记了 ZF118", u"ZF118" in hand)

    # ================= E 探针 =================
    print(u"\n== E 探针 ==")
    check(u"E1 探针 UTF-8 报告在（%s）" % REPORT, os.path.exists(REPORT))
    if os.path.exists(REPORT):
        rep = read(REPORT)
        check(u"E2 报告全绿", u"verdict: ALL OK" in rep)
        check(u"E3 报告里没有 [FAIL]", u"[FAIL]" not in rep)
        check(u"E4 报告里验过「形状匹配」（照着图纸摆一遍能匹配到这条配方）",
              u"getRecipeFor" in rep or u"形状" in rep)
        check(u"E5 报告里验过负向对照（换掉中心那颗星就不该匹配）", u"负向" in rep)
        check(u"E6 报告里验过「合成出来的东西真能点亮星轨坠那条进度」",
              u"starfall" in rep and u"进度" in rep)
    arc = os.path.join(CHECK, u"Zf118Check.java")
    check(u"E7 探针存档在 check/（先抄后删，§10.1）", os.path.exists(arc))
    check(u"E8 探针源码已从 src 删掉", not os.path.exists(os.path.join(JAVA, u"Zf118Check.java")))
    check(u"E9 PotatoST.java 里没有残留钩子",
          u"Zf118Check" not in read(os.path.join(JAVA, u"PotatoST.java")))

    # ================= F 改前件 =================
    print(u"\n== F 改前件 ==")
    check(u"F1 zf118_pre 在", os.path.isdir(BK))
    check(u"F2 改前件清单在", os.path.exists(os.path.join(BK, u"_sha1.txt")))
    check(u"F3 _zf118_newfiles.txt 记着「本轮开始前不该存在」的路径",
          os.path.exists(os.path.join(BK, u"_zf118_newfiles.txt")))
    check(u"F4 改前件里抄了 59 份配方", len([n for n in os.listdir(BK_RDIR)
                                            if n.endswith(u".json")]) == N_RECIPE - 1)
    return report()


def report():
    print(u"")
    print(u"通过 = %d   失败 = %d" % (n_pass, len(fails)))
    for f in fails:
        print(u"  !! " + f)
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())
