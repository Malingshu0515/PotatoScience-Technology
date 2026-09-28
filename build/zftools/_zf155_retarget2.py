# -*- coding: utf-8 -*-
u"""_zf155_retarget2.py —— 跟平补刀：**比较字面量写在下一行**的那三处（消息改了、判据没改）。

扫描（`_zf155_retarget2_scan.py`）确认只剩这三处是"真判据"：
  `_zf73_verify.py:218` / `_zf78_verify.py:515` / `_zf79_verify.py:257` —— 全是 `== 587` 形状。
其余残留（`_zf139` 的 print 标题、`_zf149_jar`/`_zf149_verify` 的注释链）是**历史叙述**，一律不动。

跑法：python build\\zftools\\_zf155_retarget2.py [--write]
"""
import io
import os
import sys

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

ZT = r"E:\PotatoST\build\zftools"
FIXES = [
    (u"_zf73_verify.py", u"all(v == 587 for v in counts.values())",
     u"all(v == 594 for v in counts.values())"),
    (u"_zf78_verify.py", u"len(set(counts.values())) == 1 and list(counts.values())[0] == 587)",
     u"len(set(counts.values())) == 1 and list(counts.values())[0] == 594)"),
    (u"_zf79_verify.py", u"len(set(counts.values())) == 1 and list(counts.values())[0] == 587)",
     u"len(set(counts.values())) == 1 and list(counts.values())[0] == 594)"),
]


def main(argv):
    write = u"--write" in argv
    bad = 0
    for fn, old, new in FIXES:
        p = os.path.join(ZT, fn)
        text = io.open(p, encoding="utf-8", errors="replace").read()
        if new in text and old not in text:
            print(u"  [跳过] %s 已经是新值" % fn)
            continue
        if text.count(old) != 1:
            print(u"  !! %s 锚点命中 %d 次" % (fn, text.count(old)))
            bad += 1
            continue
        print(u"  [改] %s：%s" % (fn, old))
        if write:
            io.open(p, u"w", encoding="utf-8", newline=u"").write(text.replace(old, new, 1))
    print(u"\n%s（问题 %d）" % (u"已落盘" if write else u"（没加 --write，只算不写）", bad))
    return 1 if bad else 0


if __name__ == u"__main__":
    sys.exit(main(sys.argv[1:]))
