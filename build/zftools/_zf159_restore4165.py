#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
_zf159_restore4165.py —— 把被我误删的 §4.165 整节**从 git HEAD 逐字接回**。

事故：给档案插 §4.167 / §4.166 时，`edit` 的 old_string 只写了 §4.165 的**标题行**，
      new_string 里却忘了把它接回去 ⇒ **整节（标题 + 20 行正文）被顶掉**。
      幸好那一节已经进了 HEAD（ZF158 那次提交带的），所以能**逐字**取回。

做法：从 `HEAD:docs/开发档案.md` 取 §4.165 那一节的原文（从它的标题到下一个标题之前），
      插回工作区里 §4.167 标题的**前面**；然后逐字节核对：
      ① 工作区里 §4.165 那一节 == HEAD 里的同一节（逐字）；
      ② §4.167 / §4.166 两节都还在；
      ③ 文件没有引入 CR / BOM。

跑法：
    python build\\zftools\\_zf159_restore4165.py --dry
    python build\\zftools\\_zf159_restore4165.py
"""

import io
import os
import subprocess
import sys

ROOT = r"E:\PotatoST"
GIT = r"C:\Program Files\Git\cmd\git.exe"
DOC = os.path.join(ROOT, "docs", "开发档案.md")
REL = "docs/开发档案.md"
ANCHOR = u'### 4.167 【兼容雷】'

dry = "--dry" in sys.argv
try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass


def git_show(rev_path):
    p = subprocess.run([GIT, "-C", ROOT, "show", rev_path], capture_output=True)
    if p.returncode != 0:
        print("[FAIL] git show %s 失败：%s" % (rev_path, p.stderr.decode("utf-8", "replace")[:300]))
        sys.exit(1)
    return p.stdout.decode("utf-8")


head = git_show("HEAD:" + REL)
hl = head.split("\n")
starts = [i for i, l in enumerate(hl) if l.startswith(u"### 4.165 ")]
if len(starts) != 1:
    print("[FAIL] HEAD 里 §4.165 标题命中 %d 处（必须正好 1）" % len(starts))
    sys.exit(1)
start = starts[0]
end = next((i for i in range(start + 1, len(hl))
            if hl[i].startswith(u"### ") or hl[i].startswith(u"## ")), len(hl))
section = "\n".join(hl[start:end]) + "\n"
print("从 HEAD 取回 §4.165：%d 行 / %d 字" % (end - start, len(section)))

cur = io.open(DOC, encoding="utf-8").read()
if u"### 4.165 " in cur:
    print("[INFO] 工作区里已经有 §4.165 —— 不重复插（幂等）")
    sys.exit(0)
if cur.count(ANCHOR) != 1:
    print("[FAIL] 锚点 §4.167 命中 %d 处（必须正好 1）" % cur.count(ANCHOR))
    sys.exit(1)
if u"### 4.166 " not in cur:
    print("[FAIL] §4.166 不在工作区里 —— 停手，人工看")
    sys.exit(1)

if dry:
    print("[dry] 会把那一节插到 §4.167 之前")
    sys.exit(0)

io.open(os.path.join(ROOT, "build", "zftools", "check",
                     "开发档案.md.before-restore4165"), "w",
        encoding="utf-8", newline="\n").write(cur)

new = cur.replace(ANCHOR, section + ANCHOR, 1)
io.open(DOC, "w", encoding="utf-8", newline="\n").write(new)

# ---------- 逐字节核对 ----------
again = io.open(DOC, encoding="utf-8").read()
al = again.split("\n")
s2 = [i for i, l in enumerate(al) if l.startswith(u"### 4.165 ")]
problems = []
if len(s2) != 1:
    problems.append("接回后 §4.165 标题命中 %d 处" % len(s2))
else:
    e2 = next((i for i in range(s2[0] + 1, len(al))
               if al[i].startswith(u"### ") or al[i].startswith(u"## ")), len(al))
    got = "\n".join(al[s2[0]:e2]) + "\n"
    if got != section:
        problems.append("接回的那一节与 HEAD **不是逐字相同**")
    else:
        print("[OK] §4.165 那一节与 HEAD 逐字相同（%d 行）" % (e2 - s2[0]))
for must in (u"### 4.166 ", u"### 4.167 ", u"## 6. "):
    if must not in again:
        problems.append("接回后找不到：%r" % must)
b = io.open(DOC, "rb").read()
if b.startswith(b"\xef\xbb\xbf"):
    problems.append("写出了 BOM")
# 只允许**新增**行，不允许删：HEAD 的每一行都还得在
missing = [l for l in hl if l.strip() and l not in al]
if missing:
    problems.append("接回后相对 HEAD 少了 %d 行（例：%r）" % (len(missing), missing[0][:80]))

print("")
if problems:
    print("失败 %d 项：" % len(problems))
    for p in problems:
        print("  [FAIL] " + p)
    sys.exit(1)
print("结论：§4.165 已逐字接回，且相对 HEAD 一行都没少")
sys.exit(0)
