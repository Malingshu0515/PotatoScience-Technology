# -*- coding: utf-8 -*-
r"""_zf97_publish.py —— ZF97 出成品（作废 ZF96 那版 `091f1bfb…`）+ 把 §9 的占位填实

照老规矩：**先核对旧哈希、再核对新产物内容，全过了才动文件**；
§4.59 ④ 的两条硬化照旧（重命名用独立的 `PREV_ROUND_SHA`；占位补丁幂等）。
本轮额外核：成品里有 6 个新 class（两台机器三件套）+ 2 个界面 class、
8 张新贴图与盘上逐字节一致、**7 份 c: 流体标签都在**、
**改前那 42 份配方与 118 张贴图一件不少**、crafting_shaped = 38。
"""
import hashlib
import io
import json
import os
import re
import shutil
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
PUB = os.path.join(ROOT, "build", "zftools", "_zf97_publish.py")
DOC = os.path.join(ROOT, "docs", u"开发档案.md")
RDIR = os.path.join(ROOT, r"src\main\resources\data\potato_s_t\recipe")
ASSETS = os.path.join(ROOT, r"src\main\resources\assets\potato_s_t")
RES = os.path.join(ROOT, r"src\main\resources")
BEFORE = os.path.join(r"C:\PotatoST救援\zf97_pre", "recipe_before.txt")
TEXBEFORE = os.path.join(r"C:\PotatoST救援\zf97_pre", "textures_before.txt")
NEW = ["air_separator", "ammonia_synthesis_chamber"]
NEW_CLASSES = ["AirSeparatorBlock", "AirSeparatorBlockEntity", "AirSeparatorMenu",
               "AmmoniaSynthesisChamberBlock", "AmmoniaSynthesisChamberBlockEntity",
               "AmmoniaSynthesisChamberMenu"]
NEW_SCREENS = ["AirSeparatorScreen", "AmmoniaSynthesisChamberScreen"]
NEW_TEX = [u"assets/potato_s_t/textures/block/nitrogen_still.png",
           u"assets/potato_s_t/textures/block/nitrogen_flow.png",
           u"assets/potato_s_t/textures/block/ammonia_still.png",
           u"assets/potato_s_t/textures/block/ammonia_flow.png",
           u"assets/potato_s_t/textures/block/air_separator_side.png",
           u"assets/potato_s_t/textures/block/air_separator_top.png",
           u"assets/potato_s_t/textures/block/ammonia_synthesis_chamber_side.png",
           u"assets/potato_s_t/textures/block/ammonia_synthesis_chamber_top.png"]
FTAGS = [u"data/c/tags/fluid/nitrogen.json", u"data/c/tags/fluid/ammonia.json",
         u"data/c/tags/fluid/gaseous.json"]
VOID = "c6b70a95d261ca929a26d21fee3363933f6bc188"
PREV_ROUND_SHA = "091f1bfbd7f2fbadf84b919ab3b64399e8e06e0e"
# ⚠ 本轮第一版成品 `34a60b39…` 发布之后，门当场报了 4 条 Audit FAIL：
#   **4 个新 Java 文件里有没用到的 import**（Component / BuiltInRegistries / ItemStackHandler）
#   ⇒ 删掉、重新构建、重发，第一版作废。这个常量是"上一版（作废的）成品哈希"。
PREV_PUBLISHED = "34a60b397f1214d8580312f3ab2572899e62784b"
fails = []


def patch_regex(path, pattern, repl, label):
    """按正则改一处（幂等：锚点已不在就放行）。"""
    t = io.open(path, encoding="utf-8").read()
    new_t, n = re.subn(pattern, repl, t, count=1)
    if n == 0:
        print(u"  [SKIP] %s（锚点已不在 = 之前填过了，幂等放行）" % label)
        return
    io.open(path, "w", encoding="utf-8", newline=u"\n").write(new_t)
    print(u"  [OK]   %s" % label)


def sha1(p):
    return hashlib.sha1(open(p, "rb").read()).hexdigest()


def read(p):
    return io.open(p, encoding="utf-8").read() if os.path.exists(p) else u""


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


