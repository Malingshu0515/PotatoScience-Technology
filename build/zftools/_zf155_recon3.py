# -*- coding: utf-8 -*-
r"""ZF155 侦察③（只读）：写码前必须钉死的最后一批 API 事实。

要回答：
  ① MinecraftServer#getRecipeManager / registryAccess 是不是 public；/reload 会不会**换掉** RecipeManager 实例
  ② PlayerList 有没有 getServer()（OnDatapackSyncEvent 只给 PlayerList）
  ③ RegistryOps.create 的签名（我要用它把配方编码回 JSON）
  ④ SmithingMenu 全文：结果怎么出、哪些槽被消耗（模板到底扣不扣）
  ⑤ NeoForge 的 EventBusSubscriber 注解签名（本工程既有用法）
产出：_zf155_recon3.txt
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
OUTF = os.path.join(ZFTOOLS, "_zf155_recon3.txt")


def w(s=u""):
    OUT.append(s)


def flush():
    with io.open(OUTF, "w", encoding="utf-8", newline="\n") as fh:
        fh.write(u"\n".join(OUT) + u"\n")
    sys.stdout.write("wrote %s (%d lines)\n" % (OUTF, len(OUT)))


def rd(zf, n):
    try:
        return zf.read(n).decode("utf-8", "replace")
    except KeyError:
        return None


def head(t):
    w(u"")
    w(u"=" * 78)
    w(u"### " + t)
    w(u"=" * 78)


def grep(txt, needles, ctx=2):
    if txt is None:
        w(u"!! 读不到")
        return
    lines = txt.split("\n")
    for i, ln in enumerate(lines):
        if any(nd in ln for nd in needles):
            for j in range(max(0, i - ctx), min(len(lines), i + ctx + 1)):
                w(u"%s %5d | %s" % (u">>" if j == i else u"  ", j + 1, lines[j].rstrip()))
            w(u"   " + u"-" * 44)


def full(zf, name, lo=None, hi=None):
    txt = rd(zf, name)
    if txt is None:
        w(u"!! 读不到 " + name)
        return
    lines = txt.split("\n")
    lo = 1 if lo is None else lo
    hi = len(lines) if hi is None else hi
    w(u"---- %s [%d..%d] / %d" % (name, lo, hi, len(lines)))
    for i in range(lo - 1, min(hi, len(lines))):
        w(u"%5d | %s" % (i + 1, lines[i].rstrip()))


with zipfile.ZipFile(SOURCES_JAR) as zf:
    head(u"① MinecraftServer：getRecipeManager / registryAccess / reloadResources")
    t = rd(zf, "net/minecraft/server/MinecraftServer.java")
    grep(t, [u"public RecipeManager getRecipeManager", u"public RegistryAccess",
             u"public HolderLookup.Provider registryAccess", u"reloadResources(",
             u"this.resources =", u"ReloadableServerResources", u"getPlayerList().reloadResources",
             u"public ReloadableServerResources", u"resources.getRecipeManager"], ctx=3)

    head(u"② PlayerList：getServer / reloadResources 全文 / placeNewPlayer 尾部")
    t = rd(zf, "net/minecraft/server/players/PlayerList.java")
    grep(t, [u"public MinecraftServer getServer", u"public void reloadResources",
             u"public void placeNewPlayer", u"MinecraftServer server"], ctx=1)
    w(u"")
    full(zf, "net/minecraft/server/players/PlayerList.java", 905, 935)
    w(u"")
    full(zf, "net/minecraft/server/players/PlayerList.java", 196, 216)

    head(u"③ RegistryOps：create 签名")
    grep(rd(zf, "net/minecraft/resources/RegistryOps.java"),
         [u"public static", u"class RegistryOps"], ctx=1)

    head(u"④ SmithingMenu 全文（结果 + 消耗哪几个槽）")
    full(zf, "net/minecraft/world/inventory/SmithingMenu.java")

    head(u"⑤ ItemCombinerMenu 的 shrinkStackInSlot / onTake 相关")
    grep(rd(zf, "net/minecraft/world/inventory/ItemCombinerMenu.java"),
         [u"shrinkStackInSlot", u"protected void onTake", u"quickMoveStack",
          u"mayPickup", u"resultSlots"], ctx=2)

    head(u"⑥ Ingredient：CODEC / getItems / test 的可见性")
    grep(rd(zf, "net/minecraft/world/item/crafting/Ingredient.java"),
         [u"public static final Codec<Ingredient> CODEC", u"public ItemStack[] getItems",
          u"public boolean test", u"public boolean isSimple", u"public boolean isCustom",
          u"public Ingredient(", u"public static Ingredient of("], ctx=0)

with zipfile.ZipFile(NF_SOURCES) as zf:
    head(u"⑦ NeoForge：EventBusSubscriber 注解 + 事件基类")
    for e in zf.namelist():
        if e.endswith(u"fml/common/Mod.java") or e.endswith(u"EventBusSubscriber.java"):
            full(zf, e)
    w(u"")
    w(u"---- NeoForge.EVENT_BUS 相关：")
    grep(rd(zf, "net/neoforged/neoforge/common/NeoForge.java"),
         [u"EVENT_BUS", u"public static"], ctx=1)

flush()
