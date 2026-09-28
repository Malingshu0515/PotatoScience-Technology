# -*- coding: utf-8 -*-
r"""ZF155 侦察（**只读，一个字节都不改**）：通用升级模板能不能"真·通用"。

用户需求（原话）：
  「加个通用升级模板 所有mod需要升级模板升级都可以用它 如果有冲突则不可以使用
    （振金剑配方：钛合金剑用这个和振金升级；之前所有振金装备的下界合金模板也改成这个）
    获取方式：下界合金升级模板 围一圈铝锭」

已定方向（用户选）：**真·通用** —— 全游戏所有 smithing 升级（含原版下界合金）都能用通用模板；
有冲突（同 base+addition 撞不同结果）的 **不可以使用**。

本脚本要钉死的事实（全部从源码实证，不凭记忆）：
  ① 原版下界合金升级配方到底是不是数据文件？在哪？几条？id 是什么？
  ② SmithingTransformRecipe 的构造器/字段/matches 长什么样？能不能构造一份"加宽模板槽"的副本？
  ③ SmithingTrimRecipe（盔甲纹饰）是不是动态配方？要不要一起管？
  ④ RecipeManager 内部表能不能改（字段是不是 final、inner map 是不是不可变）？
  ⑤ NeoForge 有没有"改配方表"的官方挂点（事件/API）？还是只能反射？
  ⑥ 服务端把配方同步给客户端（JEI）走的是哪张表？改完客户端能不能看见？
  ⑦ 锻造台取配方的调用链（ItemCombinerMenu/SmithingMenu）到底查的哪个方法？

跑法：python build\zftools\_zf155_recon.py
产出：_zf155_recon.txt（UTF-8，给人看）；控制台只打 ASCII 进度（§4.50）
"""

import io
import os
import sys
import zipfile

PROJ = r"E:\PotatoST"
ZFTOOLS = os.path.join(PROJ, "build", "zftools")
SOURCES_JAR = os.path.join(PROJ, "build", "neoForm",
                           "neoFormJoined1.21.1-20240808.144430", "sources.jar")
CLIENT_EXTRA = (r"E:\gradle-home\caches\ng_execute"
                r"\b618213606478f4c62e6974e895a173b103a054e4a7be1bf630f2feeb65c5c3b"
                r"\client-extra.jar")
GRADLE_HOME = r"E:\gradle-home"

OUT = []
OUTF = os.path.join(ZFTOOLS, "_zf155_recon.txt")


def w(line=u""):
    OUT.append(line)


def flush():
    text = u"\n".join(OUT) + u"\n"
    with io.open(OUTF, "w", encoding="utf-8", newline="\n") as fh:
        fh.write(text)
    sys.stdout.write("wrote %s (%d lines)\n" % (OUTF, len(OUT)))


def find_jar(name_part, roots, depth_limit=8):
    """在受限深度里找一个 jar（避免全盘 walk）。"""
    hits = []
    for root in roots:
        base_depth = root.rstrip("\\").count("\\")
        for dirpath, dirnames, filenames in os.walk(root):
            if dirpath.count("\\") - base_depth > depth_limit:
                dirnames[:] = []
                continue
            for fn in filenames:
                if name_part in fn and fn.endswith(".jar"):
                    hits.append(os.path.join(dirpath, fn))
    return hits


def entry_text(zf, name):
    try:
        return zf.read(name).decode("utf-8", "replace")
    except KeyError:
        return None


def grep(text, needles, ctx=0):
    lines = text.split("\n")
    for i, ln in enumerate(lines):
        for nd in needles:
            if nd in ln:
                lo = max(0, i - ctx)
                hi = min(len(lines), i + ctx + 1)
                for j in range(lo, hi):
                    mark = ">>" if j == i else "  "
                    w("%s %5d | %s" % (mark, j + 1, lines[j].rstrip()))
                if ctx:
                    w("   " + "-" * 40)
                break


def head_of(name):
    w(u"=" * 78)
    w(u"### " + name)
    w(u"=" * 78)


