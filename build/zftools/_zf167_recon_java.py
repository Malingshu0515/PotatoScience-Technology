# -*- coding: utf-8 -*-
u"""_zf167_recon_java.py —— 写代码前把「原版事实」从 sources.jar 现抠（不靠记忆）

用户这一轮点名了三件"照原版抄"的事：
  ① 可乐「食用音效用蜂蜜瓶的」⇒ 蜂蜜瓶那个音效常量到底叫什么、它怎么覆写的；
  ② 「食用后返还一个空铝罐」⇒ 原版"吃完返还容器"的标准写法（蜂蜜瓶返玻璃瓶）；
  ③ 食物「恢复3点饥饿值 9点饱和度」⇒ FoodProperties 的 nutrition / saturation 语义
     （saturation 是**修饰值**不是绝对点数：绝对点数 = nutrition × saturation × 2）。
"""
import io
import os
import sys
import zipfile

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
SOURCES = (r"E:\PotatoST\build\neoForm"
           r"\neoFormJoined1.21.1-20240808.144430\sources.jar")


def src_of(zf, want):
    hit = [n for n in zf.namelist() if n.endswith(want)]
    return zf.read(hit[0]).decode("utf-8", "replace") if hit else None


def show(src, label, lo, hi):
    print(u"\n---- %s（%d~%d）----" % (label, lo, hi))
    lines = src.split(u"\n")
    for i in range(lo, min(hi, len(lines)) + 1):
        print(u"  %5d | %s" % (i, lines[i - 1].rstrip()))


with zipfile.ZipFile(SOURCES) as zf:
    # ① 蜂蜜瓶
    s = src_of(zf, u"net/minecraft/world/item/HoneyBottleItem.java")
    if s is None:
        print(u"!! 没有 HoneyBottleItem.java")
    else:
        print(u"================ HoneyBottleItem.java 全文 ================")
        for i, line in enumerate(s.split(u"\n"), 1):
            print(u"  %5d | %s" % (i, line.rstrip()))
    # ② 音效常量名
    s = src_of(zf, u"net/minecraft/sounds/SoundEvents.java")
    print(u"\n================ SoundEvents 里 HONEY / DRINK / EAT 相关 ================")
    for i, line in enumerate(s.split(u"\n"), 1):
        if u"HONEY" in line or u"GENERIC_DRINK" in line or u"GENERIC_EAT" in line:
            print(u"  %5d | %s" % (i, line.strip()))
    # ③ 食物组件
    s = src_of(zf, u"net/minecraft/world/food/FoodProperties.java")
    print(u"\n================ FoodProperties：字段与 Builder ================")
    for i, line in enumerate(s.split(u"\n"), 1):
        t = line.strip()
        if t.startswith(u"public") and (u"saturation" in t or u"nutrition" in t or u"effect" in t
                                        or u"Builder" in t or u"alwaysEdible" in t):
            print(u"  %5d | %s" % (i, t))
    # ④ 食物效果在哪生效（eat）
    s = src_of(zf, u"net/minecraft/world/entity/LivingEntity.java")
    lines = s.split(u"\n")
    idx = [i for i, l in enumerate(lines, 1) if u"public ItemStack eat(" in l]
    print(u"\n================ LivingEntity.eat 里的效果与饱和度 ================")
    for i in idx:
        show(s, u"LivingEntity.eat", i, i + 40)
    # ⑤ ItemUtils.createFilledResult
    s = src_of(zf, u"net/minecraft/world/item/ItemUtils.java")
    print(u"\n================ ItemUtils.createFilledResult ================")
    for i, line in enumerate(s.split(u"\n"), 1):
        if u"createFilledResult" in line:
            show(s, u"ItemUtils @%d" % i, i - 2, i + 12)
    # ⑥ Item.getEatingSound / getUseAnimation
    s = src_of(zf, u"net/minecraft/world/item/Item.java")
    print(u"\n================ Item：getEatingSound / getDrinkingSound / getUseAnimation ================")
    for i, line in enumerate(s.split(u"\n"), 1):
        if u"getEatingSound" in line or u"getDrinkingSound" in line or u"getUseAnimation" in line:
            print(u"  %5d | %s" % (i, line.strip()))
