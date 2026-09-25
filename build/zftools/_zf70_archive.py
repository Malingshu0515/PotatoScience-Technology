# -*- coding: utf-8 -*-
"""_zf70_archive.py —— ZF70 归档（三个进度/成就）"""
import hashlib
import io
import os
import shutil
import sys

PROJ = r"E:\PotatoST"
ROOT = r"C:\Users\Administrator\Desktop\PotatoST救援_20260917_183054\zf70_pre"
NEW = os.path.join(ROOT, u"新增文件")

FILES = [
    # 本轮新资源：三份进度 JSON
    u"src\\main\\resources\\data\\potato_s_t\\advancement\\new_beginning.json",
    u"src\\main\\resources\\data\\potato_s_t\\advancement\\stronger_power.json",
    u"src\\main\\resources\\data\\potato_s_t\\advancement\\clean_energy.json",
    # 改了的那 4 个语言文件
    u"src\\main\\resources\\assets\\potato_s_t\\lang\\zh_cn.json",
    u"src\\main\\resources\\assets\\potato_s_t\\lang\\en_us.json",
    u"src\\main\\resources\\assets\\potato_s_t\\lang\\ja_jp.json",
    u"src\\main\\resources\\assets\\potato_s_t\\lang\\ru_ru.json",
    # 本轮新增/使用的工具
    u"build\\zftools\\_zf70_backup.py",
    u"build\\zftools\\_zf70_lang.py",
    u"build\\zftools\\_zf70_verify.py",
    u"build\\zftools\\_zf70_falsify.py",
    u"build\\zftools\\_zf70_docs.py",
    u"build\\zftools\\_zf70_docs2.py",
    u"build\\zftools\\_zf70_publish.py",
    u"build\\zftools\\_zf70_archive.py",
    u"build\\zftools\\_zf70_gate_summary.py",
    u"build\\zftools\\_zf70_gates.ps1",
    u"build\\zftools\\check\\AdvancementCheck.java",
    # 第 9 道门（本轮新立）
    u"build\\zftools\\ToolLint.py",
    # 取证日志（UTF-8 版）
    u"build\\zftools\\_zf70_probe_or_bug_utf8.txt",
    u"build\\zftools\\_zf70_probe2_utf8.txt",
    u"build\\zftools\\_zf70_falsify_utf8.txt",
    u"build\\zftools\\_zf70_verify2_utf8.txt",
    u"build\\zftools\\_zf70_lang_utf8.txt",
    u"build\\zftools\\_zf70_build_utf8.txt",
    u"build\\zftools\\_zf70_docs_utf8.txt",
    u"build\\zftools\\_zf70_docs2_utf8.txt",
    u"build\\zftools\\_zf70_toollint_utf8.txt",
    u"build\\zftools\\_zf70_gates_utf8.txt",
    u"build\\zftools\\_zf70_publish_utf8.txt",
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
        rows.append(u"%-74s %10d  %s" % (rel, os.path.getsize(dst), a))
        print(u"  [OK] %s" % rel)

    manifest = os.path.join(NEW, u"MANIFEST.txt")
    io.open(manifest, "w", encoding="utf-8", newline="\n").write(
        u"ZF70 归档清单\n"
        u"主题：三个进度（成就）—— 新的开始！/ 更强劲的电源 / 入门清洁能源（用户口述）。\n"
        u"文件：data\\potato_s_t\\advancement\\{new_beginning,stronger_power,clean_energy}.json（本目录本轮新建）。\n"
        u"三条都是普通成就（frame=task）、有提示与聊天播报、不隐藏；根=新的开始！，另两条的前置都是它。\n"
        u"★ 本轮最值钱的一条：JSON 的 requirements 是『外层 AND / 内层 OR』，\n"
        u"  用户的『和』必须写成 [[generator], [power_capturer]]；第一版写成 [[generator, power_capturer]]（= 或），\n"
        u"  探针第一次真触发就抓出来了（日志 _zf70_probe_or_bug_utf8.txt：2 项 FAIL）。见档案 §4.42。\n"
        u"★ 另一条：无头服务端里的假玩家必须挂一个没连上的 Connection，否则完成「带配方奖励」的进度会 NPE。见 §4.43。\n"
        u"验证：探针 AdvancementCheck 47 项全 OK（含真触发与负向对照）；_zf70_verify.py 87 项全 OK；\n"
        u"      反证：requirements 退回 OR 写法 ⇒ 3 条 FAIL；七项门 + 往轮校验全绿（JsonCheck 340 个 JSON 非法 0、\n"
        u"      LangCheck 四语言各 210 键、服务端 Loaded 1402 advancements = 原版 1399 + 3）。\n"
        u"改前件（7 个：4 个 lang + 档案 + 旧成品 jar 与 .sha1）在 ..\\ 下。\n"
        u"成品：release\\PotatoST-0.10.jar = 84d09345f6095408ae462dabb536307141904ea3（2,217,321 B / 708 条目）；\n"
        u"      本轮作废 ZF69 的 7db21ffdf659f11922af7a10d2818fe6b3d987a7。\n"
        u"\n" + u"\n".join(rows) + u"\n")
    print(u"\n归档目录: %s" % NEW)
    print(u"文件数 = %d   失败项 = %d" % (len(rows), len(fails)))
    for f in fails:
        print(u"  !! " + f)
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())
