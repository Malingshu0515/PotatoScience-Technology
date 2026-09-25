# -*- coding: utf-8 -*-
u"""_zf92_diff.py —— 逐行比 ZF92 改前/改后的四份 OBJ，证明"只动了该动的 vt"

判据（任何一条不成立就报出来）：
  · 差异**只出现在 `vt ` 行**（顶点 v / 法线 vn / 面 f 一行都不许变）；
  · 差异行数 = **28/份** = ZF92 的 20 行 + ZF94 的 8 行 —— 这份脚本比的一直是
    `zf92_pre` 那份快照，所以**后面几轮改动同样落在这四份 OBJ 上时，这里要跟着把期望加进去**
    （ZF94 把第二根柱子的东/西从素板副本换成格栅，正好又 2 面 × 4 顶点 = 8 行）。
    ZF92 的 20 行：两根柱子各动 3 个面 × 4 个顶点 = 24 处，其中 #02 的底面本来就是
    "盖板→盖板"（原地不动）⇒ 有 4 行值不变，实际变化 20 行；
  · 平移量只有五种（三种来自 ZF92、两种来自 ZF94）。

⚠ 第一版把期望写成 24 行，脚本直接报 4 条失败 —— 那是**我把"赋值次数"当成了"值变化行数"**，
  不是模型错。这里改成按"值真的变了"来数，并把 -17/256 的两组按 2e-6 容差并成一组
  （两组都是 17/256，分组不同只是 6 位小数四舍五入的差别）。

用法：
    python _zf92_diff.py
"""
import os
import sys

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

NEW = r"E:\PotatoST\src\main\resources\assets\potato_s_t\models\block"
OLD = r"C:\PotatoST救援\zf92_pre\src\main\resources\assets\potato_s_t\models\block"
FACINGS = ["north", "south", "east", "west"]
EXPECT_LINES = 28
EXPECT_DELTAS = {(0.0, round(34.0 / 256.0, 6)): u"ZF92 顶面（两根）",
                 (0.0, round(-17.0 / 256.0, 6)): u"ZF92 #01 正面/底面",
                 (0.0, round(-34.0 / 256.0, 6)): u"ZF92 #02 正面",
                 (round(-102.0 / 256.0, 6), round(127.0 / 256.0, 6)): u"ZF94 #02 东",
                 (round(-85.0 / 256.0, 6), round(110.0 / 256.0, 6)): u"ZF94 #02 西"}
fails = []


def main():
    for facing in FACINGS:
        name = "electric_blast_furnace_%s.obj" % facing
        a = open(os.path.join(OLD, name), "rb").read().decode("utf-8").splitlines()
        b = open(os.path.join(NEW, name), "rb").read().decode("utf-8").splitlines()
        print(u"\n=== %s ===" % name)
        if len(a) != len(b):
            fails.append(u"%s 行数变了：%d → %d" % (name, len(a), len(b)))
            continue
        diff = [(i, x, y) for i, (x, y) in enumerate(zip(a, b)) if x != y]
        print(u"  行数 %d（不变）；值真的变了的行 %d（期望 %d）" % (len(a), len(diff), EXPECT_LINES))
        nondiff = [(i, x, y) for i, x, y in diff if not (x.startswith(u"vt ") and y.startswith(u"vt "))]
        if nondiff:
            fails.append(u"%s 有 %d 行不是 vt 却变了（第一条：第 %d 行 %r → %r）"
                         % (name, len(nondiff), nondiff[0][0] + 1, nondiff[0][1], nondiff[0][2]))
        else:
            print(u"  ✓ 差异全部落在 `vt` 行：顶点 / 法线 / 面 一行未动")
        if len(diff) != EXPECT_LINES:
            fails.append(u"%s 差异行 %d，期望 %d" % (name, len(diff), EXPECT_LINES))
        deltas = {}
        for i, x, y in diff:
            ux, vx = (float(t) for t in x.split()[1:3])
            uy, vy = (float(t) for t in y.split()[1:3])
            key = (round(uy - ux, 6), round(vy - vx, 6))
            # -17/256 的两组因四舍五入差 1e-6，按 2e-6 容差并组
            merged = None
            for k in deltas:
                if abs(k[0] - key[0]) <= 2e-6 and abs(k[1] - key[1]) <= 2e-6:
                    merged = k
                    break
            deltas.setdefault(merged or key, []).append(i + 1)
        print(u"  平移量分组（贴图 UV 单位，1 格 = 1/256 贴图）：")
        for (du, dv), lines in sorted(deltas.items(), key=lambda kv: -len(kv[1])):
            # 比对也带 2e-6 容差：OBJ 里的数是 6 位小数，相减后末位会差 1
            tag = u"**不在预期里**"
            for want, label in EXPECT_DELTAS.items():
                if abs(du - want[0]) <= 2e-6 and abs(dv - want[1]) <= 2e-6:
                    tag = label
                    break
            print(u"    (%+.6f, %+.6f)  %-22s 共 %d 行" % (du, dv, tag, len(lines)))
            if tag == u"**不在预期里**":
                fails.append(u"%s 出现预期外的平移量 (%+.6f,%+.6f)" % (name, du, dv))
            if len(lines) % 4:
                fails.append(u"%s 平移量 (%+.6f,%+.6f) 对应 %d 行，不是 4 的倍数"
                             % (name, du, dv, len(lines)))
        if len(deltas) != len(EXPECT_DELTAS):
            fails.append(u"%s 平移量分了 %d 组，期望 %d 组" % (name, len(deltas), len(EXPECT_DELTAS)))
        print(u"  首条差异：第 %d 行  %s  →  %s" % (diff[0][0] + 1, diff[0][1], diff[0][2]))
    print(u"\n失败项 = %d" % len(fails))
    for f in fails:
        print(u"  !! " + f)
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())
