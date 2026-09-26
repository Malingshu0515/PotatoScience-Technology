# -*- coding: utf-8 -*-
u"""_zf124_java.py —— ZF124：把**创造模式标签页的图标**从铝锭换成星轨坠（锚点替换）

用户原话（附成就界面截图）：「把成就的 新的开始！这一分类改成 PotatoS&T
创造模式标签页换成星轨追的物品贴图」（「星轨追」按「星轨坠」理解）。

地点：`ModItems.POTATO_ST_TAB` 的 `.icon(() -> new ItemStack(ALUMINUM_INGOT.get()))`。

⚠ 两处顺序都核过：
  · `STARFALL_PENDANT` 声明在 **483 行**，`POTATO_ST_TAB` 在 **541 行** ⇒ 静态字段序没问题；
  · 而且 `.icon(...)` 里是个 **lambda**，真正求值在"造标签页"时（注册之后），
    那时候两个字段都早就初始化完了 —— 不会踩 §4.1 那种"注册还没完成就取物品"的雷。

跑法：
    python build\\zftools\\_zf124_java.py            # 只校验
    python build\\zftools\\_zf124_java.py --write    # 落盘
"""
import io
import os
import sys

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

ROOT = r"E:\PotatoST"
P = os.path.join(ROOT, r"src\main\java\com\potatost\mod\ModItems.java")

OLD = u'''                    .icon(() -> new ItemStack(ALUMINUM_INGOT.get()))'''
NEW = u'''                    // 0.11 ZF124：创造页图标 铝锭 → **星轨坠**（用户原话「创造模式标签页换成星轨坠的
                    // 物品贴图」）。`.icon(...)` 是 lambda、求值在造标签页时 ⇒ 与字段声明顺序无关
                    //（STARFALL_PENDANT 在 483 行、本行在 54x 行，静态序也本来就对）。
                    .icon(() -> new ItemStack(STARFALL_PENDANT.get()))'''

MARKER = u".icon(() -> new ItemStack(STARFALL_PENDANT.get()))"


def read(p):
    return io.open(p, encoding="utf-8").read()


def main(argv):
    do_write = "--write" in argv
    txt = read(P)
    if MARKER in txt:
        print(u"  [跳过] 已经是星轨坠（幂等）")
        print(u"通过 = 1   失败 = 0")
        return 0
    n = txt.count(OLD)
    if n != 1:
        print(u"  [STOP] 锚点命中 %d 次（应为 1）—— 一个字节都没写" % n)
        print(u"失败 = 1")
        return 1
    # 自检：星轨坠的字段必须声明在创造页之前（静态序）
    i_pend = txt.find(u"DeferredItem<Item> STARFALL_PENDANT =")
    i_tab = txt.find(u'CREATIVE_MODE_TABS.register("potato_s_t_tab"')
    print(u"  [自检] STARFALL_PENDANT 在第 %d 字符处、创造页注册在第 %d 字符处 ⇒ %s"
          % (i_pend, i_tab, u"顺序正确" if 0 <= i_pend < i_tab else u"**顺序有问题**"))
    if not (0 <= i_pend < i_tab):
        print(u"失败 = 1")
        return 1
    out = txt.replace(OLD, NEW, 1)
    if do_write:
        io.open(P, "w", encoding="utf-8", newline=u"\n").write(out)
        print(u"  [改]   ModItems.java：创造页图标 → 星轨坠")
        print(u"落盘：%s" % os.path.relpath(P, ROOT))
    else:
        print(u"  [改]   （只校验，没落盘；加 --write 才写）")
    print(u"通过 = 1   失败 = 0")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
