# -*- coding: utf-8 -*-
# _zf135_docs.py —— ZF135 文档：贴图清单加一节 + 档案加变更行与 4.125
import io
import os
import sys

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = r"E:\PotatoST"
LIST = os.path.join(ROOT, "docs", "贴图清单.md")
ARCH = os.path.join(ROOT, "docs", "开发档案.md")


def read(p):
    return io.open(p, encoding="utf-8").read()


def write(p, t):
    io.open(p, "w", encoding="utf-8", newline="\n").write(t)


def main():
    # ① 贴图清单：纯追加
    raw = read(LIST)
    sec = read(os.path.join(HERE, "_zf135_section.md"))
    if u"## ZF135（0.11）" in raw:
        print(u"  [幂等] 贴图清单已有 ZF135 小节")
    else:
        if not raw.endswith(u"\n"):
            raw += u"\n"
        write(LIST, raw + sec)
        back = read(LIST)
        print(u"  %s 贴图清单纯追加（%d -> %d 字节）"
              % (u"[OK]" if back.startswith(raw) and u"## ZF135（0.11）" in back else u"[!!]",
                 len(raw.encode()), len(back.encode())))

    # ② 档案：变更行（插在 ZF133 之后）
    raw = read(ARCH)
    if u"| ZF135 |" in raw:
        print(u"  [幂等] 档案已有 ZF135 变更行")
    else:
        row = read(os.path.join(HERE, "_zf135_row.txt")).strip()
        lines = raw.split(u"\n")
        idx = None
        for i, ln in enumerate(lines):
            if ln.startswith(u"| ZF133 |"):
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
        print(u"  [OK] 变更表已插入 ZF135 行")

    # ③ 档案：4.125
    raw = read(ARCH)
    if u"### 4.125 " in raw:
        print(u"  [幂等] 档案已有 4.125")
    else:
        anchor = u"### 4.124 "
        if raw.count(anchor) != 1:
            print(u"  !! 4.124 锚点 %d 次，停手" % raw.count(anchor))
            return 1
        idx = raw.index(anchor)
        write(ARCH, raw[:idx] + read(os.path.join(HERE, "_zf135_pitfall.md")) + raw[idx:])
        print(u"  [OK] 已插入 4.125（在 4.124 之前）")

    back = read(ARCH)
    ok = (u"| ZF135 |" in back and u"### 4.125 " in back and u"### 4.124 " in back
          and u"## ZF135（0.11）" in read(LIST))
    print(u"  %s 回读：ZF135 行 / 4.125 / 4.124 / 清单小节 都在" % (u"[OK]" if ok else u"[!!]"))
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
