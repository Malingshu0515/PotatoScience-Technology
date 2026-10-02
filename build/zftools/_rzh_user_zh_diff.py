# -*- coding: utf-8 -*-
"""Dump the user's own zh_cn.json edits: key -> (HEAD value, working-tree value).

Old side is read from `git show HEAD:<path>` so nothing is hand-copied.
Writes UTF-8 by itself (console is GBK; never print CJK to stdout).
"""
import json
import subprocess
import sys
from pathlib import Path

REPO = Path(r"E:\PotatoST")
REL = "src/main/resources/assets/potato_s_t/lang/zh_cn.json"
GIT = r"C:\Program Files\Git\cmd\git.exe"
OUT = REPO / "build" / "zftools" / "_rzh_user_zh_diff.txt"

old_raw = subprocess.run(
    [GIT, "show", "HEAD:" + REL],
    cwd=str(REPO), capture_output=True, check=True,
).stdout.decode("utf-8")
new_raw = (REPO / REL).read_text(encoding="utf-8")

old = json.loads(old_raw)
new = json.loads(new_raw)

added = [k for k in new if k not in old]
removed = [k for k in old if k not in new]
changed = [k for k in new if k in old and old[k] != new[k]]

lines = []
lines.append("# zh_cn.json user edits  (HEAD=%s)" % subprocess.run(
    [GIT, "rev-parse", "--short", "HEAD"], cwd=str(REPO),
    capture_output=True, check=True).stdout.decode().strip())
lines.append("# old keys=%d  new keys=%d  added=%d  removed=%d  changed=%d"
             % (len(old), len(new), len(added), len(removed), len(changed)))
lines.append("")

if added:
    lines.append("## ADDED KEYS")
    for k in added:
        lines.append("+ %s" % k)
        lines.append("    NEW: %s" % new[k])
    lines.append("")
if removed:
    lines.append("## REMOVED KEYS")
    for k in removed:
        lines.append("- %s" % k)
        lines.append("    OLD: %s" % old[k])
    lines.append("")

lines.append("## CHANGED (%d)" % len(changed))
lines.append("")
for i, k in enumerate(changed, 1):
    lines.append("[%03d] %s" % (i, k))
    lines.append("  OLD: %s" % old[k])
    lines.append("  NEW: %s" % new[k])
    lines.append("")

OUT.write_text("\n".join(lines), encoding="utf-8", newline="\n")
print("changed=%d added=%d removed=%d -> %s" % (len(changed), len(added), len(removed), OUT))
