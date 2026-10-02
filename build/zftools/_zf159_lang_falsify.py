#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
_zf159_lang_falsify.py —— 反证刀：证明修严后的 `_zf159_lang.py` **真的会改、只改该改的、且幂等**。

全程在 `build\\zftools\\_zf159_falsify\\` 沙箱里跑，**绝不碰 src**。

沙箱输入 = **git HEAD 里的那五份 lang**（权威的"改前态"，不是备份 —— 备份是第一版写坏后的中间态）。
判据是"命中"而不是"没崩"：

  ① 第一次跑：必须成功；
  ② 回读：目标行**确实变了**、**旧尾巴一行不少地还在**、键数不变、无 BOM/CR、
     并且**除了目标行与 pour.rejected，没有任何键与 HEAD 不同**；
  ③ 第二次跑：必须走"已经改过"的幂等分支（不再是"又插一遍"）；
  ④ 第三次跑：行数不再增长（专门盯第一版那个"插两遍"的病）。
"""

import io
import json
import os
import shutil
import subprocess
import sys

ROOT = r"E:\PotatoST"
GIT = r"C:\Program Files\Git\cmd\git.exe"
LANGREL = "src/main/resources/assets/potato_s_t/lang"
FILES = ["zh_cn.json", "en_us.json", "ja_jp.json", "ru_ru.json", "lzh.json"]
SANDBOX = os.path.join(ROOT, "build", "zftools", "_zf159_falsify")
GATE = os.path.join(ROOT, "build", "zftools", "_zf159_lang.py")

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

problems = []
notes = []

# ---------- ① 搭沙箱：HEAD 版 lang + 沙箱版门 ----------
if os.path.isdir(SANDBOX):
    shutil.rmtree(SANDBOX)
sandbox_lang = os.path.join(SANDBOX, "lang")
os.makedirs(sandbox_lang)
for fn in FILES:
    b = subprocess.run([GIT, "-C", ROOT, "show", "HEAD:" + LANGREL + "/" + fn],
                       capture_output=True).stdout
    if not b:
        print("[FAIL] 拿不到 HEAD:%s" % fn)
        sys.exit(1)
    open(os.path.join(sandbox_lang, fn), "wb").write(b)

gate_src = io.open(GATE, encoding="utf-8").read()
needle_lang = 'LANG = os.path.join(ROOT, "src", "main", "resources", "assets", "potato_s_t", "lang")'
assert needle_lang in gate_src, "门的 LANG 常量变了，反证刀要跟着改"
gate_sandbox = gate_src.replace(
    needle_lang, 'LANG = r"%s"' % sandbox_lang).replace(
    'BACKUP = os.path.join(ROOT, "build", "zftools", "_zf159_lang_backup")',
    'BACKUP = r"%s"' % os.path.join(SANDBOX, "backup"))
sandbox_gate = os.path.join(SANDBOX, "_gate.py")
io.open(sandbox_gate, "w", encoding="utf-8", newline="\n").write(gate_sandbox)
notes.append("① 沙箱就绪：5 份 HEAD 原件 + 沙箱版门")

head = {fn: json.loads(io.open(os.path.join(sandbox_lang, fn), encoding="utf-8").read()) for fn in FILES}


def run_gate():
    r = subprocess.run([sys.executable, sandbox_gate], capture_output=True, text=True, encoding="utf-8")
    return r.returncode, (r.stdout or "") + (r.stderr or "")


# ---------- ② 第一次：必须真的改 ----------
rc1, out1 = run_gate()
if rc1 != 0:
    problems.append("第一次跑失败：\n" + out1[-1500:])
else:
    notes.append("② 第一次跑：退出码 0")

after1 = {}
for fn in FILES:
    after1[fn] = json.loads(io.open(os.path.join(sandbox_lang, fn), encoding="utf-8").read())
    h, a = head[fn], after1[fn]
    if len(h) != len(a):
        problems.append("%s：键数被改了（%d -> %d）" % (fn, len(h), len(a)))
        continue
    changed = [k for k in set(h) | set(a) if h.get(k) != a.get(k)]
    expect = {"tooltip.potato_s_t.diesel_generator_controller",
              "gui.potato_s_t.diesel_generator.pour.rejected"}
    if set(changed) != expect:
        problems.append("%s：变动的键不是预期那两个：%s" % (fn, sorted(set(changed) ^ expect)))
        continue
    tb = h["tooltip.potato_s_t.diesel_generator_controller"].split("\n")
    ta = a["tooltip.potato_s_t.diesel_generator_controller"].split("\n")
    # 找出第一处不同
    idx = next((i for i in range(max(len(tb), len(ta)))
                if (tb[i] if i < len(tb) else None) != (ta[i] if i < len(ta) else None)), None)
    if idx is None:
        problems.append("%s：tooltip 一个字都没改（门没生效）" % fn)
        continue
    if ta[:idx] != tb[:idx]:
        problems.append("%s：目标行之前被动过" % fn)
        continue
    if ta[-len(tb[idx + 1:]):] != tb[idx + 1:]:
        problems.append("%s：旧尾巴没被完整保留" % fn)
        continue
    raw = io.open(os.path.join(sandbox_lang, fn), "rb").read()
    if raw.startswith(b"\xef\xbb\xbf") or b"\r" in raw:
        problems.append("%s：写出了 BOM 或 CR" % fn)
        continue
    notes.append("%s：第 %d 行起被换（旧 %d 行 -> 新 %d 行），键数仍 %d，旧尾巴完整保留"
                 % (fn, idx, len(tb), len(ta), len(a)))

# ---------- ③ 第二次：必须幂等 ----------
rc2, out2 = run_gate()
if rc2 != 0:
    problems.append("第二次跑（幂等）失败：\n" + out2[-900:])
elif "已经改过" not in out2:
    problems.append("第二次跑没走幂等分支（输出里没有『已经改过』）")
else:
    notes.append("③ 第二次跑：识别为『已经改过』，未再动盘")

# ---------- ④ 第三次：专门盯"插两遍"那个病 ----------
rc3, out3 = run_gate()
after3 = {fn: json.loads(io.open(os.path.join(sandbox_lang, fn), encoding="utf-8").read()) for fn in FILES}
for fn in FILES:
    if after3[fn] != after1[fn]:
        problems.append("%s：第三次跑之后内容又变了（不幂等）" % fn)
    else:
        n = len(after3[fn]["tooltip.potato_s_t.diesel_generator_controller"].split("\n"))
        dup = after3[fn]["tooltip.potato_s_t.diesel_generator_controller"].count(u"烧什么、发多少")
        if fn == "zh_cn.json" and dup != 1:
            problems.append("%s：『烧什么、发多少』出现 %d 次（应该 1 次）—— 就是第一版那个病" % (fn, dup))
notes.append("④ 第三次跑：内容与第二次逐字相同（幂等）")

print("\n".join(notes))
print("")
if problems:
    print("反证失败 %d 项：" % len(problems))
    for p in problems:
        print("  [FAIL] " + p)
    sys.exit(1)
print("结论：门真的会改、只改该改的两处、尾巴一字不丢、且连续跑三遍幂等 —— 反证通过")
sys.exit(0)
