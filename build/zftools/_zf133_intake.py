# -*- coding: utf-8 -*-
"""_zf133_intake.py —— ZF133 素材入库（星璨钢斧）

用户原话（2026-09-26）：

    加个星璨钢斧 贴图E:\\PotatoST\\build\\用户素材 1192耐久 挖掘等级钻石 1：夜晚时不消耗耐久
    手持时获得急迫1 1s 2：shift+右键 扣除120点耐久 发射一道冲击波 15s冷却（玩家朝向 宽度6格就可以）
    破坏沿途所有原木/去皮原木 和树叶 碰到斧子不可以开采的方块 或 10s内未碰到任何原木 则冲击波消失
    在末地时 冲击波将具有10+0.5n的远程伤害（n为玩家基础伤害）

本脚本只做两件事（**不动任何被测文件**）：
  ① 找到用户给的贴图、量它的真实规格（尺寸/模式/像素数，真解码 —— §4.92 那刀）；
  ② 记一笔来源凭据（sha1 + 落盘路径），写进 `build/用户素材/_来源凭据.json`。

跑法：python build/zftools/_zf133_intake.py            （只看，不写）
      python build/zftools/_zf133_intake.py --write    （写凭据）
"""
import hashlib
import io
import json
import os
import sys

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
sys.path.insert(0, r"E:\PotatoST\build\zftools")

import _zf66_png  # 现成的真 PNG 解码器（§4.92：只看文件头的检查不算数）

ROOT = r"E:\PotatoST"
MAT = os.path.join(ROOT, "build", "用户素材", "星璨钢斧.png")
PROV = os.path.join(ROOT, "build", "用户素材", "_来源凭据.json")

WRITE = "--write" in sys.argv


def sha1(path):
    h = hashlib.sha1()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def main():
    print("=" * 72)
    print("ZF133 素材入库：星璨钢斧")
    print("=" * 72)

    assert os.path.isfile(MAT), "素材不在：" + MAT
    data = open(MAT, "rb").read()
    print("文件      : %s" % MAT)
    print("字节      : %d" % len(data))
    print("sha1      : %s" % hashlib.sha1(data).hexdigest())
    print("sha256    : %s" % hashlib.sha256(data).hexdigest())

    # ---- 真解码（不信文件头，逐像素解出来；§4.92 那一刀就是为这种事立的） ----
    # _zf66_png.read_png 返回 (w, h, ctype, px)，px 是 RGBA 四元组列表
    w, h, ctype, px = _zf66_png.read_png(MAT)
    print("解码宽高  : %d x %d" % (w, h))
    print("色型(ctype): %d  (0=灰 2=RGB 3=调色板 4=灰+α 6=RGBA)" % ctype)
    print("像素数    : %d  （应等于 %d，不等就是 IDAT 坏）" % (len(px), w * h))
    assert len(px) == w * h, "IDAT 解出来的像素数与 IHDR 不符"

    # ---- 内容画像：不透明像素占比 / 主色 ----
    opaque = [p for p in px if p[3] > 0]
    print("非全透明像素: %d / %d (%.1f%%)" % (len(opaque), len(px),
                                         100.0 * len(opaque) / max(1, len(px))))
    colors = {}
    for p in opaque:
        key = (p[0], p[1], p[2])
        colors[key] = colors.get(key, 0) + 1
    top = sorted(colors.items(), key=lambda kv: -kv[1])[:8]
    print("主色前 8  :")
    for (r, g, b), n in top:
        print("            #%02x%02x%02x  %d px" % (r, g, b, n))

    # ---- 素材是不是 16x16 的物品图标（本工程物品贴图的规矩） ----
    verdict = "ITEM_ICON" if (w, h) == (16, 16) else "NEEDS_CONVERT"
    print("判定      : %s" % verdict)

    # ---- 落盘目标（物品贴图规范路径） ----
    dest = os.path.join(ROOT, "src", "main", "resources", "assets", "potato_s_t",
                        "textures", "item", "star_steel_axe.png")
    print("目标路径  : %s" % dest)
    print("目标已存在: %s" % os.path.isfile(dest))

    if WRITE:
        # ⚠ 这个文件体例是 **{键: 记录}** 的字典（键 = 素材文件名），不是数组。
        #   我第一版按"数组 + entries 字段"写，`doc.get('entries', [])` 拿到空表，
        #   于是把整份 29 条的凭据**写成了一个 1 元数组**（当场丢掉 28 条，已用
        #   `git checkout --` 还原）。教训与 §4.17 同源：**改共享数据文件前先读清它的体例**，
        #   并且写前必须断言"新条数 = 旧条数 + 1"。
        doc = json.load(io.open(PROV, encoding="utf-8"))
        assert isinstance(doc, dict), "凭据文件的体例变了（期望 dict，实得 %s）" % type(doc).__name__
        before = len(doc)
        key = "星璨钢斧.png"

        rec = {
            "原名": "星璨钢斧.png",
            "sha1": hashlib.sha1(data).hexdigest(),
            "sha256": hashlib.sha256(data).hexdigest(),
            "bytes": len(data),
            "解码": "%dx%d" % (w, h),
            "轮次": "ZF133",
            "说明": "用户给星璨钢斧的物品贴图（16x16 RGBA，可以直接用）；"
                    "落盘到 assets/potato_s_t/textures/item/star_steel_axe.png",
        }
        if doc.get(key, {}).get("sha1") == rec["sha1"]:
            print("凭据已存在（同 sha1），不重复写")
            return
        doc[key] = rec
        assert len(doc) == before + 1, "写前断言失败：条数没涨"
        io.open(PROV, "w", encoding="utf-8", newline="\n").write(
            json.dumps(doc, ensure_ascii=False, indent=2) + "\n")
        after = len(json.load(io.open(PROV, encoding="utf-8")))
        assert after == before + 1, "写后复核失败：%d -> %d" % (before, after)
        print("凭据已追加：%s（%d -> %d 条）" % (PROV, before, after))


main()
