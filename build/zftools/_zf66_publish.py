# -*- coding: utf-8 -*-
"""_zf66_publish.py —— ZF66 出成品（钛合金剑 / 钛合金镐）

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
SRC_ROOT = r"E:\PotatoST\src\main\resources"
VOID = "c71dfa484fa83f08e19c10cb3d1d100a72c6bd41"      # ZF65 那一版，本轮作废

WANT_FILES = [
    "assets/potato_s_t/textures/item/titanium_alloy_sword.png",
    "assets/potato_s_t/textures/item/titanium_alloy_pickaxe.png",
    "assets/potato_s_t/models/item/titanium_alloy_sword.json",
    "assets/potato_s_t/models/item/titanium_alloy_pickaxe.json",
    "data/potato_s_t/recipe/titanium_alloy_sword.json",
    "data/potato_s_t/recipe/titanium_alloy_pickaxe.json",
    "com/potatost/mod/ModTiers.class",
]

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
        fails.append(u"release 里的旧 jar 不是 ZF65 那一版（%s）" % old)

    with zipfile.ZipFile(SRC) as z:
        names = z.namelist()
        if [n for n in names if "Check" in n]:
            fails.append(u"新 jar 里混进了探针类: %s" % [n for n in names if "Check" in n][:4])
        if [n for n in names if n.startswith("mezz/")]:
            fails.append(u"新 jar 里混进了 JEI 的东西（红线）")

        for w in WANT_FILES:
            if w not in names:
                fails.append(u"新 jar 里缺: %s" % w)
            else:
                print(u"  [OK] %s" % w)

        # 中文名的旧贴图不许跟进来
        bad = [n for n in names if n.startswith("assets/potato_s_t/textures/item/")
               and any(ord(c) > 127 for c in n)]
        if bad:
            fails.append(u"jar 里有中文文件名的贴图: %s" % bad)

        # 贴图字节与源码树一致
        for rel in WANT_FILES[:2]:
            local = os.path.join(SRC_ROOT, rel.replace("/", os.sep))
            if rel in names and os.path.isfile(local):
                a = hashlib.sha1(z.read(rel)).hexdigest()
                b = sha1(local)
                if a != b:
                    fails.append(u"%s 的字节与源码树不一致（%s vs %s）" % (rel, a[:12], b[:12]))

        # 配方在 jar 里也要能解析出正确形状
        for tool, shape in (("sword", ["X", "X", "S"]), ("pickaxe", ["XXX", " S ", " S "])):
            rel = "data/potato_s_t/recipe/titanium_alloy_%s.json" % tool
            if rel in names:
                r = json.loads(z.read(rel).decode("utf-8"))
                if r.get("pattern") != shape or r.get("result", {}).get("id") != "potato_s_t:titanium_alloy_" + tool:
                    fails.append(u"%s 的形状/产出不对: %s -> %s" % (rel, r.get("pattern"), r.get("result")))

        lang = json.loads(z.read("assets/potato_s_t/lang/zh_cn.json").decode("utf-8"))
        print(u"zh_cn 键数        : %d（应为 204）" % len(lang))
        if len(lang) != 204:
            fails.append(u"zh_cn 键数变了: %d" % len(lang))
        for k, v in (("item.potato_s_t.titanium_alloy_sword", u"钛合金剑"),
                     ("item.potato_s_t.titanium_alloy_pickaxe", u"钛合金镐")):
            if lang.get(k) != v:
                fails.append(u"lang %s = %r（应为 %s）" % (k, lang.get(k), v))

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
