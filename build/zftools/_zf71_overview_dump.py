# -*- coding: utf-8 -*-
"""_zf71_overview_dump.py —— 把"这个 mod 现在有什么"从**项目文件里**挖出来

给英文更新公告用。**不靠记忆**：物品/方块名字取 en_us.json，机器数值从 java 常量里抓，
配方/进度/矿石从 data/ 目录数。公告里每个数字都必须能在这里找到出处。
"""
import io
import json
import os
import re
import sys

PROJ = r"E:\PotatoST"
RES = os.path.join(PROJ, r"src\main\resources")
JAVA = os.path.join(PROJ, r"src\main\java\com\potatost\mod")
LANG = os.path.join(RES, r"assets\potato_s_t\lang\en_us.json")


def read(p, enc="utf-8"):
    with io.open(p, encoding=enc) as fh:
        return fh.read()


def main():
    lang = json.loads(read(LANG))
    items = sorted((k[len("item.potato_s_t."):], v) for k, v in lang.items() if k.startswith("item.potato_s_t."))
    blocks = sorted((k[len("block.potato_s_t."):], v) for k, v in lang.items() if k.startswith("block.potato_s_t."))

    print(u"===== 物品 %d 个 =====" % len(items))
    for k, v in items:
        print(u"  %-34s %s" % (k, v))
    print(u"===== 方块 %d 个 =====" % len(blocks))
    for k, v in blocks:
        print(u"  %-34s %s" % (k, v))

    print(u"===== 机器数值（从 java 里抓常量）=====")
    for fn in sorted(os.listdir(JAVA)):
        if not fn.endswith("BlockEntity.java"):
            continue
        t = read(os.path.join(JAVA, fn))
        hits = []
        for pat in (r"MAX_ENERGY\s*=\s*([0-9_]+)", r"ENERGY_PER_TICK\s*=\s*([0-9_]+)",
                    r"DURATION_TICKS\s*=\s*([0-9_]+)", r"ENERGY_PER_ITEM\s*=\s*([0-9_]+)",
                    r"ENERGY_CAPACITY\s*=\s*([0-9_]+)"):
            for m in re.finditer(pat, t):
                hits.append(pat.split(r"\s")[0] + "=" + m.group(1))
        if hits:
            print(u"  %-42s %s" % (fn, ", ".join(hits)))

    print(u"===== 配方 =====")
    rdir = os.path.join(RES, r"data\potato_s_t\recipe")
    kinds = {}
    for n in sorted(os.listdir(rdir)):
        d = json.loads(read(os.path.join(rdir, n)))
        t = d.get("type", "?").replace("minecraft:", "")
        kinds.setdefault(t, []).append((n[:-5], d.get("result", {}).get("id", "?")))
    for t in sorted(kinds):
        print(u"  %s: %d" % (t, len(kinds[t])))
        for n, r in kinds[t]:
            print(u"      %-34s -> %s" % (n, r))

    print(u"===== 进度 =====")
    adir = os.path.join(RES, r"data\potato_s_t\advancement")
    for n in sorted(os.listdir(adir)):
        d = json.loads(read(os.path.join(adir, n)))
        key = d["display"]["title"]["translate"]
        print(u"  %-24s %s   (icon %s)" % (n[:-5], lang.get(key, "?"), d["display"]["icon"]["id"]))

    print(u"===== 世界生成 =====")
    for sub in ("configured_feature", "placed_feature"):
        d = os.path.join(RES, r"data\potato_s_t\worldgen", sub)
        if os.path.isdir(d):
            print(u"  %s: %s" % (sub, ", ".join(sorted(x[:-5] for x in os.listdir(d)))))

    print(u"===== 音效/唱片/流体/标签 =====")
    sj = json.loads(read(os.path.join(RES, r"assets\potato_s_t\sounds.json")))
    print(u"  sounds.json 键 %d: %s" % (len(sj), ", ".join(sorted(sj))))
    for p in (r"data\potato_s_t\jukebox_song", r"data\potato_s_t\tags\item"):
        d = os.path.join(RES, p)
        if os.path.isdir(d):
            print(u"  %s: %s" % (p, ", ".join(sorted(x[:-5] for x in os.listdir(d)))))
    print(u"  贴图 %d 张" % sum(1 for dp, dn, fns in os.walk(os.path.join(RES, r"assets\potato_s_t\textures"))
                              for f in fns if f.endswith(".png")))
    print(u"  语言键 %d（%s）" % (len(lang), os.path.basename(LANG)))
    print(u"  lang 键总数: %s" % ", ".join(
        "%s=%d" % (f[:-5], len(json.loads(read(os.path.join(RES, r"assets\potato_s_t\lang", f)))))
        for f in sorted(os.listdir(os.path.join(RES, r"assets\potato_s_t\lang")))))
    return 0


if __name__ == "__main__":
    sys.exit(main())
