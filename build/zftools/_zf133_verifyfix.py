# -*- coding: utf-8 -*-
"""_zf133_verifyfix.py —— 常驻校验里几条**过时/写错**的判据（改了代码就得改判据）

| 检查 | 问题 | 改成 |
|---|---|---|
| B17 | 判据写的是 `"wave.owner.equals("`，而实现后来改成了 `target.getUUID().equals(wave.owner)`（修末地伤害时改的）| 盯"伤害循环里排除发射者 UUID"这件事 |
| F1 | 判据是"模型里没有 `minecraft:item/`" —— 而 `"parent": "minecraft:item/handheld"` 里**本来就有** `minecraft:item/` ⇒ 恒 FAIL（假判据）| 只看 `textures.layer0` 指不指自己 |
| 新增 B20/B21 | `MAX_DISTANCE`（射程上限）与 `originY`（发射时冻结高度）是这一轮补的两条规则，必须有判据 | 加两条 |
| 新增 A17 | 伤害常数与"显示总伤害"的**记账关系**（1 + 参数 + 档位加成）要盯住，防止有人只改一处 | 加一条 |

跑法：python build\\zftools\\_zf133_verifyfix.py
"""
import io
import sys

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
P = r"E:\PotatoST\build\zftools\_zf133_verify.py"

EDITS = [
    # B17
    ("""    ok("B17 不误伤发射者（按 UUID 排掉）",
       "LivingEntity.class" in shock and "wave.owner.equals(" in shock)""",
     """    ok("B17 不误伤发射者（伤害循环里跳过发射者 UUID）",
       "target.getUUID().equals(wave.owner)" in shock)"""),

    # F1
    ("""    ok("F1 斧子的模型不再借原版贴图（不在上面那张表里）",
       "star_steel_axe.json" not in borrowed)""",
     """    # ⚠ 判据要盯**贴图**，不能盯 `minecraft:item/` 这个前缀 ——
    #   `"parent": "minecraft:item/handheld"` 里也有它，第一版就是这么写出假 FAIL 的。
    axe_model = read(os.path.join(RES, r"models\\item\\star_steel_axe.json"))
    ok("F1 斧子的模型 layer0 指自己的贴图（没借原版）",
       "potato_s_t:item/star_steel_axe" in axe_model)"""),

    # 新增
    ("""    ok("B19 射线只发一次包", "broadcastWave" in shock and "ShockwaveNetworking.broadcastWave(player," in shock)""",
     """    ok("B19 射线只发一次包", "broadcastWave" in shock and "ShockwaveNetworking.broadcastWave(player," in shock)
    ok("B20 射程上限 64 格（补的规则，防跑飞）",
       "MAX_DISTANCE = 64" in shock and "wave.travelled * STEP_PER_TICK > MAX_DISTANCE" in shock)
    ok("B21 高度基准在发射那一刻冻结（originY，不是每 tick 现读玩家 Y）",
       "private final int originY;" in shock and "int oy = wave.originY;" in shock
       and "boolean alongX, int sign, int originY)" in shock)
    ok("B22 末地伤害真的接在采样循环里（不只是有个公式函数）",
       "damageAt(wave, owner, pos)" in shock and "dimension() == Level.END" in shock)"""),

    # A 组新增：伤害记账
    ("""    ok("A16 客户端不判定（只在服务端出手）", "if (level.isClientSide) {" in axe)""",
     """    ok("A16 客户端不判定（只在服务端出手）", "if (level.isClientSide) {" in axe)
    # 1.21 的记账：物品主手修饰符 = createAttributes 参数 + 档位加成；显示总伤害 = 属性基础值 1 + 修饰符
    ok("A17 伤害常数与档位加成配套（探针实测显示总伤害 17.0，改一处必须改注释与判据）",
       "STAR_STEEL_DAMAGE = 8.0F" in tiers
       and "ModTiers.STAR_STEEL_DAMAGE, ModTiers.STAR_STEEL_SPEED_MODIFIER" in items)"""),
]


def main():
    s = io.open(P, encoding="utf-8").read()
    for i, (a, b) in enumerate(EDITS):
        n = s.count(a)
        assert n == 1, "第 %d 段锚点 %d 次：%r" % (i + 1, n, a.splitlines()[0][:70])
        s = s.replace(a, b, 1)
        print("[OK] 第 %d 段" % (i + 1))
    io.open(P, "w", encoding="utf-8", newline="\n").write(s)
    print("判据已更新")


main()
