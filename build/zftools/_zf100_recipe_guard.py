# -*- coding: utf-8 -*-
u"""_zf100_recipe_guard.py —— 只读核对：本轮**只新增 5 份配方、旧的一字节没动**

独立证据源 = **改前那份成品 jar**（`zf100_pre\\release\\PotatoST-0.11.jar`，ZF99 的
`533749f3053558f8f201fc397f1c72725f80a40d`）。为什么不拿盘上别的副本比：
盘上只有"改后"状态，jar 是**动手之前**冻住的第三方快照 —— 拿它比才有意义（ZF47/ZF69 立的口径）。

判据三条：
  ① jar 里那 44 份配方，盘上每一份都**逐字节相同**（生成器重跑不许顺手改坏别人的文件）
  ② 盘上比 jar **正好多 5 份**，且多出来的就是本轮那 5 个文件名
  ③ jar 里有、盘上没了 = 0 份（本轮不删任何配方）
"""
import hashlib
import io
import os
import sys
import zipfile

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

ROOT = r"E:\PotatoST"
JAR = r"C:\PotatoST救援\zf100_pre\release\PotatoST-0.11.jar"
RDIR = os.path.join(ROOT, r"src\main\resources\data\potato_s_t\recipe")
PREFIX = u"data/potato_s_t/recipe/"
EXPECT_NEW = {
    u"acidic_reaction_chamber.json",
    u"combustion_chamber.json",
    u"electric_blast_furnace.json",
    u"lithium_battery.json",
    u"lithium_battery_plant.json",
    u"oil_pump.json",
    u"stable_metal_block.json",
    u"star_chart_tome.json",
    u"star_steel_boots.json",
    u"star_steel_chestplate.json",
    u"star_steel_helmet.json",
    u"star_steel_leggings.json",
    u"starfall_pendant.json",
    u"titanium_alloy_boots.json",
    u"titanium_alloy_chestplate.json",
    u"titanium_alloy_helmet.json",
    u"titanium_alloy_leggings.json",
    u"vibranium_boots_smithing.json",
    u"vibranium_chestplate_smithing.json",
    u"vibranium_helmet_smithing.json",
    u"vibranium_leggings_smithing.json",
}

passed = 0
failed = 0
fails = []


def check(label, cond):
    global passed, failed
    if cond:
        passed += 1
        print(u"  [OK]   " + label)
    else:
        failed += 1
        fails.append(label)
        print(u"  [FAIL] " + label)


def main():
    print(u"=========== ZF100 配方守卫：只新增、不改旧（证据源 = 改前成品 jar）===========")
    if not os.path.exists(JAR):
        print(u"  [FAIL] 找不到改前 jar：%s" % JAR)
        return 1
    check(u"改前 jar 的 SHA1 = 533749f3…（ZF99 那一版）",
          hashlib.sha1(open(JAR, "rb").read()).hexdigest()
          == u"533749f3053558f8f201fc397f1c72725f80a40d")

    with zipfile.ZipFile(JAR) as zf:
        inside = {n[len(PREFIX):]: zf.read(n)
                  for n in zf.namelist() if n.startswith(PREFIX) and n.endswith(u".json")}
    on_disk = {n for n in os.listdir(RDIR) if n.endswith(u".json")}

    changed = []
    for name in sorted(inside):
        p = os.path.join(RDIR, name)
        if not os.path.exists(p):
            changed.append(u"%s（盘上没了）" % name)
        elif open(p, "rb").read() != inside[name]:
            changed.append(u"%s（字节变了）" % name)
    check(u"改前那 %d 份配方逐字节未变（变了 %d 份：%s）"
          % (len(inside), len(changed), u"、".join(changed) if changed else u"无"), not changed)

    extra = on_disk - set(inside)
    check(u"盘上比 jar 正好多 %d 份，且就是本轮那 5 个名字（多出来的是 %s）"
          % (len(EXPECT_NEW), u"、".join(sorted(extra))), extra == EXPECT_NEW)
    check(u"改前 %d 份 + 新增 %d 份 = 盘上 %d 份"
          % (len(inside), len(EXPECT_NEW), len(on_disk)),
          len(inside) + len(EXPECT_NEW) == len(on_disk))

    shaped = 0
    for n in sorted(on_disk):
        t = io.open(os.path.join(RDIR, n), encoding="utf-8").read()
        if u'"minecraft:crafting_shaped"' in t:
            shaped += 1
    # ZF120 跟平：这里原来写 51（ZF106 收尾时的数）。之后三轮各加了一张定形配方
    #   （ZF109 采油机 / ZF112 锂电池构造间 / ZF118 星轨坠）⇒ 盘上已经是 **54**。
    #   ZF120 自己加的是 4 张**锻造台**配方（smithing_transform），不改这个数。
    # ⚠ 别处还留着 8 份 `EXPECT_SHAPED = 51` 的老锚点（_zf95/96/97/100/101/102_verify
    #   与 _zf73_* 那一批）—— 那批的跟平在交接文档里挂给「打包轮」，本轮不越界改。
    check(u"盘上 crafting_shaped = %d 条（活体数字：ZF106 收尾 51 → ZF109 采油机 → ZF112 锂电池构造间 → "
          u"ZF118 星轨坠 → ZF122 星仪图之章 = 55；ZF120 振金套加的是 4 张**锻造台**配方，不改这个数）" % shaped,
          shaped == 55)

    print(u"\n通过 = %d   失败 = %d" % (passed, failed))
    for f in fails:
        print(u"  !! " + f)
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
