# -*- coding: utf-8 -*-
u"""_zf140_pre.py —— ZF140 的改前件（§10：**先建备份，再动第一个字节**）

用户原话（配一张黑洞图）：
「因为图片问题 天空盒一个点会看到明显的拉伸现象 解决不了 那正好在那个地方（四张星图都需要）
补个黑洞 图给你了 估计得抠一下 只剩黑洞本体 然后放到拉伸的地方」

⇒ 本轮要动的盘上文件：
  ① `client\\SkyboxRenderer.java`（加两极黑洞盖片 —— **唯一一处代码改动**）
  ② `build\\用户素材\\_来源凭据.json`（把新素材登记进去）
  ③ `docs\\开发档案.md` / `docs\\贴图清单.md`
  ④ `release\\PotatoST-0.11.jar` + `.sha1`（旧成品作废）
  ⑤ 九道门与所有 `_zf*_verify/_falsify/_gatesnap`（一条命令都不改，但按惯例进清单）

跑法：
    python build\\zftools\\_zf140_pre.py
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
BK = r"C:\PotatoST救援\zf140_pre"
TOOLS = r"build\zftools"

FILES = [
    r"src\main\java\com\potatost\mod\client\SkyboxRenderer.java",
    TOOLS + r"\_zf140_img.py",
    TOOLS + r"\_zf140_intake.py",
    TOOLS + r"\_zf140_cutout.py",
    TOOLS + r"\_zf140_sim.py",
    TOOLS + r"\_zf140_jpeg_dump.ps1",
    r"build\用户素材\_来源凭据.json",
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
    r"docs\UpdateAnnouncement_EN.md",
    r"release\PotatoST-0.11.jar",
    r"release\PotatoST-0.11.jar.sha1",
]

NEW = [
    r"src\main\resources\assets\potato_s_t\textures\skybox\black_hole.png",
    TOOLS + r"\_zf140_mapping.py",
    TOOLS + r"\_zf140_verify.py",
    TOOLS + r"\_zf140_falsify.py",
    TOOLS + r"\_zf140_gates.py",
    TOOLS + r"\_zf140_publish.py",
    TOOLS + r"\_zf140_docs.py",
    TOOLS + r"\_zf140_live.py",
    TOOLS + r"\_zf140_build.log",
]

# 这两条是「用户素材进门」的产物：素材本身当然在动手前就得先落到盘上（否则没法解码），
# 所以它们**不算新增件**，但也没必要假装它们不存在 —— 单独列出来，跑之前先核一遍哈希。
INTAKE = [
    r"build\用户素材\黑洞.jpg",
    TOOLS + r"\_zf140_hole.bgra",
]

INTAKE_SHA1 = {
    r"build\用户素材\黑洞.jpg": "c3466747283dde0d93b786d21bfdc330703f690ff2849ebe3ed3ac387c560421",
}

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
    for pat in ("_zf*_verify.py", "_zf*_falsify.py", "_zf*_falsify*.py", "_zf*_gatesnap.py",
                "_zf*_gates.py"):
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

    POINT = [r"src\main\java\com\potatost\mod\client\SkyboxRenderer.java",
             TOOLS + r"\_zf140_sim.py", r"build\用户素材\_来源凭据.json",
             r"docs\开发档案.md", r"docs\贴图清单.md"]
    miss = [rel for rel in POINT if not os.path.exists(os.path.join(BK, rel))]
    if miss:
        fails.append(u"点名件没抄到：%s" % u"、".join(miss))
    else:
        notes.append(u"点名件全在（**含唯一一处代码改动 SkyboxRenderer.java** / 软件模拟器 / 凭据 / 两份文档）")

    existed = [rel for rel in NEW if os.path.exists(os.path.join(ROOT, rel))]
    if existed:
        fails.append(u"这些「新增件」已经存在了：%s" % u"、".join(existed))
    else:
        notes.append(u"新增件 %d 条：动手前一条都不存在" % len(NEW))

    for rel, want in INTAKE_SHA1.items():
        p = os.path.join(ROOT, rel)
        got = hashlib.sha256(open(p, "rb").read()).hexdigest()
        if got != want:
            fails.append(u"进门素材 %s 的 sha256 不是 %s（读到 %s）" % (rel, want, got))
        else:
            notes.append(u"进门素材 sha256 对得上：%s = %s…" % (rel, got[:16]))
    miss = [rel for rel in INTAKE if not os.path.exists(os.path.join(ROOT, rel))]
    if miss:
        fails.append(u"进门产物不在：%s" % u"、".join(miss))

    io.open(os.path.join(BK, u"_zf140_newfiles.txt"), "w", encoding="utf-8",
            newline=u"\n").write(u"本轮开始前这些路径应当不存在：\n" + u"\n".join(NEW) + u"\n")
    io.open(os.path.join(BK, u"_sha1.txt"), "w", encoding="utf-8", newline=u"\n").write(
        u"\n".join(lines) + u"\n")
    io.open(os.path.join(BK, u"_说明.txt"), "w", encoding="utf-8", newline=u"\n").write(
        u"ZF140 改前件：四张星图的极点补黑洞盖片（用户给的图，抠出本体做成独立贴图）\n"
        u"备份脚本：build/zftools/_zf140_pre.py\n"
        u"⚠ 唯一一处代码改动是 client/SkyboxRenderer.java（只加，不改既有行）。\n"
        u"⚠ 清单里含**别的线当时未提交的改动**（TextureCheck.py / 各 BlockEntity / lang 等）；\n"
        u"   那是「改前件」的定义：备份的是**我当时看到的盘面**，不是某个提交。\n")
    print(u"\n".join(u"  [OK] " + n for n in notes))
    print(u"改前件 %d 份 → %s" % (ok, BK))
    print(u"失败项 = %d" % len(fails))
    for f in fails:
        print(u"  !! " + f)
    return 1 if fails else 0


if __name__ == u"__main__":
    sys.exit(main())
