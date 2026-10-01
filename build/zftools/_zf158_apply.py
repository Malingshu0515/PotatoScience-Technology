# -*- coding: utf-8 -*-
u"""_zf158_apply.py —— ZF158 落地（幂等，默认 dry-run）：

  ① **生成器表跟平**：`_zf45_recipes.py` 里 13 行 15 处 `("item", "potato_s_t:<金属>_plate")`
     → `("tag", "c:plates/<金属>")`。
     为什么非改不可：那张表自称是这 35 份 JSON 的**唯一来源**（改配方改表再 `--write`），
     而 ZF156 把**盘上的** 29 处原料改成了标签、**没动表** ⇒ 谁跑一次 `--write` 就把上一轮 revert 了。
  ② **热力金属换图纸**（用户原话：「热力金属改成铜板夹银锭（铜板银锭互相调换一下位置）」）：
     表里 `pattern=["SSS","CCC","SSS"]` → `["CCC","SSS","CCC"]`（C=铜板、S=银锭），
     即外圈由银锭换成铜板、中行由铜板换成银锭。
  ③ 跑 `_zf45_recipes.py --write` 让**生成器**重出 JSON —— 顺便当"表 == 盘"的机器证明：
     改完表之后重出，除了 thermal_metal **一份都不该变**（变了就说明表与盘还有别处不一致）。

跑法：python build\\zftools\\_zf158_apply.py [--write]
"""
import hashlib
import io
import os
import re
import subprocess
import sys

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding=u"utf-8", errors="replace")

ROOT = r"E:\PotatoST"
ZT = os.path.join(ROOT, "build", "zftools")
GEN = os.path.join(ZT, u"_zf45_recipes.py")
RECIPE = os.path.join(ROOT, r"src\main\resources\data\potato_s_t\recipe")
METALS = [u"aluminum", u"cobalt", u"copper", u"iron", u"nickel", u"silver", u"steel"]
PLATE_PAT = re.compile(u'"item", "potato_s_t:(' + u"|".join(METALS) + u')_plate"')

THERMAL_OLD = (u"    # \u3010\u94f6\u952d\u3011\u00d73 / \u3010\u94dc\u677f\u3011\u00d73 / \u3010\u94f6\u952d\u3011\u00d73 "
               u"\u2192 \u70ed\u529b\u91d1\u5c5e\n"
               u"    dict(name=\"thermal_metal\", category=\"misc\", "
               u"result=(\"potato_s_t:thermal_metal\", 1),\n"
               u"         pattern=[\"SSS\", \"CCC\", \"SSS\"],")
THERMAL_NEW = (u"    # \u3010\u94dc\u677f\u3011\u00d73 / \u3010\u94f6\u952d\u3011\u00d73 / \u3010\u94dc\u677f\u3011\u00d73 "
               u"\u2192 \u70ed\u529b\u91d1\u5c5e\n"
               u"    # \u26a0 0.13 ZF158\uff1a\u7528\u6237\u539f\u8bdd\u300c\u70ed\u529b\u91d1\u5c5e\u6539\u6210\u94dc\u677f\u5939\u94f6\u952d"
               u"\uff08\u94dc\u677f\u94f6\u952d\u4e92\u76f8\u8c03\u6362\u4e00\u4e0b\u4f4d\u7f6e\uff09\u300d"
               u"\u2014\u2014\u4e0e\u65e7\u56fe\u7eb8\u4e92\u4e3a\u4e0a\u4e0b\u98a0\u5012\u3002\n"
               u"    dict(name=\"thermal_metal\", category=\"misc\", "
               u"result=(\"potato_s_t:thermal_metal\", 1),\n"
               u"         pattern=[\"CCC\", \"SSS\", \"CCC\"],")


def sha(p):
    return hashlib.sha1(open(p, "rb").read()).hexdigest()


def snap():
    out = {}
    for dirpath, _d, filenames in os.walk(RECIPE):
        for fn in filenames:
            p = os.path.join(dirpath, fn)
            out[os.path.relpath(p, RECIPE)] = sha(p)
    return out


def main(argv):
    write = u"--write" in argv
    gen = io.open(GEN, encoding="utf-8", newline=u"").read()
    hits = PLATE_PAT.findall(gen)
    print(u"① 生成器表里「自家板当物品」%d 处：%s" % (len(hits), u", ".join(sorted(set(hits)))))

    gen2 = PLATE_PAT.sub(lambda m: u'"tag", "c:plates/%s"' % m.group(1), gen)
    if gen2 == gen:
        print(u"   （已经跟平过了，幂等）")
    if THERMAL_OLD in gen2:
        gen2 = gen2.replace(THERMAL_OLD, THERMAL_NEW, 1)
        print(u"② 热力金属：pattern [\"SSS\",\"CCC\",\"SSS\"] → [\"CCC\",\"SSS\",\"CCC\"]")
    elif THERMAL_NEW in gen2:
        print(u"② 热力金属（已经是铜板夹银锭，幂等）")
    else:
        print(u"!! 热力金属那条的锚点没找到 —— 停手")
        return 2

    if not write:
        print(u"（没加 --write：只算不写）")
        return 0

    before = snap()
    io.open(GEN, u"w", encoding="utf-8", newline=u"").write(gen2)
    print(u"   已写 _zf45_recipes.py")

    print(u"③ 跑生成器 --write（表是唯一来源，顺便证明表与盘一致）")
    r = subprocess.run([sys.executable, GEN, u"--write"], cwd=ROOT,
                       stdout=subprocess.PIPE, stderr=subprocess.STDOUT, timeout=600)
    out = r.stdout.decode("utf-8", "replace")
    print(u"   rc=%d" % r.returncode)
    tail = [l for l in out.split(u"\n") if u"定形配方" in l or u"失败项" in l]
    for l in tail:
        print(u"   " + l.strip())
    if r.returncode != 0:
        for l in out.split(u"\n"):
            if u"FAIL" in l:
                print(u"   " + l.strip()[:140])
        return 1

    after = snap()
    changed = sorted(k for k in set(before) | set(after)
                     if before.get(k) != after.get(k))
    print(u"④ 重出之后变了的文件 %d 份：%s" % (len(changed), u", ".join(changed)))
    extra = [c for c in changed if c != u"thermal_metal.json"]
    if extra:
        print(u"!! 除了 thermal_metal 还有别的文件被重出改动了（说明表与盘还有别处不一致）：")
        for e in extra[:10]:
            print(u"   " + e)
        return 1
    if changed != [u"thermal_metal.json"]:
        print(u"!! 预期正好改掉 thermal_metal.json 一份，实际 %s" % changed)
        return 1

    print(u"⑤ 新图纸：")
    print(io.open(os.path.join(RECIPE, u"thermal_metal.json"), encoding="utf-8").read())
    return 0


if __name__ == u"__main__":
    sys.exit(main(sys.argv[1:]))
