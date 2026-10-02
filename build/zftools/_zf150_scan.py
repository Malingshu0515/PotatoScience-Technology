# -*- coding: utf-8 -*-
"""_zf150_scan.py —— 把全工程里所有 `579` 扫出来并**分类**（只读）

为什么要分类：加 16 个语言键（每份 +4）后，579 → 583。
但不是所有 579 都该改 —— 至少有四种：

  A  **盘上语言键数**        ⇒ 改成 583
  B  **已发布 jar 里的键数**  ⇒ **不许动**（那是成品的事实，本轮没打包）
  C  **文档/交接里的活体数字** ⇒ 改成 583
  D  **历史叙述**（"ZF125 的 579"、"482 → 579"）⇒ 保留

所以先扫全、按上下文打标，人工可核，再决定改哪些。
"""
import io
import os
import re
import sys

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

ROOT = r"E:\PotatoST"
TOOLS = os.path.join(ROOT, "build", "zftools")
DOCS = os.path.join(ROOT, "docs")
OUT = os.path.join(TOOLS, "_zf150_scan.txt")

# 判断"已发布 jar"的上下文关键词
JAR_HINT = (u"RELEASE", u"release", u"成品", u"jar", u"JAR", u"PotatoST-0.1")
# 判断"历史叙述"的关键词
HIST_HINT = (u"ZF125", u"ZF117", u"ZF139", u"ZF145", u"ZF112", u"ZF109", u"起",
             u"→", u"->", u"之前", u"原来", u"当时", u"老")

rows = []
for base, exts in ((TOOLS, (".py", ".ps1", ".txt")), (DOCS, (".md",))):
    for fn in sorted(os.listdir(base)):
        if not fn.endswith(exts):
            continue
        p = os.path.join(base, fn)
        if not os.path.isfile(p):
            continue
        try:
            t = io.open(p, encoding="utf-8").read()
        except Exception:
            continue
        for i, ln in enumerate(t.split(u"\n"), 1):
            if not re.search(r"\b579\b", ln):
                continue
            stripped = ln.strip()
            is_comment = stripped.startswith(u"#") or stripped.startswith(u"//")
            jar = any(h in ln for h in JAR_HINT)
            hist = any(h in ln for h in HIST_HINT)
            if jar and u"公告" not in ln and u"交接" not in ln:
                kind = u"B 已发布jar（别动）"
            elif is_comment or hist:
                kind = u"D 注释/历史（保留）"
            else:
                kind = u"A/C 判据或活体数字（要改）"
            rows.append((kind, fn, i, stripped[:110]))

rows.sort()
lines = [u"# 全工程 579 分类清单（只读扫描）", u""]
for kind in (u"A/C 判据或活体数字（要改）", u"B 已发布jar（别动）", u"D 注释/历史（保留）"):
    sub = [r for r in rows if r[0] == kind]
    lines.append(u"=" * 78)
    lines.append(u"%s —— %d 处" % (kind, len(sub)))
    lines.append(u"=" * 78)
    for _, fn, i, s in sub:
        lines.append(u"  %-26s :%-5d %s" % (fn, i, s))
    lines.append(u"")

text = u"\n".join(lines)
io.open(OUT, "w", encoding="utf-8").write(text)
print(text)
print(u"[报告] %s" % OUT)
