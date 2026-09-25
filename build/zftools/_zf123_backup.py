# -*- coding: utf-8 -*-
u"""_zf123_backup.py —— ZF123 的改前件（§10：**先建备份，再动第一个字节**）

用户实测报的两件事：
  ① 「jei看不到合金冶炼炉的配方了」—— 查客户端日志定位到 **ZF112（2026-09-25 22:19 提交 0a286b8）**
     留下的一个客户端雷：`PotatoSTJeiPlugin.MACHINES` 加了 `lithium_battery_plant`，
     可 `iconFor()` 的 switch **没加对应的 case** ⇒ 返回 `ItemStack.EMPTY`
     ⇒ JEI 在 `createDrawableItemStack` 当场抛 `IllegalArgumentException: Ingredient is invalid…`
     ⇒ **整个插件的分类与配方全被丢弃**（不是只有合金炉：12 台机器一台都没有 JEI 页面）。
     证据：`run\\client\\logs\\2026-09-25-2.log.gz`（22:30 那一场）起每一场都报，
     而 `2026-09-25-1`（22:24）那一场是绿的；日志里最后一个注册成功的分类是
     `ammonia_synthesis_chamber`（= MACHINES 里锂电前面那台），锂电那条**从来没有出现过**。
  ② 「星璨钢貌似还只有英文名称了」—— 盘上查不出问题（`_zf123_langaudit.py` 的三项审计全绿），
     按"待用户补线索"处理，本轮**不瞎改**。

⚠ 轮号：`ZF120`（振金套）/ `ZF122`（星仪图之章，已提交 0489cf9）都被并行线占了 ⇒ 本轮取 **ZF123**。

跑法：
    python build\\zftools\\_zf123_backup.py
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
BK = r"C:\PotatoST救援\zf123_pre"
JAVA = r"src\main\java\com\potatost\mod"
JEI = JAVA + r"\client\jei"
TOOLS = r"build\zftools"
LANG = r"src\main\resources\assets\potato_s_t\lang"

FILES = [
    JEI + r"\PotatoSTJeiPlugin.java",
    JEI + r"\MachineRecipeCategory.java",
    JAVA + r"\MachineRecipes.java",
    JAVA + r"\PotatoST.java",
    LANG + r"\zh_cn.json",
    LANG + r"\en_us.json",
    LANG + r"\ja_jp.json",
    LANG + r"\ru_ru.json",
    r"docs\开发档案.md",
    r"docs\多会话协作交接.md",
    r"docs\UpdateAnnouncement_EN.md",
    r"release\PotatoST-0.11.jar",
    r"release\PotatoST-0.11.jar.sha1",
    # 取证用的客户端日志（异常现场；拷进备份里就不怕日志轮转被冲掉）
    r"run\client\logs\2026-09-25-1.log.gz",
    r"run\client\logs\2026-09-25-2.log.gz",
]

NEW = [TOOLS + r"\_zf123_%s.py" % s for s in
       ("backup", "java", "langaudit", "verify", "falsify", "docs", "gatesnap")]

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
           if os.path.exists(os.path.join(ROOT, rel))
           and os.path.exists(os.path.join(BK, rel))
           and sha1(os.path.join(ROOT, rel)) != sha1(os.path.join(BK, rel))]
    if bad:
        fails.append(u"回读不一致：%s" % u"、".join(bad))
    else:
        notes.append(u"回读证明：%d 份备份与盘上逐字节相同" % ok)

    for rel in (JEI + r"\PotatoSTJeiPlugin.java", r"docs\开发档案.md"):
        if not os.path.exists(os.path.join(BK, rel)):
            fails.append(u"点名件没抄到：%s" % rel)
    notes.append(u"点名件全在（含 PotatoSTJeiPlugin.java）")

    io.open(os.path.join(BK, u"_zf123_newfiles.txt"), "w", encoding="utf-8",
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
