# -*- coding: utf-8 -*-
u"""_zf146_pre.py —— ZF146 的改前件（§10：**先建备份，再动第一个字节**）

别人反馈的 bug（用户转述，原话）：
    「星轨坠 中途退出游戏就不会落下 再次进入就不能使用了」

⇒ 本轮要动的盘上文件：
  ① `src\\main\\java\\com\\potatost\\mod\\StarfallRitualManager.java` —— **本轮唯一的源码改动**
     （仪式状态从"类里的 static Map + 抓住 ServerLevel 引用"改成"存进存档的 SavedData"）；
  ② `PotatoST.java` —— 只因为要挂临时探针 `Zf146Check.java`（挂完必摘，逐字节核对回这份备份）；
  ③ `_zf114_verify.py` —— 它按 C5~C15/D/E 钉着星轨坠的常量与语义，本轮**不许把它改红**，
     所以要留一份基线（本轮**不改它**，只拿它当"没被弄红"的对照）；
  ④ 九道门与所有常驻校验脚本（一条命令都不改，按惯例进清单）；
  ⑤ `docs\\开发档案.md` / `docs\\多会话协作交接.md`；
  ⑥ 旧成品与 `.sha1`。

跑法：
    python build\\zftools\\_zf146_pre.py
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
BK = r"C:\PotatoST救援\zf146_pre"
TOOLS = r"build\zftools"
MOD = r"src\main\java\com\potatost\mod"

FILES = [
    MOD + r"\StarfallRitualManager.java",
    MOD + r"\PotatoST.java",
    MOD + r"\StarfallPendantItem.java",
    MOD + r"\StarfallMeteorEntity.java",
    TOOLS + r"\_zf114_verify.py",
    TOOLS + r"\_zf114_falsify.py",
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
    r"release\PotatoST-0.11.jar",
    r"release\PotatoST-0.11.jar.sha1",
]

NEW = [
    TOOLS + r"\_zf146_verify.py",
    TOOLS + r"\_zf146_falsify.py",
    TOOLS + r"\_zf146_gates.py",
    TOOLS + r"\_zf146_probe.py",
    TOOLS + r"\_zf146_runserver.py",
    TOOLS + r"\_zf146_publish.py",
    TOOLS + r"\_zf146_docs.py",
    TOOLS + r"\_zf146_build.log",
    TOOLS + r"\check\Zf146Check.java",
    TOOLS + r"\check\zf146_星轨坠重启取证.log",
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
    for pat in ("_zf*_verify.py", "_zf*_falsify.py", "_zf*_falsify*.py", "_zf*_gates.py"):
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

    POINT = [MOD + r"\StarfallRitualManager.java", MOD + r"\PotatoST.java",
             TOOLS + r"\_zf114_verify.py"]
    miss = [rel for rel in POINT if not os.path.exists(os.path.join(BK, rel))]
    if miss:
        fails.append(u"点名件没抄到：%s" % u"、".join(miss))
    else:
        notes.append(u"点名件全在（要重写的状态机 + 探针挂载点 + 不许弄红的 ZF114 常驻校验）")

    existed = [rel for rel in NEW if os.path.exists(os.path.join(ROOT, rel))]
    if existed:
        fails.append(u"这些「新增件」已经存在了：%s" % u"、".join(existed))
    else:
        notes.append(u"新增件 %d 条：动手前一条都不存在" % len(NEW))

    io.open(os.path.join(BK, u"_zf146_newfiles.txt"), "w", encoding="utf-8",
            newline=u"\n").write(u"本轮开始前这些路径应当不存在：\n" + u"\n".join(NEW) + u"\n")
    io.open(os.path.join(BK, u"_sha1.txt"), "w", encoding="utf-8", newline=u"\n").write(
        u"\n".join(lines) + u"\n")
    io.open(os.path.join(BK, u"_说明.txt"), "w", encoding="utf-8", newline=u"\n").write(
        u"ZF146 改前件：星轨坠的仪式状态改存存档（SavedData），"
        u"修「中途退出游戏就不会落下 / 再次进入就不能使用了」\n"
        u"备份脚本：build/zftools/_zf146_pre.py\n"
        u"⚠ StarfallRitualManager.java 是这一轮唯一的源码改动，这里是它改之前的唯一留底。\n")
    print(u"\n".join(u"  [OK] " + n for n in notes))
    print(u"改前件 %d 份 → %s" % (ok, BK))
    print(u"失败项 = %d" % len(fails))
    for f in fails:
        print(u"  !! " + f)
    return 1 if fails else 0


if __name__ == u"__main__":
    sys.exit(main())
