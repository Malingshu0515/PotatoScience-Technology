# -*- coding: utf-8 -*-
"""_zf70_publish.py —— ZF70 出成品（三个进度/成就）

⚠ 沿用 ZF63 的教训：**先查完、全过才拷**。
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
RES = r"E:\PotatoST\src\main\resources"
VOID = "7db21ffdf659f11922af7a10d2818fe6b3d987a7"      # ZF69 那一版，本轮作废

ADV = ["new_beginning", "stronger_power", "clean_energy"]
LANG_KEYS = ["advancements.potato_s_t.%s.%s" % (a, k) for a in ADV for k in ("title", "description")]

fails = []


def sha1(path):
    h = hashlib.sha1()
    with io.open(path, "rb") as fh:
        h.update(fh.read())
    return h.hexdigest()


def main():
    global fails
    if not os.path.isfile(SRC):
        print(u"源 jar 不存在: %s" % SRC)
        return 1

    old = sha1(DST) if os.path.isfile(DST) else u"(无)"
    print(u"旧 release jar    : %s  (%d B)" % (old, os.path.getsize(DST) if os.path.isfile(DST) else 0))
    print(u"应当作废的旧 SHA1 : %s" % VOID)
    if old != VOID:
        fails.append(u"release 里的旧 jar 不是 ZF69 那一版（%s）" % old)

    with zipfile.ZipFile(SRC) as z:
        names = z.namelist()

        for a in ADV:
            rel = "data/potato_s_t/advancement/%s.json" % a
            if rel not in names:
                fails.append(u"新 jar 里缺 %s" % rel)
                continue
            want = io.open(os.path.join(RES, "data", "potato_s_t", "advancement", a + ".json"), "rb").read()
            got = z.read(rel)
            ok = got == want
            print(u"  [%s] %-52s %d B" % (u"OK" if ok else u"FAIL", rel, len(got)))
            if not ok:
                fails.append(u"%s 与源文件不一致" % rel)

        # 「和」必须是两组（§4.42）—— 出成品前再钉一次
        d = json.loads(z.read("data/potato_s_t/advancement/stronger_power.json").decode("utf-8"))
        req = d.get("requirements")
        ok = req == [["generator"], ["power_capturer"]]
        print(u"  [%s] stronger_power 的 requirements = %s（『和』= 两组）" % (u"OK" if ok else u"FAIL", req))
        if not ok:
            fails.append(u"stronger_power 的 requirements 不是两组（『和』会退化成『或』）")

        # 四语言 6 键都在（少了游戏里显示原始 key）
        for l in ("zh_cn", "en_us", "ja_jp", "ru_ru"):
            rel = "assets/potato_s_t/lang/%s.json" % l
            if rel not in names:
                fails.append(u"缺 %s" % rel)
                continue
            lang = json.loads(z.read(rel).decode("utf-8"))
            missing = [k for k in LANG_KEYS if k not in lang]
            ok = not missing
            print(u"  [%s] %s：6 个进度键齐全（%d 键）%s" % (u"OK" if ok else u"FAIL", l, len(lang),
                                                       u"" if ok else u" 缺 " + str(missing)))
            if not ok:
                fails.append(u"%s 缺进度键 %s" % (l, missing))

        checks = [n for n in names if "Check" in n]
        if checks:
            fails.append(u"新 jar 里混进了探针类: %s" % checks)
        if [n for n in names if n.startswith("mezz/")]:
            fails.append(u"新 jar 里混进了 JEI 的东西（红线）")

        # 前几轮的产物回归
        for rel in ("data/potato_s_t/recipe/heat_sink.json",
                    "assets/potato_s_t/textures/item/photovoltaic_component.png",
                    "data/minecraft/tags/item/swords.json",
                    "data/minecraft/tags/item/pickaxes.json",
                    "com/potatost/mod/ModTiers.class",
                    "assets/potato_s_t/models/block/alloy_smelter_north.obj",
                    "assets/potato_s_t/models/block/alloy_smelter.mtl",
                    "assets/potato_s_t/sounds/alloy_smelter_running.ogg"):
            if rel not in names:
                fails.append(u"缺少前几轮的产物: %s" % rel)
        print(u"  [OK]   前几轮产物 8 项都在")

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
