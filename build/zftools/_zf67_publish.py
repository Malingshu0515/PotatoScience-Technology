# -*- coding: utf-8 -*-
"""_zf67_publish.py —— ZF67 出成品（钛合金工具挂上原版"能附魔"标签）

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
VOID = "9239a74de93cb35785059f26d384b6966ff5420d"      # ZF66 那一版，本轮作废

WANT_TAGS = {
    "data/minecraft/tags/item/swords.json": "potato_s_t:titanium_alloy_sword",
    "data/minecraft/tags/item/pickaxes.json": "potato_s_t:titanium_alloy_pickaxe",
}

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
        fails.append(u"release 里的旧 jar 不是 ZF66 那一版（%s）" % old)

    with zipfile.ZipFile(SRC) as z:
        names = z.namelist()
        if [n for n in names if "Check" in n]:
            fails.append(u"新 jar 里混进了探针类")
        if [n for n in names if n.startswith("mezz/")]:
            fails.append(u"新 jar 里混进了 JEI 的东西（红线）")

        for rel, item in WANT_TAGS.items():
            if rel not in names:
                fails.append(u"新 jar 里缺: %s" % rel)
                continue
            d = json.loads(z.read(rel).decode("utf-8"))
            ok = d.get("replace") is False and d.get("values") == [item]
            print(u"  [%s] %-42s %s" % (u"OK" if ok else u"FAIL", rel,
                                        json.dumps(d, ensure_ascii=False)))
            if not ok:
                fails.append(u"%s 内容不对（应 replace:false 且只加 %s）" % (rel, item))

        # 工具那几样还在（回归）
        for rel in ("assets/potato_s_t/textures/item/titanium_alloy_sword.png",
                    "assets/potato_s_t/models/item/titanium_alloy_pickaxe.json",
                    "data/potato_s_t/recipe/titanium_alloy_sword.json",
                    "com/potatost/mod/ModTiers.class"):
            if rel not in names:
                fails.append(u"缺少上一轮的产物: %s" % rel)

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
