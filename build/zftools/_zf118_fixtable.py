# -*- coding: utf-8 -*-
u"""_zf118_fixtable.py —— 把生成器表里**陈旧的那条** `lithium_battery` 改成盘上的真图纸

怎么发现的：ZF118 加星轨坠配方时按规矩跑 `_zf45_recipes.py --write`，
我的脚本在写盘前先比对了 zf118_pre 里那 59 份配方 —— **当场报出 `lithium_battery.json` 被改了**。
diff 一看：盘上（ZF112 之后的）是

    四角/两侧 = `minecraft:paper`，中心那格 = `potato_s_t:lithium_battery_component`

而生成器表里还是 ZF100 那版（`aluminum_plate` / `copper_plate` / `lithium_carbonate`）。
⇒ **ZF112 那轮改了配方 JSON 却没改生成器表**（档案 §5「不要手写 JSON」那条规矩踩了），
于是生成器一跑就把这张图纸**打回旧版**。本轮把它对上：表改成 ZF112 的真图纸，
再把 JSON 从改前件**逐字节还原**（其实还原后与"用新表重跑"的结果一致，两条路互证）。

本脚本：① 还原 JSON；② 改表；③ 用表重跑这一条并断言与还原后的 JSON 逐字节相同。
"""
import hashlib
import io
import json
import os
import subprocess
import sys

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

ROOT = r"E:\PotatoST"
GEN = os.path.join(ROOT, r"build\zftools\_zf45_recipes.py")
JSONP = os.path.join(ROOT, r"src\main\resources\data\potato_s_t\recipe\lithium_battery.json")
BKJSON = r"C:\PotatoST救援\zf118_pre\src\main\resources\data\potato_s_t\recipe\lithium_battery.json"

OLD = (u'    # ① 三元聚合物锂电池：四角铝板 / 两侧铜板 / 中心电容 + 碳酸锂 + 外壳\n'
       u'    dict(name="lithium_battery", category="redstone",\n'
       u'         result=("potato_s_t:lithium_battery", 1),\n'
       u'         pattern=["ACA", "PLP", "AMA"],\n'
       u'         key={"A": ("item", "potato_s_t:aluminum_plate"),\n'
       u'              "C": ("item", "potato_s_t:capacitor"),\n'
       u'              "P": ("item", "potato_s_t:copper_plate"),\n'
       u'              "L": ("item", "potato_s_t:lithium_carbonate"),\n'
       u'              "M": ("item", "potato_s_t:common_metal_block")}),\n')

NEW = (u'    # ① 三元聚合物锂电池：四角纸 / 两侧纸 / 中心电容 + 锂电池原件 + 外壳\n'
       u'    #    ⚠ ZF112（用户：「三元锂配方里的碳酸锂改成锂电池原件 金属板统一换成纸」）\n'
       u'    #      改了这张图纸，但**只改了 JSON、没改本表**（踩了「不要手写 JSON」那条规矩）。\n'
       u'    #      ZF118 加星轨坠时按规矩重跑生成器 ⇒ 当场把 JSON 打回旧版、被脚本的前置断言抓住\n'
       u'    #      （`_zf118_recipe.py` 写完前先比 zf118_pre 的哈希）。现在表与盘一致。\n'
       u'    dict(name="lithium_battery", category="redstone",\n'
       u'         result=("potato_s_t:lithium_battery", 1),\n'
       u'         pattern=["ACA", "PLP", "AMA"],\n'
       u'         key={"A": ("item", "minecraft:paper"),\n'
       u'              "C": ("item", "potato_s_t:capacitor"),\n'
       u'              "P": ("item", "minecraft:paper"),\n'
       u'              "L": ("item", "potato_s_t:lithium_battery_component"),\n'
       u'              "M": ("item", "potato_s_t:common_metal_block")}),\n')

fails, notes = [], []


def read(p):
    return io.open(p, encoding="utf-8").read()


def sha1(p):
    return hashlib.sha1(open(p, "rb").read()).hexdigest()


def main():
    # ① 从改前件逐字节还原 JSON
    if not os.path.exists(BKJSON):
        fails.append(u"改前件里没有 lithium_battery.json")
    else:
        want = open(BKJSON, "rb").read()
        cur = open(JSONP, "rb").read()
        if cur == want:
            notes.append(u"lithium_battery.json 本来就没被动（跳过还原）")
        else:
            open(JSONP, "wb").write(want)
            if open(JSONP, "rb").read() != want:
                fails.append(u"还原失败")
            else:
                notes.append(u"lithium_battery.json 已从改前件逐字节还原（sha1 %s）" % sha1(JSONP))

    # ② 改表
    gen = read(GEN)
    if u'"item", "minecraft:paper"' in gen and u'name="lithium_battery"' in gen:
        notes.append(u"生成器表里那条已经是新图纸（跳过）")
    elif gen.count(OLD) != 1:
        fails.append(u"表里锚点出现 %d 次（要求 1）—— 先看清再改" % gen.count(OLD))
    else:
        io.open(GEN, "w", encoding="utf-8", newline=u"").write(gen.replace(OLD, NEW, 1))
        compile(read(GEN), GEN, "exec")
        notes.append(u"生成器表：lithium_battery 改成盘上的真图纸（纸 ×6 + 锂电池原件）")

    if fails:
        print(u"\n".join(u"  [OK] " + n for n in notes))
        print(u"\n失败项 = %d" % len(fails))
        for f in fails:
            print(u"  !! " + f)
        return 1

    # ③ 用（新）表重跑生成器，断言这张 JSON 与还原件逐字节相同
    r = subprocess.run([sys.executable, GEN, "--write"], stdout=subprocess.PIPE,
                       stderr=subprocess.STDOUT, timeout=180)
    if r.returncode != 0:
        fails.append(u"生成器 --write 退出码 %d" % r.returncode)
    else:
        notes.append(u"生成器 --write 退出码 0")
    if os.path.exists(BKJSON):
        same = open(JSONP, "rb").read() == open(BKJSON, "rb").read()
        if same:
            notes.append(u"用新表重跑出来的 lithium_battery.json == 改前件（两条路互证）")
        else:
            fails.append(u"用新表重跑的结果与改前件不同 —— 表还是不对")
    # 顺手核一下：现在盘上 60 份配方里，除了新加的那份，其余还是逐字节等于改前件
    RDIR = os.path.dirname(JSONP)
    BKDIR = r"C:\PotatoST救援\zf118_pre\src\main\resources\data\potato_s_t\recipe"
    changed = []
    for n in sorted(os.listdir(RDIR)):
        if not n.endswith(".json") or n == "starfall_pendant.json":
            continue
        if not os.path.exists(os.path.join(BKDIR, n)) or \
                sha1(os.path.join(RDIR, n)) != sha1(os.path.join(BKDIR, n)):
            changed.append(n)
    if changed:
        fails.append(u"还有配方与改前件不同：%s" % changed)
    else:
        notes.append(u"盘上 %d 份旧配方全部逐字节等于改前件"
                     % len([n for n in os.listdir(RDIR) if n.endswith('.json') and n != 'starfall_pendant.json']))

    print(u"\n".join(u"  [OK] " + n for n in notes))
    print(u"\n失败项 = %d" % len(fails))
    for f in fails:
        print(u"  !! " + f)
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())
