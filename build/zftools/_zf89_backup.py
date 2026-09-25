# -*- coding: utf-8 -*-
u"""_zf89_backup.py —— ZF89 **动手前**的改前件（§10）

本轮：用户又往 `textures/block` 里放了一张 `汽油.png`（16×16 / 8 位 / RGBA / 全不透明），
照 ZF88 那套把它转档成 `gasoline_still.png` + `gasoline_flow.png`。

改前件 = 所有"会被这一轮动到"的文件：
  · 两张汽油流体贴图（要被覆盖）
  · 用户刚放的原图 `汽油.png`（要被挪走）
  · 来源凭据（要追加一条）
  · 两份文档、成品 jar 与 .sha1
  · `_zf78_falsify.py`（要把 ZF89 挂进反证名单，并加一把刀）
电力高炉那一轮调查**全是只读**（只新建 `_zf89_*.py` 工具与预览图，没动任何既有字节），
所以那部分没有改前件 —— 这一点写在这里以免以后误以为漏了。
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
BK = r"C:\PotatoST救援\zf89_pre"
TEXB = r"src\main\resources\assets\potato_s_t\textures\block"
FILES = [
    TEXB + r"\gasoline_still.png",
    TEXB + r"\gasoline_flow.png",
    TEXB + u"\\汽油.png",
    r"build\用户素材\_来源凭据.json",
    r"build\zftools\_zf78_falsify.py",
    r"docs\开发档案.md",
    r"docs\贴图清单.md",
    r"release\PotatoST-0.11.jar",
    r"release\PotatoST-0.11.jar.sha1",
]
fails = []


def sha1(p):
    return hashlib.sha1(open(p, "rb").read()).hexdigest()


def main():
    if os.path.isdir(BK):
        print(u"  [SKIP] 备份根已存在：%s" % BK)
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
    io.open(os.path.join(BK, u"_sha1.txt"), "w", encoding="utf-8",
            newline=u"\n").write(u"\n".join(lines) + u"\n")
    print(u"改前件 %d 份 → %s" % (ok, BK))
    print(u"失败项 = %d" % len(fails))
    for f in fails:
        print(u"  !! " + f)
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())
