# -*- coding: utf-8 -*-
"""_zf150_apply.py —— ZF150：四种「粒」（铝/银/钴/镍）注册落地

用户原话（0.12）：「嗯嗯放素材了几张图 其中四种粒你先注册一下 配方就是原版的
（对应锭合成9个粒 9个粒合成1个锭 记得加标签兼容别的mod）重复一遍！现在是0.12版本」

本脚本负责**资源侧**（Java 注册与配方由别处负责）：
  ① 四张素材 → `textures/item/<材料>_nugget.png`（原字节复制）+ ASCII 留档
  ② 四个 `models/item/<材料>_nugget.json`（parent `minecraft:item/generated`）
  ③ 凭据登记

素材实测（`_zf150_look.txt`）：四张都是 16×16 / 8 位 RGBA / **零半透明**，
且**形状完全相同**（不透明都恰好 34 像素）、共用同一套描边色
（`#585f68` 深描边 + `#393c40` 阴影），只有高光色按金属变 ⇒ 一整套粒。
"""
import hashlib
import io
import json
import os
import sys

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
sys.path.insert(0, r"E:\PotatoST\build\zftools")
from PngRecolor import read_png  # noqa: E402

ROOT = r"E:\PotatoST"
U = os.path.join(ROOT, "build", u"用户素材")
A = os.path.join(ROOT, r"src\main\resources\assets\potato_s_t")
TEXI = os.path.join(A, "textures", "item")
MODELI = os.path.join(A, "models", "item")
PROV = os.path.join(U, u"_来源凭据.json")

# (素材名, 材料, 期望 sha1 前 12)
JOBS = [(u"铝粒_001.png", "aluminum", "1ab2ccd1c126"),
        (u"银粒_001.png", "silver", "bb2661ab051a"),
        (u"钴粒_001.png", "cobalt", "6e37a26b80aa"),
        (u"镍粒_001.png", "nickel", "6dff9b39cba1")]

fails = []


def sha1(p):
    return hashlib.sha1(open(p, "rb").read()).hexdigest()


def main():
    print(u"① 素材体检 + 原字节上线")
    raws = {}
    for src, mat, want in JOBS:
        p = os.path.join(U, src)
        if not os.path.exists(p):
            fails.append(u"找不到 %s" % src)
            print(u"  !! 找不到 %s" % src)
            continue
        blob = open(p, "rb").read()
        got = hashlib.sha1(blob).hexdigest()
        w, h, rgba = read_png(p)
        op = sum(1 for i in range(w * h) if rgba[i * 4 + 3] == 255)
        semi = sum(1 for i in range(w * h) if 0 < rgba[i * 4 + 3] < 255)
        ok = (blob[:8] == b"\x89PNG\r\n\x1a\n" and (w, h, blob[24], blob[25]) == (16, 16, 8, 6)
              and semi == 0 and op > 0 and got[:12] == want)
        print(u"  %s %-16s %d B  %dx%d 位深%d 类型%d 不透明 %d 半透明 %d  sha1 %s"
              % (u"[OK]" if ok else u"[!!]", src, len(blob), w, h, blob[24], blob[25],
                 op, semi, got[:12]))
        if not ok:
            fails.append(u"%s 体检不过" % src)
        raws[mat] = blob
    if fails:
        for f in fails:
            print(u"  !! " + f)
        return 1

    for src, mat, _ in JOBS:
        raw = raws[mat]
        dst = os.path.join(TEXI, mat + "_nugget.png")
        io.open(dst, "wb").write(raw)
        if open(dst, "rb").read() != raw:
            fails.append(u"%s_nugget.png 写出不一致" % mat)
            print(u"  !! %s_nugget.png 写出不一致" % mat)
            continue
        io.open(os.path.join(U, mat + "_nugget.png"), "wb").write(raw)   # ASCII 留档
        print(u"  [OK] textures/item/%-22s sha1 %s" % (mat + "_nugget.png", sha1(dst)[:12]))

    print(u"\n② 物品模型（照抄同类物品的写法）")
    # 样板：同目录已有的 *_ingot.json，确认形状后再写
    sample = os.path.join(MODELI, "silver_ingot.json")
    sample_txt = io.open(sample, encoding="utf-8").read()
    print(u"  样板 silver_ingot.json：%s" % sample_txt.replace(u"\n", u" "))
    for src, mat, _ in JOBS:
        mp = os.path.join(MODELI, mat + "_nugget.json")
        obj = {"parent": "minecraft:item/generated",
               "textures": {"layer0": "potato_s_t:item/%s_nugget" % mat}}
        io.open(mp, "w", encoding="utf-8", newline="\n").write(
            json.dumps(obj, indent=2, ensure_ascii=False) + "\n")
        back = json.loads(io.open(mp, encoding="utf-8").read())
        ok = back["textures"]["layer0"] == "potato_s_t:item/%s_nugget" % mat
        print(u"  %s models/item/%-22s layer0=%s"
              % (u"[OK]" if ok else u"[!!]", mat + "_nugget.json", back["textures"]["layer0"]))
        if not ok:
            fails.append(u"%s_nugget.json 写出不对" % mat)

    print(u"\n③ 凭据登记")
    prov = json.loads(io.open(PROV, encoding="utf-8").read())
    for src, mat, _ in JOBS:
        raw = raws[mat]
        key = mat + "_nugget.png"
        prov[key] = {
            u"原名": src,
            "sha1": hashlib.sha1(raw).hexdigest(),
            "bytes": len(raw),
            u"说明": (u"用户 ZF150（0.12）给的四种粒之一（素材原名 `%s`）⇒ 原字节复制成 "
                      u"textures/item/%s_nugget.png。四张形状完全相同（不透明都 34 像素）、"
                      u"共用同一套描边色，只有高光色按金属变 ⇒ 一整套同模粒。" % (src, mat)),
        }
    io.open(PROV, "w", encoding="utf-8", newline="\n").write(
        json.dumps(prov, indent=2, ensure_ascii=False) + "\n")
    print(u"  [OK] 凭据条目 %d 条" % len(prov))

    print(u"\n失败项 = %d" % len(fails))
    for f in fails:
        print(u"  !! " + f)
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())
