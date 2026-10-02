#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
_zf152_unprobe.py —— 把 ZF152 的一次性取证探针**原样拆掉**（只删自己加的那几行）。

⚠ 轮号说明：本轮动手时先按 ZF150 命名，做到一半发现另一条线（翻译润色）已经占了
  `_zf150_*`，于是统一改用 **ZF152**。探针类因此叫 `Zf152Check.java`。

背景：本工程的硬规矩是"探针跑完必须拆"（0.11 ZF133 那次忘了拆，
`Audit.ps1` 一路红 130 条、谁跑 runClient 都会自动开工）。这个脚本做四件事：

  1. 删 `src\\main\\java\\com\\potatost\\mod\\Zf152Check.java`（先存到 build\\zftools\\check\\）；
  2. 从 `PotatoST.java` 里删掉 `Zf152Check.register();` **连同它上面那两行注释和一行空行**
     （就是加进去的那 4 行，别多删）；
  3. 逐字节核对：删完之后的 PotatoST.java 必须**恰好**等于"原文 - 那 4 行"；
  4. 扫一遍 src，确认 `Zf152Check` 这个名字绝迹。

⚠ 同一条线上有别的会话在**同时**改 `PotatoST.java`（实测 2026-09-28 13:44 就撞过一次：
  另一条线往同一个位置插了它自己的 `Zf151Check.register();`）。所以：
  **本脚本只认自己那一段文本、只替换一次**，别人的行一行都不碰。

跑法：
    python build\\zftools\\_zf152_unprobe.py --dry     # 只看会删什么
    python build\\zftools\\_zf152_unprobe.py           # 真删
"""

import io
import os
import shutil
import sys

ROOT = r"E:\PotatoST"
SRC = os.path.join(ROOT, "src", "main", "java", "com", "potatost", "mod")
CHECK = os.path.join(SRC, "Zf152Check.java")
MAIN = os.path.join(SRC, "PotatoST.java")
STASH = os.path.join(ROOT, "build", "zftools", "check")

# 在 PotatoST.java 里插进去的那一段（**逐字节**，换行算 \n）
BLOCK = (
    "\n"
    "        // ---- ZF152 一次性取证探针（板材 c:plates/* 兼容）----\n"
    "        // 【临时】跑过一次真服务端、把 build/zftools/_zf152_probe.txt 写出来之后，\n"
    "        // 用 `python build\\zftools\\_zf152_unprobe.py` 把这一行连同 Zf152Check.java 一起删掉。\n"
    "        Zf152Check.register();\n"
)

dry = "--dry" in sys.argv

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

problems = []

# ---------- ① 备份并删除探针类 ----------
if os.path.isfile(CHECK):
    if dry:
        print("[dry] 会删除 %s" % CHECK)
    else:
        os.makedirs(STASH, exist_ok=True)
        dst = os.path.join(STASH, "Zf152Check.java")
        shutil.copyfile(CHECK, dst)
        with io.open(CHECK, "rb") as fh:
            a = fh.read()
        with io.open(dst, "rb") as fh:
            b = fh.read()
        if a != b:
            problems.append("备份与原文不一致：%s" % CHECK)
        else:
            os.remove(CHECK)
            print("[OK] 已删除探针类（备份在 %s）" % dst)
else:
    print("[INFO] 探针类本来就不在：%s" % CHECK)

# ---------- ② 从主类里摘掉钩子 ----------
with io.open(MAIN, "rb") as fh:
    raw = fh.read()
text = raw.decode("utf-8")

if "Zf152Check" not in text:
    print("[INFO] PotatoST.java 里已经没有 Zf152Check 钩子了")
else:
    if BLOCK not in text:
        problems.append("PotatoST.java 里找不到那 4 行钩子原文（可能被人改过）—— 请手工看一眼，别硬删")
    else:
        new = text.replace(BLOCK, "", 1)
        if dry:
            print("[dry] 会从 PotatoST.java 删掉这 4 行：")
            for ln in BLOCK.split("\n"):
                if ln:
                    print("      " + ln)
        else:
            # 备份原文（"逐字节核对"这条规矩要留证）
            os.makedirs(STASH, exist_ok=True)
            with io.open(os.path.join(STASH, "PotatoST.java.before-unprobe-zf152"), "wb") as fh:
                fh.write(raw)
            with io.open(MAIN, "wb") as fh:
                fh.write(new.encode("utf-8"))

            # ---------- ③ 逐字节核对 ----------
            with io.open(MAIN, "rb") as fh:
                got = fh.read()
            if got != new.encode("utf-8"):
                problems.append("写回后逐字节核对失败：%s" % MAIN)
            elif b"Zf152Check" in got:
                problems.append("写回后仍残留 Zf152Check 字样：%s" % MAIN)
            else:
                print("[OK] PotatoST.java 已摘掉钩子（%d 字节 -> %d 字节，逐字节核对通过）"
                      % (len(raw), len(got)))

# ---------- ④ 形状自检：Zf152Check 这个名字在 src 下应当绝迹 ----------
if not dry:
    leftover = []
    for dp, dn, fn in os.walk(os.path.join(ROOT, "src")):
        for f in fn:
            p = os.path.join(dp, f)
            try:
                with io.open(p, "rb") as fh:
                    if b"Zf152Check" in fh.read():
                        leftover.append(p)
            except Exception:
                pass
    if leftover:
        problems.append("src 下仍残留 Zf152Check 引用：%s" % ", ".join(leftover))
    else:
        print("[OK] src 下已无 Zf152Check 任何引用")
    # 顺带报一下"别人还挂着的探针"，免得把别人的算到自己头上
    others = []
    for f in os.listdir(SRC):
        if f.startswith("Zf") and f.endswith("Check.java"):
            others.append(f)
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
