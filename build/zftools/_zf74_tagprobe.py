# -*- coding: utf-8 -*-
u"""_zf74_tagprobe.py —— 只读取证：① 本工程有没有流体标签 ② 上游/别的 mod 用什么流体标签名

三路取证：
  A. 本工程 `data/**/tags/fluid/**` 有没有东西（预期：一个都没有）；
  B. NeoForge 21.1.235 自己带了哪些**通用流体标签**：
     · `Tags.java` 里 `Tags.Fluids` 的常量名；
     · neoforge jar 里 `data/c/tags/fluid/*.json`（上游用数据包形式声明的 c: 标签）；
  C. 机器上真实存在的别的 mod 的 jar 里，`data/*/tags/fluid/*.json` 有没有
     oxygen / hydrogen / chlorine / oil / gas 之类 —— 这决定"我们挂什么名字才真的通用"。
"""
import glob
import io
import os
import re
import sys
import zipfile

PROJ = r"E:\PotatoST"
GRADLE = r"E:\gradle-home"
MODS_DIRS = [
    os.path.join(PROJ, u"run", u"client", u"mods"),
    r"E:\game\pcl快照\.minecraft\versions\存档\mods",
]

NEEDLES = (u"oxygen", u"hydrogen", u"chlorine", u"crude_oil", u"oil", u"gas")


def find(patterns):
    hits = []
    for p in patterns:
        hits.extend(glob.glob(p, recursive=True))
    hits = [h for h in hits if os.path.isfile(h)]
    hits.sort(key=lambda p: os.path.getmtime(p), reverse=True)
    return hits[0] if hits else None


def part_a():
    print(u"===== A. 本工程的流体标签 =====")
    root = os.path.join(PROJ, u"src", u"main", u"resources", u"data")
    found = []
    for dp, _dn, fn in os.walk(root):
        if u"tags" in dp:
            for f in fn:
                found.append(os.path.relpath(os.path.join(dp, f), root))
    print(u"  data/ 下 tags 文件共 %d 个：" % len(found))
    for f in sorted(found):
        print(u"    %s" % f)
    fluid_tags = [f for f in found if u"fluid" in f.replace(u"\\", u"/").lower()]
    print(u"  其中 **流体** 标签 = %d 个" % len(fluid_tags))


def part_b():
    print(u"\n===== B. NeoForge 21.1.235 自带的通用流体标签 =====")
    src = find([os.path.join(GRADLE, u"**", u"neoforge-*-sources.jar")])
    uni = find([os.path.join(GRADLE, u"**", u"neoforge-*-universal.jar")])
    if src:
        with zipfile.ZipFile(src) as zf:
            text = zf.read(u"net/neoforged/neoforge/common/Tags.java").decode(u"utf-8", u"replace")
        m = re.search(r"class Fluids\s*\{(.*?)\n    \}", text, re.S)
        body = m.group(1) if m else u""
        names = re.findall(r'TagKey<Fluid>\s+([A-Z_0-9]+)\s*=\s*create\("([^"]+)"', body)
        print(u"  Tags.Fluids 常量 %d 个：" % len(names))
        for const, path in names:
            mark = u"  <== 命中" if any(n in path.lower() for n in NEEDLES) else u""
            print(u"    %-22s c:%s%s" % (const, path, mark))
    if uni:
        print(u"  上游 jar 里 data/c/tags/fluid/ 条目：")
        with zipfile.ZipFile(uni) as zf:
            ent = [n for n in zf.namelist() if u"/tags/fluid/" in n and n.startswith(u"data/")]
        if not ent:
            print(u"    （没有：上游只用 java 常量声明 c: 标签，不附带 json）")
        for n in sorted(ent):
            print(u"    %s" % n)


def part_c():
    print(u"\n===== C. 本机别的 mod 怎么挂流体标签 =====")
    jars = []
    for d in MODS_DIRS:
        if os.path.isdir(d):
            jars.extend(sorted(glob.glob(os.path.join(d, u"*.jar"))))
    print(u"  扫描 mod jar：%d 个" % len(jars))
    hits = 0
    for jar in jars:
        try:
            with zipfile.ZipFile(jar) as zf:
                names = [n for n in zf.namelist()
                         if n.startswith(u"data/") and u"/tags/fluid/" in n]
                keep = [n for n in names if any(k in n.lower() for k in NEEDLES)]
                if not keep:
                    continue
                print(u"  --- %s" % os.path.basename(jar))
                for n in sorted(keep)[:12]:
                    try:
                        payload = zf.read(n).decode(u"utf-8", u"replace")
                    except Exception:
                        payload = u"(读不出)"
                    values = re.findall(r'"([^"]+)"', payload)
                    print(u"      %s -> %s" % (n, u", ".join(values[:6])))
                    hits += 1
        except Exception:
            continue
    print(u"  命中条目 = %d" % hits)
    if hits == 0:
        print(u"  （本机没有可供对照的、带气体/油类流体标签的 mod）")


def main():
    part_a()
    part_b()
    part_c()
    return 0


if __name__ == "__main__":
    sys.exit(main())
