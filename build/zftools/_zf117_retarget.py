# -*- coding: utf-8 -*-
u"""_zf117_retarget.py —— 活体数字重定目标：四语言键数 **432 → 448**（+16 = 8 节点 × 2）

与 ZF114 的 `_zf114_live.py` 同一套做法（那次是 417 → 432），但**范围更窄**
（432 这个数字在别处也可能是 sha1 片段，不能全盘替换）：

  改：`build\\zftools\\_zf*_verify.py` —— **21 份**（每一处 `432` 都是键数断言或它的文案）；
      `docs\\UpdateAnnouncement_EN.md` 的 `(432 keys each)`。
  不改：`_zf114_live.py` / `_zf115_lang.py`（往轮的一次性脚本，里面的 432 是**它那一轮的基线**）、
      `_zf117_*`（本轮自己的）、`docs\\开发档案.md`（历史行）、任何 sha1 里的 432。

`EXPECT_KEYS` 那种行**顺手补出处**（项目惯例：这行注释是账本）：
  `EXPECT_KEYS = 432  # … + ZF112 锂电池构造间 9 键` → `... = 448  # … + ZF112 ... + ZF117 进度 16 键`

改完立刻回读断言：① 21 份里一个 `432` 都不剩；② 除被改的行，其余字节逐字不变；
③ 每份脚本 `compile()` 过；④ 四语言真的各 448 键。
"""
import glob
import io
import json
import os
import re
import sys

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

ROOT = r"E:\PotatoST"
TOOLS = os.path.join(ROOT, r"build\zftools")
LANG = os.path.join(ROOT, r"src\main\resources\assets\potato_s_t\lang")
ANN = os.path.join(ROOT, r"docs\UpdateAnnouncement_EN.md")

OLD, NEW = u"432", u"448"
SUFFIX = u" + ZF117 进度 16 键"

fails, notes = [], []


def read(p):
    return io.open(p, encoding="utf-8").read()


def main():
    targets = sorted(p for p in glob.glob(os.path.join(TOOLS, "_zf*_verify.py"))
                     if u"_zf117_" not in os.path.basename(p))
    for p in targets:
        name = os.path.basename(p)
        raw = read(p)
        if OLD not in raw:
            continue
        lines = raw.split(u"\n")
        hits, changed_expect = 0, 0
        for i, l in enumerate(lines):
            if OLD not in l:
                continue
            hits += l.count(OLD)
            m = re.match(u"^(\\s*EXPECT_KEYS\\s*=\\s*)" + OLD + u"(\\s*)(#.*)$", l)
            if m and SUFFIX.strip() not in l:
                lines[i] = m.group(1) + NEW + m.group(2) + m.group(3) + SUFFIX
                changed_expect += 1
            else:
                lines[i] = l.replace(OLD, NEW)
        text = u"\n".join(lines)
        try:
            compile(text, p, "exec")
        except SyntaxError as e:
            fails.append(u"%s：改完语法错 %s" % (name, e))
            continue
        back_old = [i for i, l in enumerate(text.split(u"\n")) if OLD in l]
        if back_old:
            fails.append(u"%s：还剩 432（行 %s）" % (name, back_old[:3]))
            continue
        # 只准动那些行：把两边都按行比对，差异行必须都含 448
        a, b = raw.split(u"\n"), text.split(u"\n")
        if len(a) != len(b):
            fails.append(u"%s：行数变了 %d → %d" % (name, len(a), len(b)))
            continue
        diff = [i for i in range(len(a)) if a[i] != b[i]]
        bad = [i for i in diff if NEW not in b[i]]
        if bad:
            fails.append(u"%s：有非预期差异行 %s" % (name, bad[:3]))
            continue
        io.open(p, "w", encoding="utf-8", newline=u"").write(text)
        notes.append(u"%-22s %d 处 %s → %s（其中 EXPECT_KEYS %d 处补出处）"
                     % (name, hits, OLD, NEW, changed_expect))

    # 英文公告
    raw = read(ANN)
    if u"(%s keys each)" % OLD in raw:
        text = raw.replace(u"(%s keys each)" % OLD, u"(%s keys each)" % NEW, 1)
        io.open(ANN, "w", encoding="utf-8", newline=u"").write(text)
        if u"(%s keys each)" % NEW not in read(ANN):
            fails.append(u"公告：回读后不是 448")
        else:
            notes.append(u"docs\\UpdateAnnouncement_EN.md  (432 keys each) → (448 keys each)")
    elif u"(%s keys each)" % NEW not in raw:
        fails.append(u"公告里既没有 432 也没有 448 的键数句")

    # 落地数字
    counts = {}
    for n in ("zh_cn", "en_us", "ja_jp", "ru_ru"):
        counts[n] = len(json.loads(read(os.path.join(LANG, n + u".json"))))
    if set(counts.values()) != {int(NEW)}:
        fails.append(u"四语言键数不是各 448：%s" % counts)
    else:
        notes.append(u"四语言各 %s 键" % NEW)

    print(u"\n".join(u"  [OK] " + n for n in notes))
    print(u"\n失败项 = %d" % len(fails))
    for f in fails:
        print(u"  !! " + f)
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())
