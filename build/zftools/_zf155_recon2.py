# -*- coding: utf-8 -*-
r"""ZF155 侦察②（**只读**）：把「运行期拓宽配方表」的挂点钉死。

侦察①的结论已经排除了几条路（见 _zf155_recon.txt）：
  * Ingredient 是 **final**，不能子类化；但它有 public 的 of(...)/getItems()/isCustom()/getValues()
  * SmithingTransformRecipe 的 template/base/addition/result 是 **包私有 final 字段**
  * RecipeManager 的 byType/byName 是 **private 非 final**，且是 Immutable* ⇒ 只能整体换掉
  * 原版下界合金升级是 **9 条数据配方**；盔甲纹饰是 **18 条数据配方**（不是动态）
本脚本要回答：
  ① RecipeManager 里那个可疑的 builder 块（155~185 行）是不是 NeoForge 的 replaceRecipes？
  ② NeoForge 有没有 CompoundIngredient / ICustomIngredient，名字叫什么，能不能用它做「原模板 or 通用模板」
  ③ 服务端什么时候把配方同步给客户端（登录 / reload），NeoForge 的 OnDatapackSyncEvent 在包之前还是之后？
  ④ 纹饰（smithing_trim）为什么注定不能通用 —— TrimPattern 与模板物品是不是一一绑定
  ⑤ 生产环境运行时是 Mojang 名还是 SRG 名（决定反射能不能按名字用）

跑法：python build\zftools\_zf155_recon2.py
产出：_zf155_recon2.txt（UTF-8）
"""

import io
import os
import sys
import zipfile

PROJ = r"E:\PotatoST"
ZFTOOLS = os.path.join(PROJ, "build", "zftools")
SOURCES_JAR = os.path.join(PROJ, "build", "neoForm",
                           "neoFormJoined1.21.1-20240808.144430", "sources.jar")
NF_SOURCES = (r"E:\gradle-home\caches\modules-2\files-2.1\net.neoforged\neoforge"
              r"\21.1.235\4566e557485e2cf5843d29a9c44795f5f731d36d"
              r"\neoforge-21.1.235-sources.jar")

OUT = []
OUTF = os.path.join(ZFTOOLS, "_zf155_recon2.txt")


def w(line=u""):
    OUT.append(line)


def flush():
    with io.open(OUTF, "w", encoding="utf-8", newline="\n") as fh:
        fh.write(u"\n".join(OUT) + u"\n")
    sys.stdout.write("wrote %s (%d lines)\n" % (OUTF, len(OUT)))


def head(t):
    w(u"")
    w(u"=" * 78)
    w(u"### " + t)
    w(u"=" * 78)


def entry(zf, name):
    try:
        return zf.read(name).decode("utf-8", "replace")
    except KeyError:
        return None


def full(zf, name, lo=None, hi=None):
    txt = entry(zf, name)
    if txt is None:
        w(u"!! 读不到 %s" % name)
        return u""
    lines = txt.split("\n")
    lo = 1 if lo is None else lo
    hi = len(lines) if hi is None else hi
    w(u"---- %s  [%d..%d] / 共 %d 行" % (name, lo, hi, len(lines)))
    for i in range(lo - 1, min(hi, len(lines))):
        w(u"%5d | %s" % (i + 1, lines[i].rstrip()))
    return txt


def grep(txt, needles, ctx=1, tag=u""):
    lines = txt.split("\n")
    for i, ln in enumerate(lines):
        if any(nd in ln for nd in needles):
            for j in range(max(0, i - ctx), min(len(lines), i + ctx + 1)):
                w(u"%s %5d | %s" % (u">>" if j == i else u"  ", j + 1, lines[j].rstrip()))
            if ctx:
                w(u"   " + u"-" * 44)


MC = {
    "RecipeManager": "net/minecraft/world/item/crafting/RecipeManager.java",
    "Ingredient": "net/minecraft/world/item/crafting/Ingredient.java",
    "MinecraftServer": "net/minecraft/server/MinecraftServer.java",
    "PlayerList": "net/minecraft/server/players/PlayerList.java",
    "ServerGamePacketListenerImpl": "net/minecraft/server/network/ServerGamePacketListenerImpl.java",
    "ReloadableServerResources": "net/minecraft/server/ReloadableServerResources.java",
    "TrimPatterns": "net/minecraft/world/item/armortrim/TrimPatterns.java",
    "TrimPattern": "net/minecraft/world/item/armortrim/TrimPattern.java",
    "RecipeHolder": "net/minecraft/world/item/crafting/RecipeHolder.java",
    "RecipeSerializer": "net/minecraft/world/item/crafting/RecipeSerializer.java",
}

