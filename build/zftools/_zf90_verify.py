# -*- coding: utf-8 -*-
u"""_zf90_verify.py —— ZF90 常驻校验：四块板改用铁板贴图 + 通用 plate.png 已删 + 三个工具雷已修

分区：
  A 五个模型指向（银/铝/镍/钴 → iron_plate；铁/钢/铜 不动）+ 全量"引用的贴图必须存在"
  B 通用 plate.png 已删、可还原（改前件在）、全仓再无 `item/plate` 引用
  C 三个工具雷已修（TextureCheck 的清单表用真文件名 / `--plan` 保留手写小节 / 备份脚本重跑会中止）
  D 文档、E 成品 jar
"""
import hashlib
import io
import json
import os
import re
import struct
import sys
import zipfile

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import _zf66_png  # noqa: E402

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

ROOT = r"E:\PotatoST"
ASSETS = os.path.join(ROOT, r"src\main\resources\assets\potato_s_t")
MODELI = os.path.join(ASSETS, "models", "item")
TEXI = os.path.join(ASSETS, "textures", "item")
USERART = os.path.join(ROOT, "build", u"用户素材")
DOCS = os.path.join(ROOT, "docs")
TOOLS = os.path.join(ROOT, "build", "zftools")
JAR = os.path.join(ROOT, "release", "PotatoST-0.11.jar")


def _pixels(p):
    w, h, ctype, px = _zf66_png.read_png(p)
    return [q if len(q) == 4 else (q[0], q[1], q[2], 255) for q in px]

BK = r"C:\PotatoST救援\zf90_pre"
BK_PLATE = os.path.join(BK, r"src\main\resources\assets\potato_s_t\textures\item\plate.png")
PLATE_OLD_SHA1 = u"a28b0654"          # 通用 plate.png 的前 8 位（改前件与 ZF83 校验里都记着）
FOUR = [u"silver_plate", u"aluminum_plate", u"nickel_plate", u"cobalt_plate"]
THREE = [u"iron_plate", u"steel_plate", u"copper_plate"]

passed = 0
failed = 0
fails = []


def check(label, cond):
    global passed, failed
    if cond:
        passed += 1
        print(u"  [OK]   " + label)
    else:
        failed += 1
        fails.append(label)
        print(u"  [FAIL] " + label)


def eq(label, want, got):
    check(u"%s（期望 %r，实际 %r）" % (label, want, got), want == got)


def read(p):
    return io.open(p, encoding="utf-8").read() if os.path.exists(p) else None


def sha1f(p):
    return hashlib.sha1(open(p, "rb").read()).hexdigest()


def layer0(name):
    t = read(os.path.join(MODELI, name + u".json"))
    if t is None:
        return None
    try:
        return json.loads(t).get("textures", {}).get("layer0")
    except Exception:
        return u"(JSON 坏了)"


