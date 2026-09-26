# -*- coding: utf-8 -*-
u"""_zf142_pre.py —— ZF142 的改前件（§10：**先建备份，再动第一个字节**）

用户原话（接在 ZF140 汇报里"条纹只是被盖住、没治好；真正的治法是给四张星图的极带做极滤波"
那段之后）：「可以尝试加一点点模糊」

⇒ 本轮要动的盘上文件：
  ① **四张星图本体**（`textures/skybox/sky_{verdant,mystic,ember,tarantula}.png`）——
     这是本轮唯一"用户素材级别的原件"，必须逐字节留底；
  ② `_zf140_verify.py`（它有一条 B9「四张星图相对上次提交一个字节没动」，
     本轮之后这条**按设计不再成立**，要改成"只在极带被动过"）；
  ③ `docs\\开发档案.md` / `docs\\贴图清单.md`；
  ④ 九道门与所有常驻校验脚本（一条命令都不改，按惯例进清单）；
  ⑤ 旧成品与 `.sha1`。

跑法：
    python build\\zftools\\_zf142_pre.py
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
BK = r"C:\PotatoST救援\zf142_pre"
TOOLS = r"build\zftools"
SKY = r"src\main\resources\assets\potato_s_t\textures\skybox"

FILES = [
    SKY + r"\sky_verdant.png",
    SKY + r"\sky_mystic.png",
    SKY + r"\sky_ember.png",
    SKY + r"\sky_tarantula.png",
    TOOLS + r"\_zf140_verify.py",
    TOOLS + r"\_zf140_sim.py",
    TOOLS + r"\_zf142_poleblur.py",
    TOOLS + r"\_zf140_img.py",
    TOOLS + r"\Audit.ps1",
    TOOLS + r"\ToolLint.py",
    TOOLS + r"\LangCheck.ps1",
    TOOLS + r"\RecipeCheck.ps1",
    TOOLS + r"\ModelCheck.py",
    TOOLS + r"\TextureCheck.py",
    TOOLS + r"\JsonCheck.py",
    TOOLS + r"\SoundCheck.py",
    r"docs\开发档案.md",
    r"docs\贴图清单.md",
    r"docs\多会话协作交接.md",
    r"release\PotatoST-0.11.jar",
    r"release\PotatoST-0.11.jar.sha1",
]

NEW = [
    TOOLS + r"\_zf142_verify.py",
    TOOLS + r"\_zf142_falsify.py",
    TOOLS + r"\_zf142_look.py",
    TOOLS + r"\_zf142_gates.py",
    TOOLS + r"\_zf142_publish.py",
    TOOLS + r"\_zf142_docs.py",
    TOOLS + r"\_zf142_build.log",
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

    POINT = [SKY + r"\sky_%s.png" % n for n in ("verdant", "mystic", "ember", "tarantula")]
    POINT.append(TOOLS + r"\_zf140_verify.py")
    miss = [rel for rel in POINT if not os.path.exists(os.path.join(BK, rel))]
    if miss:
        fails.append(u"点名件没抄到：%s" % u"、".join(miss))
    else:
        notes.append(u"点名件全在（**四张星图本体** + 要改判据的 `_zf140_verify.py`）")

    existed = [rel for rel in NEW if os.path.exists(os.path.join(ROOT, rel))]
    if existed:
        fails.append(u"这些「新增件」已经存在了：%s" % u"、".join(existed))
    else:
        notes.append(u"新增件 %d 条：动手前一条都不存在" % len(NEW))

    io.open(os.path.join(BK, u"_zf142_newfiles.txt"), "w", encoding="utf-8",
            newline=u"\n").write(u"本轮开始前这些路径应当不存在：\n" + u"\n".join(NEW) + u"\n")
    io.open(os.path.join(BK, u"_sha1.txt"), "w", encoding="utf-8", newline=u"\n").write(
        u"\n".join(lines) + u"\n")
    io.open(os.path.join(BK, u"_说明.txt"), "w", encoding="utf-8", newline=u"\n").write(
        u"ZF142 改前件：四张星图的**极带横向模糊**（极滤波），带外一个字节不许动\n"
        u"备份脚本：build/zftools/_zf142_pre.py\n"
        u"⚠ 四张星图是**用户素材级别的原件**，这里是它们被改之前的唯一留底。\n")
    print(u"\n".join(u"  [OK] " + n for n in notes))
    print(u"改前件 %d 份 → %s" % (ok, BK))
    print(u"失败项 = %d" % len(fails))
    for f in fails:
        print(u"  !! " + f)
    return 1 if fails else 0


if __name__ == u"__main__":
    sys.exit(main())
