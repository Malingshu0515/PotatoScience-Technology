# -*- coding: utf-8 -*-
# _zf132_docs.py —— ZF132 文档：贴图清单加一节 + 档案加变更行与 4.114
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
    sec = read(os.path.join(HERE, "_zf132_section.md"))
    if u"## ZF132（0.11）" in raw:
        print(u"  [幂等] 贴图清单已有 ZF132 小节")
    else:
        if not raw.endswith(u"\n"):
            raw += u"\n"
        write(LIST, raw + sec)
        back = read(LIST)
        print(u"  %s 贴图清单纯追加（%d -> %d 字节）"
              % (u"[OK]" if back.startswith(raw) and u"## ZF132（0.11）" in back else u"[!!]",
                 len(raw.encode()), len(back.encode())))

    # ② 档案：变更行
    raw = read(ARCH)
    if u"| ZF132 |" in raw:
        print(u"  [幂等] 档案已有 ZF132 变更行")
    else:
        row = read(os.path.join(HERE, "_zf132_row.txt")).strip()
        lines = raw.split(u"\n")
        idx = None
        for i, ln in enumerate(lines):
            if ln.startswith(u"| ZF131 |"):
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
        print(u"  [OK] 变更表已插入 ZF132 行")

    # ③ 档案：4.114
    raw = read(ARCH)
    if u"### 4.114 " in raw:
        print(u"  [幂等] 档案已有 4.114")
    else:
        anchor = u"### 4.113 "
        if raw.count(anchor) != 1:
            print(u"  !! 4.113 锚点 %d 次，停手" % raw.count(anchor))
            return 1
        idx = raw.index(anchor)
        write(ARCH, raw[:idx] + read(os.path.join(HERE, "_zf132_pitfall.md")) + raw[idx:])
        print(u"  [OK] 已插入 4.114（在 4.113 之前）")

    back = read(ARCH)
    ok = (u"| ZF132 |" in back and u"### 4.114 " in back and u"### 4.113 " in back
          and u"## ZF132（0.11）" in read(LIST))
    print(u"  %s 回读：ZF132 行 / 4.114 / 4.113 / 清单小节 都在" % (u"[OK]" if ok else u"[!!]"))
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
