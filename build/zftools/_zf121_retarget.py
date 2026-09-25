# -*- coding: utf-8 -*-
u"""_zf121_retarget.py —— ZF121 把**往轮常驻校验**里被本轮改动作废的判据改准（不是放宽）

三处，逐条说清"为什么必须改、改成什么、有没有变松"：

1. `_zf111_verify.py`
   - `MAX_ENERGY_PER_TICK = 12_000;` → `14_500;`（那是**全表最大值**这个活体数字；
     ZF121 的振金那条是 14500，比星璨钢的 12000 更贵 ⇒ 常量必须跟着走，
     否则 ZF42 那条静态守卫会误报"最贵的一条跑不起来"）。
   - 类注释 `12000 ≤ 32768` → `14500 ≤ 32768`（同一条活体数字）。
   **没有变松**：判据仍然是"常量等于那个具体的数"，只是那个数换了。

2. `_zf119_verify.py` 的 B6
   - 原话「**没有任何配方**产出它（用户明说「目前没配方」）」—— 用户 ZF121 给了**合金冶炼炉**
     配方（写死在 Java 表 `AlloySmelterRecipes` 里，**不是数据包配方**）。
     B6 扫的是 `data/potato_s_t/recipe/*.json`，所以**判据本身仍然成立**，
     但**措辞会骗人**（读者会以为振金锭没有任何来源）⇒ 改成
     「没有任何**数据包/工作台**配方产出它（它的来源是合金冶炼炉 · ZF121）」。
   **没有变松**：断言还是 `hits == []`，一个字节都没放宽。

3. `_zf114_verify.py` 的 F5b
   - 同一条口径：粗振金仍然没有数据包配方，但它**现在是合金炉那条配方的消耗品**了
     ⇒ 措辞补一句，判据不动。

⚠ 并行那条线（ZF120 振金套）也在改 `_zf111_verify.py`（键数 449 → 454 那笔账）。
   本轮**只动上面点名的那两行**，别的一个字不碰。

跑法：
    python build\\zftools\\_zf121_retarget.py            # 只校验
    python build\\zftools\\_zf121_retarget.py --write    # 落盘
"""
import io
import os
import sys

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

ROOT = r"E:\PotatoST"
TOOLS = os.path.join(ROOT, "build", "zftools")


def read(p):
    return io.open(p, encoding="utf-8").read()


def write(p, text):
    io.open(p, "w", encoding="utf-8", newline=u"\n").write(text)


EDITS = []

EDITS.append((
    u"_zf111_verify.py",
    u'''    check(u"MAX_ENERGY_PER_TICK = 12000（纯 int 常量，静态守卫能读）",
          "public static final int MAX_ENERGY_PER_TICK = 12_000;" in recipes)''',
    u'''    # ⚠ ZF121 retarget：这个常量是**全表最贵那条**的每 tick 耗电（活体数字）。
    #   振金那条 14500 比星璨钢的 12000 更贵 ⇒ 常量必须跟着走，判据本身没放宽。
    check(u"MAX_ENERGY_PER_TICK = 14500（纯 int 常量，静态守卫能读）",
          "public static final int MAX_ENERGY_PER_TICK = 14_500;" in recipes)'''))

EDITS.append((
    u"_zf111_verify.py",
    u'''    check(u"12000 ≤ 储能 32768（写在类注释里）", "12000 ≤ 32768" in be)''',
    u'''    # ⚠ ZF121 retarget：同一条活体数字（最贵那条 12000 → 14500）。
    check(u"14500 ≤ 储能 32768（写在类注释里）", "14500 ≤ 32768" in be)'''))

EDITS.append((
    u"_zf119_verify.py",
    u'''    eq(u"B6 **没有任何配方**产出它（用户明说「目前没配方」）", [], hits)''',
    u'''    # ⚠ ZF121：用户给了**合金冶炼炉**配方（写死在 Java 表 AlloySmelterRecipes 里，
    #   不是数据包配方）⇒ 这句措辞会骗人，改成"没有数据包/工作台配方"。
    #   **判据一个字都没放宽**：还是 hits == []（本段扫的就是 data/potato_s_t/recipe/）。
    #   振金锭的真实来源（合金炉那条）由 `_zf121_verify.py` 常驻盯着。
    eq(u"B6 **没有任何数据包/工作台配方**产出它（来源是合金冶炼炉 · ZF121）", [], hits)'''))

EDITS.append((
    u"_zf114_verify.py",
    u'''    check(u"F5b 粗振金仍然没有配方（「先不给」对它仍成立）",
          not os.path.exists(os.path.join(RECIPES, u"raw_vibranium.json")))''',
    u'''    # ⚠ ZF121：粗振金仍然没有**数据包**配方，但它现在是**合金冶炼炉**那条振金配方的
    #   消耗品（1 个）⇒ 措辞补一句，判据不动。
    check(u"F5b 粗振金仍然没有数据包配方（它现在是合金炉的消耗品 · ZF121）",
          not os.path.exists(os.path.join(RECIPES, u"raw_vibranium.json")))'''))


def main(argv):
    do_write = "--write" in argv
    fails, done, out = [], 0, {}
    for name, old, new in EDITS:
        p = os.path.join(TOOLS, name)
        if p not in out:
            out[p] = read(p)
        txt = out[p]
        marker = new.strip().split(u"\n")[0][:40]
        if marker in txt and old not in txt:
            print(u"  [跳过] %-22s 已改过（幂等）" % name)
            done += 1
            continue
        n = txt.count(old)
        if n != 1:
            fails.append(u"%s 的锚点匹配到 %d 次（应为 1）" % (name, n))
            continue
        out[p] = txt.replace(old, new, 1)
        print(u"  [改]   %-22s %s" % (name, old.strip().split(u"\n")[0][:60]))
        done += 1
    if fails:
        print(u"")
        print(u"锚点对不上，**一个字节都没写**：")
        for f in fails:
            print(u"  !! " + f)
        return 1
    if do_write:
        for p, txt in out.items():
            write(p, txt)
        print(u"\n落盘：%d 个文件" % len(out))
    else:
        print(u"\n（只校验，没落盘；加 --write 才写）")
    print(u"通过 = %d   失败 = 0" % done)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
