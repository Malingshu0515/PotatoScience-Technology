# -*- coding: utf-8 -*-
u"""_zf137_verify.py —— 本轮（星璨钢头盔给夜视 **III / 13 s，且不闪**）的常驻校验

用户改过三次口：
  ① 「星璨钢头盔穿戴加个夜视效果 1级 4s」
  ② 「星璨钢头盔改成5s夜视」
  ③ 「头盔改成8s夜视III吧 **或者**让视野不会因为夜视快没了而一闪一闪也可以」

**最后那两条不能同时成立**，本轮把判据从源码里挖出来核实过
（`GameRenderer.getNightVisionScale` + `MobEffectInstance.endsWithin`）：

```java
return !mobeffectinstance.endsWithin(200) ? 1.0F
     : 0.7F + Mth.sin((duration - nanoTime) * (float) Math.PI * 0.2F) * 0.3F;
// endsWithin(n) = !isInfiniteDuration() && duration <= n
```

⇒ **剩余时长 ≤ 200 tick（10 s）就闪**（亮度 0.4~1.0、周期 10 tick = 0.5 秒），**不看等级**
⇒ 4 s / 5 s / 8 s 全都会闪。要"不闪"只能让**剩余时长永远 > 200 tick**。
本轮取"不闪"这条（用户说"或者…也可以"），等级按他说的给 **III**：
单次 **260 tick（13 s）**、剩余掉到 **220 tick（11 s）** 就续 ⇒ 剩余恒在 220~260。

**要钉住的五个口径**（用户都没说全，写错一条就变成另一种东西）：
  ① 只**头盔**（不是"每件"，也不是"满套"）；
  ② **不分昼夜、不分维度**；
  ③ 等级 **III**（amplifier 2）；
  ④ **不闪**：`余量(220) > 原版闪烁阈值(200)` 且 `时长(260) > 余量(220)` —— 这两条是本轮的核心；
  ⑤ 是"一直续"，**不许**写成伤害吸收那种"周期给一次"（`ABSORPTION_REFRESH = 0`）。

取证口沿用 ZF103 那套（`importlib` 复用它的常量池 / 字节码 / javap 工具）：
  · 常量与组件 —— `javap -p -c -constants` 的字段声明行 + `static {}` 的常量串；
  · **调用点** —— `call_arg_sequences(disasm, "ensure")` 里那一条带 `NIGHT_VISION` 的序列，
    能把 `(效果, 等级, 时长, 余量)` 四个参数一次钉死（比"名字在不在"强一级，§4.71/§4.76）；
  · 源码结构 —— "那一块里没有 `isNight`"这种事，只有读源码才判得了。

跑法：
    $env:PYTHONIOENCODING='utf-8'
    python E:\\PotatoST\\build\\zftools\\_zf137_verify.py      # 退出码 0 = 全过
"""
import importlib.util
import io
import json
import os
import re
import sys

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

PROJ = r"E:\PotatoST"
TOOLS = os.path.join(PROJ, "build", "zftools")
LANG = os.path.join(PROJ, r"src\main\resources\assets\potato_s_t\lang")

# 用户最后要的数（照原话抄，不是从源码抄 —— §4.27）
SECONDS = 13                    # 取"不闪"那条 ⇒ 单次时长必须 > 10 s
TICKS = SECONDS * 20            # 13 s = 260 tick
LEVEL = 2                       # 夜视 III ⇔ amplifier 2
MARGIN = 220                    # NIGHT_VISION_MARGIN：剩余掉到它就续
FLICKER_TICKS = 200             # ★ 原版 GameRenderer.getNightVisionScale 的闪烁阈值（从源码核实）

_spec = importlib.util.spec_from_file_location("v", os.path.join(TOOLS, "_zf103_verify.py"))
v = importlib.util.module_from_spec(_spec)
_argv = sys.argv
sys.argv = ["x"]
_spec.loader.exec_module(v)
sys.argv = _argv

fails = []


def check_ok(ok, label, detail=u""):
    v.check(ok, label, detail)
    return ok


