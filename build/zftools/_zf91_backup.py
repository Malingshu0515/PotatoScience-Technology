# -*- coding: utf-8 -*-
u"""_zf91_backup.py —— ZF91 **动手前**的改前件（§10）

本轮：用户发来 `电力高炉.bbmodel`（41423 字节，sha256 `15028bf3…`）—— 那是**改版后的模型**
（19 个 mesh、各 8 顶点 / 6 面 = 114 个面，带 origin+rotation，UV 是逐顶点给的真实 UV），
要拿它**替换**成品里那四份"整张贴图铺每个面"的 OBJ。

改前件 = 会被这一轮动到的全部文件：
  · 四份 `electric_blast_furnace_{north,south,east,west}.obj`（要被覆盖）
  · `electric_blast_furnace.mtl`（本轮不动，但它是配套件，留一份）
  · 四个 model JSON（本轮不动，留一份）
  · 用户发来的 `.bbmodel`（原件留档）
  · `_zf89_verify.py`（C 段那几条"四份 OBJ 仍只有 4 个 UV 点"的可证伪断言必须改成新真相）
  · `_zf78_falsify.py`（要把 ZF91 挂进反证名单并加刀）
  · 两份文档、旧成品 jar 与 `.sha1`
"""
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
BK = r"C:\PotatoST救援\zf91_pre"
MB = r"src\main\resources\assets\potato_s_t\models\block"
FILES = [
    MB + r"\electric_blast_furnace_north.obj",
    MB + r"\electric_blast_furnace_south.obj",
    MB + r"\electric_blast_furnace_east.obj",
    MB + r"\electric_blast_furnace_west.obj",
    MB + r"\electric_blast_furnace.mtl",
    r"src\main\resources\assets\potato_s_t\models\item\electric_blast_furnace.json",
    r"build\zftools\_zf89_verify.py",
    r"build\zftools\_zf78_falsify.py",
    r"docs\开发档案.md",
    r"docs\贴图清单.md",
    r"release\PotatoST-0.11.jar",
    r"release\PotatoST-0.11.jar.sha1",
]
SRC_BB = r"C:\Users\Administrator\.dsh\attachments\v1\files\15\15028bf3d0dc6e7234ea03ec6a697b72858bc12ff7383c401b7c394fd2aab366\电力高炉.bbmodel"
EXPECT_BB = "15028bf3d0dc6e7234ea03ec6a697b72858bc12ff7383c401b7c394fd2aab366"
fails = []


def sha1(p):
    return hashlib.sha1(open(p, "rb").read()).hexdigest()


def sha256(p):
    return hashlib.sha256(open(p, "rb").read()).hexdigest()


def main():
    if os.path.isdir(BK):
        print(u"  [STOP] 备份根已存在：%s（重跑会覆盖改前件，直接中止）" % BK)
        return 1
    lines = []
    ok = 0
    for rel in FILES:
        src = os.path.join(ROOT, rel)
        if not os.path.exists(src):
            fails.append(u"缺文件：%s" % rel)
            lines.append(u"MISSING  %s" % rel)
            continue
        dst = os.path.join(BK, rel)
        os.makedirs(os.path.dirname(dst), exist_ok=True)
        before = sha1(src)
        shutil.copy2(src, dst)
        after = sha1(dst)
        if before != after:
            fails.append(u"%s：拷贝后哈希不一致" % rel)
        else:
            ok += 1
            lines.append(u"%s  %10d  %s" % (after, os.path.getsize(dst), rel))
    # 用户工程原件留档（改名避免中文名；字节不动）
    if not os.path.exists(SRC_BB):
        fails.append(u"用户工程文件不在：%s" % SRC_BB)
    else:
        h = sha256(SRC_BB)
        if h != EXPECT_BB:
            fails.append(u".bbmodel 的 sha256 变了：%s" % h)
        dst = os.path.join(BK, "user", "electric_blast_furnace.bbmodel")
        os.makedirs(os.path.dirname(dst), exist_ok=True)
        shutil.copy2(SRC_BB, dst)
        if sha256(dst) != h:
            fails.append(u".bbmodel 拷贝后哈希不一致")
        else:
            ok += 1
            lines.append(u"sha256 %s  %10d  %s" % (h, os.path.getsize(dst),
                                                  u"user\\electric_blast_furnace.bbmodel"))
    io.open(os.path.join(BK, u"_sha1.txt"), "w", encoding="utf-8",
            newline=u"\n").write(u"\n".join(lines) + u"\n")
    print(u"改前件 %d 份 → %s" % (ok, BK))
    print(u"失败项 = %d" % len(fails))
    for f in fails:
        print(u"  !! " + f)
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())
