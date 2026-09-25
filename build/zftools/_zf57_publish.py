# -*- coding: utf-8 -*-
"""_zf57_publish.py —— ZF57 出成品：build/libs 的新 jar → release\\PotatoST-0.10.jar + .sha1"""
import hashlib
import io
import json
import os
import shutil
import sys
import zipfile

SRC = r"E:\PotatoST\build\libs\potato_s_t-0.10.jar"
DST = r"E:\PotatoST\release\PotatoST-0.10.jar"
SHA = DST + ".sha1"
VOID = "b0c86fcd0b103e32d9024f0dd8a38a1c2a76aaf0"      # ZF56 那一版，本轮作废

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
        fails.append(u"release 里的旧 jar 不是 ZF56 那一版（%s）" % old)

    with zipfile.ZipFile(SRC) as z:
        names = z.namelist()
        bad = [n for n in names if "Check" in n]
        if bad:
            fails.append(u"新 jar 里混进了探针类: %s" % bad[:5])
        bs = json.loads(z.read("assets/potato_s_t/blockstates/alloy_smelter.json").decode("utf-8"))
        if bs["variants"].get("formed=false", {}).get("model") != "potato_s_t:block/alloy_smelter":
            fails.append(u"jar 里 blockstate 的 formed=false 不对")
        for facing in ("north", "east", "south", "west"):
            if ("facing=%s,formed=true" % facing) not in bs["variants"]:
                fails.append(u"jar 里缺 facing=%s,formed=true" % facing)
        tip = json.loads(z.read("assets/potato_s_t/lang/zh_cn.json").decode("utf-8"))
        value = tip["tooltip.potato_s_t.alloy_smelter"]
        if u"7 合金炉主控" not in value or u"2222|5115" not in value:
            fails.append(u"jar 里的中文介绍不是 ZF57 那版图纸")

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
