#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
_zf159_unprobe.py —— 把 ZF159 的一次性取证探针**原样拆掉**（只删自己加的那几行）。

本工程的硬规矩是"探针跑完必须拆"（0.11 ZF133 忘了拆 ⇒ `Audit.ps1` 红 130 条、
谁跑 runClient 都会自动开工）。这个脚本只做四件事，每件都先备份、再逐字节核对：

  1. 删 `src\\main\\java\\com\\potatost\\mod\\Zf159Check.java`（先存到 build\\zftools\\check\\）；
  2. 从 `PotatoST.java` 里删掉 `Zf159Check.register();` **连同它上面那三行注释和一行空行**
     （就是加进去的那 5 行，别多删）；
  3. 逐字节核对：删完之后的 PotatoST.java 必须**恰好**等于"原文 - 那 5 行"；
  4. 扫一遍 src，确认 `Zf159Check` 这个名字绝迹，并**报出还挂着别人的哪些探针**（一个都不碰）。

⚠ 同一条线上有别的会话在**同时**改 `PotatoST.java`（2026-10-01 23:45 实测：另一条线
  刚加了 `Zf160Check.java`）。所以本脚本只认自己那一段文本、只替换一次，别人的行一行都不碰。

跑法：
    python build\\zftools\\_zf159_unprobe.py --dry
    python build\\zftools\\_zf159_unprobe.py
"""

import io
import os
import shutil
import sys

ROOT = r"E:\PotatoST"
SRC = os.path.join(ROOT, "src", "main", "java", "com", "potatost", "mod")
CHECK = os.path.join(SRC, "Zf159Check.java")
MAIN = os.path.join(SRC, "PotatoST.java")
STASH = os.path.join(ROOT, "build", "zftools", "check")

# 在 PotatoST.java 里插进去的那一段（**逐字节**，换行算 \n）
BLOCK = (
    "\n"
    "        // ---- ZF159 一次性取证探针（流体/粉尘跨模组兼容）----\n"
    "        // 【临时】跑过一次真服务端、把 build/zftools/_zf159_probe.txt 写出来之后，\n"
    "        // 用 `python build\\zftools\\_zf159_unprobe.py` 把这一行连同 Zf159Check.java 一起删掉。\n"
    "        Zf159Check.register();\n"
)

dry = "--dry" in sys.argv
try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

problems = []

# ---------- ① 备份并删除探针类 ----------
if os.path.isfile(CHECK):
    if dry:
        print("[dry] 会删除 %s" % CHECK)
    else:
        os.makedirs(STASH, exist_ok=True)
        dst = os.path.join(STASH, "Zf159Check.java")
        shutil.copyfile(CHECK, dst)
        a = io.open(CHECK, "rb").read()
        b = io.open(dst, "rb").read()
        if a != b:
            problems.append("备份与原文不一致：%s" % CHECK)
        else:
            os.remove(CHECK)
            print("[OK] 已删除探针类（备份在 %s）" % dst)
else:
    print("[INFO] 探针类本来就不在：%s" % CHECK)

# ---------- ② 从主类里摘掉钩子 ----------
raw = io.open(MAIN, "rb").read()
text = raw.decode("utf-8")

if "Zf159Check" not in text:
    print("[INFO] PotatoST.java 里已经没有 Zf159Check 钩子了")
else:
    if BLOCK not in text:
        problems.append("PotatoST.java 里找不到那 5 行钩子原文（可能被人改过）—— 请手工看一眼，别硬删")
    else:
        new = text.replace(BLOCK, "", 1)
        if dry:
            print("[dry] 会从 PotatoST.java 删掉这 5 行：")
            for ln in BLOCK.split("\n"):
                if ln:
                    print("      " + ln)
        else:
            os.makedirs(STASH, exist_ok=True)
            io.open(os.path.join(STASH, "PotatoST.java.before-unprobe-zf159"), "wb").write(raw)
            io.open(MAIN, "wb").write(new.encode("utf-8"))
            got = io.open(MAIN, "rb").read()
            if got != new.encode("utf-8"):
                problems.append("写回后逐字节核对失败：%s" % MAIN)
            elif b"Zf159Check" in got:
                problems.append("写回后仍残留 Zf159Check 字样：%s" % MAIN)
            else:
                print("[OK] PotatoST.java 已摘掉钩子（%d 字节 -> %d 字节，逐字节核对通过）"
                      % (len(raw), len(got)))
            # 顺带确认**没有**动到别人刚加的挂载点
            for other in ("Zf160Check", "Zf158Check", "Zf157Check"):
                if (other.encode() in raw) != (other.encode() in got):
                    problems.append("把别人的挂载点 %s 的行数改动了！" % other)

# ---------- ③ 自检：Zf159Check 在 src 下应当绝迹 ----------
if not dry:
    leftover = []
    for dp, dn, fn in os.walk(os.path.join(ROOT, "src")):
        for f in fn:
            p = os.path.join(dp, f)
            try:
                if b"Zf159Check" in io.open(p, "rb").read():
                    leftover.append(p)
            except Exception:
                pass
    if leftover:
        # ⚠ 这里**只报告不报红**：第一次跑就把别人的探针里「…`Zf159Check`，汇合点不能叠罗汉」
        #   那句注释当成了残留引用 ⇒ 假红。注释里的提及不是引用（真正的判据在下面那段去注释的检查）。
        print("[INFO] 这些文件里**提到过** Zf159Check（可能只是注释）：%s" % ", ".join(leftover))
    else:
        print("[OK] src 下已无 Zf159Check 任何引用")
    # ⚠ 判据要分清"引用"和"只是注释里提了一句"：第一次跑就把别人的探针里
    #   「…`Zf159Check`，汇合点不能叠罗汉」这句注释当成了残留引用 ⇒ 假红。
    #   真正的残留是**代码**里出现（去注释后再看）。
    import re as _re
    code_refs = []
    for dp, dn, fn in os.walk(os.path.join(ROOT, "src")):
        for f in fn:
            if not f.endswith(".java"):
                continue
            p = os.path.join(dp, f)
            try:
                s = io.open(p, encoding="utf-8").read()
            except Exception:
                continue
            stripped = _re.sub(r"//[^\n]*", "", _re.sub(r"/\*.*?\*/", "", s, flags=_re.S))
            if "Zf159Check" in stripped:
                code_refs.append(p)
    if code_refs:
        problems.append("src 的**代码**里仍引用 Zf159Check：%s" % ", ".join(code_refs))
    else:
        print("[OK] src 的代码里已无 Zf159Check（注释里的提及不算）")
    others = [f for f in os.listdir(SRC) if f.startswith("Zf") and f.endswith("Check.java")]
    print("[INFO] 此刻 src 下还挂着的探针（**不是本轮的**，别删）：%s"
          % (", ".join(sorted(others)) if others else "（无）"))

print("")
if problems:
    print("失败 %d 项：" % len(problems))
    for p in problems:
        print("  [FAIL] " + p)
    sys.exit(1)
print("结论：探针已拆干净（--dry 模式下什么都没改）" if dry else "结论：探针已拆干净")
sys.exit(0)
