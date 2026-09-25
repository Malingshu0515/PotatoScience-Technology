# -*- coding: utf-8 -*-
"""_zf71_archive.py —— ZF71 归档（英文公告；**本轮不动 jar**）"""
import hashlib
import io
import os
import shutil
import sys

PROJ = r"E:\PotatoST"
ROOT = r"C:\Users\Administrator\Desktop\PotatoST救援_20260917_183054\zf71_pre"
NEW = os.path.join(ROOT, u"新增文件")

FILES = [
    # 本轮唯一的交付物：英文公告
    u"docs\\UpdateAnnouncement_EN.md",
    # 改了的档案
    u"docs\\开发档案.md",
    # 本轮新增的工具
    u"build\\zftools\\_zf71_overview_dump.py",
    u"build\\zftools\\_zf71_javadoc_dump.py",
    u"build\\zftools\\_zf71_verify.py",
    u"build\\zftools\\_zf71_falsify.py",
    u"build\\zftools\\_zf71_backup.py",
    u"build\\zftools\\_zf71_docs.py",
    u"build\\zftools\\_zf71_archive.py",
    u"build\\zftools\\_zf71_gates.ps1",
    # 取证日志（UTF-8 版）
    u"build\\zftools\\_zf71_overview_dump_utf8.txt",
    u"build\\zftools\\_zf71_javadoc_dump_utf8.txt",
    u"build\\zftools\\_zf71_backup_utf8.txt",
    u"build\\zftools\\_zf71_verify_utf8.txt",
    u"build\\zftools\\_zf71_falsify2_utf8.txt",
    u"build\\zftools\\_zf71_docs_utf8.txt",
    u"build\\zftools\\_zf71_gates_utf8.txt",
    # 成品（本轮没动，一起留档以证明"没动"）
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
        rows.append(u"%-60s %10d  %s" % (rel, os.path.getsize(dst), a))
        print(u"  [OK] %s" % rel)

    manifest = os.path.join(NEW, u"MANIFEST.txt")
    io.open(manifest, "w", encoding="utf-8", newline="\n").write(
        u"ZF71 归档清单（文档轮：不动 jar）\n"
        u"主题：给玩家一份英文公告 —— docs\\UpdateAnnouncement_EN.md（可整段贴 Discord/Modrinth）。\n"
        u"内容不是凭记忆写的：先跑 _zf71_overview_dump.py 把「这个 mod 现在有什么」从项目里挖出来，\n"
        u"机器数值从 java 常量抓、英文名从 en_us.json 抓；再由 _zf71_verify.py（83 项）逐条事实核对。\n"
        u"★ 核对抓到我自己数错：公告第一版写「8 个深层变体」，实际是 7（把拼错名的孤儿贴图\n"
        u"  textures\\block\\deepslate_aluminiu_ore.png 当成了第 8 个）。\n"
        u"★ 反证：改两个数字（液压机 24,000→34,000、高炉 10 s→12 s）⇒ 校验 2 项 FAIL；\n"
        u"  其中高炉那条**第一次没抓到**（只查了常量、没查公告正文），补断言后再反证才挂。\n"
        u"★ 顺手核出 5 个真问题（都写进档案 §9，等用户拍板，本轮一行没改）：\n"
        u"  ① 微型粉碎机 tooltip 缺「粗钛→钛粉」那条配方（四语言都没有；JEI 里有），且铜线那行少个「·」；\n"
        u"  ② 合金炉主控 alloy_smelter 与三元聚合物锂电池 lithium_battery **根本没有配方**（生存做不出来），\n"
        u"     加上 advanced/stable_metal_block 共 4 个方块只能创造取；\n"
        u"  ③ 锂电池英文名 Ternary polymer lithium battery 与其它方块命名风格不一致；\n"
        u"  ④ aluminium（tooltip）vs Aluminum Ingot（物品名）拼法不统一；\n"
        u"  ⑤ 孤儿贴图 deepslate_aluminiu_ore.png（拼错名、无引用）—— 铝其实没有深层变体。\n"
        u"门：九道门 + 往轮校验全绿（ToolLint 213 个脚本 0 语法错、JsonCheck 340 个 JSON 0 非法、\n"
        u"    LangCheck 四语言各 210 键、ZF71 verify 83 项 0 失败）。\n"
        u"改前件（1 个：docs\\开发档案.md）在 ..\\ 下。\n"
        u"成品：release\\PotatoST-0.10.jar **仍是 ZF70 的**\n"
        u"      84d09345f6095408ae462dabb536307141904ea3（2,217,321 B / 708 条目）—— 本轮不动 jar，**不作废**。\n"
        u"\n" + u"\n".join(rows) + u"\n")
    print(u"\n归档目录: %s" % NEW)
    print(u"文件数 = %d   失败项 = %d" % (len(rows), len(fails)))
    for f in fails:
        print(u"  !! " + f)
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())
