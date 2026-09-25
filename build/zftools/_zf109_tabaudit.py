# -*- coding: utf-8 -*-
r"""_zf109_tabaudit.py —— 创造模式物品栏账目（0.11 ZF109，**只读**）

**为什么会有这个脚本**：用户实测反馈「创造模式物品栏没看见采油机  jei也搜不到
但是 jei有配方」—— 采油机注册了方块与物品，却**没进创造页**：
原版创造菜单只显示"被某个页 accept 过的物品"，JEI 的物品搜索也是照创造页建的 ⇒
两边一起看不见，而合成配方（datapack）照旧在 JEI 里 ⇒ 用户看到的就是这个组合。
档案 §6.14 那张"加一个机器方块要动哪些文件"的清单里**第 3 条**就是这个，
我漏了，而且没有做成检查项（§4.17：没有检查项就必然漏第二次）。

本脚本把这笔账**做成可重跑的检查**：拿 `ModBlocks` 里注册的每一个方块物品，
去 `ModItems` 的创造页里找 `output.accept(ModBlocks.<常量>.get())`。

用法：python build\zftools\_zf109_tabaudit.py [--quiet]
退出码 0 = 全部都在创造页里。
"""
import io
import os
import re
import sys

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

ROOT = r"E:\PotatoST"
MODBLOCKS = os.path.join(ROOT, r"src\main\java\com\potatost\mod\ModBlocks.java")
MODITEMS = os.path.join(ROOT, r"src\main\java\com\potatost\mod\ModItems.java")

# 方块物品的注册写法（本工程就这两种：DeferredHolder<Item, BlockItem> / DeferredBlock 的 item）
REG = re.compile(r"DeferredHolder<Item,\s*BlockItem>\s+(\w+)\s*=\s*\n?\s*"
                 r"ModItems\.ITEMS\.register\(\"([a-z_0-9]+)\"")


def main():
    quiet = "--quiet" in sys.argv
    mb = io.open(MODBLOCKS, encoding="utf-8").read()
    mi = io.open(MODITEMS, encoding="utf-8").read()
    reg = REG.findall(mb)
    accepted = set(re.findall(r"output\.accept\(ModBlocks\.(\w+)\.get\(\)\)", mi))
    missing = [(c, i) for c, i in reg if c not in accepted]
    print(u"ModBlocks 注册的方块物品 = %d" % len(reg))
    print(u"创造页 accept 到的 ModBlocks 物品 = %d" % len(accepted))
    print(u"**没进创造页的 = %d**" % len(missing))
    for c, i in missing:
        print(u"    %-34s  %s" % (c, i))
    if not quiet:
        extra = sorted(accepted - set(c for c, _ in reg))
        if extra:
            print(u"（另外页里有 %d 个 accept 常量在 ModBlocks 里找不到同名注册，"
                  u"多半是别的注册写法：%s）" % (len(extra), u", ".join(extra[:6])))
    return 1 if missing else 0


if __name__ == "__main__":
    sys.exit(main())
