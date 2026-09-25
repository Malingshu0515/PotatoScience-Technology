# -*- coding: utf-8 -*-
u"""_zf74_archive.py —— ZF74 归档（流体挂 c: 通用标签），逐份核 SHA1 + MANIFEST"""
import hashlib
import io
import os
import shutil
import sys

PROJ = r"E:\PotatoST"
ROOT = r"C:\PotatoST救援\zf74_pre"
NEW = os.path.join(ROOT, u"新增文件")

FILES = [
    u"src\\main\\java\\com\\potatost\\mod\\ModFluids.java",
    u"src\\main\\resources\\data\\c\\tags\\fluid\\gaseous.json",
    u"src\\main\\resources\\data\\c\\tags\\fluid\\crude_oil.json",
    u"src\\main\\resources\\data\\c\\tags\\fluid\\oxygen.json",
    u"src\\main\\resources\\data\\c\\tags\\fluid\\hydrogen.json",
    u"src\\main\\resources\\data\\c\\tags\\fluid\\chlorine.json",
    u"docs\\开发档案.md",
    u"docs\\v0.11规划.md",
    u"docs\\UpdateAnnouncement_EN.md",
    u"release\\PotatoST-0.11.jar",
    u"release\\PotatoST-0.11.jar.sha1",
    u"build\\zftools\\Audit.ps1",
    u"build\\zftools\\_zf72_verify.py",
    u"build\\zftools\\_zf74_tagprobe.py",
    u"build\\zftools\\_zf74_backup.py",
    u"build\\zftools\\_zf74_docs.py",
    u"build\\zftools\\_zf74_docs2.py",
    u"build\\zftools\\_zf74_docs3.py",
    u"build\\zftools\\_zf74_verify.py",
    u"build\\zftools\\_zf74_falsify.py",
    u"build\\zftools\\_zf74_fix2.py",
    u"build\\zftools\\_zf74_auditfix.py",
    u"build\\zftools\\_zf74_mkgates.py",
    u"build\\zftools\\_zf74_gates.ps1",
    u"build\\zftools\\_zf74_archive.py",
    u"build\\zftools\\_zf74_build_utf8.txt",
    u"build\\zftools\\_zf74_publish_utf8.txt",
    u"build\\zftools\\_zf74_verify_utf8.txt",
    u"build\\zftools\\_zf74_falsify_utf8.txt",
    u"build\\zftools\\_zf74_gates_utf8.txt",
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
        rows.append(u"%-62s %10d  %s" % (rel, os.path.getsize(dst), a))
        print(u"  [OK] %s" % rel)

    io.open(os.path.join(NEW, u"MANIFEST.txt"), "w", encoding="utf-8", newline=u"\n").write(
        u"ZF74 归档清单（流体挂 c: 通用标签 + 判定也认标签）\n"
        u"用户问题：「以前的流体（氧气 氯气 氢气）可以和别的mod配方通用吗 可以的话以后的流体也通用\n"
        u"          不行的话看看能不能加个标签」\n"
        u"★ 答案（有取证，`_zf74_tagprobe.py` 只读三路对照）：**改之前完全不通用** ——\n"
        u"  本工程 60 个标签文件里**流体标签 0 个**；上游 NeoForge 21.1.235 声明了 `Tags.Fluids.GASEOUS`\n"
        u"  （`data/c/tags/fluid/gaseous.json` 目前只挂 legacy 别名 `#forge:gaseous`，等于等各 mod 自己挂）；\n"
        u"  本机 mod 扫描抓到 机械动力·柴油动力 自带 `data/c/tags/fluid/crude_oil.json`\n"
        u"  ⇒ 原油通用名 = **`c:crude_oil`**。\n"
        u"★ 本轮挂上 5 份（全 `replace:false`，源+流动都挂，照上游 c:water 写法）：\n"
        u"  `c:gaseous`（氧/氢/氯）、`c:crude_oil`（原油）、`c:oxygen`、`c:hydrogen`、`c:chlorine`。\n"
        u"★ 判定也认标签：`ModFluids.isGas` = 自家 3 种（写死，标签没加载也认）**或** `#c:gaseous`\n"
        u"  ⇒ 别的 mod 的氧气也能灌进高压气罐、油桶也照样拒收它（双向通用，不只挂出去）。\n"
        u"★ 门也补了：`Audit.ps1` 原来只认 lang 里的 item/block 键，把流体 id 全判成「不存在」（13 条假 FAIL）；\n"
        u"  现在从 `ModFluids.java` 抄流体 id，并**新增硬检查：每种流体都必须挂进某个 c: 标签**\n"
        u"  ⇒ 用户「以后的流体也通用」这条规矩由机器守着，将来忘挂标签门会直接红。\n"
        u"★ 同版本重打包：release\\PotatoST-0.11.jar 重新发布 ⇒ **上一版 `2a35a9eeda99…` 作废**；\n"
        u"  新成品 = `39e66beb0a7ee2037c466ff343a6d4dc42484274`（2,227,272 B / 724 条目）；\n"
        u"  `PotatoST-0.10.jar`（`84d09345…`）仍然原样保留。\n"
        u"★ 反证 4 刀全中（gaseous 少挂一个氧 / crude_oil 改 replace:true / isGas 不再认标签 / 档案删作废声明）。\n"
        u"  ⚠ 第 3 刀**第一次没抓住**：B2 原来查子串 `Tags.Fluids.GASEOUS`，而那段**注释里**也有这个词\n"
        u"  —— 与 ZF73 的 A14 同属「子串断言 ≠ 代码断言」，一轮里犯两次，已改成断言真的调用。\n"
        u"★ 门：九道门 + 往轮校验全绿（Audit 0/7、ToolLint 251 脚本 0 语法 0 流程/27 历史、LangCheck 0、\n"
        u"  RecipeCheck 0、ModelCheck 0/1、TextureCheck 0/23/9、JsonCheck 0、SoundCheck 0；\n"
        u"  ZF69 34 / ZF70 87 / ZF71 83 / ZF72 57 / ZF73 58 / ZF74 29 全 0 失败），\n"
        u"  唯一 SKIP = ZF69 复现性（备份根被删进回收站，脚本响亮报 SKIP-NO-BACKUP）。\n"
        u"\n" + u"\n".join(rows) + u"\n")
    print(u"\n归档目录: %s" % NEW)
    print(u"文件数 = %d   失败项 = %d" % (len(rows), len(fails)))
    for f in fails:
        print(u"  !! " + f)
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())
