# -*- coding: utf-8 -*-
# _zf137_docs.py —— ZF137 文档：贴图清单加一节 + 档案加变更行与 4.126
#
# 4.126 记的是本轮那条方法论：**改文案要连带查"谁把这句话当判据"**。
import io
import os
import sys

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = r"E:\PotatoST"
LIST = os.path.join(ROOT, "docs", "贴图清单.md")
ARCH = os.path.join(ROOT, "docs", "开发档案.md")
PIT = os.path.join(HERE, "_zf137_pitfall.md")


def read(p):
    return io.open(p, encoding="utf-8").read()


def write(p, t):
    io.open(p, "w", encoding="utf-8", newline="\n").write(t)


def main():
    # ① 贴图清单
    raw = read(LIST)
    sec = read(os.path.join(HERE, "_zf137_section.md"))
    if u"## ZF137（0.11）" in raw:
        print(u"  [幂等] 清单已有 ZF137 小节")
    else:
        if not raw.endswith(u"\n"):
            raw += u"\n"
        write(LIST, raw + sec)
        back = read(LIST)
        print(u"  %s 贴图清单纯追加（%d -> %d 字节）"
              % (u"[OK]" if back.startswith(raw) and u"## ZF137（0.11）" in back else u"[!!]",
                 len(raw.encode()), len(back.encode())))

    # ② 档案变更行
    raw = read(ARCH)
    if u"| ZF137 |" in raw:
        print(u"  [幂等] 档案已有 ZF137 变更行")
    else:
        row = read(os.path.join(HERE, "_zf137_row.txt")).strip()
        lines = raw.split(u"\n")
        idx = None
        for i, ln in enumerate(lines):
            if ln.startswith(u"| ZF136 |"):
                idx = i
        if idx is None:
            for i, ln in enumerate(lines):
                if ln.startswith(u"| ZF"):
                    idx = i
        if idx is None:
            print(u"  !! 找不到变更表，停手")
            return 1
        lines.insert(idx + 1, row)
        write(ARCH, u"\n".join(lines))
        print(u"  [OK] 变更表已插入 ZF137 行")

    # ③ 雷区（号在 pitfall 文件里写死，先查有没有被占）
    raw = read(ARCH)
    import re
    nums = [int(m.group(1)) for m in
            (re.match(r"^### 4\.(\d+) ", ln) for ln in raw.split(u"\n")) if m]
    want = max(nums) + 1
    pit = read(PIT).replace(u"__NUM__", u"4.%d" % want)
    if u"### 4.%d " % want in raw:
        print(u"  [幂等] 档案已有 4.%d" % want)
    else:
        anchor = u"### 4.%d " % (want - 1)
        if raw.count(anchor) != 1:
            print(u"  !! 锚点 %s 出现 %d 次，停手" % (anchor.strip(), raw.count(anchor)))
            return 1
        idx = raw.index(anchor)
        write(ARCH, raw[:idx] + pit + raw[idx:])
        print(u"  [OK] 已插入 4.%d（在 4.%d 之前）" % (want, want - 1))

    back = read(ARCH)
    ok = (u"| ZF137 |" in back and u"### 4.%d " % want in back
          and u"## ZF137（0.11）" in read(LIST))
    print(u"  %s 回读：ZF137 行 / 4.%d / 清单小节 都在" % (u"[OK]" if ok else u"[!!]", want))
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
