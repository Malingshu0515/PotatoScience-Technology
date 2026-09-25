# -*- coding: utf-8 -*-
u"""_zf93_publish.py —— ZF93 出成品（作废 ZF92 那版 `e9b8ab96…`）+ 把 §9 的占位填实

照老规矩：**先核对旧哈希、再核对新产物内容，全过了才动文件**；
§4.59 ④ 的两条硬化照旧（重命名用独立的 `PREV_ROUND_SHA`；占位补丁幂等）。
本轮额外核的是**本轮的正题**：成品里四样新资源（音频 / 贴图 / 物品模型 / 曲目数据）
必须与盘上**逐字节一致**，音频还要**现场量一遍时长**（不抄注释）。
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

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

ROOT = r"E:\PotatoST"
SRC = os.path.join(ROOT, "build", "libs", "potato_s_t-0.11.jar")
DST = os.path.join(ROOT, "release", "PotatoST-0.11.jar")
SHA = DST + ".sha1"
PUB = os.path.join(ROOT, "build", "zftools", "_zf93_publish.py")
DOC = os.path.join(ROOT, "docs", u"开发档案.md")
ASSETS = os.path.join(ROOT, r"src\main\resources\assets\potato_s_t")
DATA = os.path.join(ROOT, r"src\main\resources\data\potato_s_t")
ITEM = "music_disc_jasmine_flower"
SONG = "jasmine_flower"
VOID = "3599165bc5d7bba88c1fcaec33312b78b772aed7"
PREV_ROUND_SHA = "e9b8ab969ae4b30e77745f64e8e0c4499438f1c1"
EXPECT_KEYS = 272
EXPECT_LENGTH = 147.1
fails = []


def sha1(p):
    return hashlib.sha1(open(p, "rb").read()).hexdigest()


def ogg_duration(path):
    data = io.open(path, "rb").read()
    pos, last, rate = 0, 0, None
    while pos < len(data) and data[pos:pos + 4] == b"OggS":
        seg = data[pos + 26]
        body = pos + 27 + seg
        n = sum(data[pos + 27:body])
        g = struct.unpack("<q", data[pos + 6:pos + 14])[0]
        if g > 0:
            last = g
        if rate is None and data[body:body + 7] == b"\x01vorbis":
            rate = struct.unpack("<I", data[body + 12:body + 16])[0]
        pos = body + n
    return (last / float(rate)) if (last and rate) else None


def patch(path, old, new, label, expect=1, optional=False):
    t = io.open(path, encoding="utf-8").read()
    hits = t.count(old)
    if hits != expect:
        if optional and hits == 0:
            print(u"  [SKIP] %s（锚点已不在 = 之前填过了，幂等放行）" % label)
            return
        fails.append(u"%s：锚点命中 %d 次（必须 %d 次）" % (label, hits, expect))
        return
    io.open(path, "w", encoding="utf-8", newline=u"\n").write(t.replace(old, new, 1))
    print(u"  [OK]   %s" % label)


def main():
    old = sha1(DST) if os.path.exists(DST) else u"(缺)"
    if old != VOID:
        fails.append(u"当前成品 %s ≠ 预期要作废的 %s" % (old, VOID))
    if not os.path.exists(SRC):
        fails.append(u"没有构建产物 %s" % SRC)
        print(u"  [FAIL] 缺构建产物 ⇒ 一个字节都不动")
        return 1
    new = sha1(SRC)
    size = os.path.getsize(SRC)

    pairs = [
        (u"assets/potato_s_t/sounds/%s.ogg" % ITEM,
         os.path.join(ASSETS, "sounds", ITEM + ".ogg"), u"音频"),
        (u"assets/potato_s_t/textures/item/%s.png" % ITEM,
         os.path.join(ASSETS, "textures", "item", ITEM + ".png"), u"贴图"),
        (u"assets/potato_s_t/models/item/%s.json" % ITEM,
         os.path.join(ASSETS, "models", "item", ITEM + ".json"), u"物品模型"),
        (u"data/potato_s_t/jukebox_song/%s.json" % SONG,
         os.path.join(DATA, "jukebox_song", SONG + ".json"), u"曲目数据"),
    ]
    with zipfile.ZipFile(SRC) as zf:
        names = zf.namelist()
        entries = len(names)
        bad = [n for n in names if "Check" in n.split("/")[-1] and n.endswith(".class")]
        if bad:
            fails.append(u"成品里带探针：%s" % bad)
        evil = [n for n in names
                if (n.startswith(u"assets/") or n.startswith(u"data/"))
                and not re.fullmatch(u"[a-z0-9/._-]+", n)]
        if evil:
            fails.append(u"成品里有非 ASCII 条目：%s" % evil)
        else:
            print(u"  [OK]   assets/ 与 data/ 的条目名全合法")
        for rel, disk, what in pairs:
            if rel not in names:
                fails.append(u"成品里没有 %s" % rel)
                continue
            if zf.read(rel) != open(disk, "rb").read():
                fails.append(u"成品里的%s与盘上不一致（%s）" % (what, rel))
            else:
                print(u"  [OK]   成品里的%s与盘上逐字节一致（%s，%d 字节）"
                      % (what, rel.split("/")[-1], zf.getinfo(rel).file_size))
        # 音频时长现场量一遍（两条算法：这里用 granule；soundfile 那条在 _zf93_verify.py 里）
        d = ogg_duration(os.path.join(ASSETS, "sounds", ITEM + ".ogg"))
        if d is None or abs(d - EXPECT_LENGTH) >= 0.5:
            fails.append(u"音频实测时长 %s 与 length_in_seconds %s 差 ≥ 0.5 s" % (d, EXPECT_LENGTH))
        else:
            print(u"  [OK]   音频实测 %.6f s，与 length_in_seconds %.1f 对得上" % (d, EXPECT_LENGTH))
        inside = json.loads(zf.read(u"assets/potato_s_t/lang/zh_cn.json").decode("utf-8"))
        if len(inside) != EXPECT_KEYS:
            fails.append(u"成品里 zh_cn 键数 %d ≠ %d" % (len(inside), EXPECT_KEYS))
        else:
            print(u"  [OK]   成品里 zh_cn 键数 = %d" % EXPECT_KEYS)
    if new == old:
        fails.append(u"新旧哈希相同 ⇒ 源码没变？")

    if fails:
        print(u"  [FAIL] 以上 %d 条没过 ⇒ 一个字节都不动" % len(fails))
        for f in fails:
            print(u"    !! " + f)
        return 1

    shutil.copy2(SRC, DST)
    io.open(SHA, "w", encoding="ascii", newline=u"\n").write(new + u"\n")
    print(u"① 已发布 release\\PotatoST-0.11.jar = %s（%d B / %d 条目）" % (new, size, entries))
    print(u"   作废 %s（ZF92）" % VOID[:8])

    patch(DOC, u"__ZF93_SHA1__", new, u"§9 ZF93 条目：成品哈希填实", optional=True)
    patch(DOC, u"__ZF93_BYTES__", str(size), u"§9 ZF93 条目：字节数填实", optional=True)
    patch(DOC, u"__ZF93_ENTRIES__", str(entries), u"§9 ZF93 条目：条目数填实", optional=True)
    patch(DOC, u"**成品**：`release\\PotatoST-0.11.jar` = `%s`" % PREV_ROUND_SHA,
          u"**当时的成品**：`release\\PotatoST-0.11.jar` = `%s`" % PREV_ROUND_SHA,
          u"§9 ZF92 条目：成品 → 当时的成品", optional=True)
    patch(PUB, u'VOID = "%s"' % VOID, u'VOID = "%s"' % new, u"发布脚本 VOID 跟到最新")

    print(u"\n失败项 = %d" % len(fails))
    for f in fails:
        print(u"  !! " + f)
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())
