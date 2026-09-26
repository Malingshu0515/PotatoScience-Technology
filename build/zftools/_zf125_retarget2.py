# -*- coding: utf-8 -*-
u"""_zf125_retarget2.py —— 把"活体数字"**真正**跟平：464 → **476**（ZF125 四语言 +12 键）

⚠ **本脚本是补第一版 `_zf125_retarget.py` 的漏**：

  第一版我只用 PowerShell 的
      Get-ChildItem build\\zftools -File -Include *.py,*.txt -Recurse | Select-String '\\b464\\b'
  捞了一遍，只捞到 4 份（`_zf100~_zf103`）。**那个写法漏文件** ——
  交接文档 §118 明明白白写着"加/删一个语言键要一起改 **17 份**校验器"，
  而全门快照一跑，红的是 **20+ 份**（`_zf71 _zf73 _zf75 _zf78 _zf79 _zf80 _zf81 _zf82 _zf93
  _zf96 _zf97 _zf98 _zf107 _zf109 _zf111 _zf112 _zf114 _zf117 _zf118 _zf119 _zf122` …），
  每一条都是"期望 464、实际 476" —— **判据过期，不是本轮改错**。

  这一次不再靠手捞：用工程自己的门（`grep 工具` / ripgrep）把
  **所有** `_zf*_verify.py` 里含 `464` 的都列出来，逐份断言"命中次数 == 预期"再改。

**为什么是 476 而不是 475**：本轮先加了 11 键（464 → 475），随后常驻体检
`_zf123_langaudit.py` 抓出「接线口这个注册 id 没有语言键」⇒ 照盘上先例
（`alloy_smelter_port` / `alloy_smelter_part` 都有 `block.potato_s_t.*` 键）
补了第 12 个键 `block.potato_s_t.diesel_generator_port` ⇒ **464 + 12 = 476**。

跑法：
    python build\\zftools\\_zf125_retarget2.py
"""
import io
import os
import re
import sys

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

ZT = r"E:\PotatoST\build\zftools"

OLD, NEW = u"464", u"476"

# 逐份给出"预期命中次数"（**用 Python 精确数出来的**，不是靠 grep 工具那 8 条上限的截断输出）
# 第一版我按截断输出填的预期，11 份当场报"命中次数不对"并停手（这正是"断言不匹配就别改"的价值）。
FILES = {
    u"_zf81_verify.py": 2,
    u"_zf109_verify.py": 3,
    u"_zf112_verify.py": 5,
    u"_zf117_verify.py": 6,
    u"_zf118_verify.py": 2,
    u"_zf119_verify.py": 4,
}

# 第一版已经跟到 475 的 4 份：本轮补了第 12 个键 ⇒ 475 → 476
FILES_475 = {
    u"_zf100_verify.py": 1,
    u"_zf101_verify.py": 1,
    u"_zf102_verify.py": 1,
    u"_zf103_verify.py": 2,
}

# 残留体检时豁免的：只有注释里提到历史数字，没有真判据
EXEMPT = (u"_zf121_verify.py", u"_zf125_verify.py")

notes, fails = [], []


def count(text, num):
    return len(re.findall(r"\b%s\b" % num, text))


def sweep(name, old, new, times):
    path = os.path.join(ZT, name)
    if not os.path.exists(path):
        fails.append(u"%s 不在盘上" % name)
        return
    text = io.open(path, encoding="utf-8", newline=u"").read()
    n_old = count(text, old)
    n_new = count(text, new)
    if n_old == 0 and n_new >= times:
        notes.append(u"%s：已经是 %s（%d 处）" % (name, new, n_new))
        return
    if n_old != times:
        fails.append(u"%s：%s 命中 %d 次（预期 %d）—— 停手" % (name, old, n_old, times))
        return
    io.open(path, "w", encoding="utf-8", newline=u"").write(
        re.sub(r"\b%s\b" % old, new, text))
    back = io.open(path, encoding="utf-8", newline=u"").read()
    if count(back, old):
        fails.append(u"%s：改完还残留 %s" % (name, old))
        return
    notes.append(u"%s：%d 处 %s → %s" % (name, times, old, new))


def main():
    for name in sorted(FILES):
        sweep(name, OLD, NEW, FILES[name])
    for name in sorted(FILES_475):
        sweep(name, u"475", NEW, FILES_475[name])

    # 残留体检：盘上所有 _zf*_verify.py 里不该再有裸的 464（豁免名单见上）
    left = []
    for fn in sorted(os.listdir(ZT)):
        if not fn.startswith(u"_zf") or not fn.endswith(u"_verify.py") or fn in EXEMPT:
            continue
        t = io.open(os.path.join(ZT, fn), encoding="utf-8").read()
        if count(t, OLD):
            left.append(fn)
    if left:
        fails.append(u"这些 _zf*_verify.py 里还有 464：%s" % u"、".join(left))
    else:
        notes.append(u"除豁免的 %d 份外，盘上 _zf*_verify.py 里再无裸的 464" % len(EXEMPT))

    print(u"\n".join(u"  [OK] " + n for n in notes))
    print(u"改了 %d 份" % len([n for n in notes if u"476" in n]))
    print(u"失败项 = %d" % len(fails))
    for f in fails:
        print(u"  !! " + f)
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())
