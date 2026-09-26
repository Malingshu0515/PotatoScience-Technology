# -*- coding: utf-8 -*-
r"""_zf141_api.py —— 只读：把探针要用的四个 API 签名从 sources.jar 现抠（不靠记忆）。

要抠的四件事（写探针前必须知道确切的参数表，否则就是编译错误来回撞）：
  ① ItemStack.mineBlock / postHurtEnemy 的签名
  ② RecipeManager.getRecipeFor 的签名
  ③ CraftingInput.of 的签名
  ④ Tool（DataComponents.TOOL 的类型）record 的分量
"""
import sys
import zipfile

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
SOURCES = r"E:\PotatoST\build\neoForm\neoFormJoined1.21.1-20240808.144430\sources.jar"

WANT = [
    (u"net/minecraft/world/item/ItemStack.java",
     [u"mineBlock", u"postHurtEnemy", u"getMaxDamage", u"getDamageValue"]),
    (u"net/minecraft/world/item/crafting/RecipeManager.java", [u"getRecipeFor"]),
    (u"net/minecraft/world/item/crafting/CraftingInput.java", [u"static CraftingInput of"]),
    (u"net/minecraft/world/item/component/Tool.java", [u"public record Tool", u"Tool("]),
    (u"net/minecraft/world/item/TieredItem.java", [u"getTier"]),
]


def main():
    zf = zipfile.ZipFile(SOURCES)
    names = zf.namelist()
    for want, marks in WANT:
        hit = [n for n in names if n.endswith(want)]
        if not hit:
            print(u"!! 没有 %s" % want)
            continue
        src = zf.read(hit[0]).decode(u"utf-8", u"replace")
        lines = src.split(u"\n")
        print(u"")
        print(u"=" * 78)
        print(u"---- %s ----（%d 行）" % (want.split(u"/")[-1], len(lines)))
        print(u"=" * 78)
        for i, line in enumerate(lines, 1):
            s = line.strip()
            if not any(m in line for m in marks):
                continue
            # 只打"声明行"（带 public/static/record 的），属性行看个签名就够
            print(u"  %5d | %s" % (i, s))


main()
