# -*- coding: utf-8 -*-
u"""_zf73_archive.py —— ZF73 归档（0.11 石油线第一批），逐份核 SHA1 + 写 MANIFEST"""
import hashlib
import io
import os
import shutil
import sys

PROJ = r"E:\PotatoST"
ROOT = r"C:\PotatoST救援\zf73_pre"
NEW = os.path.join(ROOT, u"新增文件")

FILES = [
    # 文档（改了的三份）
    u"docs\\UpdateAnnouncement_EN.md",
    u"docs\\开发档案.md",
    u"docs\\贴图清单.md",
    u"gradle.properties",
    # 成品（新版本；0.10 原样保留在 release\\ 里）
    u"release\\PotatoST-0.11.jar",
    u"release\\PotatoST-0.11.jar.sha1",
    # 新增的 java
    u"src\\main\\java\\com\\potatost\\mod\\FluidContainerItem.java",
    u"src\\main\\java\\com\\potatost\\mod\\OilBucketContents.java",
    u"src\\main\\java\\com\\potatost\\mod\\OilBucketItem.java",
    # 改过的 java
    u"src\\main\\java\\com\\potatost\\mod\\ModFluids.java",
    u"src\\main\\java\\com\\potatost\\mod\\ModBlocks.java",
    u"src\\main\\java\\com\\potatost\\mod\\ModItems.java",
    u"src\\main\\java\\com\\potatost\\mod\\TankContents.java",
    u"src\\main\\java\\com\\potatost\\mod\\HighPressureTankItem.java",
    u"src\\main\\java\\com\\potatost\\mod\\FillingMachineBlockEntity.java",
    u"src\\main\\java\\com\\potatost\\mod\\FillingMachineMenu.java",
    # 资源
    u"src\\main\\resources\\assets\\potato_s_t\\models\\item\\oil_bucket.json",
    u"src\\main\\resources\\assets\\potato_s_t\\blockstates\\crude_oil.json",
    u"src\\main\\resources\\assets\\potato_s_t\\models\\block\\crude_oil.json",
    u"src\\main\\resources\\assets\\potato_s_t\\textures\\block\\crude_oil_still.png",
    u"src\\main\\resources\\assets\\potato_s_t\\textures\\block\\crude_oil_flow.png",
    u"src\\main\\resources\\assets\\potato_s_t\\lang\\zh_cn.json",
    u"src\\main\\resources\\assets\\potato_s_t\\lang\\en_us.json",
    u"src\\main\\resources\\assets\\potato_s_t\\lang\\ja_jp.json",
    u"src\\main\\resources\\assets\\potato_s_t\\lang\\ru_ru.json",
    u"src\\main\\resources\\data\\potato_s_t\\recipe\\oil_bucket.json",
    # 工具
    u"build\\zftools\\_zf73_backup.py",
    u"build\\zftools\\_zf73_api_probe.py",
    u"build\\zftools\\_zf73_api_probe2.py",
    u"build\\zftools\\_zf73_api_probe3.py",
    u"build\\zftools\\_zf73_lang.py",
    u"build\\zftools\\_zf73_repro.py",
    u"build\\zftools\\_zf73_verify.py",
    u"build\\zftools\\_zf73_docs.py",
    u"build\\zftools\\_zf73_falsify.py",
    u"build\\zftools\\_zf73_publish.py",
    u"build\\zftools\\_zf73_announce.py",
    u"build\\zftools\\_zf73_verifypatch.py",
    u"build\\zftools\\_zf73_gatefix.py",
    u"build\\zftools\\_zf73_gatefix2.py",
    u"build\\zftools\\_zf73_archive.py",
    u"build\\zftools\\_zf73_gates.ps1",
    u"build\\zftools\\check\\OilCheck.java",
    u"build\\zftools\\_zf45_recipes.py",
    u"build\\zftools\\_zf69_repro.py",
    u"build\\zftools\\_zf69_verify.py",
    u"build\\zftools\\_zf71_verify.py",
    u"build\\zftools\\_zf34_archive.py",
    # 日志
    u"build\\zftools\\_zf73_build1_utf8.txt",
    u"build\\zftools\\_zf73_build2_utf8.txt",
    u"build\\zftools\\_zf73_probe_utf8.txt",
    u"build\\zftools\\_zf73_verify_utf8.txt",
    u"build\\zftools\\_zf73_falsify_utf8.txt",
    u"build\\zftools\\_zf73_publish_utf8.txt",
    u"build\\zftools\\_zf73_gates_utf8.txt",
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
        rows.append(u"%-64s %10d  %s" % (rel, os.path.getsize(dst), a))
        print(u"  [OK] %s" % rel)

    io.open(os.path.join(NEW, u"MANIFEST.txt"), "w", encoding="utf-8", newline=u"\n").write(
        u"ZF73 归档清单（0.11 石油线第一批：原油 + 油桶 + 两刀白名单 + 灌装机接口化）\n"
        u"成品：release\\PotatoST-0.11.jar = 2a35a9eeda99b125e59637ceb6bf74be33bd1d16（2,225,933 B / 718 条目）\n"
        u"      release\\PotatoST-0.10.jar = 84d09345f6095408ae462dabb536307141904ea3 **原样保留、不作废**\n"
        u"      （0.10 → 0.11 是版本升级，不是同版本重打包；mod_version 已由 0.10 提到 0.11）\n"
        u"★ 用户给的原油贴图（16x16 JPEG、近黑 rgb16~21、sha256 d8b4c276…）已转成真 PNG：\n"
        u"  textures\\block\\crude_oil_still.png 与 crude_oil_flow.png（像素逐点不变，仅换容器格式）\n"
        u"★ 探针 OilCheck **105 项全 [OK]**：流体参数（tickDelay 30 / slope 2 / drop 2、不无限、原版桶舀不走）、\n"
        u"  液体方块与 fluid 互指、正向白名单 11 条、油桶 3000/单流体/拒气体/白条、气罐拒原油但气体仍可混装、\n"
        u"  世界舀取 14 条（含异种拒收且源方块还在、装满后不吞方块）、灌装机 17 条（tryFillSlot 真灌 + 扣 60 FE\n"
        u"  + 界面 id = 注册 id 11）、配方照用户原话硬摆能合成 1 个 + 两条负向对照、四语言键可解析\n"
        u"★ 反证 4 刀：① 源码 isGas 挖掉一个气体（A14 挂，实测 5≠6）② 配方 count 1→2（B10 挂）\n"
        u"  ③ 贴图换成假 PNG（B1 挂）④ 语言删键（B12 挂）；每刀逐字节还原、复跑全绿。\n"
        u"  ⚠ 第 1 刀**第一次没被抓住** —— A14 原来是子串断言（OXYGEN.get() 在别处也出现），\n"
        u"    改成「抽出方法体数 6 个比较 + 不许出现 !=」之后才挂：反证的价值就在这儿。\n"
        u"★ 门：九道门 + 往轮校验**全绿**（Audit 0/7 提示、ToolLint 240 脚本 0 语法 0 流程/27 历史提示、\n"
        u"  LangCheck 0、RecipeCheck 0、ModelCheck 0/1、TextureCheck 0/23 警告/9 待画、JsonCheck 340 JSON 0、\n"
        u"  SoundCheck 0，各 verify：ZF69 34 / ZF70 87 / ZF71 83 / ZF72 57 / ZF73 58 全 0 失败）。\n"
        u"  两处**响亮的 SKIP**（不是静默跳过）：① `_zf69_repro.py` 的备份根被删进回收站 ⇒ 该项本轮没校验；\n"
        u"  ② `_zf72_verify.py` 的 7 条「当时源码状态」快照断言在 v0.11 起改为 SKIP。\n"
        u"★ 顺手修掉的三处**假绿**：`_zf69_repro.py` 找不到备份目录时曾经 exit 0；`_zf69_verify.py` 的配方/JSON\n"
        u"  计数写死成等号（改成下界）与 jar 路径写死成 0.10（改成跟着 mod_version 走）；`_zf34_archive.py` 一个\n"
        u"  非法转义让 ToolLint 记「语法失败 1」。\n"
        u"★ 公告 `docs\\UpdateAnnouncement_EN.md` 已升到 **0.11**（新增「Crude oil and the Oil Bucket」一节 +\n"
        u"  known gaps 两条：油田世界生成未做、油桶不能倒出）——`_zf71_verify.py` 是活体核对，公告跟不上就会自己挂。\n"
        u"\n" + u"\n".join(rows) + u"\n")
    print(u"\n归档目录: %s" % NEW)
    print(u"文件数 = %d   失败项 = %d" % (len(rows), len(fails)))
    for f in fails:
        print(u"  !! " + f)
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())
