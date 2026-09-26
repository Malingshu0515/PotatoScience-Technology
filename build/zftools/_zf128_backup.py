# -*- coding: utf-8 -*-
u"""_zf128_backup.py —— ZF128 的改前件（§10：**先建备份，再动第一个字节**）

用户原话（接着 ZF124 那条挂着的账问的）：
「成就栏换成毒马铃薯 但是成就还是粉碎机可以嘛」

查证（`build\\neoForm\\neoFormJoined1.21.1-20240808.144430\\sources.jar`，本工程编译用的那份）：
`AdvancementTab.java` 第 51 行 `this.icon = display.getIcon();`、第 53 行把**同一个 `display`**
交给根节点 widget；`AdvancementWidget.java` 第 162 行画的是 `this.display.getIcon()`
⇒ **页签图标与根节点图标是同一个字段**，拆不开（用户选的是"换，判据/说明照旧"）。

⚠ **`PotatoST.java` 一开始就写进清单**（探针挂载点；ZF117/ZF119/ZF126 三次漏账的教训）。

跑法：
    python build\\zftools\\_zf128_backup.py
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
BK = r"C:\PotatoST救援\zf128_pre"
TOOLS = r"build\zftools"
ADV = r"src\main\resources\data\potato_s_t\advancement"

FILES = [
    ADV + r"\new_beginning.json",
    r"src\main\java\com\potatost\mod\PotatoST.java",      # ← 探针挂载点，先写进清单
    TOOLS + r"\_zf70_verify.py",
    TOOLS + r"\_zf107_verify.py",
    TOOLS + r"\_zf124_verify.py",
    TOOLS + r"\_zf107_adv.py",
    r"src\main\resources\assets\potato_s_t\lang\zh_cn.json",
    r"src\main\resources\assets\potato_s_t\lang\en_us.json",
    r"src\main\resources\assets\potato_s_t\lang\ja_jp.json",
    r"src\main\resources\assets\potato_s_t\lang\ru_ru.json",
    r"docs\开发档案.md",
    r"docs\多会话协作交接.md",
    r"docs\UpdateAnnouncement_EN.md",
    r"release\PotatoST-0.11.jar",
    r"release\PotatoST-0.11.jar.sha1",
]

NEW = [
    r"src\main\java\com\potatost\mod\Zf128Check.java",
    TOOLS + r"\check\Zf128Check.java",
    TOOLS + r"\_zf128_json.py",
    TOOLS + r"\_zf128_gatefix.py",
    TOOLS + r"\_zf128_verify.py",
    TOOLS + r"\_zf128_falsify.py",
    TOOLS + r"\_zf128_mount.py",
    TOOLS + r"\_zf128_unprobe.py",
    TOOLS + r"\_zf128_docs.py",
    TOOLS + r"\_zf128_gatesnap.py",
    TOOLS + r"\_zf128_commit.py",
    TOOLS + r"\_zf128_commit_msg.txt",
    TOOLS + r"\_zf128_probe_utf8.txt",
]

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
    for pat in ("_zf*_verify.py", "_zf*_falsify.py", "_zf*_guard.py",
                "_zf*_repro.py", "_zf*_audit.py"):
        for p in sorted(glob.glob(os.path.join(ROOT, TOOLS, pat))):
            rel = os.path.relpath(p, ROOT)
            if rel not in todo:
                todo.append(rel)
    for p in sorted(glob.glob(os.path.join(ROOT, ADV, "*.json"))):
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

    POINT = [ADV + r"\new_beginning.json", r"src\main\java\com\potatost\mod\PotatoST.java",
             TOOLS + r"\_zf70_verify.py", TOOLS + r"\_zf107_verify.py",
             TOOLS + r"\_zf124_verify.py", TOOLS + r"\_zf107_adv.py",
             r"docs\开发档案.md", r"docs\多会话协作交接.md"]
    miss = [rel for rel in POINT if not os.path.exists(os.path.join(BK, rel))]
    if miss:
        fails.append(u"点名件没抄到：%s" % u"、".join(miss))
    else:
        notes.append(u"点名件全在（**含探针挂载点 PotatoST.java** / 根成就 JSON / 三份往轮门 / 生成器 / 两份文档）")

    existed = [rel for rel in NEW if os.path.exists(os.path.join(ROOT, rel))]
    if existed:
        fails.append(u"这些「新增件」已经存在了：%s" % u"、".join(existed))
    else:
        notes.append(u"新增件 %d 条：动手前一条都不存在" % len(NEW))

    io.open(os.path.join(BK, u"_zf128_newfiles.txt"), "w", encoding="utf-8",
            newline=u"\n").write(u"本轮开始前这些路径应当不存在：\n" + u"\n".join(NEW) + u"\n")
    io.open(os.path.join(BK, u"_sha1.txt"), "w", encoding="utf-8", newline=u"\n").write(
        u"\n".join(lines) + u"\n")
    io.open(os.path.join(BK, u"_说明.txt"), "w", encoding="utf-8", newline=u"\n").write(
        u"ZF128 改前件：成就页签图标 微型粉碎机 → 毒马铃薯（判据/说明不变）\n"
        u"备份脚本：build/zftools/_zf128_backup.py\n"
        u"⚠ 本清单**一开始就含** PotatoST.java（探针挂载点）。\n")
    print(u"\n".join(u"  [OK] " + n for n in notes))
    print(u"改前件 %d 份 → %s" % (ok, BK))
    print(u"失败项 = %d" % len(fails))
    for f in fails:
        print(u"  !! " + f)
    return 1 if fails else 0


if __name__ == u"__main__":
    sys.exit(main())