def main():
    print(u"=========== ZF90 校验：其它锭板子一律用铁板那张 ===========")
    print(u"\n== A 五个模型指向 ==")
    for name in FOUR:
        p = os.path.join(MODELI, name + u".json")
        check(u"%s.json 在" % name, os.path.exists(p))
        eq(u"%s.json 的 layer0 = iron_plate" % name,
           u"potato_s_t:item/iron_plate", layer0(name))
        t = read(p) or u""
        check(u"%s.json 的 parent 仍是 item/generated" % name,
              u"minecraft:item/generated" in t)
    for name in THREE:
        eq(u"%s.json 仍指向自己的图（没被这轮误改）" % name,
           u"potato_s_t:item/" + name, layer0(name))

    # 全量扫描：每个 item 模型引用的 potato_s_t:item/* 贴图必须真的存在（孤儿引用=紫黑块）
    missing = []
    for n in sorted(os.listdir(MODELI)):
        if not n.endswith(u".json"):
            continue
        t = read(os.path.join(MODELI, n)) or u""
        for m in re.finditer(r"potato_s_t:item/([a-z0-9_/]+)", t):
            f = m.group(1).split(u"/")[-1] + u".png"
            if not os.path.exists(os.path.join(TEXI, f)):
                missing.append((n, f))
    check(u"每个物品模型引用的贴图都真的存在（缺：%s）" % (missing or u"无"), not missing)

    print(u"\n== B 通用 plate.png 已删、可还原 ==")
    check(u"textures/item/plate.png 已不存在", not os.path.exists(os.path.join(TEXI, u"plate.png")))
    check(u"改前件里那份 plate.png 还在（可还原）", os.path.exists(BK_PLATE))
    if os.path.exists(BK_PLATE):
        h = sha1f(BK_PLATE)
        check(u"改前件那份就是原来那张（sha1 %s…）" % PLATE_OLD_SHA1, h.startswith(PLATE_OLD_SHA1))
    left = sorted(n for n in os.listdir(TEXI) if u"plate" in n)
    eq(u"textures/item 里的板现在正好三张", [u"copper_plate.png", u"iron_plate.png", u"steel_plate.png"], left)
    # 全仓再无 item/plate 引用（模型 / 方块状态 / 任何 json）
    refs = []
    for dp, dn, fn in os.walk(os.path.join(ROOT, "src", "main", "resources")):
        for f in fn:
            if not f.endswith(u".json"):
                continue
            p = os.path.join(dp, f)
            t = io.open(p, encoding="utf-8", errors="replace").read()
            if u"potato_s_t:item/plate" + u"\"" in t or u"potato_s_t:item/plate" + u"}" in t:
                refs.append(os.path.relpath(p, ROOT))
    check(u"全仓再没有任何地方引用 item/plate（%s）" % (refs or u"无"), not refs)

    print(u"\n== C 三个工具雷已修 ==")
    tc = read(os.path.join(TOOLS, u"TextureCheck.py")) or u""
    check(u"清单表改成打印模型**真正引用**的贴图（不再拿模型名拼 .png）",
          u"paths = sorted(set(r.split" in tc and u"model名" not in tc)
    check(u"`--plan` 会把 `---` 之后的手写小节原样接回",
          u'mark = u"\\n---\\n\\n## ZF"' in tc)
    bk = read(os.path.join(TOOLS, u"_zf90_backup.py")) or u""
    check(u"备份脚本根已存在时**直接中止**（不再往下覆盖）",
          u"备份根已存在" in bk and u"return 1" in bk)
    listing = read(os.path.join(DOCS, u"贴图清单.md")) or u""
    secs = [l for l in listing.split(u"\n") if l.startswith(u"## ZF")]
    check(u"贴图清单里各轮手写小节还在（%d 个）" % len(secs), len(secs) >= 10)
    check(u"贴图清单里没有那四个不存在的文件了（aluminum/cobalt/nickel/silver_plate.png）",
          not any(u"`%s.png`" % n in listing for n in FOUR))

    print(u"\n== D 文档 ==")
    arch = read(os.path.join(DOCS, u"开发档案.md")) or u""
    check(u"档案里有 ZF90 那一行", u"| ZF90 |" in arch)
    check(u"档案里有 §4.59（三个静默吃掉内容的写法）", u"### 4.59" in arch)
    check(u"档案里写了 plate.png 的旧 sha1（可追溯）", PLATE_OLD_SHA1 in arch)
    check(u"贴图清单里有 ZF90 一节", u"## ZF90（0.11）" in listing)

    print(u"\n== F 两个桶拿回自己的图（本轮中途用户又放的）==")
    for item_name, zh in ((u"diesel_bucket", u"柴油桶"), (u"gasoline_bucket", u"汽油桶")):
        t = os.path.join(TEXI, item_name + u".png")
        check(u"textures/item/%s.png 在（%s）" % (item_name, zh), os.path.exists(t))
        if os.path.exists(t):
            b = open(t, "rb").read()
            w, h = struct.unpack(">II", b[16:24])
            eq(u"%s.png 16×16 / 8 位 / RGBA" % item_name, (16, 16, 8, 6), (w, h, b[24], b[25]))
            keep = os.path.join(USERART, item_name + u".png")
            check(u"留档原图在（build/用户素材/%s.png）" % item_name, os.path.exists(keep))
            if os.path.exists(keep):
                check(u"%s 盘上成品与留档原图**逐像素一致**" % item_name, _pixels(keep) == _pixels(t))
        eq(u"%s.json 的 layer0 指向自己的图" % item_name,
           u"potato_s_t:item/" + item_name, layer0(item_name))
        check(u"%s.json 不再借原版水桶" % item_name,
              u"minecraft:item/water_bucket" not in (read(os.path.join(MODELI, item_name + u".json")) or u""))
    check(u"中文名源文件 柴油桶_001.png / 汽油桶.png 都已被挪走",
          not os.path.exists(os.path.join(TEXI, u"柴油桶_001.png"))
          and not os.path.exists(os.path.join(TEXI, u"汽油桶.png")))
    # 活体数字：借原版贴图的模型 7 → 6 → **5**（ZF90 当时的真相）；
    # ⚠ ZF104/105/106（盔甲线）又加进来 8 件盔甲模型 + 硬质钛合金 ⇒ **5 → 13**
    #   ⇒ 公告与第 8 道门（`_zf71_verify.py`）必须**同时**是 13（两边一起改，别只改一边）；
    #   **ZF110** 星璨钢头盔拿到自己的背包图标 ⇒ **13 → 12**（这三处一起改）
    ann = read(os.path.join(DOCS, u"UpdateAnnouncement_EN.md")) or u""
    check(u"英文公告已改成 12 models still do this", u"12 models still do this" in ann)
    check(u"英文公告里不再写 5/6/7/13 models", not any(u"%d models still do this" % n in ann
                                                     for n in (5, 6, 7, 13)))
    z71 = read(os.path.join(TOOLS, u"_zf71_verify.py")) or u""
    check(u"`_zf71_verify.py` 的期望值同步成 12", u"n_draw == 12" in z71)
    listing = read(os.path.join(DOCS, u"贴图清单.md")) or u""
    # ZF110 重跑过 `TextureCheck.py --plan` ⇒ 表头跟着活体数字走（现在 12 个）
    check(u"贴图清单的待画表头已变 12 个", u"## 待画（12 个" in listing)
    for item_name in (u"diesel_bucket", u"gasoline_bucket"):
        check(u"贴图清单的「已有」表里出现 %s.png" % item_name,
              (u"`%s.png`" % item_name) in listing)

    print(u"\n== G 铜板第二版（用户重导出）==")
    cp = os.path.join(TEXI, u"copper_plate.png")
    cp_keep = os.path.join(USERART, u"copper_plate_v2.png")
    check(u"留档原图在（build/用户素材/copper_plate_v2.png）", os.path.exists(cp_keep))
    if os.path.exists(cp) and os.path.exists(cp_keep):
        check(u"盘上铜板与留档 v2 **逐像素一致**", _pixels(cp) == _pixels(cp_keep))
        b = open(cp, "rb").read()
        w, h = struct.unpack(">II", b[16:24])
        eq(u"copper_plate.png 16×16 / 8 位 / RGBA", (16, 16, 8, 6), (w, h, b[24], b[25]))
    prov = json.loads(read(os.path.join(USERART, u"_来源凭据.json")) or u"{}")
    for key in (u"diesel_bucket.png", u"gasoline_bucket.png", u"copper_plate_v2.png"):
        e = prov.get(key)
        check(u"来源凭据里有 %s" % key, isinstance(e, dict))
        if isinstance(e, dict):
            eq(u"凭据里 %s 的 sha1 与实际文件一致" % key,
               sha1f(os.path.join(USERART, key)), e.get("sha1"))
    # 旧那版铜板（929 B）必须还取得到（在 zf90_pre 自带的成品 jar 里）
    old_jar = os.path.join(BK, r"release\PotatoST-0.11.jar")
    check(u"改前成品 jar 在（旧的铜板图可从它取回）", os.path.exists(old_jar))
    if os.path.exists(old_jar):
        with zipfile.ZipFile(old_jar) as zf:
            e = u"assets/potato_s_t/textures/item/copper_plate.png"
            old = zf.read(e) if e in zf.namelist() else None
        check(u"改前 jar 里的铜板是**上一版**（929 字节那版，与现盘上不同）",
              old is not None and old != open(cp, "rb").read())

    print(u"\n== E 成品 jar ==")
    if not os.path.exists(JAR):
        check(u"成品 jar 存在", False)
    else:
        sha = sha1f(JAR)
        rec = read(JAR + u".sha1")
        check(u".sha1 与 jar 一致（%s…）" % sha[:8], rec is not None and rec.strip().lower() == sha)
        with zipfile.ZipFile(JAR) as zf:
            names = zf.namelist()
            bad = [n for n in names if u"Check" in n.split(u"/")[-1] and n.endswith(u".class")]
            check(u"成品里没有探针 class（%s）" % (bad or u"0 个"), not bad)
            entry = u"assets/potato_s_t/textures/item/plate.png"
            check(u"成品里**没有** plate.png 条目", entry not in names)
            # ⚠ 本轮真踩过的坑：用户中途丢进来的 `汽油桶.png`（中文名）**被第一次打包打进了 jar**
            #   （§4.24 违规、游戏会报错）。源目录的中文名检查挡不住"检查之后、打包之前"才落盘的文件，
            #   所以这里补一条**成品侧**的断言：assets/ 与 data/ 下的条目名必须全是
            #   `[a-z0-9/._-]`（ResourceLocation 的字符集）。
            evil = [n for n in names
                    if (n.startswith(u"assets/") or n.startswith(u"data/"))
                    and not re.fullmatch(u"[a-z0-9/._-]+", n)]
            check(u"成品里 assets/ 与 data/ 的条目名全合法（越界：%s）" % (evil[:5] or u"无"), not evil)
            ip = u"assets/potato_s_t/textures/item/iron_plate.png"
            check(u"成品里的 iron_plate.png 与盘上一致",
                  ip in names and zf.read(ip) == open(os.path.join(TEXI, u"iron_plate.png"), "rb").read())
            for name in FOUR + THREE:
                e = u"assets/potato_s_t/models/item/%s.json" % name
                inside = zf.read(e).decode("utf-8") if e in names else u""
                want = u"potato_s_t:item/iron_plate" if name in FOUR else u"potato_s_t:item/" + name
                check(u"成品里的 %s.json 指向 %s" % (name, want.split(u"/")[-1]), want in inside)
            # 两个桶：成品里也要指向自己的图，且贴图条目与盘上一致
            for item_name in (u"diesel_bucket", u"gasoline_bucket"):
                e = u"assets/potato_s_t/models/item/%s.json" % item_name
                inside = zf.read(e).decode("utf-8") if e in names else u""
                check(u"成品里的 %s.json 指向自己的图" % item_name,
                      (u"potato_s_t:item/" + item_name) in inside)
            for nm in (u"diesel_bucket.png", u"gasoline_bucket.png", u"copper_plate.png"):
                e = u"assets/potato_s_t/textures/item/" + nm
                check(u"成品里的 %s 与盘上一致" % nm,
                      e in names and zf.read(e) == open(os.path.join(TEXI, nm), "rb").read())

    print(u"\n== H 文档与产物一致性（§4.59 ④ 的常驻保险）==")
    rel_sha = (read(JAR + u".sha1") or u"").strip().lower()
    arch = read(os.path.join(DOCS, u"开发档案.md")) or u""
    # 取 §9 里**最后一个**"**成品**"行（= 最新那一轮），它必须与 release 的 .sha1 一致
    last = None
    for l in arch.split(u"\n"):
        if l.startswith(u"**成品**：") and u"PotatoST-0.11.jar" in l:
            last = l
    check(u"§9 里有「**成品**」那一行", last is not None)
    if last:
        m = re.search(r"`([0-9a-f]{40})`", last)
        got = m.group(1) if m else u"(没读到哈希)"
        check(u"最新「**成品**」行的哈希 == release\\PotatoST-0.11.jar.sha1（文档 %s… / 盘上 %s…）"
              % (got[:8], rel_sha[:8]), got == rel_sha)
        check(u"最新「**成品**」行不是「当时的成品」（同一轮重跑把它标错的坑）",
              not last.startswith(u"**当时的成品**"))

    print(u"\n------------------------------")
    print(u"通过 = %d   失败 = %d" % (passed, failed))
    for f in fails:
        print(u"  !! " + f)
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
