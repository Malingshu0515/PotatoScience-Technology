# -*- coding: utf-8 -*-
"""_zf69_publish.py —— ZF69 出成品（散热装置配方：加热装置围一圈青金石）

⚠ 沿用 ZF63 的教训：**先查完、全过才拷**。
"""
import hashlib
import io
import json
import os
import re
import shutil
import struct
import sys
import zipfile

SRC = r"E:\PotatoST\build\libs\potato_s_t-0.10.jar"
DST = r"E:\PotatoST\release\PotatoST-0.10.jar"
SHA = DST + ".sha1"
RECIPE = r"E:\PotatoST\src\main\resources\data\potato_s_t\recipe\heat_sink.json"
PHOTO = r"E:\PotatoST\src\main\resources\assets\potato_s_t\textures\item\photovoltaic_component.png"
VOID = "8c4547e467b295049682a7fd84d4ae026dd0a2c9"      # ZF68 那一版，本轮作废

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
        fails.append(u"release 里的旧 jar 不是 ZF68 那一版（%s）" % old)

    want = io.open(RECIPE, "rb").read()
    with zipfile.ZipFile(SRC) as z:
        names = z.namelist()
        rel = "data/potato_s_t/recipe/heat_sink.json"
        if rel not in names:
            fails.append(u"新 jar 里缺 %s" % rel)
        else:
            got = z.read(rel)
            ok = got == want
            print(u"  [%s] %s 与源文件逐字节一致（%d B）" % (u"OK" if ok else u"FAIL", rel, len(got)))
            if not ok:
                fails.append(u"%s 内容与源文件不一致" % rel)

        d = json.loads(want.decode("utf-8"))
        cells = [d["pattern"][r][c] for r in range(3) for c in range(3)]
        k = d["key"]
        ok = (cells[4] == "H" and k["H"]["item"] == "potato_s_t:heater"
              and all(cells[i] == "L" for i in range(9) if i != 4)
              and k["L"]["item"] == "minecraft:lapis_lazuli"
              and d["result"]["id"] == "potato_s_t:heat_sink" and d["result"]["count"] == 1)
        print(u"  [%s] 配方 = 外圈青金石 + 中心加热装置 ⇒ 1 个散热装置" % (u"OK" if ok else u"FAIL"))
        if not ok:
            fails.append(u"配方内容不是用户说的那张图")

        checks = [n for n in names if "Check" in n]
        if checks:
            fails.append(u"新 jar 里混进了探针类: %s" % checks)
        if [n for n in names if n.startswith("mezz/")]:
            fails.append(u"新 jar 里混进了 JEI 的东西（红线）")

        crafting = 0
        for n in names:
            if re.match(r"data/potato_s_t/recipe/.*\.json$", n):
                try:
                    dd = json.loads(z.read(n).decode("utf-8"))
                except Exception:
                    continue
                if dd.get("type") == "minecraft:crafting_shaped":
                    crafting += 1
        ok = crafting == 28
        print(u"  [%s] jar 里定形配方 = %d 条（期望 28）" % (u"OK" if ok else u"FAIL", crafting))
        if not ok:
            fails.append(u"jar 里定形配方 %d 条，应为 28" % crafting)

        # 本轮用户自己放的新贴图（顺手带上）
        rel = "assets/potato_s_t/textures/item/photovoltaic_component.png"
        if rel not in names:
            fails.append(u"新 jar 里缺 %s" % rel)
        else:
            got = z.read(rel)
            ok = got == io.open(PHOTO, "rb").read()
            w, h = struct.unpack(">II", got[16:24])
            real = got[:8] == b"\x89PNG\r\n\x1a\n"
            print(u"  [%s] %s = %dx%d，真 PNG=%s（源文件 %d B）" % (u"OK" if (ok and real and (w, h) == (16, 16)) else u"FAIL",
                                                                   os.path.basename(rel), w, h, real, len(got)))
            if not (ok and real and (w, h) == (16, 16)):
                fails.append(u"光伏原件贴图不对（与源文件一致=%s / 真 PNG=%s / %dx%d）" % (ok, real, w, h))

        # 前几轮的产物回归（别把旧东西弄丢）
        for rel in ("data/minecraft/tags/item/swords.json",
                    "data/minecraft/tags/item/pickaxes.json",
                    "com/potatost/mod/ModTiers.class",
                    "assets/potato_s_t/models/block/alloy_smelter_north.obj",
                    "assets/potato_s_t/models/block/alloy_smelter.mtl",
                    "assets/potato_s_t/textures/item/titanium_alloy_sword.png",
                    "assets/potato_s_t/textures/item/titanium_alloy_pickaxe.png",
                    "assets/potato_s_t/sounds/alloy_smelter_running.ogg",
                    "data/potato_s_t/recipe/heater.json"):
            if rel not in names:
                fails.append(u"缺少前几轮的产物: %s" % rel)
        print(u"  [OK]   前几轮产物 9 项都在" if not fails else u"  [--]   前几轮产物见图")

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
