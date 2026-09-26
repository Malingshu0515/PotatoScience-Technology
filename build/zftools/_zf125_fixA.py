# -*- coding: utf-8 -*-
u"""_zf125_fixA.py —— 修 `_zf125_java.py` 的 A 处手误（ZF125）

**事故**：`_zf125_java.py` 里 A 处的写法是
    apply(u"A ModBlocks", ..., A_ANCHOR, A_NEW)
而 `A_NEW` 只写了"新增的那一段"，**忘了把锚点本身接回去**
（B/C/D/E 四处都写成了 `NEW = ANCHOR + 新内容`，只有 A 漏了）。
于是 `LITHIUM_BATTERY_PLANT.get()).build(null));` 这一行**被整行吃掉了**，
`ModBlocks.java:998` 变成一个空行，编译报 `1012: 非法的表达式开始`。

**修法**：把那一行原样补回去（只补这一行，别的一律不动），并逐字节证明
"现在是 A 处的**预期**结果"。

跑法：
    python build\\zftools\\_zf125_fixA.py
"""
import hashlib
import io
import os
import sys

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

ROOT = r"E:\PotatoST"
PATH = os.path.join(ROOT, r"src\main\java\com\potatost\mod\ModBlocks.java")
BK = r"C:\PotatoST救援\zf125_pre\src\main\java\com\potatost\mod\ModBlocks.java"

BROKEN = (u"            () -> BlockEntityType.Builder.of(LithiumBatteryPlantBlockEntity::new,\n"
          u"\n"
          u"    // ===== 大型柴油发电机（0.11 ZF125）=====\n")

FIXED = (u"            () -> BlockEntityType.Builder.of(LithiumBatteryPlantBlockEntity::new,\n"
         u"                    LITHIUM_BATTERY_PLANT.get()).build(null));\n"
         u"\n"
         u"    // ===== 大型柴油发电机（0.11 ZF125）=====\n")

notes, fails = [], []


def main():
    text = io.open(PATH, encoding="utf-8", newline=u"").read()
    nl = u"\r\n" if u"\r\n" in text else u"\n"
    broken = BROKEN.replace(u"\n", nl)
    fixed = FIXED.replace(u"\n", nl)
    n = text.count(broken)
    if n == 1:
        io.open(PATH, "w", encoding="utf-8", newline=u"").write(text.replace(broken, fixed, 1))
        notes.append(u"补回被吃掉的那一行（锚点 1 次命中）")
    elif text.count(fixed) == 1:
        notes.append(u"事故点已经修过了（锚点 0 次、修好的形态 1 次）—— 本次只做校验")
    else:
        fails.append(u"事故点命中 %d 次（要 1 次）—— 文件可能已经被改坏，别瞎修" % n)

    after = io.open(PATH, encoding="utf-8", newline=u"").read()
    if u"LITHIUM_BATTERY_PLANT.get()).build(null));" not in after:
        fails.append(u"补回去之后仍然找不到那一行")
    # 方块 + 方块实体 + 物品 三处注册都叫这个名字
    if after.count(u"diesel_generator_controller") != 3:
        fails.append(u"diesel_generator_controller 出现 %d 次（应是 3：方块 + 方块实体 + 物品）"
                     % after.count(u"diesel_generator_controller"))

    # 与改前件逐字节比：差异必须**只**是 ZF125 新增的那一段
    if os.path.exists(BK):
        before = io.open(BK, encoding="utf-8", newline=u"").read()
        i = 0
        while i < min(len(before), len(after)) and before[i] == after[i]:
            i += 1
        tail_before = before[i:]
        tail_after = after[i:]
        notes.append(u"与改前件首个不同字节在偏移 %d（= 第 %d 行）"
                     % (i, before[:i].count(nl) + 1))
        notes.append(u"改前件尾部 %r / 现状尾部前 40 字符 %r"
                     % (tail_before, tail_after[:40]))
        # ⚠ 差异点落在"共同前缀吃掉了锚点行那个换行"之后 ⇒ 这里只剩**一个**换行
        if not tail_after.startswith((u"\n    // ===== 大型柴油发电机（0.11 ZF125）=====").replace(u"\n", nl)):
            fails.append(u"差异不是从新增段开始的 —— 别的地方也被动了")
        if tail_before.strip() != u"}":
            fails.append(u"改前件的尾部不是单个右花括号：%r" % tail_before[:60])
    else:
        fails.append(u"改前件不在：%s" % BK)

    notes.append(u"现状 sha1 %s（%d B）" % (hashlib.sha1(open(PATH, "rb").read()).hexdigest()[:16],
                                          os.path.getsize(PATH)))
    print(u"\n".join(u"  [OK] " + n for n in notes))
    print(u"失败项 = %d" % len(fails))
    for f in fails:
        print(u"  !! " + f)
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())
