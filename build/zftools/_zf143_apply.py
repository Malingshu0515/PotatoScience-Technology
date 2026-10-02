# -*- coding: utf-8 -*-
"""_zf143_apply.py —— ZF143：四种锭（银 / 镍 / 铝 / 钴）换上用户给的新图

用户原话：「把四种锭的图优化一下 我放用户素材里了」

素材（都在 `build/用户素材/`，各约 3 KB，2026-09-26 23:37 放的）：

| 素材 | 落点 | sha1(前12) |
|---|---|---|
| `银锭.png` | `textures/item/silver_ingot.png` | `d117b9fdc72a` |
| `镍锭.png` | `textures/item/nickel_ingot.png` | `d34b5bca78b8` |
| `铝锭.png` | `textures/item/aluminum_ingot.png` | `bb47d148f325` |
| `钴锭.png` | `textures/item/cobalt_ingot.png` | `3104 → 0581cfa56669` |

**凭什么"优化"就是这个**（不是猜）：
  · 四张全是 **16×16 / 8 位 RGBA / 零半透明**，且**四张形状完全相同**
    （不透明都恰好 135 像素）⇒ 是一套同模的四种金属锭；
  · 要被换掉的四张现有图是 **160×160 的程序生成占位色块**（8~10 色），
    游戏按 16×16 渲染 ⇒ 在包里几乎是一坨白/灰，**分不出金属**（对照图 `_zf143_preview.png` 左列）；
  · 文件名与物品一一对应（银/镍/铝/钴锭），**模型本来就指向自己** ⇒ 换图即可，**一个模型都不用改**。
"""
import hashlib
import io
import json
import os
import shutil
import sys

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
sys.path.insert(0, r"E:\PotatoST\build\zftools")
from PngRecolor import read_png  # noqa: E402

ROOT = r"E:\PotatoST"
U = os.path.join(ROOT, "build", u"用户素材")
T = os.path.join(ROOT, r"src\main\resources\assets\potato_s_t\textures\item")
MODELI = os.path.join(ROOT, r"src\main\resources\assets\potato_s_t\models\item")
PROV = os.path.join(U, u"_来源凭据.json")
PRE = os.path.join(ROOT, r"build\zftools\zf143_pre")

# (素材名, 物品id, 期望新图 sha1 前12)
JOBS = [(u"银锭.png", "silver_ingot", "d117b9fdc72a"),
        (u"镍锭.png", "nickel_ingot", "d34b5bca78b8"),
        (u"铝锭.png", "aluminum_ingot", "bb47d148f325"),
        (u"钴锭.png", "cobalt_ingot", "0581cfa56669")]

fails = []


def sha1(p):
    return hashlib.sha1(open(p, "rb").read()).hexdigest()


def main():
    os.makedirs(PRE, exist_ok=True)
    print(u"① 素材体检")
    raws = {}
    for src, item, want in JOBS:
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
              and semi == 0 and got[:12] == want)
        print(u"  %s %-16s %d B  %dx%d 位深%d 类型%d 不透明 %d 半透明 %d  sha1 %s"
              % (u"[OK]" if ok else u"[!!]", src, len(blob), w, h, blob[24], blob[25],
                 op, semi, got[:12]))
        if not ok:
            fails.append(u"%s 体检不过（期望 sha1 %s）" % (src, want))
        raws[item] = blob
    if fails:
        print(u"\n体检未过，停手：")
        for f in fails:
            print(u"  !! " + f)
        return 1

    print(u"\n② 备份被顶掉的四张（现有 160×160 占位）")
    for _, item, _ in JOBS:
        dst = os.path.join(T, item + ".png")
        if not os.path.exists(dst):
            fails.append(u"缺在用 %s.png" % item)
            print(u"  !! 缺在用 %s.png" % item)
            continue
        shutil.copyfile(dst, os.path.join(PRE, item + ".png"))
        h1 = sha1(dst)
        h2 = sha1(os.path.join(PRE, item + ".png"))
        w0, h0, _ = read_png(dst)
        print(u"  %s %-16s %dx%d  sha1 %s  -> zf143_pre/ 校验 %s"
              % (u"[OK]" if h1 == h2 else u"[!!]", item, w0, h0, h1[:12],
                 u"一致" if h1 == h2 else u"不一致"))
        if h1 != h2:
            fails.append(u"%s 备份校验失败" % item)
    if fails:
        return 1

    print(u"\n③ 原字节上线 + 留档（ASCII 名）")
    for _, item, _ in JOBS:
        raw = raws[item]
        dst = os.path.join(T, item + ".png")
        io.open(dst, "wb").write(raw)
        if open(dst, "rb").read() != raw:
            fails.append(u"%s.png 写出后逐字节不一致" % item)
            print(u"  !! %s.png 写出不一致" % item)
            continue
        # 留档：ASCII 名，与其余素材一致（原件留在原处，用户要求"原件一律保留"）
        io.open(os.path.join(U, item + ".png"), "wb").write(raw)
        print(u"  [OK] textures/item/%-18s sha1 %s  （留档 build/用户素材/%s.png）"
              % (item + ".png", sha1(dst)[:12], item))

    print(u"\n④ 模型指向（应本来就指向自己）")
    for _, item, _ in JOBS:
        mp = os.path.join(MODELI, item + ".json")
        if not os.path.exists(mp):
            fails.append(u"缺模型 %s.json" % item)
            print(u"  !! 缺模型 %s.json" % item)
            continue
        l0 = json.loads(io.open(mp, encoding="utf-8").read()).get("textures", {}).get("layer0")
        ok = l0 == u"potato_s_t:item/" + item
        print(u"  %s %-16s layer0 = %s" % (u"[OK]" if ok else u"[!!]", item, l0))
        if not ok:
            fails.append(u"%s 的 layer0 不是自己（%s）" % (item, l0))

    print(u"\n⑤ 凭据登记")
    prov = json.loads(io.open(PROV, encoding="utf-8").read())
    for src, item, _ in JOBS:
        raw = raws[item]
        key = item + ".png"
        note = (u"用户 ZF143 给的四种锭新贴图（素材原名 `%s`，16x16 / 8位 RGBA / 零半透明）"
                u"⇒ 原字节复制上线，顶掉原来那张 **160x160 的程序生成占位色块**"
                u"（占位在游戏里几乎是一坨白/灰、分不出金属，见 `_zf143_preview.png` 左列）。"
                u"模型本来就指向自己，一个都没改。" % src)
        if key in prov:
            prov[key][u"原名"] = src
            prov[key]["sha1"] = hashlib.sha1(raw).hexdigest()
            prov[key]["bytes"] = len(raw)
            prov[key][u"说明"] = note
        else:
            prov[key] = {u"原名": src, "sha1": hashlib.sha1(raw).hexdigest(),
                         "bytes": len(raw), u"说明": note}
        print(u"  [OK] %s" % key)
    io.open(PROV, "w", encoding="utf-8", newline="\n").write(
        json.dumps(prov, indent=2, ensure_ascii=False) + "\n")
    back = json.loads(io.open(PROV, encoding="utf-8").read())
    print(u"  凭据条目 %d 条" % len(back))

    print(u"\n失败项 = %d" % len(fails))
    for f in fails:
        print(u"  !! " + f)
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())
