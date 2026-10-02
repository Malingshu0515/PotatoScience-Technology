# -*- coding: utf-8 -*-
"""_zf133_parentfix4.py —— ★★ 真凶：**空气早退被我自己的"语义摆正"补丁删掉了**

## 铁证（`[WB]` 一次跑，126 条记录）
```
[WB] 挡住 t=1 100, 160, 97 = Air hard=0.0     ×6
[WB] 挡住 t=1 100, 161, 97 = Air hard=0.0     ×6
...（整片都是 Air）...
```
⇒ 波把**空气**判成了"斧子挖不动的方块"：`isCorrectToolForDrops(空气)` 当然是 false，
于是 `blocked = true`，波在**第 1 tick 就散**。这就是"少拆一格 / 一格不拆 / 末影人打不到"
这一长串症状的**同一个**根因。

## 为什么会这样（如实记）
`_zf133_parentfix2.py` 里我打算"把'有没有方块'的判据与注释摆正"，
脚本的 OLD 锚点从 `BlockState state = ...` 开始、NEW 在中间插了一段解释，
**但没把原来那句 `if (state.isAir()) { continue; }` 写回 NEW 里** ——
于是那句被整段替换掉了。而"空气"恰好是**最不容易在肉眼复查里被发现**的那一格
（报告里显示的是"少拆一格"，不是"波不动"）。

## 教训（要进档案）
**"解释性重写"和"功能行"不能放在同一次替换里。** 我那一刀只想加注释，
却顺手把一条 `continue` 吞了 —— 而探针当时报的是"少拆一格"，
我把方向猜成了"判据顺序问题"（于是又改了一次判据），白烧了四轮。
正确的做法：**改注释就只改注释**（纯注释块单独替换），功能行一个字别动。

跑法：python build\\zftools\\_zf133_parentfix4.py
"""
import io
import sys

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
SHOCK = r"E:\PotatoST\src\main\java\com\potatost\mod\ShockwaveManager.java"

OLD = """                // ⚠ 这一句判的是"**这一格有没有方块**"，不是"是不是空气方块"：
                //   发射者自己就站在波的出口上（用户要的"朝面向"必然如此），
                //   实体占着的那一格 `getBlockState` 同样是空气 —— 用"有没有方块"来判，
                //   那一格就会**自然穿过去**；用别的判据（比如"实体所在格也算障碍"）
                //   会把波在第 1 tick 就挡死，用户永远放不出这道波（[D14] 诊断实测过）。
                if (state.isAir()) {
                    continue;
                }

"""
OLD_FALLBACK = """                float hardness = state.getDestroySpeed(wave.level, pos);"""
NEW = """                // ⚠⚠ 这一句**不能删**（我删过一次，代价是四轮排查）：
                //   空气/实体占着的格子要**直接穿过去**。少了它，
                //   `isCorrectToolForDrops(空气)` 返回 false ⇒ 每一格空气都被当成
                //   "斧子挖不动的方块" ⇒ `blocked = true` ⇒ 波在第 1 tick 就散。
                //   探针当时的表现是"少拆一格"，非常容易误判成判据顺序问题。
                if (state.isAir()) {
                    continue;
                }

                float hardness = state.getDestroySpeed(wave.level, pos);"""

# 去掉 [WB] 诊断（产品代码不留）
WB_OLD = """                if (!owner.getMainHandItem().isCorrectToolForDrops(state)) {
                    System.out.println("[WB] 挡住 t=" + wave.totalTicks + " " + pos.toShortString()
                            + " = " + state.getBlock().getName().getString()
                            + " hard=" + hardness);
                    blocked = true;
                }"""
WB_NEW = """                if (!owner.getMainHandItem().isCorrectToolForDrops(state)) {
                    blocked = true;
                }"""

s = io.open(SHOCK, encoding="utf-8").read()

if s.count(OLD) == 1:
    s = s.replace(OLD, NEW, 1)
    print("[OK] 空气早退已补回（注释块位置）")
elif s.count(OLD_FALLBACK) == 1:
    s = s.replace(OLD_FALLBACK, NEW, 1)
    print("[OK] 空气早退已补回（直接插在硬度之前）")
else:
    print("[FAIL] 找不到插入点（OLD=%d FALLBACK=%d）" % (s.count(OLD), s.count(OLD_FALLBACK)))
    sys.exit(1)

n = s.count(WB_OLD)
assert n == 1, "[WB] 诊断锚点 %d 次" % n
s = s.replace(WB_OLD, WB_NEW, 1)
print("[OK] [WB] 诊断已撤")

assert s.count("if (state.isAir()) {") == 1, "空气早退出现 %d 次" % s.count("if (state.isAir()) {")
io.open(SHOCK, "w", encoding="utf-8", newline="\n").write(s)
print("完成")
