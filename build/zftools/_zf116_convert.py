# -*- coding: utf-8 -*-
"""_zf116_convert.py —— ZF116：星璨钢胸甲 / 护腿 / 靴子 三件上线

用户第二次说「又放了」。三件都在 build/用户素材/：
  星璨钢胸甲.png  3260 B  sha1 87d52aa95f70
  星璨钢护腿.png  3072 B  sha1 98b513d2734e
  星璨钢靴子.png  3195 B  sha1 db88fae1670d
实测三件都是 **16×16 / 8 位 RGBA / 背景透明 / 半透明像素 0** ⇒ **原字节复制**，零重编码。

连带（与 ZF110 头盔那次同一套）：
  · 三个模型 `layer0`：minecraft:item/iron_* -> potato_s_t:item/star_steel_*
  · 活体数字「还在借原版贴图的模型」**12 -> 9**，三处一起改：
      ① docs/UpdateAnnouncement_EN.md 那句
      ② _zf71_verify.py 的 n_draw 期望 + 文案
      ③ _zf90_verify.py 的两条断言（含"不再写 5/6/7/13"那条要加 12）
  · docs/贴图清单.md 重跑 --plan（表头 12 -> 9）

⚠ 这轮是**并发环境**（同一棵树上还有 ZF111~ZF115 三条正在跑）：
  凡是改别人的文件，一律「读 → 字符串替换 → 立刻回读断言」，且**只替换唯一出现的那一处**，
  替换不到就**报错停手**，绝不整份覆盖。
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
TOOLS = os.path.join(ROOT, "build", "zftools")
USERART = os.path.join(ROOT, "build", "用户素材")
TEXI = os.path.join(ROOT, r"src\main\resources\assets\potato_s_t\textures\item")
MODELI = os.path.join(ROOT, r"src\main\resources\assets\potato_s_t\models\item")
DOCS = os.path.join(ROOT, "docs")

OLD_N, NEW_N = 12, 9
fails = []

JOBS = [
    ("星璨钢胸甲.png", "star_steel_chestplate", "87d52aa95f70"),
    ("星璨钢护腿.png", "star_steel_leggings", "98b513d2734e"),
    ("星璨钢靴子.png", "star_steel_boots", "db88fae1670d"),
]


def sha1(p):
    return hashlib.sha1(open(p, "rb").read()).hexdigest()


def patch(path, old, new, label, expect=1):
    """读-替换-回读。出现次数不对就报错停手（并发环境下绝不整份覆盖）。"""
    raw = io.open(path, encoding="utf-8").read()
    n = raw.count(old)
    if n != expect:
        fails.append("%s：锚点出现 %d 次（期望 %d）—— 停手不改" % (label, n, expect))
        print("     !! %s 锚点出现 %d 次（期望 %d），跳过" % (label, n, expect))
        return False
    io.open(path, "w", encoding="utf-8", newline="\n").write(raw.replace(old, new))
    back = io.open(path, encoding="utf-8").read()
    if old in back or new not in back:
        fails.append("%s：回读断言失败" % label)
        print("     !! %s 回读断言失败" % label)
        return False
    print("     [OK] %s" % label)
    return True


def main():
    print("=" * 74)
    print("① 三张素材体检（规格 + 前置哈希）")
    for srcname, item, want in JOBS:
        p = os.path.join(USERART, srcname)
        if not os.path.exists(p):
            fails.append("找不到 %s" % srcname)
            print("  !! 找不到 %s" % srcname)
            continue
        got = sha1(p)[:12]
        w, h, rgba = read_png(p)
        b = open(p, "rb").read()
        opaque = sum(1 for i in range(w * h) if rgba[i * 4 + 3] == 255)
        semi = sum(1 for i in range(w * h) if 0 < rgba[i * 4 + 3] < 255)
        print("  %s  %d B  %dx%d 位深%d 类型%d  不透明 %d 半透明 %d  sha1 %s%s"
              % (srcname, len(b), w, h, b[24], b[25], opaque, semi, got,
                 "" if got == want else "  !! 哈希与预期不符（期望 %s）" % want))
        if got != want:
            fails.append("%s 哈希不符" % srcname)
        if (w, h, b[24], b[25]) != (16, 16, 8, 6):
            fails.append("%s 规格不是 16x16/8/RGBA" % srcname)
        if semi:
            fails.append("%s 有半透明像素 %d 个" % (srcname, semi))
    if fails:
        print("\n前置检查未过，停手。")
        return 1

    print("\n" + "=" * 74)
    print("② 原字节复制到 textures/item/")
    for srcname, item, _ in JOBS:
        src = os.path.join(USERART, srcname)
        dst = os.path.join(TEXI, item + ".png")
        raw = open(src, "rb").read()
        io.open(dst, "wb").write(raw)
        if open(dst, "rb").read() != raw:
            fails.append("%s 写出后逐字节不一致" % item)
            print("  !! %s 写出后不一致" % item)
        else:
            print("  [OK] %-26s %d B  sha1 %s" % (item + ".png", len(raw), sha1(dst)[:12]))

    print("\n" + "=" * 74)
    print("③ 三个模型 layer0 改指向自己")
    for _, item, _ in JOBS:
        mp = os.path.join(MODELI, item + ".json")
        data = json.loads(io.open(mp, encoding="utf-8").read())
        old = data["textures"]["layer0"]
        want = "potato_s_t:item/" + item
        if old == want:
            print("  [幂等] %s 已指向 %s" % (item, want))
            continue
        data["textures"]["layer0"] = want
        io.open(mp, "w", encoding="utf-8", newline="\n").write(
            json.dumps(data, indent=2, ensure_ascii=False) + "\n")
        after = json.loads(io.open(mp, encoding="utf-8").read())["textures"]["layer0"]
        if after != want:
            fails.append("%s 改指向失败" % item)
            print("  !! %s 改指向失败（%s）" % (item, after))
        else:
            print("  [OK] %-22s %s -> %s" % (item, old, after))

    print("\n" + "=" * 74)
    print("④ 活体数字 %d -> %d（三处一起改）" % (OLD_N, NEW_N))

    # ① 公告
    ann = os.path.join(DOCS, "UpdateAnnouncement_EN.md")
    raw = io.open(ann, encoding="utf-8").read()
    if "%d models still do this" % NEW_N in raw:
        print("     [幂等] 公告已是 %d" % NEW_N)
    else:
        patch(ann,
              "%d models still do this — the count\n  went up to 13 when the eight new armour pieces borrowed the vanilla iron armour sprites, and is\n  back down to 12 now that the Star Steel helmet has its own sprite); on top of"
              % OLD_N,
              "%d models still do this — the eight armour pieces used to borrow the vanilla iron\n  armour sprites, and this number is falling as their own sprites arrive: 13 -> 12 (Star Steel\n  helmet) -> %d (Star Steel chestplate, leggings and boots)); on top of" % (NEW_N, NEW_N),
              "公告「%d models still do this」-> %d" % (OLD_N, NEW_N))

    # ② _zf71_verify.py
    z71 = os.path.join(TOOLS, "_zf71_verify.py")
    raw = io.open(z71, encoding="utf-8").read()
    if "n_draw == %d" % NEW_N in raw:
        print("     [幂等] _zf71_verify.py 已是 %d" % NEW_N)
    else:
        patch(z71,
              'check(n_draw == %d and u"%d models still do this" in doc,\n          u"还在借原版贴图的模型 = %%d 个（公告写 %d）" %% n_draw)'
              % (OLD_N, OLD_N, OLD_N),
              'check(n_draw == %d and u"%d models still do this" in doc,\n          u"还在借原版贴图的模型 = %%d 个（公告写 %d）" %% n_draw)'
              % (NEW_N, NEW_N, NEW_N),
              "_zf71_verify.py n_draw %d -> %d" % (OLD_N, NEW_N))

    # ③ _zf90_verify.py（三条断言）
    z90 = os.path.join(TOOLS, "_zf90_verify.py")
    raw = io.open(z90, encoding="utf-8").read()
    if "%d models still do this" % NEW_N in raw:
        print("     [幂等] _zf90_verify.py 已是 %d" % NEW_N)
    else:
        patch(z90,
              u'check(u"英文公告已改成 %d models still do this", u"%d models still do this" in ann)'
              % (OLD_N, OLD_N),
              u'check(u"英文公告已改成 %d models still do this", u"%d models still do this" in ann)'
              % (NEW_N, NEW_N),
              "_zf90 公告断言 %d -> %d" % (OLD_N, NEW_N))
        patch(z90,
              u'check(u"英文公告里不再写 5/6/7/13 models", not any(u"%%d models still do this" %% n in ann\n                                                     for n in (5, 6, 7, 13)))',
              u'check(u"英文公告里不再写 5/6/7/13/12 models", not any(u"%%d models still do this" %% n in ann\n                                                        for n in (5, 6, 7, 13, 12)))',
              "_zf90 旧数字黑名单加 12")
        patch(z90,
              u'check(u"`_zf71_verify.py` 的期望值同步成 %d", u"n_draw == %d" in z71)'
              % (OLD_N, OLD_N),
              u'check(u"`_zf71_verify.py` 的期望值同步成 %d", u"n_draw == %d" in z71)'
              % (NEW_N, NEW_N),
              "_zf90 z71 同步断言 %d -> %d" % (OLD_N, NEW_N))

    print("\n" + "=" * 74)
    print("失败项 = %d" % len(fails))
    for f in fails:
        print("  !! " + f)
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())