# ------------------------------------------------------------------ 开 ①
if not os.path.exists(SOURCES_JAR):
    w(u"!! sources.jar 不存在：%s" % SOURCES_JAR)
    flush()
    sys.exit(1)

MC = {
    "SmithingTransformRecipe": "net/minecraft/world/item/crafting/SmithingTransformRecipe.java",
    "SmithingTrimRecipe": "net/minecraft/world/item/crafting/SmithingTrimRecipe.java",
    "SmithingRecipe": "net/minecraft/world/item/crafting/SmithingRecipe.java",
    "SmithingRecipeInput": "net/minecraft/world/item/crafting/SmithingRecipeInput.java",
    "RecipeManager": "net/minecraft/world/item/crafting/RecipeManager.java",
    "SmithingMenu": "net/minecraft/world/inventory/SmithingMenu.java",
    "ItemCombinerMenu": "net/minecraft/world/inventory/ItemCombinerMenu.java",
    "Ingredient": "net/minecraft/world/item/crafting/Ingredient.java",
    "RecipeType": "net/minecraft/world/item/crafting/RecipeType.java",
    "Recipes": "net/minecraft/world/item/crafting/Recipes.java",
    "ServerPlayer": "net/minecraft/server/level/ServerPlayer.java",
}

with zipfile.ZipFile(SOURCES_JAR) as zf:
    names = set(zf.namelist())
    w(u"① 源码 jar：%s" % SOURCES_JAR)
    w(u"   条目数 %d" % len(names))
    for k, v in sorted(MC.items()):
        w(u"   %-26s %s" % (k, u"有" if v in names else u"** 没有 **"))

    # ---------------------------------------------------------- ② 三个核心类全文
    for key in ("SmithingRecipe", "SmithingTransformRecipe", "SmithingTrimRecipe",
                "SmithingRecipeInput"):
        head_of(u"② 原版源码全文：" + MC[key])
        txt = entry_text(zf, MC[key])
        if txt is None:
            w(u"!! 读不到")
            continue
        for i, ln in enumerate(txt.split("\n")):
            w(u"%5d | %s" % (i + 1, ln.rstrip()))

    # ---------------------------------------------------------- ③ RecipeManager 关键段
    head_of(u"③ RecipeManager：字段 / apply / 查表 / 同步")
    txt = entry_text(zf, MC["RecipeManager"])
    grep(txt, [u"private final", u"public class RecipeManager", u"void apply(",
               u"byType", u"byName", u"getRecipeFor", u"getRecipes()",
               u"Map<RecipeType", u"ImmutableMap", u"Maps.newHashMap",
               u"getRemainingItems", u"finalizeRecipeLoading", u"RecipeMap",
               u"SmithingTrimRecipe", u"trim"], ctx=1)

    # ---------------------------------------------------------- ④ 锻造台调用链
    head_of(u"④ SmithingMenu / ItemCombinerMenu：结果怎么算出来的")
    for key in ("SmithingMenu", "ItemCombinerMenu"):
        w(u"---- " + MC[key])
        txt = entry_text(zf, MC[key])
        grep(txt, [u"getRecipeFor", u"matches(", u"RecipeType", u"createResult",
                   u"getRecipeInput", u"slotsChanged", u"RecipeManager",
                   u"assemble", u"mayPickup", u"isTemplateIngredient",
                   u"onTake", u"award"], ctx=1)
        w(u"")

    # ---------------------------------------------------------- ⑤ Ingredient 构造口
    head_of(u"⑤ Ingredient：能不能自己造一个「两件都收」的原料")
    txt = entry_text(zf, MC["Ingredient"])
    grep(txt, [u"public abstract class Ingredient", u"static Ingredient of",
               u"public abstract boolean test", u"CODEC", u"class Ingredient",
               u"getItems", u"values"], ctx=1)

    # ---------------------------------------------------------- ⑥ 原版配方数据
