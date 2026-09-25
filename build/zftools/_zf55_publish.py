# -*- coding: utf-8 -*-
"""_zf55_publish.py —— ZF55 出成品：build/libs 的新 jar → release\\PotatoST-0.10.jar + .sha1

规矩（§11 / §13）：产物只放 release\\，不往 PCL2 实例里塞；每次重发都要**作废上一版 SHA1**。
"""
import hashlib
import io
import os
import shutil
import sys
import zipfile

SRC = r"E:\PotatoST\build\libs\potato_s_t-0.10.jar"
DST = r"E:\PotatoST\release\PotatoST-0.10.jar"
SHA = DST + ".sha1"
VOID = "1438234abc71620738c5f094f75d232390d27b62"      # ZF54 那一版，本轮作废

fails = []


def sha1(path):
    h = hashlib.sha1()
    with io.open(path, "rb") as fh:
        h.update(fh.read())
    return h.hexdigest()


def main():
    if not os.path.isfile(SRC):
        return u"源 jar 不存在: %s" % SRC

    old = sha1(DST) if os.path.isfile(DST) else u"(无)"
    print(u"旧 release jar : %s  (%d B)" % (old, os.path.getsize(DST) if os.path.isfile(DST) else 0))
    print(u"应当作废的旧 SHA1 : %s" % VOID)
    if old != VOID:
        fails.append(u"release 里的旧 jar 不是 ZF54 那一版（%s），先确认是不是漏发了" % old)

    with zipfile.ZipFile(SRC) as z:
        names = z.namelist()
    bad = [n for n in names if "Check" in n or "AlloyShellCheck" in n]
    if bad:
        fails.append(u"新 jar 里混进了探针/检查类: %s" % bad[:5])
    need = ["models/block/alloy_smelter_south.obj", "models/block/alloy_smelter.mtl",
            "blockstates/alloy_smelter_part.json", "blockstates/alloy_smelter_port.json"]
    for suffix in need:
        if not any(n.endswith(suffix) for n in names):
            fails.append(u"新 jar 里缺 %s" % suffix)

    shutil.copy2(SRC, DST)
    new = sha1(DST)
    io.open(SHA, "w", encoding="ascii", newline="\n").write(new + "\n")

    print(u"新 release jar : %s  (%d B, %d 条目)" % (new, os.path.getsize(DST), len(names)))
    print(u"sha1 文件      : %s" % io.open(SHA, encoding="ascii").read().strip())
    print(u"作废           : %s" % VOID)
    print(u"失败项 = %d" % len(fails))
    for f in fails:
        print(u"  !! " + f)
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())
