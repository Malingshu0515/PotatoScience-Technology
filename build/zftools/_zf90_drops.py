# -*- coding: utf-8 -*-
u"""_zf90_drops.py —— ZF90 中途用户又放的两样（表驱动 + 幂等）

  · `柴油桶_001.png`（16×16 RGBA 真 PNG）→ `textures/item/diesel_bucket.png`
    ⇒ 再把 `models/item/diesel_bucket.json` 从借原版水桶（`minecraft:item/water_bucket`）
      改指自己的图。**这一步会让「借原版贴图的模型」从 7 个降到 6 个** ——
      活体数字要一起改（英文公告 + `_zf71_verify.py`），归 `_zf90_counters.py` 管。
  · `copper_plate.png` 被用户**换了一版**（929 B → 3297 B，同一块铜板、重导出）
    ⇒ 盘上文件名本来就对，只做两件事：原字节进 `build/用户素材/`、按本工程规格**重编码**一份
      （逐像素核对 256/256），并写进来源凭据。

做法沿用 ZF86~ZF89：**用户的画一个像素都不改**（重编码只换容器，不换像素）；
原图按 §4.24 留档；中文名一律不留。
"""
import hashlib
import io
import json
import os
import struct
import sys
import zlib

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import _zf66_png  # noqa: E402

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

ROOT = r"E:\PotatoST"
TEXI = os.path.join(ROOT, r"src\main\resources\assets\potato_s_t\textures\item")
MODELI = os.path.join(ROOT, r"src\main\resources\assets\potato_s_t\models\item")
USERART = os.path.join(ROOT, "build", u"用户素材")
# (源文件, 目标贴图, 留档名, 模型文件或 None, 模型新 layer0, 说明)
JOBS = [
    (u"柴油桶_001.png", u"diesel_bucket.png", u"diesel_bucket.png",
     u"diesel_bucket.json", u"potato_s_t:item/diesel_bucket",
     u"用户放的柴油桶素材（柴油桶_001.png）⇒ textures/item/diesel_bucket.png"),
    (u"copper_plate.png", u"copper_plate.png", u"copper_plate_v2.png",
     None, None,
     u"用户重导出的铜板素材（copper_plate.png 新版，929→3297 字节，同一块板）⇒ 原样重编码"),
    (u"汽油桶.png", u"gasoline_bucket.png", u"gasoline_bucket.png",
     u"gasoline_bucket.json", u"potato_s_t:item/gasoline_bucket",
     u"用户放的汽油桶素材（汽油桶.png）⇒ textures/item/gasoline_bucket.png"),
]
fails = []


def sha1b(b):
    return hashlib.sha1(b).hexdigest()


def write_png(path, px):
    raw = b""
    for y in range(16):
        raw += b"\x00" + b"".join(bytes(px[y * 16 + x]) for x in range(16))

    def chunk(tag, payload):
        return (struct.pack(">I", len(payload)) + tag + payload
                + struct.pack(">I", zlib.crc32(tag + payload) & 0xFFFFFFFF))

    io.open(path, "wb").write(b"\x89PNG\r\n\x1a\n"
                              + chunk(b"IHDR", struct.pack(">IIBBBBB", 16, 16, 8, 6, 0, 0, 0))
                              + chunk(b"IDAT", zlib.compress(raw, 9)) + chunk(b"IEND", b""))


def pixels(path):
    w, h, ctype, px0 = _zf66_png.read_png(path)
    return (w, h, ctype, [p if len(p) == 4 else (p[0], p[1], p[2], 255) for p in px0])


