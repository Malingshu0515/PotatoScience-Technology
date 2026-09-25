# -*- coding: utf-8 -*-
"""_zf65_precheck.py —— 证明 zf65_pre 里那三份"事后重建的改前件"确实是 ZF64 的状态。

原理：改前件（ZF64 状态）编译出来的 class，应当与 **ZF64 成品 jar** 里的同名 class **逐字节相同**。
      相同 ⇒ 重建是忠实的（至少字节码等价）；不同 ⇒ 重建有误，备份不算数。

用法（三步之间要跑 gradle compileJava）：
    python _zf65_precheck.py apply     # 把改前件换进源码树（当前版本先存到 _zf65_swap）
    gradlew.bat compileJava --offline
    python _zf65_precheck.py compare   # 与 release/PotatoST-0.10.jar 里的 class 逐字节比
    python _zf65_precheck.py restore   # 把 ZF65 版本换回来
    gradlew.bat compileJava --offline
"""
import hashlib
import io
import os
import shutil
import sys
import zipfile

PROJ = r"E:\PotatoST"
PRE = r"C:\Users\Administrator\Desktop\PotatoST救援_20260917_183054\zf65_pre"
SWAP = os.path.join(PROJ, r"build\zftools\_zf65_swap")
JAR = r"C:\Users\Administrator\Desktop\PotatoST救援_20260917_183054\zf64_pre\新增文件\release\PotatoST-0.10.jar"
CLASSES = os.path.join(PROJ, r"build\classes\java\main")

FILES = [
    (r"src\main\java\com\potatost\mod\AlloySmelterBlockEntity.java",
     r"com/potatost/mod/AlloySmelterBlockEntity.class"),
    (r"src\main\java\com\potatost\mod\client\sound\MachineRunningSound.java",
     r"com/potatost/mod/client/sound/MachineRunningSound.class"),
    (r"src\main\java\com\potatost\mod\PotatoST.java",
     r"com/potatost/mod/PotatoST.class"),
]


def sha1(path):
    h = hashlib.sha1()
    with io.open(path, "rb") as fh:
        h.update(fh.read())
    return h.hexdigest()


def apply_pre():
    for rel, _ in FILES:
        cur = os.path.join(PROJ, rel)
        keep = os.path.join(SWAP, rel)
        folder = os.path.dirname(keep)
        if not os.path.isdir(folder):
            os.makedirs(folder)
        shutil.copy2(cur, keep)                       # 先把 ZF65 版本存好
        shutil.copy2(os.path.join(PRE, rel), cur)     # 再换进改前件
        print(u"  apply  %-58s %s -> %s" % (rel, sha1(keep)[:12], sha1(cur)[:12]))
    print(u"改前件已换进源码树（ZF65 版本存于 _zf65_swap）")


def compare():
    fails = 0
    with zipfile.ZipFile(JAR) as z:
        for rel, entry in FILES:
            got = os.path.join(CLASSES, entry.replace("/", os.sep))
            if not os.path.isfile(got):
                print(u"  [FAIL] 编译产物不存在: %s" % entry)
                fails += 1
                continue
            a = hashlib.sha1(z.read(entry)).hexdigest()
            b = sha1(got)
            ok = a == b
            fails += 0 if ok else 1
            print(u"  [%s] %-52s jar %s  build %s" % (u"OK" if ok else u"FAIL",
                                                      entry.split("/")[-1], a[:12], b[:12]))
    print(u"逐字节相同的 class = %d / %d" % (len(FILES) - fails, len(FILES)))
    return 1 if fails else 0


def restore():
    for rel, _ in FILES:
        keep = os.path.join(SWAP, rel)
        cur = os.path.join(PROJ, rel)
        shutil.copy2(keep, cur)
        print(u"  restore %-57s %s" % (rel, sha1(cur)[:12]))
    print(u"ZF65 版本已换回源码树")


if __name__ == "__main__":
    what = sys.argv[1] if len(sys.argv) > 1 else ""
    if what == "apply":
        apply_pre()
    elif what == "compare":
        sys.exit(compare())
    elif what == "restore":
        restore()
    else:
        print(__doc__)
        sys.exit(2)
