# -*- coding: utf-8 -*-
u"""_zf126_backup.py —— ZF126 的改前件（§10：**先建备份，再动第一个字节**）

用户原话（附一张游戏内截图：Jade 那种悬浮框，标题「柴油发电机接线口」、里面一行「柴油 7.49B」）：
「这个加个fe缓存 18k的fe」

⇒ 一件小事：大型柴油发电机的 **FE 缓冲**从 ZF125 时自定的 7200（= 1 tick 的产量）
   改成**用户给的 18000**，并在界面上**画出来**（界面上原来只有柴油罐 + 工作指示灯）。

跑法：
    python build\\zftools\\_zf126_backup.py
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
BK = r"C:\PotatoST救援\zf126_pre"
JAVA = r"src\main\java\com\potatost\mod"
TOOLS = r"build\zftools"

FILES = [
    JAVA + r"\DieselGeneratorBlockEntity.java",
    JAVA + r"\client\DieselGeneratorScreen.java",
    JAVA + r"\DieselGeneratorMenu.java",
    TOOLS + r"\_zf125_verify.py",
    TOOLS + r"\_zf125_falsify.py",
    r"docs\开发档案.md",
    r"docs\多会话协作交接.md",
    r"release\PotatoST-0.11.jar",
    r"release\PotatoST-0.11.jar.sha1",
]

NEW = [TOOLS + r"\_zf126_%s.py" % s for s in
       ("backup", "java", "verify", "falsify", "unprobe", "docs")] + \
      [JAVA + r"\Zf126Check.java", TOOLS + r"\check\Zf126Check.java"]

fails, notes, lines = [], [], []
ok = 0


def sha1(p):
    return hashlib.sha1(open(p, "rb").read()).hexdigest()


def main():
    global ok
    if os.path.isdir(BK):
        print(u"  [STOP] 备份根已存在：%s" % BK)
        return 1
    todo = list(FILES)
    for pat in ("_zf*_verify.py", "_zf*_falsify.py"):
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
    bad = [rel for rel in todo
           if os.path.exists(os.path.join(ROOT, rel)) and os.path.exists(os.path.join(BK, rel))
           and sha1(os.path.join(ROOT, rel)) != sha1(os.path.join(BK, rel))]
    if bad:
        fails.append(u"回读不一致：%s" % u"、".join(bad))
    else:
        notes.append(u"回读证明：%d 份备份与盘上逐字节相同" % ok)

    for rel in (JAVA + r"\DieselGeneratorBlockEntity.java", TOOLS + r"\_zf125_verify.py",
                r"docs\开发档案.md"):
        if not os.path.exists(os.path.join(BK, rel)):
            fails.append(u"点名件没抄到：%s" % rel)
    notes.append(u"点名件全在（方块实体 / ZF125 的校验器 / 开发档案）")

    probe = [rel for rel in NEW if not rel.endswith(u"_zf126_backup.py")]
    existed = [rel for rel in probe if os.path.exists(os.path.join(ROOT, rel))]
    if existed:
        fails.append(u"这些「新增件」已经存在了：%s" % u"、".join(existed))
    else:
        notes.append(u"新增件 %d 条：动手前一条都不存在" % len(probe))

    io.open(os.path.join(BK, u"_zf126_newfiles.txt"), "w", encoding="utf-8",
            newline=u"\n").write(u"本轮开始前这些路径应当不存在：\n" + u"\n".join(NEW) + u"\n")
    io.open(os.path.join(BK, u"_sha1.txt"), "w", encoding="utf-8", newline=u"\n").write(
        u"\n".join(lines) + u"\n")
    io.open(os.path.join(BK, u"_说明.txt"), "w", encoding="utf-8", newline=u"\n").write(
        u"ZF126 改前件：大型柴油发电机的 FE 缓冲 7200 → 18000（用户给定）+ 界面上画出来\n"
        u"备份脚本：build/zftools/_zf126_backup.py\n")
    print(u"\n".join(u"  [OK] " + n for n in notes))
    print(u"改前件 %d 份 → %s" % (ok, BK))
    print(u"失败项 = %d" % len(fails))
    for f in fails:
        print(u"  !! " + f)
    return 1 if fails else 0


if __name__ == u"__main__":
    sys.exit(main())
