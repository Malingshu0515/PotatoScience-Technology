# -*- coding: utf-8 -*-
u"""_zf148_recon3.py —— ZF148 侦察③：帕秋莉的 en_us 回退证据 + 本 mod 的真实进度骨架。

只读。输出 UTF-8。
"""
import io, json, os, re, sys, zipfile

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding=u"utf-8", errors=u"replace")
JAR = r"E:\PotatoST\libs\Patchouli-1.21.1-93-NEOFORGE.jar"
ADV = r"E:\PotatoST\src\main\resources\data\potato_s_t\advancement"
LANG = r"E:\PotatoST\src\main\resources\assets\potato_s_t\lang\zh_cn.json"


def pr(s=u""):
    print(s)


z = zipfile.ZipFile(JAR)

pr(u"================ ① 帕秋莉里的 en_us / fallback 证据 ================")
for n in z.namelist():
    if not n.endswith(u".class"):
        continue
    raw = z.read(n)
    if b"en_us" in raw or b"fallback" in raw.lower():
        ss = set()
        for m in re.finditer(rb"[ -~]{3,}", raw):
            s = m.group().decode(u"ascii")
            if u"en_us" in s or u"fallback" in s.lower() or u"Lang" in s or u"lang" in s:
                ss.add(s)
        if ss:
            pr(u"  %s -> %s" % (n, sorted(ss)[:12]))

pr()
pr(u"================ ② 加载器里和语言目录有关的常量串 ================")
for cls in (u"vazkii/patchouli/client/book/BookContentResourceListenerLoader.class",
            u"vazkii/patchouli/client/book/BookContentResourceDirectLoader.class",
            u"vazkii/patchouli/client/book/BookContentsBuilder.class"):
    pr(u"---- %s ----" % cls)
    raw = z.read(cls)
    ss = []
    for m in re.finditer(rb"[ -~]{4,}", raw):
        s = m.group().decode(u"ascii")
        if (u"/" in s or u"." in s) and u"(" not in s and u";" not in s and u"Lnet" not in s:
            ss.append(s)
    for s in ss:
        pr(u"    " + s)
z.close()

pr()
pr(u"================ ③ 本 mod 进度树（真实流程骨架） ================")
lang = json.load(open(LANG, encoding=u"utf-8"))


def txt(key, *cands):
    for c in cands:
        if c and c in lang:
            return lang[c]
    for c in cands:
        if c and (c + u".title") in lang:
            return lang[c + u".title"]
    return u"??"


nodes = {}
for fn in sorted(os.listdir(ADV)):
    if not fn.endswith(u".json"):
        continue
    d = json.load(open(os.path.join(ADV, fn), encoding=u"utf-8"))
    disp = d.get(u"display", {})
    title = disp.get(u"title", {})
    desc = disp.get(u"description", {})
    par = d.get(u"parent")
    if par and u":" in par:
        par = par.split(u":", 1)[1]
    nodes[fn[:-5]] = {
        u"parent": par,
        u"frame": disp.get(u"frame", u"task"),
        u"title": title.get(u"translate") or title.get(u"text"),
        u"desc": desc.get(u"translate") or desc.get(u"text"),
    }
pr(u"  共 %d 条" % len(nodes))
kids = {}
for n, v in nodes.items():
    kids.setdefault(v[u"parent"] or u"<ROOT>", []).append(n)


def walk(pid, depth):
    for n in sorted(kids.get(pid, [])):
        v = nodes[n]
        pr(u"  %s%-28s [%-9s] %s ／ %s" % (
            u"    " * depth, n, v[u"frame"], txt(1, v[u"title"]), txt(1, v[u"desc"])))
        walk(n, depth + 1)


walk(u"<ROOT>", 0)
