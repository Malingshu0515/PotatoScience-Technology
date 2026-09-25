# -*- coding: utf-8 -*-
"""_zf64_archive.py —— ZF64 归档（JEI 说明行删除 / 进度箭头 / 合金炉循环电机声）"""
import hashlib
import io
import os
import shutil
import sys

PROJ = r"E:\PotatoST"
ROOT = r"C:\Users\Administrator\Desktop\PotatoST救援_20260917_183054\zf64_pre"
NEW = os.path.join(ROOT, u"新增文件")

FILES = [
    # 本轮**新建**的源码 / 资源
    u"src\\main\\java\\com\\potatost\\mod\\client\\gui\\parts\\ProgressArrowPart.java",
    u"src\\main\\resources\\assets\\potato_s_t\\sounds\\alloy_smelter_running.ogg",
    # 探针（已从 src 删除，这里是唯一留存）
    u"build\\zftools\\check\\AlloySoundCheck.java",
    # 本轮的工具与日志
    u"build\\zftools\\_zf64_backup.py",
    u"build\\zftools\\_zf64_ogg.py",
    u"build\\zftools\\_zf64_envelope.py",
    u"build\\zftools\\_zf64_env.py",
    u"build\\zftools\\_zf64_makesfx.log",
    u"build\\zftools\\_zf64_verify.py",
    u"build\\zftools\\_zf64_gates.ps1",
    u"build\\zftools\\_zf64_publish.py",
    u"build\\zftools\\_zf64_docs.py",
    u"build\\zftools\\_zf64_archive.py",
    u"build\\zftools\\_zf64_probe_utf8.txt",
    u"build\\zftools\\zf64_falsify1.log",
    u"build\\zftools\\zf64_falsify2.log",
    u"build\\zftools\\zf64_falsify3.log",
    u"build\\zftools\\_zf64_gates_utf8.txt",
    u"build\\zftools\\zf64_arrow_preview.png",
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
        u"ZF64 归档清单\n"
        u"主题：① 删掉 JEI 里那条标签判定说明（用户：「所有的这种文字可以删掉 给玩家看没必要列出来 还占空间 不美观」）；\n"
        u"      ② 合金炉界面加「正在熔炼」的进度箭头（同时也是进度条），朝下，22x22，中线 x=70；\n"
        u"      ③ 运行中循环电机声：用户给的 freesound #453361 素材（原为立体声）→ 单声道 44100 Hz 8.27s 循环。\n"
        u"清理：tag_inputs 键从 4 个语言文件删除（203 → 202 键）；探针 AlloySoundCheck 已从 src 删除（副本在此）。\n"
        u"成品：release\\PotatoST-0.10.jar = c305c922c307253c2432623c8a8bc6f8d6233cfe（2,191,317 B / 692 条目）；\n"
        u"      本轮作废 ZF63 的 b2e60d50df5f4f87e1ab367360c3ed249d17cb9c。\n"
        u"改前件（10 个）在 ..\\src\\ 下，与源码树逐份核过哈希。\n"
        u"\n" + u"\n".join(rows) + u"\n")
    print(u"\n归档目录: %s" % NEW)
    print(u"文件数 = %d   失败项 = %d" % (len(rows), len(fails)))
    for f in fails:
        print(u"  !! " + f)
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())
