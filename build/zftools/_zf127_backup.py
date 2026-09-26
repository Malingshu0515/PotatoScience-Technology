# -*- coding: utf-8 -*-
u"""_zf127_backup.py —— ZF127 的改前件（§10：**先建备份，再动第一个字节**）

用户原话：
「加一个银线轴 和铜线轴一致（先搞银线 配方什么的都一致只不过铜的换成银的）
  材质先不画 连接线缆还是一样的像素大小 只不过变成银白色的 传输速率 16134Fe/t」

⇒ 本轮做**银线 / 银线轴**这一档线缆：
   · 物品 `silver_wire`（银线）+ `silver_wire_spool`（银线轴，32 点耐久，与铜线轴一致）；
   · 配方与铜线轴**逐字对应**，只把铜换成银（铜线 2 锭→4 根 / 线轴 8 根+空线轴→1 个）；
   · 贴图**先不画**（借用原版，与项目里一贯的占位做法一致）；
   · 连接线缆**像素尺寸不变**（`WIRE_RADIUS` 一个字节不改），只是**颜色**变银白色；
   · 单线速率 **16134 FE/t**（用户给的数；铜线仍是 2048）。

⚠ **这一轮要把 `PotatoST.java`（探针挂载点）写进改前件清单** —— ZF117 / ZF119 / ZF126
   连着漏了三次，每次都得事后补账。这次先写进 FILES 再动任何字节。

跑法：
    python build\\zftools\\_zf127_backup.py
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
BK = r"C:\PotatoST救援\zf127_pre"
JAVA = r"src\main\java\com\potatost\mod"
TOOLS = r"build\zftools"

FILES = [
    # ---- Java（4 份要改 + 1 份探针挂载点）----
    JAVA + r"\ModItems.java",
    JAVA + r"\TerminalBlock.java",
    JAVA + r"\TerminalBlockEntity.java",
    JAVA + r"\client\TerminalRenderer.java",
    JAVA + r"\PotatoST.java",
    # ---- 四语言 ----
    r"src\main\resources\assets\potato_s_t\lang\zh_cn.json",
    r"src\main\resources\assets\potato_s_t\lang\en_us.json",
    r"src\main\resources\assets\potato_s_t\lang\ja_jp.json",
    r"src\main\resources\assets\potato_s_t\lang\ru_ru.json",
    # ---- 配方生成器表 + 本轮的快照门 ----
    TOOLS + r"\_zf45_recipes.py",
    TOOLS + r"\_zf127_gatesnap.py",
    # ---- 文档 ----
    r"docs\开发档案.md",
    r"docs\多会话协作交接.md",
    r"docs\贴图清单.md",
    r"docs\UpdateAnnouncement_EN.md",
    # ---- 成品与 .sha1（打包线在盯，先抄一份留底）----
    r"release\PotatoST-0.11.jar",
    r"release\PotatoST-0.11.jar.sha1",
]

NEW = [
    JAVA + r"\Zf127Check.java",
    TOOLS + r"\check\Zf127Check.java",
    TOOLS + r"\_zf127_java.py",
    TOOLS + r"\_zf127_lang.py",
    TOOLS + r"\_zf127_assets.py",
    TOOLS + r"\_zf127_retarget.py",
    TOOLS + r"\_zf127_verify.py",
    TOOLS + r"\_zf127_falsify.py",
    TOOLS + r"\_zf127_unprobe.py",
    TOOLS + r"\_zf127_docs.py",
    TOOLS + r"\_zf127_commit.py",
    TOOLS + r"\_zf127_probe_utf8.txt",
    r"src\main\resources\assets\potato_s_t\models\item\silver_wire.json",
    r"src\main\resources\assets\potato_s_t\models\item\silver_wire_spool.json",
    r"src\main\resources\data\potato_s_t\recipe\silver_wire.json",
    r"src\main\resources\data\potato_s_t\recipe\silver_wire_spool.json",
]

fails, notes, lines = [], [], []
ok = 0


def sha1(p):
    return hashlib.sha1(open(p, "rb").read()).hexdigest()


def add(todo, rel):
    if rel not in todo:
        todo.append(rel)


def main():
    global ok
    if os.path.isdir(BK):
        print(u"  [STOP] 备份根已存在：%s" % BK)
        return 1
    todo = list(FILES)
    # 常驻校验 / 反证刀 / 守卫 / 复现 / 体检：全都抄一份（活体数字随时可能被本轮顶到）
    for pat in ("_zf*_verify.py", "_zf*_falsify.py", "_zf*_guard.py",
                "_zf*_repro.py", "_zf*_audit.py", "_zf*_langaudit.py"):
        for p in sorted(glob.glob(os.path.join(ROOT, TOOLS, pat))):
            add(todo, os.path.relpath(p, ROOT))
    # 配方 JSON 与 item 模型整目录（本轮要往里加新文件，留底才能证明"别的没被动"）
    for sub in (r"src\main\resources\data\potato_s_t\recipe",
                r"src\main\resources\assets\potato_s_t\models\item"):
        for p in sorted(glob.glob(os.path.join(ROOT, sub, "*.json"))):
            add(todo, os.path.relpath(p, ROOT))

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

    # 点名件（这几份是本轮判据要用的改前件，少一份都不行）
    POINT = [JAVA + r"\PotatoST.java", JAVA + r"\TerminalBlockEntity.java",
             JAVA + r"\TerminalRenderer.java", TOOLS + r"\_zf45_recipes.py",
             r"src\main\resources\assets\potato_s_t\lang\zh_cn.json",
             r"src\main\resources\assets\potato_s_t\lang\ru_ru.json",
             r"docs\开发档案.md", r"docs\多会话协作交接.md"]
    miss = [rel for rel in POINT if not os.path.exists(os.path.join(BK, rel))]
    if miss:
        fails.append(u"点名件没抄到：%s" % u"、".join(miss))
    else:
        notes.append(u"点名件全在（**含探针挂载点 PotatoST.java** / 端子 / 渲染 / 配方表 / 中俄语言 / 两份文档）")

    existed = [rel for rel in NEW if os.path.exists(os.path.join(ROOT, rel))]
    if existed:
        fails.append(u"这些「新增件」已经存在了：%s" % u"、".join(existed))
    else:
        notes.append(u"新增件 %d 条：动手前一条都不存在" % len(NEW))

    io.open(os.path.join(BK, u"_zf127_newfiles.txt"), "w", encoding="utf-8",
            newline=u"\n").write(u"本轮开始前这些路径应当不存在：\n" + u"\n".join(NEW) + u"\n")
    io.open(os.path.join(BK, u"_sha1.txt"), "w", encoding="utf-8", newline=u"\n").write(
        u"\n".join(lines) + u"\n")
    io.open(os.path.join(BK, u"_说明.txt"), "w", encoding="utf-8", newline=u"\n").write(
        u"ZF127 改前件：银线 / 银线轴（与铜线轴一致，单线速率 16134 FE/t，贴图先不画）\n"
        u"备份脚本：build/zftools/_zf127_backup.py\n"
        u"⚠ 本清单**一开始就含** PotatoST.java（探针挂载点）—— ZF117/ZF119/ZF126 连漏三次。\n")
    print(u"\n".join(u"  [OK] " + n for n in notes))
    print(u"改前件 %d 份 → %s" % (ok, BK))
    print(u"失败项 = %d" % len(fails))
    for f in fails:
        print(u"  !! " + f)
    return 1 if fails else 0


if __name__ == u"__main__":
    sys.exit(main())
