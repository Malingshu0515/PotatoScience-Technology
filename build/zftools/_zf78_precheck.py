# -*- coding: utf-8 -*-
u"""_zf78_precheck.py —— 证明"重建的改前件"忠实：编译产物与 ZF77 成品 jar 逐字节比

背景：ZF78 我漏了《§10 动手前先抄一份》⇒ 那 8 个 java 的改前件是**改完反向套用编辑**重建的
（`_zf78_prebackup.py`）。"重建"必须能被证明不是"猜"：

  把改前件换回源码树、删掉本轮新增的 7 个 java + 探针，编译一遍，
  再与 **ZF77 成品 jar**（`release\\PotatoST-0.11.jar`，本轮尚未重打包）里的同名 class
  **逐字节比对**；class 相同 ⇒ 逻辑与当时一致。

⚠ 诚实边界：**注释不参与字节码**，所以逐字节相同只能证明"逻辑一致"，
注释措辞可能与我当时的原文有差异（MANIFEST 里如实写了这一点）。

用法：python build/zftools/_zf78_precheck.py
"""
import io
import os
import sys
import zipfile
import hashlib

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

ROOT = r"E:\PotatoST"
CLASSES = os.path.join(ROOT, "build", "classes", "java", "main")
JAR = os.path.join(ROOT, "release", "PotatoST-0.11.jar")

# 改前件覆盖的 8 个类（含它们的内部类/匿名类：class 文件名以 $ 开头）
TARGETS = [
    "com/potatost/mod/ModFluids",
    "com/potatost/mod/ModItems",
    "com/potatost/mod/ModBlocks",
    "com/potatost/mod/ModMenus",
    "com/potatost/mod/PotatoST",
    "com/potatost/mod/PotatoSTClient",
    "com/potatost/mod/client/gui/parts/EnergyBarPart",
    "com/potatost/mod/client/gui/parts/FluidTankPart",
]

passed = 0
failed = 0
fails = []


def main():
    global passed, failed
    print(u"=========== ZF78 改前件忠实性核对 ===========")
    if not os.path.exists(JAR):
        print(u"  [FAIL] 找不到参照成品 jar：%s" % JAR)
        return 1
    with zipfile.ZipFile(JAR) as zf:
        jar_names = set(zf.namelist())

        def jar_bytes(name):
            return zf.read(name)

        for target in TARGETS:
            variants = sorted(n for n in jar_names
                              if n == target + ".class" or n.startswith(target + "$"))
            if not variants:
                print(u"  [FAIL] jar 里没有 %s（参照物选错了？）" % target)
                failed += 1
                fails.append(target + u"：jar 里找不到")
                continue
            same = 0
            diff = []
            missing = []
            for name in variants:
                path = os.path.join(CLASSES, name.replace("/", os.sep))
                if not os.path.exists(path):
                    missing.append(name)
                    continue
                a = open(path, "rb").read()
                b = jar_bytes(name)
                if hashlib.sha1(a).hexdigest() == hashlib.sha1(b).hexdigest():
                    same += 1
                else:
                    diff.append(name)
            ok = not diff and not missing
            tag = u"[OK]  " if ok else u"[FAIL]"
            print(u"  %s %-52s class=%d 相同=%d 不同=%s 缺=%s"
                  % (tag, target.split("/")[-1], len(variants), same,
                     diff or u"无", missing or u"无"))
            if ok:
                passed += 1
            else:
                failed += 1
                fails.append(u"%s：不同 %s / 缺 %s" % (target, diff, missing))
    print(u"\n------------------------------")
    print(u"通过 = %d   失败 = %d" % (passed, failed))
    for f in fails:
        print(u"  !! " + f)
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
