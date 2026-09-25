# -*- coding: utf-8 -*-
u"""_zf82_gatefix.py —— 把 ZF82 门里炸出来的 6 条修掉（每条都先看清"它到底在断言什么"）

| 门 | 报的什么 | 真相 | 怎么修 |
|---|---|---|---|
| Audit A | `FluidExchangerScreen.java` 有一个未使用的 import | **我的锅** | 删掉那行 import |
| ZF66 贴图 | `textures/item` 下还有中文文件名（钢板/铁板/铜板 .jpg） | **用户新放进来的三张素材**（09-23/09-24，铜板/钢板 早已有 ASCII PNG） | 按 §4.24 挪出资源目录、逐字节留档到 `build/用户素材/`（ASCII 名 + 哈希凭据） |
| ZF71 公告 | 「还在借原版贴图的模型 = 11 个（公告写 9）」 | 本轮两个桶的模型借了原版水桶 ⇒ 9 → 11 | 公告数字 9 → 11 |
| ZF73 repro | 「只新增了 oil_bucket.json」不成立 | 本轮多了一份合成配方 | 预期新增改成 {oil_bucket, fluid_exchanger}（34 份基线仍逐字节相同，那才是这条的重点） |
| ZF73 verify A13 | 「不设 .bucket(...)：原版空桶舀不走原油」 | 断言写成了**整文件里不许出现 .bucket** —— 柴油/汽油有桶是**用户本轮点名要的** | 改成精确断言：**原油自己的属性方法里**不许有 `.bucket(` |
| ZF73 verify D2 | 同上 repro | 同上 | 同上（允许本轮那一份） |
"""
import glob
import hashlib
import io
import json
import os
import shutil
import sys

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

ROOT = r"E:\PotatoST"
TOOLS = os.path.join(ROOT, "build", "zftools")
USERART = os.path.join(ROOT, "build", u"用户素材")
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
    print(u"== ① Audit：删掉未使用的 import（我的锅）==")
    patch(r"src\main\java\com\potatost\mod\client\FluidExchangerScreen.java",
          u"import com.potatost.mod.FluidExchangerBlockEntity;\n", u"",
          u"FluidExchangerScreen：删掉未使用的 FluidExchangerBlockEntity import")

    print(u"== ② 用户新放的三张素材：挪出资源目录 + 逐字节留档（§4.24）==")
    tex = os.path.join(ROOT, "src", "main", "resources", "assets", "potato_s_t", "textures", "item")
    os.makedirs(USERART, exist_ok=True)
    prov = {}
    for p in sorted(glob.glob(os.path.join(tex, "*.jpg"))):
        name = os.path.basename(p)
        if not any(ord(c) > 127 for c in name):
            continue
        ascii_name = {u"钢板.jpg": u"steel_plate.jpg", u"铁板.jpg": u"iron_plate.jpg",
                      u"铜板.jpg": u"copper_plate.jpg"}.get(name)
        if ascii_name is None:
            fails.append(u"没给 %s 定 ASCII 名（不猜，先停下）" % name)
            continue
        dst = os.path.join(USERART, ascii_name)
        before = hashlib.sha1(open(p, "rb").read()).hexdigest()
        shutil.copy2(p, dst)
        after = hashlib.sha1(open(dst, "rb").read()).hexdigest()
        if before != after:
            fails.append(u"%s：留档后哈希不一致" % name)
            continue
        os.remove(p)
        prov[ascii_name] = {"原名": name, "sha1": after, "bytes": os.path.getsize(dst),
                            "说明": u"用户在 ZF82 前后放进 textures/item 的原始素材；"
                                    u"对应物品的 ASCII 贴图早已存在（copper_plate.png / steel_plate.png），"
                                    u"本轮只把它挪出资源目录，未改任何在用贴图"}
        print(u"  [OK]   %s → build/用户素材/%s（%s…，原文件已从资源目录移走）"
              % (name, ascii_name, after[:8]))
    if prov:
        io.open(os.path.join(USERART, u"_来源凭据.json"), "w", encoding="utf-8",
                newline=u"\n").write(json.dumps(prov, indent=2, ensure_ascii=False) + u"\n")
        print(u"  [OK]   来源凭据：build/用户素材/_来源凭据.json")
    leftover = [f for f in os.listdir(tex) if any(ord(c) > 127 for c in f)]
    if leftover:
        fails.append(u"textures/item 下还有中文文件名：%s" % leftover)
    else:
        print(u"  [OK]   textures/item 下已无中文文件名")

    print(u"== ③ 公告：借原版贴图的模型 9 → 11 ==")
    patch(r"docs\UpdateAnnouncement_EN.md", u"9 models still do this", u"11 models still do this",
          u"公告 9 → 11")
    patch(r"build\zftools\_zf71_verify.py",
          u"check(n_draw == 9 and u\"9 models still do this\" in doc,",
          u"check(n_draw == 11 and u\"11 models still do this\" in doc,",
          u"活体校验 9 → 11")

    print(u"== ④ ZF73：允许本轮那一份新配方（34 份基线仍逐字节相同）==")
    patch(r"build\zftools\_zf73_repro.py",
          u"NEW_OK = {u\"oil_bucket.json\"}",
          u"# ⚠ ZF82 又加了 fluid_exchanger.json（容器换流器的合成台配方）——\n"
          u"#   「其余 34 份逐字节未变」才是这条的真正内容，新增名单随轮次增长。\n"
          u"NEW_OK = {u\"oil_bucket.json\", u\"fluid_exchanger.json\"}",
          u"ZF73 repro：预期新增名单加 fluid_exchanger.json")
    patch(r"build\zftools\_zf73_verify.py",
          u"check(u\"D2 只新增了 oil_bucket.json\", sorted(cur - pre) == [u\"oil_bucket.json\"],",
          u"check(u\"D2 只新增了预期的那些（ZF82 起含 fluid_exchanger.json）\",\n"
          u"      sorted(cur - pre) == [u\"fluid_exchanger.json\", u\"oil_bucket.json\"],",
          u"ZF73 verify D2：允许本轮那一份")

    print(u"== ⑤ A13 改成精确断言（原油自己不许有桶；柴油/汽油有桶是用户点名要的）==")
    patch(r"build\zftools\_zf73_verify.py",
          u"check(u\"A13 不设 .bucket(...)：原版空桶舀不走原油（防白送 3 倍）\",\n"
          u"      u\".bucket(ModItems\" not in modfluids and u\".bucket(() ->\" not in modfluids)",
          u"# ⚠ 原断言是**整文件**里不许出现 .bucket —— ZF82 起柴油/汽油**必须**有桶\n"
          u"#   （用户原话「新进 柴油桶 汽油桶 … 可以被空桶收回源头液体」）。\n"
          u"#   改成精确断言：**原油那个属性方法里**不许有 .bucket(...)。\n"
          u"_crude_body = modfluids[modfluids.find(u\"crudeOilProperties()\"):]\n"
          u"_crude_body = _crude_body[:_crude_body.find(u\"}\") + 1] if u\"}\" in _crude_body else _crude_body\n"
          u"check(u\"A13 原油**自己**不设 .bucket(...)：原版空桶舀不走原油（防白送 3 倍）\",\n"
          u"      u\".bucket(\" not in _crude_body)",
          u"ZF73 A13：整文件 → 原油属性方法")

    print(u"\n失败项 = %d" % len(fails))
    for f in fails:
        print(u"  !! " + f)
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())
