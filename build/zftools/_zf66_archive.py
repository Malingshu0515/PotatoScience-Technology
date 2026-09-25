# -*- coding: utf-8 -*-
"""_zf66_archive.py —— ZF66 归档（钛合金剑 / 钛合金镐）"""
import hashlib
import io
import os
import shutil
import sys

PROJ = r"E:\PotatoST"
ROOT = r"C:\Users\Administrator\Desktop\PotatoST救援_20260917_183054\zf66_pre"
NEW = os.path.join(ROOT, u"新增文件")

FILES = [
    # 本轮新建的源码 / 资源
    u"src\\main\\java\\com\\potatost\\mod\\ModTiers.java",
    u"src\\main\\resources\\assets\\potato_s_t\\models\\item\\titanium_alloy_sword.json",
    u"src\\main\\resources\\assets\\potato_s_t\\models\\item\\titanium_alloy_pickaxe.json",
    u"src\\main\\resources\\data\\potato_s_t\\recipe\\titanium_alloy_sword.json",
    u"src\\main\\resources\\data\\potato_s_t\\recipe\\titanium_alloy_pickaxe.json",
    u"src\\main\\resources\\assets\\potato_s_t\\textures\\item\\titanium_alloy_sword.png",
    u"src\\main\\resources\\assets\\potato_s_t\\textures\\item\\titanium_alloy_pickaxe.png",
    # 探针（已从 src 删除）
    u"build\\zftools\\check\\AlloyToolCheck.java",
    # 工具与日志
    u"build\\zftools\\_zf66_backup.py",
    u"build\\zftools\\_zf66_png.py",
    u"build\\zftools\\_zf66_rename.py",
    u"build\\zftools\\_zf66_lang.py",
    u"build\\zftools\\_zf66_verify.py",
    u"build\\zftools\\_zf66_gates.ps1",
    u"build\\zftools\\_zf66_publish.py",
    u"build\\zftools\\_zf66_docs.py",
    u"build\\zftools\\_zf66_archive.py",
    u"build\\zftools\\_zf66_probe_utf8.txt",
    u"build\\zftools\\zf66_falsify_utf8.txt",
    u"build\\zftools\\zf66_falsify2.log",
    u"build\\zftools\\_zf66_recipecheck_utf8.txt",
    u"build\\zftools\\_zf66_gates_utf8.txt",
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
        u"ZF66 归档清单\n"
        u"主题：钛合金剑（耐久 2048 / 显示伤害 6.5）+ 钛合金镐（耐久 4219 / 显示伤害 4 / 挖掘等级下界合金）。\n"
        u"      贴图是用户放进 textures/item 的两张真 PNG（16x16 RGBA），按 §4.24 改名成 ASCII，改名前后 SHA1 一致。\n"
        u"      附魔权重 25（金 22）、挖掘速度 9.0（下界合金同款）、修理材料 = 轻质钛合金；两条配方照原版形状。\n"
        u"附带修掉一个闸门 bug：RecipeCheck 的 -All 开关用 @('-All') 传字符串绑不到 [switch]，\n"
        u"      ZF62~ZF65 那几轮它其实**一个配方都没检查**却打印『全部通过』；改成哈希表 splat 后补跑：27 条定形配方全过。\n"
        u"成品：release\\PotatoST-0.10.jar = 9239a74de93cb35785059f26d384b6966ff5420d（2,201,859 B / 700 条目）；\n"
        u"      本轮作废 ZF65 的 c71dfa484fa83f08e19c10cb3d1d100a72c6bd41。\n"
        u"改前件（7 个）在 ..\\src\\ 下，与源码树逐份核过哈希。\n"
        u"\n" + u"\n".join(rows) + u"\n")
    print(u"\n归档目录: %s" % NEW)
    print(u"文件数 = %d   失败项 = %d" % (len(rows), len(fails)))
    for f in fails:
        print(u"  !! " + f)
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())
