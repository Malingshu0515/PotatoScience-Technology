# -*- coding: utf-8 -*-
"""_zf67_archive.py —— ZF67 归档（工具挂原版"能附魔"标签）"""
import hashlib
import io
import os
import shutil
import sys

PROJ = r"E:\PotatoST"
ROOT = r"C:\Users\Administrator\Desktop\PotatoST救援_20260917_183054\zf67_pre"
NEW = os.path.join(ROOT, u"新增文件")

FILES = [
    # 本轮新增的两个标签文件（这就是全部改动）
    u"src\\main\\resources\\data\\minecraft\\tags\\item\\swords.json",
    u"src\\main\\resources\\data\\minecraft\\tags\\item\\pickaxes.json",
    # 探针（已从 src 删除）
    u"build\\zftools\\check\\AlloyEnchantCheck.java",
    # 工具与日志
    u"build\\zftools\\_zf67_verify.py",
    u"build\\zftools\\_zf67_gates.ps1",
    u"build\\zftools\\_zf67_publish.py",
    u"build\\zftools\\_zf67_docs.py",
    u"build\\zftools\\_zf67_archive.py",
    u"build\\zftools\\_zf67_probe_utf8.txt",
    u"build\\zftools\\zf67_falsify_utf8.txt",
    u"build\\zftools\\zf67_falsify2.log",
    u"build\\zftools\\_zf67_gates_utf8.txt",
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
        u"ZF67 归档清单\n"
        u"主题：修「附魔台不给钛合金工具附魔」。\n"
        u"根因：附魔台挑附魔的判据是 stack.isPrimaryItemFor(附魔)，看的是原版物品标签\n"
        u"      #minecraft:swords / #minecraft:pickaxes（再串 enchantable/*）；ZF66 两把工具一个都没挂，\n"
        u"      于是附魔能力 25、花费 30 级都正常，候选却是 0 条。\n"
        u"改动：**只新增两个标签 JSON**（replace:false，各只加自己那一条），既有文件一字未动。\n"
        u"      所以不需要调小附魔能力（它只决定花费，不决定能不能附）。\n"
        u"成品：release\\PotatoST-0.10.jar = 95c970e41c764f729df4ec100a20f100b4236bb2（2,202,439 B / 703 条目）；\n"
        u"      本轮作废 ZF66 的 9239a74de93cb35785059f26d384b6966ff5420d。\n"
        u"验证：探针 AlloyEnchantCheck 43 项全 OK（含原版钻石剑/镐对照，候选数完全同数 8 / 4）；\n"
        u"      反证：移走 swords.json ⇒ 探针 17 FAIL 且候选 0（复现用户现象）；replace 改 true ⇒ 复核 1 FAIL。\n"
        u"\n" + u"\n".join(rows) + u"\n")
    print(u"\n归档目录: %s" % NEW)
    print(u"文件数 = %d   失败项 = %d" % (len(rows), len(fails)))
    for f in fails:
        print(u"  !! " + f)
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())
