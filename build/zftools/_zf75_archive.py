# -*- coding: utf-8 -*-
u"""_zf75_archive.py —— ZF75 归档（世界生成：地表油田 + 海洋油田群系）"""
import hashlib
import io
import os
import shutil
import sys

PROJ = r"E:\PotatoST"
NEW = r"C:\PotatoST救援\zf75_pre\新增文件"

FILES = [
    u"src\\main\\java\\com\\potatost\\mod\\SaltyRiverBiomeSource.java",
    u"src\\main\\resources\\data\\potato_s_t\\worldgen\\configured_feature\\mini_oilfield.json",
    u"src\\main\\resources\\data\\potato_s_t\\worldgen\\placed_feature\\mini_oilfield_placed.json",
    u"src\\main\\resources\\data\\potato_s_t\\worldgen\\biome\\ocean_oilfield.json",
    u"src\\main\\resources\\data\\potato_s_t\\neoforge\\biome_modifier\\mini_oilfield.json",
    u"src\\main\\resources\\data\\potato_s_t\\neoforge\\biome_modifier\\mini_oilfield_desert_a.json",
    u"src\\main\\resources\\data\\potato_s_t\\neoforge\\biome_modifier\\mini_oilfield_desert_b.json",
    u"src\\main\\resources\\data\\potato_s_t\\tags\\worldgen\\biome\\oilfield_dense.json",
    u"src\\main\\resources\\data\\minecraft\\worldgen\\world_preset\\normal.json",
    u"src\\main\\resources\\data\\minecraft\\worldgen\\world_preset\\amplified.json",
    u"src\\main\\resources\\data\\minecraft\\worldgen\\world_preset\\large_biomes.json",
    u"src\\main\\resources\\data\\minecraft\\tags\\worldgen\\biome\\is_overworld.json",
    u"src\\main\\resources\\assets\\potato_s_t\\lang\\zh_cn.json",
    u"src\\main\\resources\\assets\\potato_s_t\\lang\\en_us.json",
    u"src\\main\\resources\\assets\\potato_s_t\\lang\\ja_jp.json",
    u"src\\main\\resources\\assets\\potato_s_t\\lang\\ru_ru.json",
    u"release\\PotatoST-0.11.jar",
    u"release\\PotatoST-0.11.jar.sha1",
    u"docs\\开发档案.md",
    u"docs\\v0.11规划.md",
    u"docs\\UpdateAnnouncement_EN.md",
    u"build\\zftools\\check\\OilfieldCheck2.java",
    u"build\\zftools\\_zf75_backup.py",
    u"build\\zftools\\_zf75_worldgen.py",
    u"build\\zftools\\_zf75_fixprobe.py",
    u"build\\zftools\\_zf75_fixprobe2.py",
    u"build\\zftools\\_zf75_docs.py",
    u"build\\zftools\\_zf75_verify.py",
    u"build\\zftools\\_zf75_mkgates.py",
    u"build\\zftools\\_zf75_gates.ps1",
    u"build\\zftools\\_zf75_gatefix.py",
    u"build\\zftools\\_zf75_gatefix2.py",
    u"build\\zftools\\_zf75_archive.py",
    u"build\\zftools\\_zf71_verify.py",
    u"build\\zftools\\_zf72_verify.py",
    u"build\\zftools\\_zf73_verify.py",
    u"build\\zftools\\_zf75_build_utf8.txt",
    u"build\\zftools\\_zf75_probe_utf8.txt",
    u"build\\zftools\\_zf75_publish_utf8.txt",
    u"build\\zftools\\_zf75_verify_utf8.txt",
    u"build\\zftools\\_zf75_falsify_utf8.txt",
    u"build\\zftools\\_zf75_gates_utf8.txt",
]


def sha1(path):
    h = hashlib.sha1()
    with io.open(path, "rb") as fh:
        h.update(fh.read())
    return h.hexdigest()


