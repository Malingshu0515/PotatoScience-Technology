# -*- coding: utf-8 -*-
"""_zf69_archive.py —— ZF69 归档（散热装置配方）"""
import hashlib
import io
import os
import shutil
import sys

PROJ = r"E:\PotatoST"
ROOT = r"C:\Users\Administrator\Desktop\PotatoST救援_20260917_183054\zf69_pre"
NEW = os.path.join(ROOT, u"新增文件")

FILES = [
    # 本轮唯一的新资源
    u"src\\main\\resources\\data\\potato_s_t\\recipe\\heat_sink.json",
    # 本轮顺手带上的：用户自己放进来的新贴图（160x160 占位 → 16x16 手绘）
    u"src\\main\\resources\\assets\\potato_s_t\\textures\\item\\photovoltaic_component.png",
    # 改了的那一份工具（配方表的唯一来源）
    u"build\\zftools\\_zf45_recipes.py",
    # 本轮新增的工具
    u"build\\zftools\\_zf69_backup.py",
    u"build\\zftools\\_zf69_repro.py",
    u"build\\zftools\\_zf69_verify.py",
    u"build\\zftools\\_zf69_texcount.py",
    u"build\\zftools\\_zf69_preview.py",
    u"build\\zftools\\_zf69_docs.py",
    u"build\\zftools\\_zf69_publish.py",
    u"build\\zftools\\_zf69_archive.py",
    u"build\\zftools\\_zf69_gates.ps1",
    u"build\\zftools\\check\\HeatSinkRecipeCheck.java",
    # 取证日志（UTF-8 版）
    u"build\\zftools\\_zf69_recipes_dry_utf8.txt",
    u"build\\zftools\\_zf69_recipes_write_utf8.txt",
    u"build\\zftools\\_zf69_repro_utf8.txt",
    u"build\\zftools\\_zf69_probe_utf8.txt",
    u"build\\zftools\\_zf69_falsify_utf8.txt",
    u"build\\zftools\\_zf69_verify2_utf8.txt",
    u"build\\zftools\\_zf69_texcount_utf8.txt",
    u"build\\zftools\\_zf69_build_utf8.txt",
    u"build\\zftools\\_zf69_docs_utf8.txt",
    u"build\\zftools\\_zf69_gates_utf8.txt",
    u"build\\zftools\\_zf69_publish_utf8.txt",
    u"build\\zftools\\_zf69_preview_utf8.txt",
    # 预览图
    u"build\\zftools\\zf69_recipe_preview.png",
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
        rows.append(u"%-72s %10d  %s" % (rel, os.path.getsize(dst), a))
        print(u"  [OK] %s" % rel)

    manifest = os.path.join(NEW, u"MANIFEST.txt")
    io.open(manifest, "w", encoding="utf-8", newline="\n").write(
        u"ZF69 归档清单\n"
        u"主题：给散热装置加配方 —— 加热装置围一圈青金石（用户原话）。\n"
        u"改法：走配方生成器表 build\\zftools\\_zf45_recipes.py（表里现在 16 条）重跑，不手写 JSON。\n"
        u"新配方：heat_sink.json = LLL / LHL / LLL（L=青金石、H=加热装置）⇒ 1 个 potato_s_t:heat_sink。\n"
        u"验证：探针 HeatSinkRecipeCheck 28 项全 OK（反证：key 两物品对调 ⇒ 10 项 FAIL）；\n"
        u"      _zf69_repro.py 证明另外 33 份配方 JSON 与改前备份逐份 SHA1 相同（33/33）；\n"
        u"      _zf69_verify.py 34 项全 OK（含档案不许再说散热装置没配方）；七项门 + 往轮校验全绿。\n"
        u"顺手带上：用户 17:15 自己放进 textures\\item 的 photovoltaic_component.png（真 PNG 16x16），\n"
        u"          旧的 160x160 占位色块被替换掉（160x160 老占位 23 → 22 张）。\n"
        u"改前件（37 个：生成器表 + 档案 + recipe\\ 下 33 份 JSON + 旧成品 jar 与 .sha1）在 ..\\ 下。\n"
        u"成品：release\\PotatoST-0.10.jar = 7db21ffdf659f11922af7a10d2818fe6b3d987a7（2,214,926 B / 704 条目）；\n"
        u"      本轮作废 ZF68 的 8c4547e467b295049682a7fd84d4ae026dd0a2c9。\n"
        u"\n" + u"\n".join(rows) + u"\n")
    print(u"\n归档目录: %s" % NEW)
    print(u"文件数 = %d   失败项 = %d" % (len(rows), len(fails)))
    for f in fails:
        print(u"  !! " + f)
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())
