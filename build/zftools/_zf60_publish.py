# -*- coding: utf-8 -*-
"""_zf60_publish.py —— ZF60 出成品：build/libs 的新 jar → release\\PotatoST-0.10.jar + .sha1"""
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
VOID = "10016a2391325d25240ec87c47d867e8dd5006a1"      # ZF59 那一版，本轮作废

TEX = ["assets/potato_s_t/textures/item/magnet.png",
       "assets/potato_s_t/textures/item/iron_powder.png",
       "assets/potato_s_t/textures/item/raw_titanium.png",
       "assets/potato_s_t/textures/item/titanium_powder.png",
       "assets/potato_s_t/textures/item/titanium_ingot.png",
       "assets/potato_s_t/textures/block/titanium_ore.png",
       "assets/potato_s_t/textures/block/deepslate_titanium_ore.png"]

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
        fails.append(u"release 里的旧 jar 不是 ZF59 那一版（%s）" % old)

    with zipfile.ZipFile(SRC) as z:
        names = z.namelist()
        bad = [n for n in names if "Check" in n]
        if bad:
            fails.append(u"新 jar 里混进了探针类: %s" % bad[:5])
        for tex in TEX:
            if tex not in names:
                fails.append(u"jar 里缺 %s" % tex)
        legacy = json.loads(z.read("assets/potato_s_t/models/item/titanium_ingot.json").decode("utf-8"))
        if "iron_ingot" in json.dumps(legacy, ensure_ascii=False):
            fails.append(u"jar 里的钛锭模型还是原版铁锭贴图")
        ore = json.loads(z.read("assets/potato_s_t/models/block/titanium_ore.json").decode("utf-8"))
        if "potato_s_t:block/titanium_ore" not in json.dumps(ore, ensure_ascii=False):
            fails.append(u"jar 里的钛矿模型没指向自己的贴图")

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
