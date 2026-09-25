# -*- coding: utf-8 -*-
"""_zf62_publish.py —— ZF62 出成品：build/libs 的新 jar → release\\PotatoST-0.10.jar + .sha1"""
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
VOID = "2eda896626b635a306985071be7928e84ed2f421"      # ZF60 那一版，本轮作废

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
        fails.append(u"release 里的旧 jar 不是 ZF60 那一版（%s）" % old)

    with zipfile.ZipFile(SRC) as z:
        names = z.namelist()
        bad = [n for n in names if "Check" in n]
        if bad:
            fails.append(u"新 jar 里混进了探针类: %s" % bad[:5])
        need = ["assets/potato_s_t/models/item/light_titanium_alloy.json",
                "data/c/tags/item/ingots/titanium_alloy.json",
                "data/c/tags/item/titanium_alloy_ingots.json"]
        for n in need:
            if n not in names:
                fails.append(u"jar 里缺 %s" % n)
        model = json.loads(z.read("assets/potato_s_t/models/item/light_titanium_alloy.json")
                           .decode("utf-8"))
        if "titanium_ingot" not in json.dumps(model, ensure_ascii=False):
            fails.append(u"轻质钛合金的模型没指向钛锭贴图")
        ingots = json.loads(z.read("data/c/tags/item/ingots.json").decode("utf-8"))
        if "potato_s_t:light_titanium_alloy" not in ingots["values"]:
            fails.append(u"c:ingots 汇总里没有轻质钛合金")
        lang = json.loads(z.read("assets/potato_s_t/lang/zh_cn.json").decode("utf-8"))
        if lang.get("item.potato_s_t.light_titanium_alloy") != u"轻质钛合金":
            fails.append(u"lang 里缺轻质钛合金的名字")
        if "gui.potato_s_t.jei.tag_inputs" not in lang:
            fails.append(u"lang 里缺 JEI 那条说明行")

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
