# -*- coding: utf-8 -*-
u"""_zf103_dump.py —— 只读诊断：把本轮几个 class 的常量池/方法表/字节码立即数打出来看

用来定位 `_zf103_verify.py` 里的假 FAIL（查错了集合、查错了 class）。
"""
import importlib.util
import sys

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

spec = importlib.util.spec_from_file_location(
    "v", r"E:\PotatoST\build\zftools\_zf103_verify.py")
m = importlib.util.module_from_spec(spec)
sys.argv = ["x"]
spec.loader.exec_module(m)

for name in sys.argv[1:] or ["ModArmorPiece", "ModArmorSet", "ModArmorItems", "ModArmorMaterials"]:
    p = m.cls(name)
    print(u"\n================ %s ================" % name)
    print(u"方法：%s" % sorted(n for n, _d in p.methods))
    print(u"int 池：%s" % sorted(p.ints))
    print(u"float 池：%s" % sorted(p.floats))
    print(u"double 池：%s" % sorted(p.doubles))
    print(u"字节码 int 立即数：%s" % sorted(p.bc_ints))
    print(u"字节码 float/double：%s" % sorted(p.bc_floats))
    interesting = sorted(s for s in p.strings
                         if any(k in s for k in ("armor", "potato", "hold_shift", "iron",
                                                 "star", "titanium", "message", "tooltip")))
    print(u"相关字符串：%s" % interesting)
