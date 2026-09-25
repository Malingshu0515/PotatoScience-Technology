# -*- coding: utf-8 -*-
"""_zf68_publish.py —— ZF68 出成品（合金炉换成用户手绘模型）

⚠ 沿用 ZF63 的教训：**先查完、全过才拷**。
"""
import hashlib
import io
import os
import re
import shutil
import sys
import zipfile

SRC = r"E:\PotatoST\build\libs\potato_s_t-0.10.jar"
DST = r"E:\PotatoST\release\PotatoST-0.10.jar"
SHA = DST + ".sha1"
VOID = "95c970e41c764f729df4ec100a20f100b4236bb2"      # ZF67 那一版，本轮作废

FACINGS = ["north", "east", "south", "west"]
# 每个朝向的目标包围盒（X0, X1, Z0, Z1），来自 AlloySmelterStructure 的 80 格（见 _zf54_verify.py）
TARGET = {
    "north": (-3.0, 1.0, 0.0, 5.0),
    "east": (-4.0, 1.0, -3.0, 1.0),
    "south": (0.0, 4.0, -4.0, 1.0),
    "west": (0.0, 5.0, 0.0, 4.0),
}

fails = []


def sha1(path):
    h = hashlib.sha1()
    with io.open(path, "rb") as fh:
        h.update(fh.read())
    return h.hexdigest()


def main():
    if not os.path.isfile(SRC):
        return u"源 jar 不存在: %s" % SRC

    old = sha1(DST) if os.path.isfile(DST) else u"(无)"
    print(u"旧 release jar    : %s  (%d B)" % (old, os.path.getsize(DST) if os.path.isfile(DST) else 0))
    print(u"应当作废的旧 SHA1 : %s" % VOID)
    if old != VOID:
        fails.append(u"release 里的旧 jar 不是 ZF67 那一版（%s）" % old)

    with zipfile.ZipFile(SRC) as z:
        names = z.namelist()
        if [n for n in names if "Check" in n]:
            fails.append(u"新 jar 里混进了探针类")
        if [n for n in names if n.startswith("mezz/")]:
            fails.append(u"新 jar 里混进了 JEI 的东西（红线）")

        # 四份 OBJ：顶点数 112、面 84、包围盒罩住结构
        for f in FACINGS:
            rel = "assets/potato_s_t/models/block/alloy_smelter_%s.obj" % f
            if rel not in names:
                fails.append(u"新 jar 里缺: %s" % rel)
                continue
            text = z.read(rel).decode("utf-8")
            vs = [tuple(float(x) for x in m) for m in re.findall(r"^v (\S+) (\S+) (\S+)$", text, re.M)]
            faces = len(re.findall(r"^f ", text, re.M))
            xs = [v[0] for v in vs]
            zs = [v[2] for v in vs]
            ys = [v[1] for v in vs]
            t = TARGET[f]
            ok = (len(vs) == 112 and faces == 84
                  and abs(min(xs) - t[0]) <= 0.01 and abs(max(xs) - t[1]) <= 0.01
                  and abs(min(zs) - t[2]) <= 0.01 and abs(max(zs) - t[3]) <= 0.01
                  and abs(min(ys) + 1.0) <= 0.001 and abs(max(ys) - 2.375) <= 0.001)
            print(u"  [%s] %-46s v=%d f=%d X[%.3f,%.3f] Y[%.3f,%.3f] Z[%.3f,%.3f]"
                  % (u"OK" if ok else u"FAIL", "alloy_smelter_%s.obj" % f, len(vs), faces,
                     min(xs), max(xs), min(ys), max(ys), min(zs), max(zs)))
            if not ok:
                fails.append(u"%s 的网格/包围盒不对（期望 v=112 f=84 X%s Z%s Y[-1,2.375]）" % (rel, t[:2], t[2:]))

        rel = "assets/potato_s_t/models/block/alloy_smelter.mtl"
        mtl = z.read(rel).decode("utf-8") if rel in names else u""
        ok = u"map_Kd potato_s_t:block/heat_resistant_metal_block" in mtl and u"newmtl alloy_smelter" in mtl
        print(u"  [%s] alloy_smelter.mtl -> %s" % (u"OK" if ok else u"FAIL",
                                                   u"heat_resistant_metal_block" if ok else u"??"))
        if not ok:
            fails.append(u"MTL 没指向耐热金属块")

        # 上一轮的产物回归
        for rel in ("data/minecraft/tags/item/swords.json",
                    "data/minecraft/tags/item/pickaxes.json",
                    "com/potatost/mod/ModTiers.class"):
            if rel not in names:
                fails.append(u"缺少上一轮的产物: %s" % rel)

    if fails:
        print(u"\n**有失败项，未拷任何文件**：")
        for f in fails:
            print(u"  !! " + f)
        return 1

    shutil.copy2(SRC, DST)
    new = sha1(DST)
    io.open(SHA, "w", encoding="ascii", newline="\n").write(new + "\n")
    print(u"新 release jar    : %s  (%d B, %d 条目)" % (new, os.path.getsize(DST), len(names)))
    print(u"sha1 文件         : %s" % io.open(SHA, encoding="ascii").read().strip())
    print(u"作废              : %s" % VOID)
    print(u"失败项 = 0")
    return 0


if __name__ == "__main__":
    sys.exit(main())
