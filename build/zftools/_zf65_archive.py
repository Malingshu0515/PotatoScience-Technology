# -*- coding: utf-8 -*-
"""_zf65_archive.py —— ZF65 归档（循环音停不下来的 bug 修复）"""
import hashlib
import io
import os
import shutil
import sys

PROJ = r"E:\PotatoST"
ROOT = r"C:\Users\Administrator\Desktop\PotatoST救援_20260917_183054\zf65_pre"
NEW = os.path.join(ROOT, u"新增文件")

FILES = [
    # 探针（已从 src 删除，这里是唯一留存）
    u"build\\zftools\\check\\AlloySoundStopCheck.java",
    # 本轮的工具与日志
    u"build\\zftools\\_zf65_backup.py",
    u"build\\zftools\\_zf65_precheck.py",
    u"build\\zftools\\_zf65_precheck.log",
    u"build\\zftools\\_zf65_verify.py",
    u"build\\zftools\\_zf65_gates.ps1",
    u"build\\zftools\\_zf65_publish.py",
    u"build\\zftools\\_zf65_docs.py",
    u"build\\zftools\\_zf65_archive.py",
    u"build\\zftools\\_zf65_probe_utf8.txt",
    u"build\\zftools\\zf65_falsify_utf8.txt",
    u"build\\zftools\\zf65_falsify2.log",
    u"build\\zftools\\_zf65_gates_utf8.txt",
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
        u"ZF65 归档清单\n"
        u"主题：修用户实测报的 bug ——「冶炼中的合金炉被破坏还是会循环播放音效 重新创建刷新一下才好」。\n"
        u"根因：running 标记的清零只写在 craftTick() 里，而拆解（挖部件格/接线口/扳手）走\n"
        u"      disassemble() → setFormed(false)，控制器方块还在、craftTick() 再也不被调用 ⇒ 标记卡在 true。\n"
        u"修法：serverTickBody() 开头无条件清零（放在 if (this.formed) 之外）；公共件 MachineRunningSound 加两条防呆。\n"
        u"⚠ 本轮**忘了在动手前抄改前件**：zf65_pre 里那 3 份是事后反向套用编辑重建的，\n"
        u"   并用 _zf65_precheck.py「换回源码树编译 → 与 ZF64 成品 jar 的 class 逐字节比对」证明忠实（3/3 相同）。\n"
        u"成品：release\\PotatoST-0.10.jar = c71dfa484fa83f08e19c10cb3d1d100a72c6bd41（2,191,444 B / 692 条目）；\n"
        u"      本轮作废 ZF64 的 c305c922c307253c2432623c8a8bc6f8d6233cfe。\n"
        u"\n" + u"\n".join(rows) + u"\n")
    print(u"\n归档目录: %s" % NEW)
    print(u"文件数 = %d   失败项 = %d" % (len(rows), len(fails)))
    for f in fails:
        print(u"  !! " + f)
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())
