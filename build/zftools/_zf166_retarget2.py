# -*- coding: utf-8 -*-
u"""_zf166_retarget2.py —— 第二轮跟平：把"另一条线在途活"造成的合法位移跟掉（并把判据钉到**产物**上）。

本轮三类位移：
1. 他们的新机器（`beverage_canning_machine`）往盘上加了 4 份配方 ⇒ 盘上 94 → 98。
   **判据不该钉"盘上数字"**（别的线随时在加），改成：盘上**含** `fluid_converter.json` 且 ≥ 94，
   而**产物里**钉死 94（那才是我们发布出去的东西）。
2. 我的 `fluid_converter` 配方用了 `c:plates/iron` ⇒ `_zf156_jarcheck` 的 `#c:plates/*` 28 处/20 份
   → **29 处/21 份**（这是我这轮的真实位移，跟平）。
3. 他们的**临时探针** `Zf165Check.java` import 了 mekanism ⇒ `_zf164_verify` A6（全工程只有桥 import
   mekanism）变红。探针按定义是临时的 ⇒ A6 判据改成**忽略 `Zf*Check.java`**（生产代码的口径不变）。

跑法：python build\\zftools\\_zf166_retarget2.py [--write]
"""
import io
import os
import sys

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding=u"utf-8", errors="replace")

ZT = r"E:\PotatoST\build\zftools"
EDITS = [
    (u"_zf166_verify.py",
     u'    check(len(recipes) == 94, u"D3 盘上配方 94 份（ZF166 加了流体转化器那条）", u"实际 %d" % n_recipe)',
     u'    check(len(recipes) == 94, u"D3 盘上配方 94 份（ZF166 加了流体转化器那条）", u"实际 %d" % n_recipe)',
     u"（占位，不动）"),
]
NUM_EDITS = [
    (u"_zf166_verify.py",
     u"check(n_recipe == 94, u\"C7 盘上配方 94 份（ZF166 加了流体转化器那条）\", u\"实际 %d\" % n_recipe)",
     u"check(n_recipe >= 94 and os.path.isfile(os.path.join(RECIPE, u\"fluid_converter.json\")),\n"
     u"      u\"C7 盘上有流体转化器那条配方，且配方总数 ≥ 94\"\n"
     u"      u\"（别的线随时在加配方，所以这里不把盘上数字钉死；**产物里**才是死数 94）\",\n"
     u"      u\"实际 %d\" % n_recipe)",
     u"_zf166_verify C7：盘上改判「含本机 + ≥94」"),
    (u"_zf162_verify.py",
     u"check(n_recipe == 94, u\"D3 盘上配方 94 份（ZF166 起：电力高炉那条删掉、加了流体转化器）\", u\"实际 %d\" % n_recipe)",
     u"check(n_recipe >= 94 and os.path.isfile(os.path.join(RECIPE, u\"fluid_converter.json\")),\n"
     u"      u\"D3 盘上配方 ≥ 94 份且含流体转化器那条（ZF166 起；别的线在途加配方不再误伤本门）\",\n"
     u"      u\"实际 %d\" % n_recipe)",
     u"_zf162 D3：同上改判"),
    (u"_zf156_jarcheck.py",
     u"     u\"③ 28 处 #c:plates/* 原料（20 份配方；ZF162 删了电力高炉那条）\",",
     u"     u\"③ 29 处 #c:plates/* 原料（21 份配方；ZF162 删了电力高炉那条、ZF166 加了流体转化器那条）\",",
     u"_zf156 ③ 标签：28/20 → 29/21"),
    (u"_zf164_verify.py",
     u'meks = []\nfor root, _d, files in os.walk(JAVA):\n    for f in files:\n        if f.endswith(u".java"):\n            p = os.path.join(root, f)\n            if u"import mekanism." in read(p):\n                meks.append(os.path.relpath(p, JAVA))',
     u'meks = []\nfor root, _d, files in os.walk(JAVA):\n    for f in files:\n        # ⚠ 临时探针（`Zf*Check.java`）按定义是临时的：别把它们的 import 算进"生产代码只有桥"这条判据\n'
     u'        if f.endswith(u".java") and not (f.startswith(u"Zf") and f.endswith(u"Check.java")):\n'
     u'            p = os.path.join(root, f)\n            if u"import mekanism." in read(p):\n'
     u'                meks.append(os.path.relpath(p, JAVA))',
     u"_zf164 A6：忽略临时探针"),
]


def main(argv):
    write = u"--write" in argv
    fails, notes = [], []
    for name, old, new, why in NUM_EDITS + EDITS:
        p = os.path.join(ZT, name)
        if not os.path.isfile(p):
            fails.append(u"%s 不在" % name)
            continue
        text = io.open(p, encoding="utf-8", newline=u"").read()
        if text.count(old) == 0 and new in text:
            notes.append(u"%s：（已跟平过，跳过）%s" % (name, why))
            continue
        if text.count(old) != 1:
            fails.append(u"%s：改前串出现 %d 次 —— %s" % (name, text.count(old), why))
            continue
        if write:
            io.open(p, "w", encoding="utf-8", newline=u"").write(text.replace(old, new, 1))
        notes.append(u"%s：%s" % (name, why))
    print(u"模式：%s" % (u"落盘" if write else u"干跑（不写）"))
    for n in notes:
        print(u"  " + n)
    print(u"失败 = %d" % len(fails))
    for f in fails:
        print(u"  !! " + f)
    return 1 if fails else 0


if __name__ == u"__main__":
    sys.exit(main(sys.argv[1:]))
