# -*- coding: utf-8 -*-
u"""_zf94_diff.py —— 逐行比 ZF94 改前/改后的四份 OBJ，证明"只动了该动的 8 行 vt"

判据：
  · 差异**只出现在 `vt ` 行**（顶点 / 法线 / 面 一行都不许变）；
  · 差异行数 = 1 根柱子 × 2 个面（东、西）× 4 个顶点 = **8 行/份**；
  · 平移量只有两种：东 (−102/256, +127/256)、西 (−85/256, +110/256)。

用法：
    python _zf94_diff.py
"""
import os
import sys

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

NEW = r"E:\PotatoST\src\main\resources\assets\potato_s_t\models\block"
OLD = r"C:\PotatoST救援\zf94_pre\src\main\resources\assets\potato_s_t\models\block"
FACINGS = ["north", "south", "east", "west"]
EXPECT_LINES = 8
EXPECT_DELTAS = {(-0.398438, 0.496094): u"东（素板副本1 → 格栅A）",
                 (-0.332031, 0.429688): u"西（素板副本2 → 格栅B）"}
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
            merged = None
            for k in deltas:
                if abs(k[0] - key[0]) <= 2e-6 and abs(k[1] - key[1]) <= 2e-6:
                    merged = k
                    break
            deltas.setdefault(merged or key, []).append(i + 1)
        print(u"  平移量分组（1 格 = 1/256 贴图）：")
        for (du, dv), lines in sorted(deltas.items(), key=lambda kv: -len(kv[1])):
            tag = u"**不在预期里**"
            for want, label in EXPECT_DELTAS.items():
                if abs(du - want[0]) <= 2e-6 and abs(dv - want[1]) <= 2e-6:
                    tag = label
                    break
            print(u"    (%+.6f, %+.6f)  %-24s 共 %d 行" % (du, dv, tag, len(lines)))
            if tag == u"**不在预期里**":
                fails.append(u"%s 出现预期外的平移量 (%+.6f,%+.6f)" % (name, du, dv))
            if len(lines) % 4:
                fails.append(u"%s 平移量 (%+.6f,%+.6f) 对应 %d 行，不是 4 的倍数" % (name, du, dv, len(lines)))
        if len(deltas) != 2:
            fails.append(u"%s 平移量分了 %d 组，期望 2 组" % (name, len(deltas)))
        print(u"  首条差异：第 %d 行  %s  →  %s" % (diff[0][0] + 1, diff[0][1], diff[0][2]))
    print(u"\n失败项 = %d" % len(fails))
    for f in fails:
        print(u"  !! " + f)
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())
