# -*- coding: utf-8 -*-
"""_zf64_publish.py —— ZF64 出成品（JEI 说明行删除 / 进度箭头 / 合金炉循环电机声）

⚠ ZF63 的教训：那个脚本**先拷文件再报错**，于是"改好脚本重跑"时旧 jar 已经被自己覆盖，
    虚报了一条"旧 jar 不是上一版"。这一版改成 **先查完、全过才拷**。
"""
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
OGG_SRC = r"E:\PotatoST\src\main\resources\assets\potato_s_t\sounds\alloy_smelter_running.ogg"
VOID = "b2e60d50df5f4f87e1ab367360c3ed249d17cb9c"      # ZF63 那一版，本轮作废

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
    print(u"旧 release jar    : %s  (%d B)" % (old, os.path.getsize(DST) if os.path.isfile(DST) else 0))
    print(u"应当作废的旧 SHA1 : %s" % VOID)
    if old != VOID:
        fails.append(u"release 里的旧 jar 不是 ZF63 那一版（%s）" % old)

    with zipfile.ZipFile(SRC) as z:
        names = z.namelist()
        bad = [n for n in names if "Check" in n]
        if bad:
            fails.append(u"新 jar 里混进了探针类: %s" % bad[:5])
        if [n for n in names if n.startswith("mezz/")]:
            fails.append(u"新 jar 里混进了 JEI 的东西（红线）")

        want = [
            u"assets/potato_s_t/sounds/alloy_smelter_running.ogg",
            u"com/potatost/mod/client/gui/parts/ProgressArrowPart.class",
            u"com/potatost/mod/client/gui/parts/ProgressArrowPart$Direction.class",
        ]
        for w in want:
            if w not in names:
                fails.append(u"新 jar 里缺: %s" % w)

        if u"assets/potato_s_t/sounds/alloy_smelter_running.ogg" in names:
            a = hashlib.sha1(z.read(u"assets/potato_s_t/sounds/alloy_smelter_running.ogg")).hexdigest()
            b = sha1(OGG_SRC)
            if a != b:
                fails.append(u"jar 里的 ogg 与源码树那一份不一致（%s vs %s）" % (a[:12], b[:12]))
            else:
                print(u"jar 里的 ogg      : %s  (%d B)" % (a[:12], len(z.read(u"assets/potato_s_t/sounds/alloy_smelter_running.ogg"))))

        sounds = json.loads(z.read(u"assets/potato_s_t/sounds.json").decode("utf-8"))
        if u"alloy_smelter_running" not in sounds:
            fails.append(u"sounds.json 里没有 alloy_smelter_running")

        lang = json.loads(z.read(u"assets/potato_s_t/lang/zh_cn.json").decode("utf-8"))
        if u"gui.potato_s_t.jei.tag_inputs" in lang:
            fails.append(u"lang 里那条被删掉的 tag_inputs 又回来了")
        if len(lang) != 202:
            fails.append(u"zh_cn 键数应为 202，实为 %d" % len(lang))
        print(u"zh_cn 键数        : %d（删掉 tag_inputs 后应为 202）" % len(lang))

    if fails:
        print(u"\n**有失败项，未拷任何文件**：")
        for f in fails:
            print(u"  !! " + f)
        return 1

    shutil.copy2(SRC, DST)
    new = sha1(DST)
    io.open(SHA, "w", encoding="ascii", newline="\n").write(new + "\n")
    print(u"新 release jar    : %s  (%d B, %d 条目)" % (new, os.path.getsize(DST), len(names)))
    print(u"sha1 文件         : %s" % io.open(SHA, encoding="ascii").read().strip())
    print(u"作废              : %s" % VOID)
    print(u"失败项 = 0")
    return 0


if __name__ == "__main__":
    sys.exit(main())
