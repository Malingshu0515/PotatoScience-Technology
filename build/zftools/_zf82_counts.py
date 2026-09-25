# -*- coding: utf-8 -*-
u"""_zf82_counts.py —— ZF82 把散落各处的"活体数字"一次改全（ZF80/ZF81 两轮都是漏这个白跑门）

本轮变化：
  · 语言键 257 → **270**（+13：2 个桶 + 2 个液体方块名 + 换流器 + 7 条状态）
  · 合成配方 29 → **30**（容器换流器）
  · 英文公告里对应那句也要跟着改

每处都断言锚点命中次数（§4.36），改完回读核对。
"""
import io
import os
import sys

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

ROOT = r"E:\PotatoST"
TOOLS = os.path.join(ROOT, "build", "zftools")
DOCS = os.path.join(ROOT, "docs")
fails = []


def read(p):
    return io.open(p, encoding="utf-8").read()


def patch(rel, old, new, label, expect=1):
    p = os.path.join(ROOT, rel)
    t = read(p)
    n = t.count(old)
    if n != expect:
        fails.append(u"%s：锚点命中 %d 次（期望 %d）" % (label, n, expect))
        return
    io.open(p, "w", encoding="utf-8", newline=u"\n").write(t.replace(old, new, expect))
    print(u"  [OK]   %s" % label)


def main():
    print(u"== ① 语言键数 257 → 270 ==")
    patch(r"build\zftools\_zf71_verify.py",
          u"set(keys.values()) == {257} and u\"257 keys each\" in doc",
          u"set(keys.values()) == {270} and u\"270 keys each\" in doc",
          u"ZF71 活体：键数 257 → 270")
    patch(r"build\zftools\_zf73_verify.py",
          u"check(u\"B11 四语言各 257 键（ZF75 biome 名 + ZF78 27 键 + ZF79 2 键 + ZF80 9 键）\", "
          u"all(v == 257 for v in counts.values()), str(counts))",
          u"check(u\"B11 四语言各 270 键（ZF78 27 + ZF79 2 + ZF80 9 + ZF82 13）\", "
          u"all(v == 270 for v in counts.values()), str(counts))",
          u"ZF73 B11：257 → 270")
    patch(r"build\zftools\_zf75_verify.py",
          u"check(u\"C2 四语言各 257 键（ZF80 起）\", all(v == 257 for v in counts.values()), str(counts))",
          u"check(u\"C2 四语言各 270 键（ZF82 起）\", all(v == 270 for v in counts.values()), str(counts))",
          u"ZF75 C2：257 → 270")
    patch(r"build\zftools\_zf78_verify.py",
          u"check(u\"四份语言键数一致且 = 257（219 + 22 + 5 + 2，ZF80 灌装机手倒/诊断又 +9）\",\n"
          u"          len(set(counts.values())) == 1 and list(counts.values())[0] == 257)",
          u"check(u\"四份语言键数一致且 = 270（ZF82 容器换流器 + 两个桶又 +13）\",\n"
          u"          len(set(counts.values())) == 1 and list(counts.values())[0] == 270)",
          u"ZF78：257 → 270")
    patch(r"build\zftools\_zf79_verify.py",
          u"check(u\"四份语言键数一致且 = 257（ZF79 时是 248，ZF80 灌装机 +9）\",\n"
          u"          len(set(counts.values())) == 1 and list(counts.values())[0] == 257)",
          u"check(u\"四份语言键数一致且 = 270（ZF82 容器换流器 + 两个桶 +13）\",\n"
          u"          len(set(counts.values())) == 1 and list(counts.values())[0] == 270)",
          u"ZF79：257 → 270")
    patch(r"build\zftools\_zf80_verify.py",
          u"EXPECT_KEYS = 257", u"EXPECT_KEYS = 270", u"ZF80 EXPECT_KEYS：257 → 270")
    patch(r"build\zftools\_zf81_verify.py",
          u"eq(u\"语言键数没变（还是 257）\", 257, len(inside))",
          u"eq(u\"语言键数（ZF82 起 270：换流器 + 两个桶 +13）\", 270, len(inside))",
          u"ZF81 jar 键数：257 → 270")

    print(u"== ② 合成配方 29 → 30 ==")
    patch(r"build\zftools\_zf71_verify.py",
          u"check(craft == 29, u\"合成配方 %d 条\" % craft)",
          u"check(craft == 30, u\"合成配方 %d 条\" % craft)",
          u"ZF71 活体：合成配方 29 → 30")

    print(u"== ③ 英文公告 ==")
    patch(r"docs\UpdateAnnouncement_EN.md",
          u"Русский (257 keys each)", u"Русский (270 keys each)",
          u"公告：键数 257 → 270")
    ann = os.path.join(DOCS, u"UpdateAnnouncement_EN.md")
    t = read(ann)
    line = (u"\n- **Diesel / Gasoline Buckets (0.11 ZF82)** - two fluid buckets that work exactly like the "
            u"vanilla bucket: pour the fluid out (place a source block) and get an empty bucket back, or pick a "
            u"source block back up with an empty bucket. Diesel and gasoline are now real world fluids with "
            u"their own blocks.\n"
            u"- **Container Fluid Exchanger (0.11 ZF82)** - left slot: an oil bucket / gas tank with fluid in it, "
            u"right slot: exactly 1 empty bucket. After 3 s it takes 1000 mB out of the container and turns that "
            u"empty bucket into the bucket of that fluid (water -> water bucket, diesel -> diesel bucket; other "
            u"mods' fluids work too as long as they have a bucket form). Fluids without a bucket form (crude oil / "
            u"naphtha / LPG) are refused. A fluid pump connected to the block drains the container in the left "
            u"slot directly (gases included - gas tanks must be pumped out).\n")
    if u"Container Fluid Exchanger (0.11 ZF82)" not in t:
        io.open(ann, "w", encoding="utf-8", newline=u"\n").write(t.rstrip(u"\n") + u"\n" + line)
        print(u"  [OK]   公告补上 ZF82 两件")
    else:
        print(u"  [OK]   公告里已经有 ZF82 那两件（跳过）")

    print(u"\n== 回读核对 ==")
    for rel, bad in [(r"build\zftools\_zf71_verify.py", u"257"),
                     (r"build\zftools\_zf73_verify.py", u"257"),
                     (r"build\zftools\_zf75_verify.py", u"257"),
                     (r"build\zftools\_zf78_verify.py", u"257"),
                     (r"build\zftools\_zf79_verify.py", u"257"),
                     (r"build\zftools\_zf80_verify.py", u"257"),
                     (r"build\zftools\_zf81_verify.py", u"257 keys")]:
        t = read(os.path.join(ROOT, rel))
        if bad in t:
            fails.append(u"%s 里还留着 %s" % (rel, bad))
    if u"257 keys each" in read(ann):
        fails.append(u"公告里还留着 257 keys each")
    print(u"残留检查完毕")
    print(u"\n失败项 = %d" % len(fails))
    for f in fails:
        print(u"  !! " + f)
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())