# ------------------------------------------------------------------ ① MC 侧
with zipfile.ZipFile(SOURCES_JAR) as zf:
    head(u"① RecipeManager 全文（找 NeoForge 加的 replaceRecipes / 公开入口）")
    full(zf, MC["RecipeManager"])

    head(u"② Ingredient：isSimple/isCustom/getValues 的可见性 + Neo 的 custom 支持")
    txt = entry(zf, MC["Ingredient"])
    grep(txt, [u"public boolean isSimple", u"public boolean isCustom", u"isCustom()",
               u"public Ingredient.Value[] getValues", u"customIngredient",
               u"class Ingredient", u"public static Ingredient of(",
               u"fromValues", u"public boolean test", u"private final"], ctx=0)

    head(u"③ 配方什么时候同步给客户端：MinecraftServer / PlayerList / 连接层")
    for key in ("MinecraftServer", "PlayerList", "ServerGamePacketListenerImpl",
                "ReloadableServerResources"):
        w(u"")
        w(u"---- " + MC[key])
        t = entry(zf, MC[key])
        if t is None:
            w(u"!! 读不到")
            continue
        grep(t, [u"ClientboundUpdateRecipesPacket", u"OnDatapackSyncEvent",
                 u"reloadResources", u"getRecipeManager", u"sendRecipes",
                 u"UpdateRecipes", u"getRecipes()"], ctx=3)

    head(u"④ 纹饰为什么不能通用：TrimPattern 与模板物品的绑定")
    full(zf, MC["TrimPatterns"])
    w(u"")
    full(zf, MC["TrimPattern"])

    head(u"⑤ RecipeHolder / RecipeSerializer 的构造口（要不要自己包一层）")
    full(zf, MC["RecipeHolder"])
    w(u"")
    t = entry(zf, MC["RecipeSerializer"])
    grep(t, [u"public interface RecipeSerializer", u"SMITHING_TRANSFORM",
             u"SMITHING_TRIM", u"register(", u"MapCodec", u"StreamCodec"], ctx=0)

# ------------------------------------------------------------------ ⑥ NeoForge 侧
head(u"⑥ NeoForge 21.1.235 官方 API：有没有改配方表的挂点")
if not os.path.exists(NF_SOURCES):
    w(u"!! 找不到 %s" % NF_SOURCES)
else:
    with zipfile.ZipFile(NF_SOURCES) as zf:
        ents = zf.namelist()
        w(u"   条目数 %d" % len(ents))

        w(u"")
        w(u"   [a] common/crafting 下的类：")
        for e in sorted(e for e in ents if u"common/crafting/" in e):
            w(u"     " + e)

        w(u"")
        w(u"   [b] event 下与 recipe/datapack/reload/server 有关的类：")
        for e in sorted(e for e in ents if u"/event/" in e and u".java" in e):
            low = e.lower()
            if (u"recipe" in low or u"datapack" in low or u"reload" in low
                    or u"server" in low or u"level" in low):
                w(u"     " + e)

        for want in (u"event/AddReloadListenerEvent.java",
                     u"event/OnDatapackSyncEvent.java",
                     u"client/event/RecipesUpdatedEvent.java",
                     u"event/server/ServerStartedEvent.java",
                     u"common/crafting/CompoundIngredient.java",
                     u"common/crafting/ICustomIngredient.java",
                     u"common/crafting/IngredientType.java"):
            for e in ents:
                if e.endswith(want):
                    w(u"")
                    full(zf, e)
                    break
            else:
                w(u"")
                w(u"   !! 没有 " + want)

        w(u"")
        w(u"   [c] 全库搜改配方表的痕迹（replaceRecipes / RecipeManager / ObfuscationReflection）：")
        hits = 0
        for e in ents:
            if not e.endswith(u".java"):
                continue
            body = entry(zf, e) or u""
            for nd in (u"replaceRecipes", u"RecipeManager", u"ObfuscationReflectionHelper",
                       u"isSimple()", u"CompoundIngredient"):
                if nd in body:
                    for i, ln in enumerate(body.split("\n")):
                        if nd in ln:
                            w(u"     %s:%d  %s" % (e, i + 1, ln.strip()[:150]))
                            hits += 1
                            if hits > 120:
                                w(u"     ... 截断")
                                break
                    if hits > 120:
                        break
            if hits > 120:
                break
        w(u"   命中 %d 行（上限 120）" % hits)

flush()