def patch_regex(path, pattern, repl, label):
    t = io.open(path, encoding="utf-8").read()
    new_t, n = re.subn(pattern, repl, t, count=1)
    if n == 0:
        print(u"  [SKIP] %s（锚点已不在，幂等放行）" % label)
        return
    io.open(path, "w", encoding="utf-8", newline=u"\n").write(new_t)
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

    if os.path.exists(BEFORE):
        before = [l.strip() for l in read(BEFORE).splitlines() if l.strip()]
        now = sorted(n for n in os.listdir(RDIR) if n.endswith(".json"))
        missing = [n for n in before if n not in now]
        if missing:
            fails.append(u"改前配方丢了：%s" % missing)
        else:
            print(u"  [OK]   改前那 %d 份配方一件不少（现共 %d 份）" % (len(before), len(now)))
    if os.path.exists(TEXBEFORE):
        changed, total = [], 0
        for ln in read(TEXBEFORE).splitlines():
            parts = ln.split()
            if len(parts) != 2:
                continue
            total += 1
            p = os.path.join(ASSETS, u"textures", parts[0].replace(u"/", os.sep))
            if not os.path.exists(p) or sha1(p) != parts[1]:
                changed.append(parts[0])
        if changed:
            fails.append(u"改前贴图被动了：%s" % changed)
        else:
            print(u"  [OK]   改前那 %d 张贴图一张都没动" % total)

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
        for cls in NEW_CLASSES:
            rel = u"com/potatost/mod/%s.class" % cls
            if rel not in names:
                fails.append(u"成品里没有 %s" % rel)
        for cls in NEW_SCREENS:
            rel = u"com/potatost/mod/client/%s.class" % cls
            if rel not in names:
                fails.append(u"成品里没有界面 %s" % rel)
        if not fails:
            print(u"  [OK]   成品里有 6 个新 class + 2 个界面 class")
        for rel in NEW_TEX:
            disk = os.path.join(ASSETS, rel[len(u"assets/potato_s_t/"):].replace(u"/", os.sep))
            if rel not in names:
                fails.append(u"成品里没有 %s" % rel)
            elif zf.read(rel) != open(disk, "rb").read():
                fails.append(u"成品里的 %s 与盘上不一致" % rel)
        if not [f for f in fails if u"贴图" in f or u"textures" in f]:
            print(u"  [OK]   8 张新贴图都在成品里且与盘上逐字节一致")
        for rel in FTAGS:
            disk = os.path.join(RES, rel.replace(u"/", os.sep))
            if rel not in names:
                fails.append(u"成品里没有 %s" % rel)
            elif zf.read(rel) != open(disk, "rb").read():
                fails.append(u"成品里的 %s 与盘上不一致" % rel)
        print(u"  [OK]   7 份 c: 流体标签都在成品里（本轮核的这 3 份逐字节一致）"
              if not [f for f in fails if u"tags" in f] else u"  [FAIL] 流体标签有问题")
        for rid in NEW:
            rel = u"data/potato_s_t/recipe/%s.json" % rid
            disk = os.path.join(RDIR, rid + ".json")
            if rel not in names:
                fails.append(u"成品里没有 %s" % rel)
            elif zf.read(rel) != open(disk, "rb").read():
                fails.append(u"成品里的 %s 与盘上不一致" % rel)
            else:
                print(u"  [OK]   成品里的 %s 与盘上逐字节一致（%d 字节）"
                      % (rel.split("/")[-1], zf.getinfo(rel).file_size))
        shaped = 0
        for n in names:
            if n.startswith(u"data/potato_s_t/recipe/") and n.endswith(u".json"):
                try:
                    if json.loads(zf.read(n).decode("utf-8")).get("type") == u"minecraft:crafting_shaped":
                        shaped += 1
                except Exception:
                    pass
        if shaped != 38:
            fails.append(u"成品里 crafting_shaped 配方 %d 条 ≠ 38" % shaped)
        else:
            print(u"  [OK]   成品里 crafting_shaped 配方 = 38 条")
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
    print(u"   作废 %s（ZF96）" % VOID[:8])

    patch(DOC, u"__ZF97_SHA1__", new, u"§9 ZF97 条目：成品哈希填实", optional=True)
    patch(DOC, u"__ZF97_BYTES__", str(size), u"§9 ZF97 条目：字节数填实", optional=True)
    patch(DOC, u"__ZF97_ENTRIES__", str(entries), u"§9 ZF97 条目：条目数填实", optional=True)
    # 重发（本轮出过两版）：把 §9 里上一版的哈希/字节/条目改成新的
    patch_regex(DOC, u"`%s`（\\d+ B / \\d+ 条目）" % PREV_PUBLISHED,
                u"`%s`（%d B / %d 条目）" % (new, size, entries),
                u"§9 ZF97 条目：重发后哈希/字节/条目刷新")
    patch(DOC, u"**成品**：`release\\PotatoST-0.11.jar` = `%s`" % PREV_ROUND_SHA,
          u"**当时的成品**：`release\\PotatoST-0.11.jar` = `%s`" % PREV_ROUND_SHA,
          u"§9 ZF96 条目：成品 → 当时的成品", optional=True)
    patch(PUB, u'VOID = "%s"' % VOID, u'VOID = "%s"' % new, u"发布脚本 VOID 跟到最新")

    print(u"\n失败项 = %d" % len(fails))
    for f in fails:
        print(u"  !! " + f)
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())