head_of(u"⑥ client-extra.jar：原版 smithing 配方到底有几条、叫什么")
if os.path.exists(CLIENT_EXTRA):
    with zipfile.ZipFile(CLIENT_EXTRA) as zf:
        ents = [n for n in zf.namelist()
                if u"/recipe/" in n and (u"smith" in n or u"trim" in n)]
        w(u"   命中 %d 条：" % len(ents))
        for n in sorted(ents):
            w(u"     " + n)
        w(u"")
        # 抽一条下界合金升级配方看内容
        sample = [n for n in ents if u"netherite" in n]
        for n in sorted(sample)[:2]:
            w(u"---- " + n)
            for i, ln in enumerate(zf.read(n).decode("utf-8", "replace").split("\n")):
                w(u"%5d | %s" % (i + 1, ln.rstrip()))
        # 全部 recipe 目录（前 12 条，看命名风格）
        allr = sorted(n for n in zf.namelist() if u"/recipe/" in n and n.endswith(u".json"))
        w(u"   原版配方总数 %d，前 12 条：" % len(allr))
        for n in allr[:12]:
            w(u"     " + n)
else:
    w(u"!! client-extra.jar 不存在：%s" % CLIENT_EXTRA)

# ------------------------------------------------------------------ ⑦ NeoForge
head_of(u"⑦ NeoForge：有没有「改配方表」的官方挂点")
cand = []
for root in (os.path.join(GRADLE_HOME, "caches", "modules-2"),
             os.path.join(GRADLE_HOME, "caches", "ng_execute")):
    if os.path.isdir(root):
        cand += find_jar("neoforge", [root], depth_limit=7)
cand = sorted(set(cand))
w(u"   找到 neoforge 相关 jar %d 个：" % len(cand))
for c in cand:
    w(u"     %s  (%d B)" % (c, os.path.getsize(c)))

nf_src = [c for c in cand if u"sources" in os.path.basename(c)]
if nf_src:
    P = nf_src[0]
    w(u"")
    w(u"   用 sources：%s" % P)
    with zipfile.ZipFile(P) as zf:
        ents = zf.namelist()
        w(u"   条目数 %d" % len(ents))

        def find_entries(sub):
            return sorted(e for e in ents if sub in e.lower())

        w(u"")
        w(u"   [a] 事件/API 里带 recipe 的类（前 40）：")
        for e in find_entries(u"recipe")[:40]:
            w(u"     " + e)
        w(u"")
        w(u"   [b] 含 Smithing 的条目：")
        for e in find_entries(u"smithing"):
            w(u"     " + e)
        w(u"")
        w(u"   [c] 含 reload 的事件：")
        for e in find_entries(u"reload"):
            w(u"     " + e)
        w(u"")
        # 关键类全文
        for want, label in (
                (u"event/AddReloadListenerEvent.java", u"AddReloadListenerEvent"),
                (u"event/RecipesUpdatedEvent.java", u"RecipesUpdatedEvent"),
                (u"crafting/IngredientCodecs", u"x"),
        ):
            for e in ents:
                if e.endswith(want):
                    w(u"---- " + e)
                    for i, ln in enumerate(zf.read(e).decode("utf-8", "replace").split("\n")):
                        w(u"%5d | %s" % (i + 1, ln.rstrip()))
                    break
        w(u"")
        w(u"   [d] 全库搜 replaceRecipes / setRecipes / RecipeManagerAccess：")
        hits = 0
        for e in ents:
            if not e.endswith(u".java"):
                continue
            try:
                body = zf.read(e).decode("utf-8", "replace")
            except Exception:
                continue
            for nd in (u"replaceRecipes", u"setRecipes", u"RecipeManagerAccess",
                       u"IRecipeManager", u"RecipeManager.getRecipes"):
                if nd in body:
                    for i, ln in enumerate(body.split("\n")):
                        if nd in ln:
                            w(u"     %s:%d  %s" % (e, i + 1, ln.strip()))
                            hits += 1
        w(u"   命中 %d 行" % hits)
else:
    w(u"!! 没找到 neoforge sources jar，[⑦] 只能靠 client-extra/反编译，先记下")

flush()
