# -*- coding: utf-8 -*-
"""_zf58_publish.py —— ZF58 出成品：build/libs 的新 jar → release\\PotatoST-0.10.jar + .sha1"""
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
VOID = "812f214209a7fdda838ac1568805117093410286"      # ZF57 那一版，本轮作废

fails = []


def sha1(path):
    h = hashlib.sha1()
    with io.open(path, "rb") as fh:
        h.update(fh.read())
    return h.hexdigest()


def obj_box(text):
    vs = [tuple(float(x) for x in m) for m in re.findall(r"^v (\S+) (\S+) (\S+)$", text, re.M)]
    xs = [v[0] for v in vs]
    zs = [v[2] for v in vs]
    return min(xs), max(xs), min(zs), max(zs)


def main():
    if not os.path.isfile(SRC):
        return u"源 jar 不存在: %s" % SRC
    old = sha1(DST) if os.path.isfile(DST) else u"(无)"
    print(u"旧 release jar : %s  (%d B)" % (old, os.path.getsize(DST) if os.path.isfile(DST) else 0))
    print(u"应当作废的旧 SHA1 : %s" % VOID)
    if old != VOID:
        fails.append(u"release 里的旧 jar 不是 ZF57 那一版（%s）" % old)

    with zipfile.ZipFile(SRC) as z:
        names = z.namelist()
        bad = [n for n in names if "Check" in n]
        if bad:
            fails.append(u"新 jar 里混进了探针类: %s" % bad[:5])
        # 模型必须罩在机器那一侧（南向 X[0,4]）——旧件是 X[-3,1]
        box = obj_box(z.read("assets/potato_s_t/models/block/alloy_smelter_south.obj").decode("utf-8"))
        print(u"jar 里 south.obj 的包围盒: X%s Z%s" % ((box[0], box[1]), (box[2], box[3])))
        if (box[0], box[1]) != (0.0, 4.0):
            fails.append(u"south.obj 的 X 范围不是 (0,4) —— 模型没跟着主控翻边")
        # 部件格要有名字（Jade 不该显示 id）
        lang = json.loads(z.read("assets/potato_s_t/lang/zh_cn.json").decode("utf-8"))
        if "block.potato_s_t.alloy_smelter_part" not in lang:
            fails.append(u"jar 里部件格还是没有 lang 条目")

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