def main():
    fails, rows = [], []
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
        rows.append(u"%-66s %10d  %s" % (rel, os.path.getsize(dst), a))
    io.open(os.path.join(NEW, u"MANIFEST.txt"), "w", encoding="utf-8", newline=u"\n").write(
        u"ZF75 归档清单（世界生成：地表油田 mini_oilfield + 海洋油田群系 ocean_oilfield）\n"
        u"起因：用户报「locate 只能查到咸水河，生物群系/结构都找不到海底油田和微型油田」。\n"
        u"  这不是 bug —— 世界生成在 ZF73 报告里就写明留到下一轮，而那一轮被流体标签问题占了。\n"
        u"  另外要澄清：**/locate 永远找不到微型油田**，它是 feature 不是 structure。\n"
        u"成品：release\\PotatoST-0.11.jar = 4528ed53cbdef41d952e8707e05c4424bd49cc41（2,231,500 B / 731 条目）\n"
        u"      **同版本重打包 ⇒ 上一版 39e66beb… 作废**；0.10 成品 84d09345… 仍原样保留。\n"
        u"★ 内容：① 地表原油湖（minecraft:lake，石头 barrier + 原油 level 0；放置参数与原版地表岩浆湖同：\n"
        u"  rarity 200 / in_square / WORLD_SURFACE_WG / biome 过滤）；② 沙漠恶地 **3 倍**（基础注入器\n"
        u"  #minecraft:is_overworld + 两份挂自建标签 #potato_s_t:oilfield_dense）；③ 海洋油田群系（水色 4047AD）；\n"
        u"  ④ 群系源把 minecraft:stony_shore 按位置哈希低概率替换（默认 0.15）。\n"
        u"★ 旧存档兼容：oil_biome / oil_chance 是**可选字段**，老 level.dat 缺字段时用\n"
        u"  Holder.Reference#unwrapLookup() 从注册表反查默认群系 ⇒ **不用开新世界**（探针钉了断言）。\n"
        u"  ⚠ 咸水河的哈希公式一个字节没改（改了旧存档群系边界会错开），油田用另一套常数 0x5EED。\n"
        u"★ 探针抓到两个真错误：(a) neoforge:add_features 的 biomes **数组只吃群系 id、不吃 tag**；\n"
        u"  (b) **#minecraft:is_desert 在 1.21.1 根本不存在**（只有 is_badlands）—— 我 ZF72 规划里那个标签\n"
        u"  是凭空写的，靠探针一连串 FAIL 逼出来；改成自建 #potato_s_t:oilfield_dense。\n"
        u"★ 探针 OilfieldCheck **20 项全 [OK]**：群系/水色/名字/#is_overworld、注入器份数 1/3/3/1、\n"
        u"  用**合成 delegate** 做的确定性规则测试（chance=1.0 全替换 400/400、0.0 全不换、咸水河规则未受影响、\n"
        u"  旧存档兜底解析）、/place feature 真放出 **60 块原油且全是源方块**。\n"
        u"★ 测试方法教训：/place feature 第一次放不出油 —— 原版 LakeFeature 的作用区是 origin 起 +15 格、\n"
        u"  且下半个透镜必须是固体，我铺的 16×16 平台不够宽 ⇒ 特征直接 return false；平台放大到 -2..26 才成。\n"
        u"★ 门：九道门 + 往轮校验全绿（Audit 0/7、ToolLint 261 脚本 0 语法 0 流程/27 历史、LangCheck 0、\n"
        u"  RecipeCheck 0、ModelCheck 0/1、TextureCheck 0/23/9、JsonCheck 0、SoundCheck 0；\n"
        u"  ZF69 34 / ZF70 87 / ZF71 83 / ZF72 57 / ZF73 58 / ZF74 29 / ZF75 35 全 0 失败）。\n"
        u"  顺带修掉三处**老轮次的坏断言**：ZF72 的 B15（漏在快照名单外）、ZF73 的键数 218→219、\n"
        u"  以及 ZF71 里「矿石数」数的是**整个 configured_feature 目录**（加了 mini_oilfield 就误报 10 种矿）\n"
        u"  —— 改成只数 ore_*。\n"
        u"\n" + u"\n".join(rows) + u"\n")
    print(u"归档目录: %s" % NEW)
    print(u"文件数 = %d   失败项 = %d" % (len(rows), len(fails)))
    for f in fails:
        print(u"  !! " + f)
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())
