# -*- coding: utf-8 -*-
u"""_zf124_backup.py —— ZF124 的改前件（§10：**先建备份，再动第一个字节**）

用户原话（附成就界面截图：鼠标停在「新的开始！」那个页签上，页签图标是微型粉碎机）：
「把成就的 新的开始！这一分类改成 PotatoS&T 创造模式标签页换成星轨追的物品贴图」

拆成两件事：
  ① **成就页签（= 根成就 `new_beginning` 的标题）** 「新的开始！」→「PotatoS&T」（四语言；
     成就界面里那个页签的悬浮名就是它，页签图标来自根成就的 `display.icon`）；
  ② **创造模式标签页的图标**：现在是**铝锭**（`ModItems.POTATO_ST_TAB` 的 `.icon(...)`）
     → 换成**星轨坠**（`ModItems.STARFALL_PENDANT`）。

⚠ 用户这句话有两种读法（"换成星轨坠贴图"说的是**创造页的图标**还是**成就页签的图标**）：
   本轮按**字面**做（创造页图标），成就页签图标**不动**，并在汇报里点名请他一句话确认。

跑法：
    python build\\zftools\\_zf124_backup.py
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
BK = r"C:\PotatoST救援\zf124_pre"
JAVA = r"src\main\java\com\potatost\mod"
LANG = r"src\main\resources\assets\potato_s_t\lang"
ADV = r"src\main\resources\data\potato_s_t\advancement"
TOOLS = r"build\zftools"

FILES = [
    JAVA + r"\ModItems.java",
    LANG + r"\zh_cn.json",
    LANG + r"\en_us.json",
    LANG + r"\ja_jp.json",
    LANG + r"\ru_ru.json",
    ADV + r"\new_beginning.json",
    TOOLS + r"\_zf70_verify.py",
    TOOLS + r"\_zf70_lang.py",
    r"docs\UpdateAnnouncement_EN.md",
    r"docs\开发档案.md",
    r"docs\多会话协作交接.md",
    r"release\PotatoST-0.11.jar",
    r"release\PotatoST-0.11.jar.sha1",
]

NEW = [TOOLS + r"\_zf124_%s.py" % s for s in
       ("backup", "java", "lang", "retarget", "verify", "falsify", "docs")]

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
    bad = [rel for rel in todo
           if os.path.exists(os.path.join(ROOT, rel)) and os.path.exists(os.path.join(BK, rel))
           and sha1(os.path.join(ROOT, rel)) != sha1(os.path.join(BK, rel))]
    if bad:
        fails.append(u"回读不一致：%s" % u"、".join(bad))
    else:
        notes.append(u"回读证明：%d 份备份与盘上逐字节相同" % ok)
    for rel in (JAVA + r"\ModItems.java", LANG + r"\zh_cn.json", r"docs\UpdateAnnouncement_EN.md"):
        if not os.path.exists(os.path.join(BK, rel)):
            fails.append(u"点名件没抄到：%s" % rel)
    notes.append(u"点名件全在（ModItems / 四语言 / 英文公告）")

    io.open(os.path.join(BK, u"_zf124_newfiles.txt"), "w", encoding="utf-8",
            newline=u"\n").write(u"本轮开始前这些路径应当不存在：\n" + u"\n".join(NEW) + u"\n")
    io.open(os.path.join(BK, u"_sha1.txt"), "w", encoding="utf-8", newline=u"\n").write(
        u"\n".join(lines) + u"\n")
    print(u"\n".join(u"  [OK] " + n for n in notes))
    print(u"改前件 %d 份 → %s" % (ok, BK))
    print(u"失败项 = %d" % len(fails))
    for f in fails:
        print(u"  !! " + f)
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())