def main():
    prov_p = os.path.join(USERART, u"_来源凭据.json")
    prov = json.loads(io.open(prov_p, encoding="utf-8").read()) if os.path.exists(prov_p) else {}
    os.makedirs(USERART, exist_ok=True)
    changed = 0

    for src_name, dst_name, keep_name, model, layer0, note in JOBS:
        src = os.path.join(TEXI, src_name)
        dst = os.path.join(TEXI, dst_name)
        keep = os.path.join(USERART, keep_name)
        print(u"== %s ==" % src_name)
        # 幂等：留档原图与当前源文件**逐字节相同** ⇒ 这一张已经处理过了
        # （对"源=目标"的那种，比如重编码过的贴图自身，这一步是必须的；否则会把自己再处理一遍）
        arch_sha = sha1b(open(keep, "rb").read()) if os.path.exists(keep) else None
        src_sha = sha1b(open(src, "rb").read()) if os.path.exists(src) else None
        if arch_sha is not None and src_sha is not None and arch_sha == src_sha:
            _, _, _, a = pixels(keep)
            _, _, _, b2 = pixels(dst)
            n = sum(1 for x, y in zip(a, b2) if x == y)
            print(u"   [SKIP] 已处理过（留档原图与源文件同哈希 %s…）；盘上成品像素一致：%s（%d/256）"
                  % (arch_sha[:8], u"是" if n == 256 else u"否", n))
            if n != 256:
                fails.append(u"%s 与留档原图不一致（%d/256）" % (dst_name, n))
            continue
        if not os.path.exists(src):
            if os.path.exists(keep):
                w, h, ctype, a = pixels(keep)
                _, _, _, b2 = pixels(dst)
                n = sum(1 for x, y in zip(a, b2) if x == y)
                print(u"   [SKIP] 已处理过；留档原图与盘上成品像素一致：%s（%d/256）"
                      % (u"是" if n == 256 else u"否", n))
                if n != 256:
                    fails.append(u"%s 与留档原图不一致（%d/256）" % (dst_name, n))
                continue
            fails.append(u"既没有源图 %s，也没有留档 %s" % (src_name, keep_name))
            continue

        w, h, ctype, px = pixels(src)
        print(u"   %d×%d ctype %s，透明像素 %d 个"
              % (w, h, ctype, sum(1 for p in px if p[3] == 0)))
        if (w, h) != (16, 16):
            fails.append(u"%s 不是 16×16（%d×%d）" % (src_name, w, h))

        raw = open(src, "rb").read()
        io.open(keep, "wb").write(raw)
        prov[keep_name] = {"sha1": sha1b(raw), "bytes": len(raw), "说明": note}
        print(u"   [OK]   原图留档 build/用户素材/%s（sha1 %s…）" % (keep_name, sha1b(raw)[:8]))

        old_sha = sha1b(open(dst, "rb").read()) if os.path.exists(dst) else None
        write_png(dst, px)
        new_sha = sha1b(open(dst, "rb").read())
        _, _, _, chk = pixels(dst)
        same = sum(1 for x, y in zip(px, chk) if x == y)
        print(u"   [OK]   %s（%s… → %s…，逐像素 %d/256）"
              % (dst_name, (old_sha or u"新建")[:8], new_sha[:8], same))
        if same != 256:
            fails.append(u"%s 重编码后像素不一致（%d/256）" % (dst_name, same))
        if old_sha == new_sha:
            fails.append(u"%s 与旧文件逐字节相同 ⇒ 等于没换" % dst_name)

        if model:
            mp = os.path.join(MODELI, model)
            t = io.open(mp, encoding="utf-8").read()
            if u'"' + layer0 + u'"' in t:
                print(u"   [SKIP] %s 已指向 %s" % (model, layer0))
            else:
                import re
                newt, n = re.subn(r'"layer0":\s*"[^"]+"', u'"layer0": "%s"' % layer0, t)
                if n != 1:
                    fails.append(u"%s：layer0 替换命中 %d 次" % (model, n))
                else:
                    io.open(mp, "w", encoding="utf-8", newline=u"\n").write(newt)
                    print(u"   [OK]   %s 的 layer0 → %s" % (model, layer0))

        if src != dst and os.path.exists(src):
            os.remove(src)
            print(u"   [OK]   删掉中文名源文件 %s" % src_name)
        changed += 1

    if changed:
        io.open(prov_p, "w", encoding="utf-8", newline=u"\n").write(
            json.dumps(prov, indent=2, ensure_ascii=False) + u"\n")

    for folder, label in ((TEXI, u"textures/item"),
                          (os.path.join(ROOT, r"src\main\resources\assets\potato_s_t\textures\block"),
                           u"textures/block")):
        left = [f for f in os.listdir(folder) if any(ord(c) > 127 for c in f)
                and not f.endswith(u".原名件")]
        if left:
            fails.append(u"%s 下还有中文名（非 .原名件）：%s" % (label, left))
        else:
            print(u"\n   [OK]   %s 下已无中文名（.原名件 除外）" % label)
    print(u"\n失败项 = %d" % len(fails))
    for f in fails:
        print(u"  !! " + f)
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())
