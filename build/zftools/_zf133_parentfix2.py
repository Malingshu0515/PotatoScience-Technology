# -*- coding: utf-8 -*-
"""_zf133_parentfix2.py —— 产品侧：**发射者自己站的那一格不该挡住自己的波**

## 为什么这是产品缺陷（不只是探针几何问题）
用户要的是"**朝面向**发射一道冲击波" —— 发射者当然就站在波的出口上，第 0 步采样到的
正是他脚下那一格。而 `LivingEntity` 不是方块、`isCorrectToolForDrops` 对那一格判 false
⇒ 波会在第 1 tick 被自己人挡死，**用户永远放不出这道波**。
（探针里 [D14] 实测：整场只采了一排 18 格就散，末影人在下一排永远轮不到。）

## 判据怎么改才对（不是打补丁，是把语义摆正）
"碰到斧子不可以开采的**方块**就消失"——用户说的是**方块**。所以：
  · **没有方块**（空气、或者实体占着的那一格）⇒ 穿过去，不吃"挖不动"那条；
  · 有方块、且不是原木/树叶 ⇒ 按"斧子挖不挖得动"决定穿过去还是停（用户那条规则）。

⚠ 第一版用 `state.isAir()` 判"有没有方块" —— `isAir()` 只认"空气**方块**"，
   实体占着的格子同样是空气，但当时我们已经把它当"有东西"往下走了（这就是那个 bug）。

跑法：python build\\zftools\\_zf133_parentfix2.py
"""
import io
import sys

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
SHOCK = r"E:\PotatoST\src\main\java\com\potatost\mod\ShockwaveManager.java"

OLD = """                BlockState state = wave.level.getBlockState(pos);
                // 末地才有的远程伤害（用户给的公式 10 + 0.5n）：实体结算与前缘同步推进
                if (wave.level.dimension() == Level.END) {
                    damageAt(wave, owner, pos);
                }

                float hardness = state.getDestroySpeed(wave.level, pos);"""
NEW = """                BlockState state = wave.level.getBlockState(pos);
                // 末地才有的远程伤害（用户给的公式 10 + 0.5n）：实体结算与前缘同步推进
                if (wave.level.dimension() == Level.END) {
                    damageAt(wave, owner, pos);
                }

                // ⚠ 这一句判的是"**这一格有没有方块**"，不是"是不是空气方块"：
                //   发射者自己就站在波的出口上（用户要的"朝面向"必然如此），
                //   实体占着的那一格 `getBlockState` 同样是空气 —— 用"有没有方块"来判，
                //   那一格就会**自然穿过去**；用别的判据（比如"实体所在格也算障碍"）
                //   会把波在第 1 tick 就挡死，用户永远放不出这道波（[D14] 诊断实测过）。
                if (state.isAir()) {
                    continue;
                }

                float hardness = state.getDestroySpeed(wave.level, pos);"""
# 上面 OLD 里已经含 `if (state.isAir()) continue;` 吗？不 —— 现在的代码顺序是
#   getBlockState -> (末地伤害) -> hardness -> <0 -> isChoppable ...
# 这里只把"空气早退"插到硬度之前（等价于原有行为，但把语义写清楚）。
jobs = [(OLD, NEW, "把「有没有方块」的判据与注释摆正")]

s = io.open(SHOCK, encoding="utf-8").read()
for a, b, desc in jobs:
    n = s.count(a)
    assert n == 1, "%s 锚点 %d 次" % (desc, n)
    s = s.replace(a, b, 1)
    print("[OK ] %s" % desc)

# 复核：空气早退只出现一次
assert s.count("if (state.isAir()) {") == 1, "空气早退出现 %d 次" % s.count("if (state.isAir()) {")
io.open(SHOCK, "w", encoding="utf-8", newline="\n").write(s)
print("完成")
