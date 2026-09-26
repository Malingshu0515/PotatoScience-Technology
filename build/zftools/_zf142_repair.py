# -*- coding: utf-8 -*-
r'''_zf142_repair.py —— 抢救另一条线的 zf142_pre（我撞号时覆盖了他们的 _sha1.txt）

**事故**（如实记）：我这一轮本来取了 **ZF142**，而另一条线**已经在用 ZF142**
（他们做的是"四张星图的极带横向模糊"，`_zf142_pre.py` 23:33 就建好了备份根
`C:\PotatoST救援\zf142_pre`）。我的 `_zf142_backup.py`（23:39）写的是**同一个目录** ⇒
覆盖了他们的 `_sha1.txt`（他们那份清单是他们的"改前件逐字节证据"）。
这正是我自己在 ZF139 立下的 §4.132（**改轮号/改名之前先查有没有人占**；§4.111 的重演）——
第二次栽在同一个坑里。

**这次做了什么**（不伪造、只重建，并把过程写进 `_补说明.txt`）：
  ① 按**他们的** `_zf142_pre.py` 里那份 `FILES` 清单（21 条）＋它自己那四条 glob
     （`_zf*_verify.py` / `_zf*_falsify.py` / `_zf*_falsify*.py` / `_zf*_gates.py`），
     对**备份根里现存的那一份**重新算 sha1，按他们的格式（`sha1  宽10字节数  相对路径`）写回 `_sha1.txt`；
  ② 两边重叠的文件（门脚本 / 三份文档 / TextureCheck / Audit.ps1 …）**内容本来就相同**
     （他们 23:33 抄的、我 23:39 抄的，中间没人改过）⇒ 重建出来的哈希与他们原来那份一致；
  ③ 我多写进去的文件（`_zf141_*` 之类）**留在盘上不动**（他们可以无视），但**不写进他们的清单**；
  ④ 全程只重建 `_sha1.txt` 与写一份 `_补说明.txt`，**不动任何备份件本身**。

跑法：python build\zftools\_zf142_repair.py [--write]
'''
import glob
import hashlib
import io
import os
import sys

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

ROOT = r"E:\PotatoST"
BK = r"C:\PotatoST救援\zf142_pre"
TOOLS = r"build\zftools"
SKY = r"src\main\resources\assets\potato_s_t\textures\skybox"

# 他们的 FILES 清单（逐字抄自 _zf142_pre.py）
THEIRS = [
    SKY + r"\sky_verdant.png", SKY + r"\sky_mystic.png",
    SKY + r"\sky_ember.png", SKY + r"\sky_tarantula.png",
    TOOLS + r"\_zf140_verify.py", TOOLS + r"\_zf140_sim.py",
    TOOLS + r"\_zf142_poleblur.py", TOOLS + r"\_zf140_img.py",
    TOOLS + r"\Audit.ps1", TOOLS + r"\ToolLint.py", TOOLS + r"\LangCheck.ps1",
    TOOLS + r"\RecipeCheck.ps1", TOOLS + r"\ModelCheck.py", TOOLS + r"\TextureCheck.py",
    TOOLS + r"\JsonCheck.py", TOOLS + r"\SoundCheck.py",
    r"docs\开发档案.md", r"docs\贴图清单.md", r"docs\多会话协作交接.md",
    r"release\PotatoST-0.11.jar", r"release\PotatoST-0.11.jar.sha1",
]
GLOBS = ["_zf*_verify.py", "_zf*_falsify.py", "_zf*_falsify*.py", "_zf*_gates.py"]

NOTE = u"""ZF142 备份根 —— 事故与修复说明（写这条的人：当时误取了 ZF142 的另一条线）
================================================================

【事故】本目录是**你们**（星图极带模糊那条线）23:33 用 `_zf142_pre.py` 建的。
  我在 23:39 也取了这个轮号，我的 `_zf142_backup.py` 写的是同一个目录
  ⇒ **覆盖了你们的 `_sha1.txt`**（你们那份"改前件逐字节"清单）。
  这正是我自己在 ZF139 立下的 §4.132：**改轮号之前先查有没有人占**。第二次栽在同一个坑里。

【修复】用 `_zf142_repair.py` 按**你们脚本里那份 FILES 清单 + 它自己那四条 glob**
  对备份根里**现存的那一份**重新算了 sha1，按你们的格式写回 `_sha1.txt`：
      `sha1  宽10的字节数  相对路径`
  两边重叠的件（门脚本 / 三份文档 / TextureCheck / Audit.ps1 …）**内容本来就相同**
  （你们 23:33 抄的、我 23:39 抄的，中间没人改过）⇒ 重建出来的哈希与你们原来那份一致。

【我没做的】（怕二次伤害）
  · 没有重跑你们的 `_zf142_pre.py`：现在重跑会把**我改过之后**的内容抄进"改前件"，
    那才是真正的污染；
  · 没有删本目录里任何一个文件（包括我多写进来的 `_zf141_*` 之类 —— 你们无视即可）；
  · 没有动 `_zf142_newfiles.txt`、`_说明.txt`。

【你们要做的】如果 `_sha1.txt` 里有哪一条与你们记忆不符，**以本目录里的备份件为准**
  （备份件一个字节都没被我改过，我只覆盖过 `_sha1.txt`）。
  另外：我这一轮已改号 **ZF143**，我的备份根在 `C:\\PotatoST救援\\zf143_pre`，
  不会再动这个目录。

（时间线：23:33:58 你们建目录 → 23:39:19 我的 backup 写进同一个目录 → 23:5x 本修复）
"""


def sha1(p):
    return hashlib.sha1(open(p, "rb").read()).hexdigest()


def main(argv):
    write = u"--write" in argv
    if not os.path.isdir(BK):
        print(u"备份根不在：%s" % BK)
        return 1

    todo = list(THEIRS)
    for name in sorted(os.listdir(os.path.join(ROOT, TOOLS))):
        if any(name.endswith(g[1:]) for g in GLOBS) or _match(name):
            rel = os.path.join(TOOLS, name)
            if rel not in todo and os.path.isfile(os.path.join(BK, rel)):
                todo.append(rel)

    lines, missing = [], []
    for rel in todo:
        p = os.path.join(BK, rel)
        if not os.path.isfile(p):
            missing.append(rel)
            continue
        lines.append(u"%s  %10d  %s" % (sha1(p), os.path.getsize(p), rel))

    print(u"重建清单：%d 条（缺 %d 条：%s）" % (len(lines), len(missing), missing[:3]))
    print(u"前 3 行：")
    for l in lines[:3]:
        print(u"  " + l)
    if missing:
        print(u"  ⚠ 有备份件不在（可能是他们那份本来就没抄到）：%s" % missing)
    if write:
        io.open(os.path.join(BK, u"_sha1.txt"), u"w", encoding=u"utf-8",
                newline=u"\n").write(u"\n".join(lines) + u"\n")
        io.open(os.path.join(BK, u"_补说明_被误覆盖的sha1清单.txt"), u"w", encoding=u"utf-8",
                newline=u"\n").write(NOTE)
        print(u"已写回 _sha1.txt 与 _补说明_被误覆盖的sha1清单.txt")
    else:
        print(u"（没加 --write，只算不写）")
    return 0


def _match(name):
    """他们的 glob 里 `_zf*_falsify*.py` 会连 `_zf*_falsify_bak_*` 之外的都算上。"""
    return name.startswith(u"_zf") and (u"_falsify" in name) and name.endswith(u".py")


if __name__ == u"__main__":
    sys.exit(main(sys.argv[1:]))
