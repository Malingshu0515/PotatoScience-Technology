# -*- coding: utf-8 -*-
u"""_zf78_publish.py —— ZF78 出成品：`build\\libs\\potato_s_t-0.11.jar` → `release\\PotatoST-0.11.jar` + `.sha1`

⚠ ZF63 的教训（§5 那行）：**发布脚本里的 VOID 必须每次跟着改**，而且要
"先核对旧哈希、再动文件" —— ZF63 那次就是脚本先拷文件后报错，导致"旧 jar"已经不是它以为的那一版。
所以这里第 ①步先断言 `release\\PotatoST-0.11.jar` 的 SHA1 **正好等于**本轮要作废的那个值，
对不上就**直接退出、一个字节都不动**。
"""
import hashlib
import io
import os
import shutil
import sys
import zipfile

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

ROOT = r"E:\PotatoST"
SRC = os.path.join(ROOT, "build", "libs", "potato_s_t-0.11.jar")
DST = os.path.join(ROOT, "release", "PotatoST-0.11.jar")
SHA = DST + ".sha1"
# 本轮要作废的上一版（ZF78 第一次打包：沥青贴图还是 4 位的，重编码后重打一次）
VOID = "330ea020cf42637ea8d3cbffedbfa6788677e59c"


fails = []


def sha1(path):
    return hashlib.sha1(open(path, "rb").read()).hexdigest()


def main():
    if not os.path.exists(SRC):
        fails.append(u"找不到构建产物：%s" % SRC)
    if not os.path.exists(DST):
        fails.append(u"找不到当前成品：%s" % DST)
    old = sha1(DST) if os.path.exists(DST) else u"(缺)"
    print(u"① 当前成品 SHA1 = %s" % old)
    if old != VOID:
        fails.append(u"与预期要作废的 %s 不一致" % VOID)
    else:
        print(u"   与预期一致 ⇒ 本轮作废它")

    new = sha1(SRC) if os.path.exists(SRC) else u"(缺)"
    size = os.path.getsize(SRC)
    with zipfile.ZipFile(SRC) as zf:
        entries = len(zf.namelist())
        checks = [n for n in zf.namelist() if os.path.basename(n).startswith("Distillation")]
        bad = [n for n in zf.namelist() if "Check" in os.path.basename(n) and n.endswith(".class")]
    print(u"② 新产物 SHA1 = %s（%d B / %d 条目）" % (new, size, entries))
    print(u"   分馏塔相关条目 %d 个；探针 class %d 个（必须是 0）" % (len(checks), len(bad)))
    if bad:
        fails.append(u"成品里带探针：%s" % bad)
    if new == old:
        fails.append(u"新旧哈希相同 ⇒ 源码没变？先确认再发")

    if fails:
        print(u"  [FAIL] 以上 %d 条没过 ⇒ **一个字节都不动**" % len(fails))
        for f in fails:
            print(u"    !! " + f)
        return 1
    shutil.copy2(SRC, DST)
    io.open(SHA, "w", encoding="ascii", newline=u"\n").write(new + u"\n")
    print(u"③ 已发布：release\\PotatoST-0.11.jar")
    print(u"   上一版 %s… **作废**（同版本重打包）" % VOID[:8])
    print(u"   .sha1 文件已写：%s" % new)
    return 0


if __name__ == "__main__":
    sys.exit(main())
