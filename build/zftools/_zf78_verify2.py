# -*- coding: utf-8 -*-
u"""_zf78_verify2.py —— 把「倒油 + 控制器排查显示」两句功能的断言补进校验脚本，并同步活体计数

① `_zf78_verify.py`：
   · ⚠ **翻转一条旧断言** —— ZF78 原来钉的是"控制器没有 useWithoutItem"，
     现在右击要显示排查信息了 ⇒ 改成"有 useWithoutItem 但仍然没有 openMenu/MenuProvider"；
   · 新增：`POUR_PER_CLICK = 1000`、`useItemOn` 真的在、SIMULATE→drain→fill 三步、
     `FluidContainerItem.contents/drain` 两个新方法、两个实现类都实现了、
     结构里有 `diagnose` + `Diagnosis`、控制器用了它、5 个新键、键数 246。
② 往轮/公告的活体计数：241 → **246**（`_zf73_verify.py` B11、`_zf75_verify.py` C2、
   `_zf71_verify.py` + 公告那行 "(241 keys each)"）。

每条替换断言正好命中 1 次。
"""
import io
import os
import sys

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

ROOT = r"E:\PotatoST"
SRC = os.path.join(ROOT, "src", "main", "java", "com", "potatost", "mod")
TOOLS = os.path.join(ROOT, "build", "zftools")
VER = os.path.join(TOOLS, "_zf78_verify.py")
ANN = os.path.join(ROOT, "docs", "UpdateAnnouncement_EN.md")

fails = []


def read(p):
    return io.open(p, encoding="utf-8").read()


def patch(path, old, new, label):
    t = read(path)
    hits = t.count(old)
    if hits != 1:
        fails.append(u"%s：锚点命中 %d 次（必须 1 次）" % (label, hits))
        return
    io.open(path, "w", encoding="utf-8", newline=u"\n").write(t.replace(old, new, 1))
    print(u"  [OK]   %s" % label)