def main():
    setc = v.cls(u"ModArmorSet")
    mats = v.cls(u"ModArmorMaterials")
    src_set = v.read_source(u"ModArmorSet")
    dis_set = v.javap_disasm(u"ModArmorSet")

    print(u"")
    print(u"================ ① 效果本身：夜视 III / 13 s（不闪） ================")
    check_ok(u"NIGHT_VISION" in setc.names,
             u"ModArmorSet 引用了 MobEffects.NIGHT_VISION（不是别的效果）")
    cst = v.field_constants(dis_set)
    check_ok(cst.get(u"HELMET_NIGHT_VISION_TICKS") == str(TICKS),
             u"HELMET_NIGHT_VISION_TICKS = %d（= %d s × 20 tick）" % (TICKS, SECONDS),
             u"javap -constants 读到 %r" % cst.get(u"HELMET_NIGHT_VISION_TICKS"))
    check_ok(cst.get(u"NIGHT_VISION_III") == str(LEVEL),
             u"NIGHT_VISION_III = %d（药水等级 III ⇔ amplifier 2）" % LEVEL,
             u"javap -constants 读到 %r" % cst.get(u"NIGHT_VISION_III"))
    check_ok(cst.get(u"NIGHT_VISION_MARGIN") == str(MARGIN),
             u"NIGHT_VISION_MARGIN = %d tick" % MARGIN,
             u"javap -constants 读到 %r" % cst.get(u"NIGHT_VISION_MARGIN"))

    # ★★ 本轮的核心：**不闪**的不变量（原版公式见文件头）
    #   剩余时长在 [余量, 时长] 之间来回 ⇒ 只要「余量 > 200」且「时长 > 余量」，
    #   剩余时长就**永远 > 200 tick** ⇒ getNightVisionScale 恒为 1.0，一点不闪。
    check_ok(MARGIN > FLICKER_TICKS,
             u"补充余量 %d > 原版闪烁阈值 %d ⇒ 剩余时长永远回不到「会闪」的区间" % (MARGIN, FLICKER_TICKS),
             u"余量 ≤ 阈值就会一闪一闪（4 s / 5 s / 8 s 版本闪的就是这个）")
    check_ok(TICKS > MARGIN,
             u"单次时长 %d > 余量 %d（差 %d tick = 每 %.1f s 续一次）"
             % (TICKS, MARGIN, TICKS - MARGIN, (TICKS - MARGIN) / 20.0))

    # ★ 调用点取证：ensure(player, NIGHT_VISION, 2, 260, 220)
    seqs = v.call_arg_sequences(dis_set, u"ensure")
    nv = [s for s in seqs if any(x == u"NIGHT_VISION" for x in s)]
    if check_ok(len(nv) == 1, u"ensure(...) 的调用点里**正好有一条**带 NIGHT_VISION",
                u"实际 %d 条（全部序列：%s）" % (len(nv), seqs)):
        s = nv[0]
        nums = [x for x in s if x.lstrip(u"-").isdigit()]
        check_ok(str(LEVEL) in nums, u"那条调用的等级参数 = %d（III 级）" % LEVEL, u"实际 %s" % s)
        check_ok(str(TICKS) in nums, u"那条调用的时长参数 = %d tick（%d s）" % (TICKS, SECONDS),
                 u"实际 %s" % s)
        check_ok(str(MARGIN) in nums,
                 u"那条调用的补充余量 = %d tick（> 200 ⇒ 不闪）" % MARGIN, u"实际 %s" % s)

    print(u"")
    print(u"================ ② 只头盔：不是在「每件/满套」那一档里 ================")
    check_ok(u"hasStarSteelHelmet" in mats.strings,
             u"ModArmorMaterials 声明了 hasStarSteelHelmet（判据只有一份）")
    check_ok(u"hasStarSteelHelmet" in setc.names,
             u"ModArmorSet 调的是 hasStarSteelHelmet(...)")
    check_ok(u"HEAD" in mats.names,
             u"那个判据读的是 EquipmentSlot.HEAD（不是别的槽）")
    # ⚠ 只查"常量池里有 HEAD"是不够的：`ARMOR_SLOTS` 数组里本来就有 HEAD
    #   ⇒ 把判据悄悄改成 CHEST 时那条断言照样绿。必须按**源码形状**钉住那一格。
    src_mats = v.read_source(u"ModArmorMaterials")
    check_ok(u"isMaterial(entity.getItemBySlot(EquipmentSlot.HEAD), STAR_STEEL)" in src_mats,
             u"判据那一行读的是 HEAD 槽（改了别的槽当场红）")
    check_ok(u"if (ModArmorMaterials.hasStarSteelHelmet(player)) {" in src_set,
             u"夜视那一块的门就是「戴着头盔」这一条")

    print(u"")
    print(u"================ ③ 不分昼夜、不分维度 ================")
    # 把"夜视那一块"从源码里切出来，只在这一块里找 isNight / dimension。
    # ⚠ 切法：从锚点起、**到第一个空行为止** —— 第一版切了固定 420 字符，
    #   结果越界吃进了下面"满套 · 末地"那一段，`dimension` 当场假 FAIL。
    i = src_set.find(u"hasStarSteelHelmet(player)")
    block = src_set[i:].split(u"\n\n")[0] if i >= 0 else u""
    check_ok(bool(block) and u"ensure(" in block, u"源码里找得到那一块（只有那一个 if）")
    check_ok(u"isNight" not in block,
             u"那一块里**没有** isNight 的门（用户说的是「穿戴就有」，不是「晚上才有」）")
    check_ok(u"dimension" not in block,
             u"那一块里**没有**维度判定（末地/下界同样给）")
    check_ok(u"level.isNight() && ModArmorMaterials.hasAnyStarSteelPiece(player)" in src_set,
             u"旁边那条「夜晚抗性 I」没被挤掉（每件那一档仍是夜晚限定）")

    print(u"")
    print(u"================ ④ 是「一直续」，不是「周期给一次」 ================")
    # 那一块的 ensure(...) 调用必须传 NIGHT_VISION_MARGIN（220），
    # **不许**传 KNOCKBACK_MARGIN（40，会闪）、也不许传 ABSORPTION_REFRESH（0，会亮一段黑一段）
    check_ok(u"HELMET_NIGHT_VISION_TICKS,\n                    NIGHT_VISION_MARGIN" in src_set
             or u"HELMET_NIGHT_VISION_TICKS, NIGHT_VISION_MARGIN" in src_set,
             u"夜视的补充余量传的是 NIGHT_VISION_MARGIN（220 tick > 200 ⇒ 不闪）")
    check_ok(not re.search(r"NIGHT_VISION_III[\s\S]{0,260}KNOCKBACK_MARGIN", src_set),
             u"没有把余量写成 KNOCKBACK_MARGIN（那会让剩余掉到 2 s ⇒ 立刻开始闪）")
    check_ok(not re.search(r"NIGHT_VISION[\s\S]{0,200}ABSORPTION_REFRESH", src_set),
             u"没有把夜视写成「周期性给一次」（那会变成亮一段、黑一段）")
    check_ok(u"ABSORPTION_REFRESH = 0" in src_set,
             u"伤害吸收那条「必须等结束才给下一次」的老口径没被动过")

    print(u"")
    print(u"================ ⑤ 满套那三条效果没被碰坏 ================")
    for name, why in ((u"hasFullStarSteelSet", u"满套判据"),
                      (u"REGENERATION", u"末地：生命恢复"),
                      (u"DAMAGE_RESISTANCE", u"抗性提升"),
                      (u"DAMAGE_BOOST", u"力量"),
                      (u"ABSORPTION", u"伤害吸收"),
                      (u"SLOW_FALLING", u"虚空救援的缓降")):
        check_ok(name in setc.names or name in setc.strings, u"还在：%s" % why)

    print(u"")
    print(u"================ ⑥ 玩家看得见：四语言说明里有这一条 ================")
    for name in (u"zh_cn.json", u"en_us.json", u"ja_jp.json", u"ru_ru.json"):
        table = json.loads(io.open(os.path.join(LANG, name), encoding="utf-8").read())
        text = table.get(u"tooltip.potato_s_t.star_steel_set", u"")
        check_ok(bool(text), u"%s：星璨钢套的说明还在" % name)
        check_ok((u"夜视" in text) or (u"Night Vision" in text) or (u"暗視" in text)
                 or (u"Ночное зрение" in text),
                 u"%s：说明里写了头盔给夜视" % name)

    print(u"")
    print(u"==============================")
    print(u"断言数 = %d   失败项 = %d" % (v.count, len(v.fails)))
    for f in v.fails:
        print(u"  !! " + f)
    print(u"结论: %s" % (u"通过" if not v.fails else u"有失败项"))
    return 1 if v.fails else 0


if __name__ == "__main__":
    sys.exit(main())
