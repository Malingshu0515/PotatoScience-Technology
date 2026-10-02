#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
_zf159_lang_repair.py —— 把五份 lang 里被我跑坏的那两处**从 HEAD 取权威原文**修回正确态。

怎么坏的（写下来免得下次再犯）：`_zf159_lang.py` 第一版按"行首 == 界面："定位，
替换完只检查"新文案在不在"，**没有校验要替换的那一行到底是不是旧文案** ⇒
第二次跑时它匹配到的正是自己上一次写进去的新行，于是把「烧什么、发多少」那行**插了两遍**。

修法：这两处**以 git HEAD 为准**（不是以备份为准 —— 备份是第一版写坏之后的中间态）：
  ① 从 `HEAD:src/main/resources/assets/potato_s_t/lang/<file>` 读出**旧值**；
  ② 用它把工作区里那个坏掉的值整体换回来（`tooltip` 与 `pour.rejected` 两个键）；
  ③ 回读核对：键数不变、除这两个键外**没有任何键**与 HEAD 不同（除了别人改的
     `message.potato_s_t.guide_book.received`，那个**不许动**）。

跑完再跑一遍 `_zf159_lang.py`（已修严的那版）把新文案正经写上去。

跑法：
    python build\\zftools\\_zf159_lang_repair.py --dry
    python build\\zftools\\_zf159_lang_repair.py
"""

import io
import json
import os
import subprocess
import sys

ROOT = r"E:\PotatoST"
GIT = r"C:\Program Files\Git\cmd\git.exe"
LANGREL = "src/main/resources/assets/potato_s_t/lang"
FILES = ["zh_cn.json", "en_us.json", "ja_jp.json", "ru_ru.json", "lzh.json"]
KEYS = [
    "tooltip.potato_s_t.diesel_generator_controller",
    "gui.potato_s_t.diesel_generator.pour.rejected",
]
# 别人正在改的键：修的时候**必须保持工作区现状**
OTHERS = ["message.potato_s_t.guide_book.received"]

dry = "--dry" in sys.argv
try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

problems = []
notes = []

for fn in FILES:
    rel = LANGREL + "/" + fn
    path = os.path.join(ROOT, rel.replace("/", os.sep))
    head_raw = subprocess.run([GIT, "-C", ROOT, "show", "HEAD:" + rel],
                              capture_output=True).stdout
    if not head_raw:
        problems.append("%s：拿不到 HEAD 版本" % fn)
        continue
    head = json.loads(head_raw.decode("utf-8"))
    work_raw = io.open(path, "rb").read()
    work = json.loads(work_raw.decode("utf-8"))

    if len(head) != len(work):
        problems.append("%s：键数 HEAD=%d 工作区=%d，不敢动" % (fn, len(head), len(work)))
        continue

    fixed = 0
    for k in KEYS:
        if work.get(k) != head.get(k):
            work[k] = head[k]
            fixed += 1
    if dry:
        notes.append("%s：[dry] 会把 %d 个键从 HEAD 修回来" % (fn, fixed))
        continue

    out = json.dumps(work, ensure_ascii=False, indent=2) + "\n"
    io.open(path, "w", encoding="utf-8", newline="\n").write(out)

    # ---- 回读核对 ----
    again = json.loads(io.open(path, encoding="utf-8").read())
    if len(again) != len(head):
        problems.append("%s：回读键数不符" % fn)
        continue
    for k in KEYS:
        if again[k] != head[k]:
            problems.append("%s：%s 没修回 HEAD" % (fn, k))
    for k in OTHERS:
        if again.get(k) != work.get(k):
            problems.append("%s：把别人的键 %s 改掉了！" % (fn, k))
    # 除了我们自己那两处 + 别人那几处，其余必须与 HEAD 逐字相同
    unexpected = [k for k in set(head) | set(again)
                  if k not in KEYS and k not in OTHERS and head.get(k) != again.get(k)]
    if unexpected:
        problems.append("%s：修完之后还有别的键与 HEAD 不同：%s" % (fn, unexpected))
    raw = io.open(path, "rb").read()
    if raw.startswith(b"\xef\xbb\xbf") or b"\r" in raw:
        problems.append("%s：写出了 BOM 或 CR" % fn)
    notes.append("%s：%d 个键已从 HEAD 修回；键数仍 %d；别人的键未动；无 BOM / 纯 LF"
                 % (fn, fixed, len(again)))

print("\n".join(notes))
print("")
if problems:
    print("失败 %d 项：" % len(problems))
    for p in problems:
        print("  [FAIL] " + p)
    sys.exit(1)
print("结论：五份 lang 已回到 HEAD 原文（--dry 未写盘）" if dry else "结论：五份 lang 已回到 HEAD 原文")
sys.exit(0)