def main():
    print(u"== ① 校验脚本：翻转控制器那条 + 补新功能的断言 ==")
    patch(VER,
          u'''    check(u"控制器没有 GUI（右击没反应是设计如此）",
          "openMenu" not in blk and "MenuProvider" not in blk and "useWithoutItem" not in blk)''',
          u'''    # ⚠ ZF78 第一版钉的是"右击没反应"；2026-09-24 用户要「排查信息能显示」⇒
    #   改成"右击有反馈，但**仍然没有 GUI**（不开界面、不存状态）"
    check(u"控制器右击会显示排查信息（用户 09-24 点名要的）", "useWithoutItem" in blk)
    check(u"控制器仍然没有 GUI（不开界面、不是 MenuProvider）",
          "openMenu" not in blk and "MenuProvider" not in blk)
    check(u"排查信息用的是 diagnose + 三套文案（数到/最像的一处/什么都没有）",
          "DistillationTowerStructure.diagnose(" in blk
          and "distillation.diagnosis.found" in blk
          and "distillation.diagnosis.none" in blk
          and "distillation.diagnosis.empty" in blk)''',
          u"翻转 + 扩展控制器断言")

    patch(VER,
          u'''    check(u"能连管道：五罐暴露成一个 IFluidHandler", "public IFluidHandler getFluidHandler()" in op)
    check(u"能量用共享的 MachineEnergyStorage（不抄匿名实现）",
          "MachineEnergyStorage.receiveOnly" in op)''',
          u'''    check(u"能连管道：五罐暴露成一个 IFluidHandler", "public IFluidHandler getFluidHandler()" in op)
    check(u"能量用共享的 MachineEnergyStorage（不抄匿名实现）",
          "MachineEnergyStorage.receiveOnly" in op)

    # ---- 2026-09-24 追加：右键倒流体（用户点名） ----
    opblk = read_src("DistillationOperatorBlock.java")
    oc2 = int_consts(opblk)
    eq(u"一次右键倒 POUR_PER_CLICK", 1000, oc2.get("POUR_PER_CLICK"))
    check(u"操作器实现了 useItemOn（拿容器右键）",
          "protected ItemInteractionResult useItemOn(" in opblk)
    check(u"倒之前先 SIMULATE 问罐子能收多少（收 0 就一滴不倒、容器内容物不丢）",
          "IFluidHandler.FluidAction.SIMULATE" in opblk)
    check(u"能收多少就只从容器取多少（drain 部分取）再灌进去",
          "container.drain(stack, accepted)" in opblk
          and "oil.fill(drained, IFluidHandler.FluidAction.EXECUTE)" in opblk)
    check(u"倒不进去 / 容器是空 都有提示（不静默）",
          "distillation.pour.rejected" in opblk and "distillation.pour.empty" in opblk)

    iface = read_src("FluidContainerItem.java")
    check(u"容器接口扩了 contents/drain 两个方向（灌装的反方向）",
          "FluidStack contents(ItemStack stack);" in iface
          and "FluidStack drain(ItemStack stack, int maxAmount);" in iface)
    for impl in ("OilBucketItem.java", "HighPressureTankItem.java"):
        t = read_src(impl)
        check(u"%s 实现了 contents + drain" % impl,
              "public FluidStack contents(ItemStack stack)" in t
              and "public FluidStack drain(ItemStack stack, int maxAmount)" in t)

    # ---- 2026-09-24 追加：诊断 API ----
    check(u"结构类里有 diagnose + Diagnosis（提示与判定分开）",
          "public record Diagnosis(" in tower and "public static Diagnosis diagnose(" in tower)
    check(u"诊断按"错格数最少"挑，并报第一处不符的格子",
          "if (wrong < bestWrong || (wrong == bestWrong && dist < bestDist))" in tower)''',
          u"补倒油 + 诊断的断言")

    patch(VER,
          u'check(u"四份语言键数一致且 = 241（219 + 22）",\n          len(set(counts.values())) == 1 and list(counts.values())[0] == 241)',
          u'check(u"四份语言键数一致且 = 246（219 + 22 + 5）",\n          len(set(counts.values())) == 1 and list(counts.values())[0] == 246)',
          u"_zf78 键数 241 → 246")
    patch(VER,
          u'''               u"tooltip.potato_s_t.distillation_controller",
               u"tooltip.potato_s_t.distillation_operator"])''',
          u'''               u"tooltip.potato_s_t.distillation_controller",
               u"tooltip.potato_s_t.distillation_operator",
               u"gui.potato_s_t.distillation.diagnosis.found",
               u"gui.potato_s_t.distillation.diagnosis.none",
               u"gui.potato_s_t.distillation.diagnosis.empty",
               u"gui.potato_s_t.distillation.pour.rejected",
               u"gui.potato_s_t.distillation.pour.empty"])''',
          u"_zf78 新键进 need 清单")

    print(u"== ② 活体计数 241 → 246 ==")
    patch(os.path.join(TOOLS, "_zf73_verify.py"),
          u'check(u"B11 四语言各 241 键（ZF75 加 biome 名 + ZF78 加 22 键）", all(v == 241 for v in counts.values()), str(counts))',
          u'check(u"B11 四语言各 246 键（ZF75 加 biome 名 + ZF78 加 27 键）", all(v == 246 for v in counts.values()), str(counts))',
          u"_zf73 B11 → 246")
    patch(os.path.join(TOOLS, "_zf75_verify.py"),
          u'check(u"C2 四语言各 241 键（ZF78 起）", all(v == 241 for v in counts.values()), str(counts))',
          u'check(u"C2 四语言各 246 键（ZF78 起）", all(v == 246 for v in counts.values()), str(counts))',
          u"_zf75 C2 → 246")
    patch(os.path.join(TOOLS, "_zf71_verify.py"),
          u'    check(len(keys) == 4 and set(keys.values()) == {241} and u"241 keys each" in doc,',
          u'    check(len(keys) == 4 and set(keys.values()) == {246} and u"246 keys each" in doc,',
          u"_zf71 键数 → 246")
    patch(ANN, u"(241 keys each)", u"(246 keys each)", u"公告 → 246 键")

    print(u"\n失败项 = %d" % len(fails))
    for f in fails:
        print(u"  !! " + f)
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())
