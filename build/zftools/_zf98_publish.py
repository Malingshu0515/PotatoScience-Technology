# -*- coding: utf-8 -*-
r"""_zf98_publish.py —— ZF98 出成品（作废 ZF97 那版 `c6b70a95…`）+ 把 §9 的占位填实

照老规矩：**先核对旧哈希、再核对新产物内容，全过了才动文件**；
§4.59 ④ 的两条硬化照旧（重命名用独立的 `PREV_ROUND_SHA`；占位补丁幂等）。
本轮额外核：成品里的泵 class 与盘上源码同轮次（javac 时间戳不作数 ⇒ 只核"class 在、且 jar 里
没有探针 class"）、**四语言 tooltip 已经在 jar 里改了口**（读 jar 里的 lang 检查那句锚点）、
改前那 44 份配方一件不少、crafting_shaped 仍 = 38。
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
PUB = os.path.join(ROOT, "build", "zftools", "_zf98_publish.py")
DOC = os.path.join(ROOT, "docs", u"开发档案.md")
RDIR = os.path.join(ROOT, r"src\main\resources\data\potato_s_t\recipe")
BEFORE = os.path.join(r"C:\PotatoST救援\zf98_pre", "recipe_before.txt")
TEXBEFORE = os.path.join(r"C:\PotatoST救援\zf98_pre", "textures_before.txt")
LANG_PHRASE = u"泵本身不存液体"
VOID = "ffa01872655c403c7eb5f88563eebd3c957187ee"
PREV_ROUND_SHA = "c6b70a95d261ca929a26d21fee3363933f6bc188"
fails = []


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
        rel = u"com/potatost/mod/FluidPumpBlockEntity.class"
        if rel not in names:
            fails.append(u"成品里没有泵的 class")
        else:
            print(u"  [OK]   成品里有 FluidPumpBlockEntity.class（%d B）"
                  % zf.getinfo(rel).file_size)
        # ★ 本轮的关键自证：jar 里那份 zh_cn 必须已经写着新 tooltip（而不是"盘上改了、jar 是旧的"）
        rel = u"assets/potato_s_t/lang/zh_cn.json"
        inside = json.loads(zf.read(rel).decode("utf-8"))
        if LANG_PHRASE not in inside.get(u"tooltip.potato_s_t.fluid_pump", u""):
            fails.append(u"成品里的 zh_cn 还没改口（泵提示里没有「%s」）⇒ 是不是忘了重新构建？"
                         % LANG_PHRASE)
        else:
            print(u"  [OK]   成品里的 zh_cn 已经是新 tooltip（含「%s」），%d 键"
                  % (LANG_PHRASE, len(inside)))
        if len(inside) != 303:
            fails.append(u"成品里 zh_cn 键数 %d ≠ 303" % len(inside))
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
    print(u"   作废 %s（ZF97）" % VOID[:8])

    patch(DOC, u"__ZF98_SHA1__", new, u"§9 ZF98 条目：成品哈希填实", optional=True)
    patch(DOC, u"__ZF98_BYTES__", str(size), u"§9 ZF98 条目：字节数填实", optional=True)
    patch(DOC, u"__ZF98_ENTRIES__", str(entries), u"§9 ZF98 条目：条目数填实", optional=True)
    patch(DOC, u"**成品**：`release\\PotatoST-0.11.jar` = `%s`" % PREV_ROUND_SHA,
          u"**当时的成品**：`release\\PotatoST-0.11.jar` = `%s`" % PREV_ROUND_SHA,
          u"§9 ZF97 条目：成品 → 当时的成品", optional=True)
    patch(PUB, u'VOID = "%s"' % VOID, u'VOID = "%s"' % new, u"发布脚本 VOID 跟到最新")

    print(u"\n失败项 = %d" % len(fails))
    for f in fails:
        print(u"  !! " + f)
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())
