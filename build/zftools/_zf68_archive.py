# -*- coding: utf-8 -*-
"""_zf68_archive.py —— ZF68 归档（合金炉换成用户手绘模型）"""
import hashlib
import io
import os
import shutil
import sys

PROJ = r"E:\PotatoST"
ROOT = r"C:\Users\Administrator\Desktop\PotatoST救援_20260917_183054\zf68_pre"
NEW = os.path.join(ROOT, u"新增文件")

FILES = [
    # 用户给的源模型（原样留存，以后换模型就覆盖它）
    u"build\\zftools\\_zf68_user_model.obj",
    # 本轮烘出来的成品（四份朝向 + MTL）
    u"src\\main\\resources\\assets\\potato_s_t\\models\\block\\alloy_smelter_north.obj",
    u"src\\main\\resources\\assets\\potato_s_t\\models\\block\\alloy_smelter_east.obj",
    u"src\\main\\resources\\assets\\potato_s_t\\models\\block\\alloy_smelter_south.obj",
    u"src\\main\\resources\\assets\\potato_s_t\\models\\block\\alloy_smelter_west.obj",
    u"src\\main\\resources\\assets\\potato_s_t\\models\\block\\alloy_smelter.mtl",
    # 工具与日志
    u"build\\zftools\\_zf68_obj.py",
    u"build\\zftools\\_zf68_render.py",
    u"build\\zftools\\_zf68_docs.py",
    u"build\\zftools\\_zf68_archive.py",
    u"build\\zftools\\_zf68_obj_write.log",
    u"build\\zftools\\_zf68_verify.log",
    u"build\\zftools\\zf68_falsify.log",
    u"build\\zftools\\zf68_baked_front.png",
    u"build\\zftools\\zf68_baked_back.png",
    u"build\\zftools\\_zf68_gates_utf8.txt",
    # 成品
    u"release\\PotatoST-0.10.jar",
    u"release\\PotatoST-0.10.jar.sha1",
]


def sha1(path):
    h = hashlib.sha1()
    with io.open(path, "rb") as fh:
        h.update(fh.read())
    return h.hexdigest()


def main():
    fails = []
    rows = []
    for rel in FILES:
        src = os.path.join(PROJ, rel)
        dst = os.path.join(NEW, rel)
        if not os.path.isfile(src):
            fails.append(u"缺文件: %s" % rel)
            continue
        folder = os.path.dirname(dst)
        if not os.path.isdir(folder):
            os.makedirs(folder)
        shutil.copy2(src, dst)
        a, b = sha1(src), sha1(dst)
        if a != b:
            fails.append(u"拷贝后哈希不一致: %s" % rel)
        rows.append(u"%-76s %10d  %s" % (rel, os.path.getsize(dst), a))
        print(u"  [OK] %s" % rel)

    manifest = os.path.join(NEW, u"MANIFEST.txt")
    io.open(manifest, "w", encoding="utf-8", newline="\n").write(
        u"ZF68 归档清单\n"
        u"主题：合金炉外观换成用户手绘的 Blockbench 模型。\n"
        u"源模型：build\\zftools\\_zf68_user_model.obj（112 顶点 / 84 面 / 14 组 / 高 3.375 格，平面 5x4）。\n"
        u"烘法：_zf68_obj.py 转 90 度 + 只平移（模型 -X 那一列 = 机器后排 j=0，两根柱子正好落在两个接线口格）。\n"
        u"贴图：按用户要求先借耐热金属块（MTL 的 map_Kd），UV 用源模型原样。\n"
        u"改前件（7 个）在 ..\\src\\ 与 ..\\build\\zftools\\ 下。\n"
        u"成品：release\\PotatoST-0.10.jar = 8c4547e467b295049682a7fd84d4ae026dd0a2c9（2,211,900 B / 703 条目）；\n"
        u"      本轮作废 ZF67 的 95c970e41c764f729df4ec100a20f100b4236bb2。\n"
        u"验证：_zf54_verify.py 57 项全 OK；反证（把前后摆反）只有 8 条语义断言挂、包围盒 20 条全过。\n"
        u"\n" + u"\n".join(rows) + u"\n")
    print(u"\n归档目录: %s" % NEW)
    print(u"文件数 = %d   失败项 = %d" % (len(rows), len(fails)))
    for f in fails:
        print(u"  !! " + f)
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())
