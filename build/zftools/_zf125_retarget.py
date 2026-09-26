# -*- coding: utf-8 -*-
u"""_zf125_retarget.py —— 把往轮判据里的"活体数字"464 跟到 475（ZF125 四语言 +11 键）

为什么必须动它们：这四份校验脚本把语言总键数写成了**字面量**（464），
本轮加了 11 个键（`block` / `tooltip` / 5 个 `status` / `invalid` / 3 个 `pour`）
⇒ 不改它们，门会红在"键数不对"上，而那是**判据过期**，不是本轮改错。

动的四处（每处只改数字与注释，判据一条没放宽）：
  `_zf100_verify.py`  EXPECT_KEYS = 464 → 475
  `_zf101_verify.py`  EXPECT_KEYS = 464 → 475
  `_zf102_verify.py`  EXPECT_KEYS = 464 → 475
  `_zf103_verify.py`  len(table) == 464 → 475（连文案里的 464 一起改）

跑法：
    python build\\zftools\\_zf125_retarget.py
"""
import io
import os
import sys

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

ROOT = r"E:\PotatoST"
TOOLS = os.path.join(ROOT, r"build\zftools")

JOBS = [
    (u"_zf100_verify.py",
     u"EXPECT_KEYS = 464           # … + ZF112 锂电池构造间 9 键 + ZF117 进度 16 键\n",
     u"EXPECT_KEYS = 475           # … + ZF112 锂电池构造间 9 键 + ZF117 进度 16 键 + ZF125 柴油发电机 11 键\n"),
    (u"_zf101_verify.py",
     u"EXPECT_KEYS = 464           # … + ZF112 锂电池构造间 9 键 + ZF117 进度 16 键\n",
     u"EXPECT_KEYS = 475           # … + ZF112 锂电池构造间 9 键 + ZF117 进度 16 键 + ZF125 柴油发电机 11 键\n"),
    (u"_zf102_verify.py",
     u"EXPECT_KEYS = 464           # … + ZF112 锂电池构造间 9 键 + ZF117 进度 16 键\n",
     u"EXPECT_KEYS = 475           # … + ZF112 锂电池构造间 9 键 + ZF117 进度 16 键 + ZF125 柴油发电机 11 键\n"),
    (u"_zf103_verify.py",
     u"check(len(table) == 464, u\"%s：总键数 464（… + ZF112 锂电池构造间 9）\" % locale,\n",
     u"check(len(table) == 475, u\"%s：总键数 475（… + ZF112 锂电池构造间 9 + ZF125 柴油发电机 11）\" % locale,\n"),
]

notes, fails = [], []


def main():
    for name, old, new in JOBS:
        path = os.path.join(TOOLS, name)
        text = io.open(path, encoding="utf-8", newline=u"").read()
        nl = u"\r\n" if u"\r\n" in text else u"\n"
        o, n = old.replace(u"\n", nl), new.replace(u"\n", nl)
        if text.count(o) == 1:
            io.open(path, "w", encoding="utf-8", newline=u"").write(text.replace(o, n, 1))
            notes.append(u"%s：464 → 475（锚点 1 次命中）" % name)
            continue
        if text.count(n) == 1:
            notes.append(u"%s：已经是 475（改过了）" % name)
            continue
        fails.append(u"%s：锚点命中 %d 次 / 已改形态 %d 次 —— 停手"
                     % (name, text.count(o), text.count(n)))
    # 残留检查：这四份里不该再有裸的 464
    for name, _, _ in JOBS:
        text = io.open(os.path.join(TOOLS, name), encoding="utf-8").read()
        if u"464" in text:
            fails.append(u"%s：还残留 464" % name)
    if not fails:
        notes.append(u"四份里再无裸的 464")
    print(u"\n".join(u"  [OK] " + x for x in notes))
    print(u"失败项 = %d" % len(fails))
    for f in fails:
        print(u"  !! " + f)
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())
