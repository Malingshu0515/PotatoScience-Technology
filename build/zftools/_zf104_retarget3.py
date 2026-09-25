# -*- coding: utf-8 -*-
r"""_zf104_retarget3.py —— 349 → 350 的第二遍：这些文件的锚点出现**两次**（标签里也有一个）

`_zf104_retarget2.py` 按"每份 1 处"的假设写，结果 8 份里 `349` 出现两次
（一次在断言、一次在断言的名字/标签字符串里）⇒ 那一遍对它们**全部跳过**（没改坏，只是没改）。
这一遍按"每份 2 处"精确替换，仍然每份改完 `py_compile`。
"""
import io
import os
import py_compile
import sys

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

ZT = r"E:\PotatoST\build\zftools"
fails = []
EXPECT2 = ["_zf71_verify.py", "_zf73_verify.py", "_zf75_verify.py", "_zf78_verify.py",
           "_zf79_verify.py", "_zf81_verify.py", "_zf82_verify.py", "_zf103_verify.py"]


def main():
    print(u"================ 349 → 350（每份 2 处）================")
    for name in EXPECT2:
        path = os.path.join(ZT, name)
        text = io.open(path, encoding="utf-8").read()
        hits = text.count(u"349")
        if hits != 2:
            fails.append(u"%s：349 命中 %d 次（应为 2）" % (name, hits))
            print(u"  [FAIL] %-22s 命中 %d 次" % (name, hits))
            continue
        orig = text
        text = text.replace(u"349", u"350")
        io.open(path, "w", encoding="utf-8", newline=u"").write(text)
        try:
            py_compile.compile(path, doraise=True)
        except Exception as exc:
            fails.append(u"%s：改后 py_compile 失败 %s" % (name, exc))
            io.open(path, "w", encoding="utf-8", newline=u"").write(orig)
            print(u"  [FAIL] %-22s py_compile 失败，已回滚" % name)
            continue
        print(u"  [OK]   %-22s 改 2 处（py_compile 通过）" % name)

    print(u"")
    print(u"================ 复查：活体脚本里还有没有 349 ================")
    left = []
    for f in sorted(os.listdir(ZT)):
        if not (f.endswith(".py") and f.startswith("_zf")):
            continue
        if f.startswith("_zf104_retarget"):
            continue
        t = io.open(os.path.join(ZT, f), encoding="utf-8").read()
        if u"349" in t and (u"verify" in f or u"falsify" in f):
            left.append(f)
    if left:
        fails.append(u"还留着 349：%s" % left)
        print(u"  [FAIL] %s" % left)
    else:
        print(u"  [OK]   已无 349")

    print(u"")
    print(u"失败项 = %d" % len(fails))
    for f in fails:
        print(u"  !! " + f)
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())
