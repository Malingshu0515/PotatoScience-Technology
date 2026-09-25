# -*- coding: utf-8 -*-
r"""_zf117_backup.py —— ZF117 **动手前**的改前件（§10）

用户原话：「嗯嗯 成就该更新了宝宝」

本轮 = **进度（成就）补线**：把 ZF107 之后新加的内容补成节点（采油机 / 星璨钢 + 套装 /
锂电池构造间 + 三元锂 / 星轨坠+粗振金），顺带补两条老空洞（海盐线 / 液体物流）。
⇒ 会被碰到的东西全在这里抄一份：
  · 8 个**新** advancement JSON（本轮开始前**不该存在**，见 `_zf117_newfiles.txt`）
  · 四份 lang（432 → 448 键）
  · `_zf107_verify.py`（它钉着"目录正好 27 份"，必须跟着改）
  · 所有 `_zf*_verify.py` / `_zf*_falsify.py` / `_zf*_gatesnap.py` / `_zf*gates.ps1`（键数 432 → 448）
  · 三份文档 + 旧成品 jar 与 .sha1

⚠ 并发环境：同一棵树上 ZF116（素材线）正在跑，它也在改 `_zf90_verify.py` / `_zf71_verify.py`。
  所以本轮的改法一律「读 → 定点替换 → 立刻回读断言」，绝不整份覆盖；
  备份也一样，逐份核副本自己的哈希。
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
BK = r"C:\PotatoST救援\zf117_pre"
ADIR = r"src\main\resources\data\potato_s_t\advancement"
LANG = r"src\main\resources\assets\potato_s_t\lang"
TOOLS = r"build\zftools"
CHECK = TOOLS + r"\check"

FILES = [
    LANG + r"\zh_cn.json",
    LANG + r"\en_us.json",
    LANG + r"\ja_jp.json",
    LANG + r"\ru_ru.json",
    TOOLS + r"\_zf107_adv.py",
    TOOLS + r"\_zf107_verify.py",
    r"docs\开发档案.md",
    r"docs\多会话协作交接.md",
    r"docs\UpdateAnnouncement_EN.md",
    r"release\PotatoST-0.11.jar",
    r"release\PotatoST-0.11.jar.sha1",
]
# 现有 27 份 advancement 也抄一份（证明本轮"只加不改"）
FILES += [ADIR + "\\" + n for n in sorted(os.listdir(os.path.join(ROOT, ADIR)))
          if n.endswith(".json")]

NEW = ([TOOLS + r"\_zf117_adv.py", TOOLS + r"\_zf117_audit.py", TOOLS + r"\_zf117_recipes.py",
        TOOLS + r"\_zf117_retarget.py", TOOLS + r"\_zf117_verify.py", TOOLS + r"\_zf117_falsify.py",
        TOOLS + r"\_zf117_docs.py", TOOLS + r"\_zf117_gatesnap.py", TOOLS + r"\_zf117_probe2.py",
        TOOLS + r"\_zf117_unprobe.py", TOOLS + r"\_zf117_probe_archive.py",
        CHECK + r"\Zf117Check.java"]
       + [ADIR + r"\%s.json" % n for n in (
           "oil_pump", "lithium_battery_plant", "lithium_battery", "star_steel",
           "star_steel_armor", "starfall", "salt", "fluid_logistics")])

fails = []


def sha1(p):
    return hashlib.sha1(open(p, "rb").read()).hexdigest()


def main():
    if os.path.isdir(BK):
        print(u"  [STOP] 备份根已存在：%s" % BK)
        return 1
    lines, ok = [], 0
    todo = list(FILES)
    for pat in ("_zf*_verify.py", "_zf*_falsify.py", "_zf*_gatesnap.py", "_zf*gates.ps1"):
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
    io.open(os.path.join(BK, u"_zf117_newfiles.txt"), "w", encoding="utf-8",
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
