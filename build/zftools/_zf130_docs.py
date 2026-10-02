# -*- coding: utf-8 -*-
# _zf130_docs.py —— ZF130 文档：贴图清单加一节 + 档案加变更行与 4.111
#
# 并发环境（别的线已跑到 ZF128）⇒ 一律「定位 -> 插入 -> 立刻回读断言」。
# 编号：117 已被别人占用，故本轮用 ZF130。
#
# ⚠ 正文放独立文件 `_zf130_section.md` / `_zf130_row.txt`，本脚本只负责插入 ——
#   上一版把长正文写成 Python 三引号字面量，末尾一个反斜杠就把结束引号转义掉，
#   连报两次 SyntaxError。**长文本不要塞进源码字面量**。
import io
import os
import sys

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = r"E:\PotatoST"
LIST = os.path.join(ROOT, "docs", "贴图清单.md")
ARCH = os.path.join(ROOT, "docs", "开发档案.md")
SECTION_MD = os.path.join(HERE, "_zf130_section.md")
ROW_TXT = os.path.join(HERE, "_zf130_row.txt")
PITFALL_MD = os.path.join(HERE, "_zf130_pitfall.md")


def read(p):
    return io.open(p, encoding="utf-8").read()


def write(p, t):
    io.open(p, "w", encoding="utf-8", newline="\n").write(t)


def main():
    # ---------- ① 贴图清单：纯追加 ----------
    if os.path.exists(SECTION_MD):
        raw = read(LIST)
        sec = read(SECTION_MD)
        if u"## ZF130（0.11）" in raw:
            print(u"  [幂等] 贴图清单已有 ZF130 小节")
        else:
            if not raw.endswith(u"\n"):
                raw += u"\n"
            write(LIST, raw + sec)
            back = read(LIST)
            ok = back.startswith(raw) and u"## ZF130（0.11）" in back
            print(u"  %s 贴图清单纯追加（%d -> %d 字节）"
                  % (u"[OK]" if ok else u"[!!]", len(raw.encode()), len(back.encode())))
    else:
        print(u"  !! 缺 %s" % SECTION_MD)

    # ---------- ② 档案：变更行 ----------
    raw = read(ARCH)
    if u"| ZF130 |" in raw:
        print(u"  [幂等] 档案已有 ZF130 变更行")
    elif os.path.exists(ROW_TXT):
        lines = raw.split(u"\n")
        idx = None
        for i, ln in enumerate(lines):
            if ln.startswith(u"| ZF128 |"):
                idx = i
        if idx is None:
            print(u"  !! 找不到 ZF128 行作锚点，停手")
            return 1
        lines.insert(idx + 1, read(ROW_TXT).strip())
        write(ARCH, u"\n".join(lines))
        print(u"  [OK] 变更表已插入 ZF130 行（追在 ZF128 之后）")
    else:
        print(u"  !! 缺 %s" % ROW_TXT)

    # ---------- ③ 档案：4.111 ----------
    raw = read(ARCH)
    if u"### 4.111 " in raw:
        print(u"  [幂等] 档案已有 4.111")
    elif os.path.exists(PITFALL_MD):
        anchor = u"### 4.110 "
        if raw.count(anchor) != 1:
            print(u"  !! 4.110 锚点 %d 次，停手" % raw.count(anchor))
            return 1
        idx = raw.index(anchor)
        write(ARCH, raw[:idx] + read(PITFALL_MD) + raw[idx:])
        print(u"  [OK] 已插入 4.111")
    else:
        print(u"  !! 缺 %s" % PITFALL_MD)

    back = read(ARCH)
    ok = (u"| ZF130 |" in back and u"### 4.111 " in back and u"### 4.110 " in back
          and u"## ZF130（0.11）" in read(LIST))
    print(u"  %s 回读：ZF130 行 / 4.111 / 4.110 / 清单小节 都在" % (u"[OK]" if ok else u"[!!]"))
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
