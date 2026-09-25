# -*- coding: utf-8 -*-
"""_zf59_publish.py —— ZF59 出成品：build/libs 的新 jar → release\\PotatoST-0.10.jar + .sha1"""
import hashlib
import io
import json
import os
import re
import shutil
import sys
import zipfile

SRC = r"E:\PotatoST\build\libs\potato_s_t-0.10.jar"
DST = r"E:\PotatoST\release\PotatoST-0.10.jar"
SHA = DST + ".sha1"
VOID = "9c917dad8c3a76bd1df917714a0273019094fb09"      # ZF58 那一版，本轮作废

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
        fails.append(u"release 里的旧 jar 不是 ZF58 那一版（%s）" % old)

    with zipfile.ZipFile(SRC) as z:
        names = z.namelist()
        bad = [n for n in names if "Check" in n]
        if bad:
            fails.append(u"新 jar 里混进了探针类: %s" % bad[:5])
        box = [tuple(float(x) for x in m) for m in re.findall(
            r"^v (\S+) (\S+) (\S+)$",
            z.read("assets/potato_s_t/models/block/alloy_smelter_south.obj").decode("utf-8"), re.M)]
        xs = [v[0] for v in box]
        if (min(xs), max(xs)) != (0.0, 4.0):
            fails.append(u"south.obj 的 X 范围不是 (0,4)")
        lang = json.loads(z.read("assets/potato_s_t/lang/zh_cn.json").decode("utf-8"))
        if "block.potato_s_t.alloy_smelter_part" not in lang:
            fails.append(u"jar 里部件格没有 lang 条目")
        tip = lang["tooltip.potato_s_t.alloy_smelter"]
        if u"58" not in tip:
            fails.append(u"jar 里的中文介绍没写「要查 58 格」")

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
