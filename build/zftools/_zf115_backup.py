# -*- coding: utf-8 -*-
u"""_zf115_backup.py —— ZF114 **动手前**的改前件（§10）

用户原话：「锂电池构造间 硫酸消耗和储罐容量都先改成原来的十分之一吧」
⇒ `ACID_PER_TICK` 10 → **1**、`TANK_CAPACITY` 8000 → **800**（一炉 = 1×600 = **600 mB**，
800 的罐照样装得下一炉）。四语言介绍里的三个数字、探针里的字面量、`_zf112_verify.py`
与 `_zf112_falsify.py` 的锚点都要跟着改。
"""
import glob
import hashlib
import io
import os
import shutil
import sys

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

ROOT = r"E:\PotatoST"
BK = r"C:\PotatoST救援\zf115_pre"
JAVA = r"src\main\java\com\potatost\mod"
TOOLS = r"build\zftools"
RES = r"src\main\resources"
CHECK = TOOLS + r"\check"

FILES = [
    JAVA + r"\LithiumBatteryPlantBlockEntity.java",
    RES + r"\assets\potato_s_t\lang\zh_cn.json",
    RES + r"\assets\potato_s_t\lang\en_us.json",
    RES + r"\assets\potato_s_t\lang\ja_jp.json",
    RES + r"\assets\potato_s_t\lang\ru_ru.json",
    CHECK + r"\Zf112Check.java",
    r"docs\开发档案.md",
    r"release\PotatoST-0.11.jar",
    r"release\PotatoST-0.11.jar.sha1",
]
NEW = [TOOLS + r"\_zf115_lang.py", TOOLS + r"\_zf115_verify.py", TOOLS + r"\_zf115_gatesnap.py"]

fails = []


def sha1(p):
    return hashlib.sha1(open(p, "rb").read()).hexdigest()


def main():
    if os.path.isdir(BK):
        print(u"  [STOP] 备份根已存在：%s" % BK)
        return 1
    lines, ok = [], 0
    todo = list(FILES)
    for pat in ("_zf*_verify.py", "_zf*_falsify.py", "_zf*_gatesnap.py"):
        for p in sorted(glob.glob(os.path.join(ROOT, TOOLS, pat))):
            rel = os.path.relpath(p, ROOT)
            if rel not in todo:
                todo.append(rel)
    for rel in todo:
        src = os.path.join(ROOT, rel)
        if not os.path.exists(src):
            fails.append(u"缺文件：%s" % rel)
            continue
        dst = os.path.join(BK, rel)
        os.makedirs(os.path.dirname(dst), exist_ok=True)
        b = sha1(src)
        shutil.copy2(src, dst)
        if b != sha1(dst):
            fails.append(u"%s：哈希不一致" % rel)
        else:
            ok += 1
            lines.append(u"%s  %10d  %s" % (b, os.path.getsize(dst), rel))
    io.open(os.path.join(BK, u"_zf115_newfiles.txt"), "w", encoding="utf-8",
            newline=u"\n").write(u"本轮开始前这些路径应当不存在：\n" + u"\n".join(NEW) + u"\n")
    io.open(os.path.join(BK, u"_sha1.txt"), "w", encoding="utf-8", newline=u"\n").write(
        u"\n".join(lines) + u"\n")
    print(u"改前件 %d 份 → %s" % (ok, BK))
    print(u"失败项 = %d" % len(fails))
    for f in fails:
        print(u"  !! " + f)
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())
