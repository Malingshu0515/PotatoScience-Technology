# -*- coding: utf-8 -*-
u"""_zf139_backup.py —— ZF139 的改前件（§10：**先建备份，再动第一个字节**）

用户原话：
「振金套你看看能不能略微加强一下 现在地位太尴尬了 比星璨麻烦很多 却大大不如晚上的星璨 简直就是个白板」
追问一轮后他拍板：**乙方案 + 一条新的套装效果**：
「用乙吧 再加一个套装效果；10%概率返还100%的伤害给攻击者 如果攻击者被反伤而死 死亡提示为
  「攻击者」踢到了铁板」

⇒ 本轮要动的盘上文件（备份清单就是它们 + 所有活着的门 + 三份文档 + 旧成品）：
  ① `ModArmorMaterials.java`（振金护甲值 3/8/6/3 → **4/9/7/4**）
  ② `ModVibraniumSet.java`（+ 常驻抗性 I、+ 免疫摔落、+ 10% 反伤）
  ③ `PotatoST.java`（探针挂载点 —— **一开始就写进清单**，ZF117/ZF119/ZF126 三次漏账的教训）
  ④~⑦ 四份 lang（+1 键 `death.attack.potato_s_t.vibranium_reflect`、改 `vibranium_set` 的值）
  ⑧ 新增 `data\\potato_s_t\\damage_type\\vibranium_reflect.json`（本工程**第一个**自定义伤害类型）
  ⑨ `_zf120_verify.py`（振金那条门：护甲值 + 满套判据计数要跟平）
  ⑩ `_zf120_lang.py`（振金说明的生成器，不同步就会被重跑打回）

跑法：
    python build\\zftools\\_zf139_backup.py
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
BK = r"C:\PotatoST救援\zf139_pre"
TOOLS = r"build\zftools"
DATA = r"src\main\resources\data\potato_s_t"

FILES = [
    r"src\main\java\com\potatost\mod\ModArmorMaterials.java",
    r"src\main\java\com\potatost\mod\ModVibraniumSet.java",
    r"src\main\java\com\potatost\mod\PotatoST.java",          # ← 探针挂载点，先写进清单
    r"src\main\resources\assets\potato_s_t\lang\zh_cn.json",
    r"src\main\resources\assets\potato_s_t\lang\en_us.json",
    r"src\main\resources\assets\potato_s_t\lang\ja_jp.json",
    r"src\main\resources\assets\potato_s_t\lang\ru_ru.json",
    TOOLS + r"\_zf120_verify.py",
    TOOLS + r"\_zf120_lang.py",
    TOOLS + r"\_zf104_gates.ps1",
    TOOLS + r"\_zf104_gatecount.py",
    TOOLS + r"\Audit.ps1",
    TOOLS + r"\ToolLint.py",
    TOOLS + r"\LangCheck.ps1",
    TOOLS + r"\RecipeCheck.ps1",
    TOOLS + r"\ModelCheck.py",
    TOOLS + r"\TextureCheck.py",
    TOOLS + r"\JsonCheck.py",
    TOOLS + r"\SoundCheck.py",
    r"docs\开发档案.md",
    r"docs\多会话协作交接.md",
    r"docs\UpdateAnnouncement_EN.md",
    r"release\PotatoST-0.11.jar",
    r"release\PotatoST-0.11.jar.sha1",
]

NEW = [
    DATA + r"\damage_type\vibranium_reflect.json",
    r"src\main\java\com\potatost\mod\Zf139Check.java",
    TOOLS + r"\check\Zf139Check.java",
    TOOLS + r"\_zf139_lang.py",
    TOOLS + r"\_zf139_gatefix.py",
    TOOLS + r"\_zf139_verify.py",
    TOOLS + r"\_zf139_falsify.py",
    TOOLS + r"\_zf139_mount.py",
    TOOLS + r"\_zf139_unprobe.py",
    TOOLS + r"\_zf139_docs.py",
    TOOLS + r"\_zf139_commit.py",
    TOOLS + r"\_zf139_commit_msg.txt",
    TOOLS + r"\_zf139_probe_utf8.txt",
    TOOLS + r"\_zf139_build.log",
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
    for pat in ("_zf*_verify.py", "_zf*_falsify.py", "_zf*_falsify*.py", "_zf*_guard.py",
                "_zf*_repro.py", "_zf*_audit.py", "_zf*_gatesnap.py"):
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

    POINT = [r"src\main\java\com\potatost\mod\ModArmorMaterials.java",
             r"src\main\java\com\potatost\mod\ModVibraniumSet.java",
             r"src\main\java\com\potatost\mod\PotatoST.java",
             TOOLS + r"\_zf120_verify.py", TOOLS + r"\_zf120_lang.py",
             TOOLS + r"\_zf104_gates.ps1",
             r"docs\开发档案.md", r"docs\多会话协作交接.md"]
    miss = [rel for rel in POINT if not os.path.exists(os.path.join(BK, rel))]
    if miss:
        fails.append(u"点名件没抄到：%s" % u"、".join(miss))
    else:
        notes.append(u"点名件全在（**含探针挂载点 PotatoST.java** / 振金两条生成器 / 门清单 / 两份文档）")

    existed = [rel for rel in NEW if os.path.exists(os.path.join(ROOT, rel))]
    if existed:
        fails.append(u"这些「新增件」已经存在了：%s" % u"、".join(existed))
    else:
        notes.append(u"新增件 %d 条：动手前一条都不存在" % len(NEW))

    io.open(os.path.join(BK, u"_zf139_newfiles.txt"), "w", encoding="utf-8",
            newline=u"\n").write(u"本轮开始前这些路径应当不存在：\n" + u"\n".join(NEW) + u"\n")
    io.open(os.path.join(BK, u"_sha1.txt"), "w", encoding="utf-8", newline=u"\n").write(
        u"\n".join(lines) + u"\n")
    io.open(os.path.join(BK, u"_说明.txt"), "w", encoding="utf-8", newline=u"\n").write(
        u"ZF139 改前件：振金套加强（乙方案 + 10% 反伤 + 死亡文案「踢到了铁板」）\n"
        u"备份脚本：build/zftools/_zf139_backup.py\n"
        u"⚠ 本清单**一开始就含** PotatoST.java（探针挂载点）。\n"
        u"⚠ 清单里含**别的线当时未提交的改动**（ModArmorSet/ModArmorMaterials 的星璨钢头盔夜视），\n"
        u"   那是「改前件」的定义：备份的是**我当时看到的盘面**，不是某个提交。\n")
    print(u"\n".join(u"  [OK] " + n for n in notes))
    print(u"改前件 %d 份 → %s" % (ok, BK))
    print(u"失败项 = %d" % len(fails))
    for f in fails:
        print(u"  !! " + f)
    return 1 if fails else 0


if __name__ == u"__main__":
    sys.exit(main())
