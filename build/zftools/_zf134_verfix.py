# -*- coding: utf-8 -*-
"""_zf134_verfix.py —— 常驻校验跟着"方向向量"改判据（并新增角度专属判据）

旧判据 B1/B2 盯的是"宽度 6 / 按 -3..+2 铺"（那时用 `int offset = lateral - HALF_WIDTH`），
现在采样改成"前缘 + 法线 × 横向偏移"（`double lat`）⇒ 判据要跟着改，否则会假红。
同时补三条**角度专属**判据（这次改动的正面凭据）：
  · B24 `fire()` 用的是**归一化单位向量**（不是主轴 + 正负）；
  · B25 退化兜底：视线垂直时用 yaw 算方向（否则除零 / 方向为 0）；
  · C14 包里带的是 `dirX/dirZ` 两个 double（旧版是 alongX+sign）。
"""
import io
import sys

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
P = r"E:\PotatoST\build\zftools\_zf133_verify.py"

OLD = '''    ok("B2 偶数宽按 -3..+2 铺（相对玩家对称）", "int offset = lateral - HALF_WIDTH;" in shock)'''

NEW = '''    # B2：ZF134 起采样是"前缘 + 法线 × 横向偏移"（任意角度）；
    #     横向偏移仍然是 -3..+2（相对玩家对称），但类型变成 double。
    ok("B2 偶数宽按 -3..+2 铺（相对玩家对称，double 版）",
       "double lat = lateral - HALF_WIDTH;" in shock)
    ok("B24 采样点 = 前缘 + 法线 × 横向偏移（任意角度的核心算式）",
       "double perpX = -wave.dirZ;" in shock and "double perpZ = wave.dirX;" in shock
       and "Math.floor(frontX + perpX * lat)" in shock
       and "Math.floor(frontZ + perpZ * lat)" in shock)
    ok("B25 朝向是**归一化单位向量**（任意角度；不是主轴 + 正负）",
       "double dirX = dx / len;" in shock and "double dirZ = dz / len;" in shock)
    ok("B26 视线垂直时用 yaw 兜底（否则水平投影退化 ⇒ 方向为零）",
       "if (len < 1.0E-4D)" in shock and "Math.sin(yaw)" in shock)'''

s = io.open(P, encoding="utf-8").read()
n = s.count(OLD)
assert n == 1, "B2 锚点 %d 次" % n
s = s.replace(OLD, NEW, 1)

# B1 的措辞（宽度/半宽/高度都不变，但顺带说明方向已与轴解耦）
s = s.replace('ok("B1 宽度 6 / 半宽 3 / 高 3",',
              'ok("B1 宽度 6 / 半宽 3 / 高 3（与方向无关）",', 1)

# C 组补一条：包里带方向向量
C_ANCHOR = '''    ok("C12 广播半径 64 格", "RANGE = 64.0D" in net)'''
C_ADD = C_ANCHOR + '''
    ok("C14 数据包带的是 dirX/dirZ 两个 double（旧版是 alongX + sign）",
       "double dirX, double dirZ, long startTick" in net
       and "ByteBufCodecs.DOUBLE, ShockwavePayload::dirX" in net)
    ok("C15 客户端渲染按法线算端点（斜着放也能正对朝向）",
       "double perpX = -wave.dirZ;" in rend and "frontX - vx, frontZ - vz" in rend)'''
n = s.count(C_ANCHOR)
assert n == 1, "C12 锚点 %d 次" % n
s = s.replace(C_ANCHOR, C_ADD, 1)

# G 组：探针要覆盖斜角那场
s = s.replace('''        ok("G4 探针覆盖九个场景",
           all(s in body for s in ("① 物品与档位", "② (b)", "③ (d)", "④ (e)",
                                   "⑤ (i)", "⑥ (h)", "⑦ (f)", "⑧ (g)", "⑨ (c)")))''',
              '''        ok("G4 探针覆盖十个场景（含 ZF134 的斜角 21°）",
           all(s in body for s in ("① 物品与档位", "② (b)", "③ (d)", "④ (e)",
                                   "⑤ (i)", "⑥ (h)", "⑦ (f)", "⑧ (g)", "⑨ (c)", "⑩ (j)")))''', 1)
s = s.replace('''        ok("G6 属性记账实测：显示总伤害 17.0", "17.0" in body)''',
              '''        ok("G6 属性记账实测：显示总伤害 17.0", "17.0" in body)
        ok("G7 斜角实测：斜线靶子全拆 + 正东对照点没被碰",
           "斜线靶子 3 根全拆" in body and "正东那一列的对照点没被碰" in body)''', 1)

io.open(P, "w", encoding="utf-8", newline="\n").write(s)
print("已更新常驻校验：B2 改写 + B24/B25/B26 + C14/C15 + G4/G7")
