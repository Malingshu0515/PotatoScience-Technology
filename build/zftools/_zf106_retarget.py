# -*- coding: utf-8 -*-
r"""_zf106_retarget.py —— 语言键数锚点 **350 → 398**（并行的另一条线又加了 48 个键）

第三次跟"活体数字"了（335 → 349 → 350 → **398**）。§4.36 口径不变：**改锚点，不放宽断言**。

⚠ 有些脚本里 `350` 出现两次（断言里一次、断言的名字/标签里一次）⇒ 这一遍统一"全替换"，
  并用"替换前后 350 的个数"核对，不再按"每份 1 处 / 2 处"分两批（前两轮就是这么返工的）。
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
OLD, NEW = u"350", u"398"
fails = []
changed_files = []


def main():
    print(u"================ 活体脚本：%s → %s ================" % (OLD, NEW))
    for name in sorted(os.listdir(ZT)):
        if not name.endswith(u".py") or not name.startswith(u"_zf"):
            continue
        if u"retarget" in name:
            continue
        if not (u"verify" in name or u"falsify" in name or u"recipe_guard" in name):
            continue
        path = os.path.join(ZT, name)
        text = io.open(path, encoding="utf-8").read()
        # 只替换"独立出现的 350"（避免动到 3500 这类），且必须成对出现在 键/KEY 语境里
        import re
        hits = len(re.findall(r"(?<![0-9])350(?![0-9])", text))
        if not hits:
            continue
        orig = text
        text = re.sub(r"(?<![0-9])350(?![0-9])", NEW, text)
        io.open(path, "w", encoding="utf-8", newline=u"").write(text)
        try:
            py_compile.compile(path, doraise=True)
        except Exception as exc:
            fails.append(u"%s：py_compile 失败 %s" % (name, exc))
            io.open(path, "w", encoding="utf-8", newline=u"").write(orig)
            print(u"  [FAIL] %-24s 已回滚" % name)
            continue
        changed_files.append(name)
        print(u"  [OK]   %-24s 改 %d 处" % (name, hits))

    print(u"")
    print(u"================ 复查：活体脚本里还有没有 350 ================")
    left = []
    import re
    for name in sorted(os.listdir(ZT)):
        if not (name.endswith(u".py") and name.startswith(u"_zf")):
            continue
        if u"retarget" in name:
            continue
        t = io.open(os.path.join(ZT, name), encoding="utf-8").read()
        if re.search(r"(?<![0-9])350(?![0-9])", t):
            left.append(name)
    if left:
        fails.append(u"还留着 350：%s" % left)
        print(u"  [FAIL] %s" % left)
    else:
        print(u"  [OK]   已无 350")

    print(u"")
    print(u"改了 %d 份：%s" % (len(changed_files), changed_files))
    print(u"失败项 = %d" % len(fails))
    for f in fails:
        print(u"  !! " + f)
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())
