# -*- coding: utf-8 -*-
u"""_zf93_backup.py —— ZF93 **动手前**的改前件（§10）

本轮：按 §6.1 加**第二张音乐唱片**《茉莉花（管弦乐）》—— 用户给了三样东西：
  ① 音频 `Jasmine_Flower_Strings_mono.ogg`（1691739 字节 / sha256 `ca2493b0…`，
     实测 **单声道 44100 Hz Ogg Vorbis，147.102132 s**，正好是本工程要的规格）；
  ② 贴图 `音乐唱片茉莉花.png`（已在 ZF92 按 §4.24 留档到 `build/用户素材/music_disc_jasmine_flower.png`）；
  ③ 一句说明「这是 茉莉花(管弦乐) 的音乐唱片 贴图在item里」。

会动到的文件（一份不落，逐份核哈希）：
  · `sound/ModSounds.java`（加声音事件）
  · `ModItems.java`（曲目键 + 物品 + 创造页）
  · `assets/potato_s_t/sounds.json`（加条目，`stream: true`）
  · 四份 lang（各 +2 键 ⇒ 270 → **272**）
  · 八个往轮校验里的**活体键数** + 英文公告那行（键数变了就得跟着改，这是老规矩）
  · `_zf78_falsify.py`（挂 ZF93 与加刀）
  · 三份文档、旧成品 jar 与 `.sha1`
  · 另把用户给的 `.ogg` 按 sha256 留档到 `zf93_pre\\user\\`
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
BK = r"C:\PotatoST救援\zf93_pre"
OGG = (r"C:\Users\Administrator\.dsh\attachments\v1\files\ca"
       r"\ca2493b0bb4cbaf6fd1784245eb0490042405bec922b6c0e4918de2a841939be"
       r"\Jasmine_Flower_Strings_mono.ogg")
OGG_SHA256 = "ca2493b0bb4cbaf6fd1784245eb0490042405bec922b6c0e4918de2a841939be"
LANG = r"src\main\resources\assets\potato_s_t\lang"
TOOLS = r"build\zftools"
FILES = [
    r"src\main\java\com\potatost\mod\sound\ModSounds.java",
    r"src\main\java\com\potatost\mod\ModItems.java",
    r"src\main\resources\assets\potato_s_t\sounds.json",
    LANG + r"\zh_cn.json",
    LANG + r"\en_us.json",
    LANG + r"\ja_jp.json",
    LANG + r"\ru_ru.json",
    TOOLS + r"\_zf71_verify.py",
    TOOLS + r"\_zf73_verify.py",
    TOOLS + r"\_zf75_verify.py",
    TOOLS + r"\_zf78_verify.py",
    TOOLS + r"\_zf79_verify.py",
    TOOLS + r"\_zf80_verify.py",
    TOOLS + r"\_zf81_verify.py",
    TOOLS + r"\_zf82_verify.py",
    TOOLS + r"\_zf78_falsify.py",
    r"docs\开发档案.md",
    r"docs\贴图清单.md",
    r"docs\UpdateAnnouncement_EN.md",
    r"release\PotatoST-0.11.jar",
    r"release\PotatoST-0.11.jar.sha1",
]
fails = []


def sha1(p):
    return hashlib.sha1(open(p, "rb").read()).hexdigest()


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
    # 用户给的音频原件（改名避免空格/大小写麻烦？—— 不，原名就是 ASCII，照原样留档）
    if not os.path.exists(OGG):
        fails.append(u"用户音频不在：%s" % OGG)
    else:
        h = hashlib.sha256(open(OGG, "rb").read()).hexdigest()
        if h != OGG_SHA256:
            fails.append(u"音频 sha256 变了：%s" % h)
        dst = os.path.join(BK, "user", "Jasmine_Flower_Strings_mono.ogg")
        os.makedirs(os.path.dirname(dst), exist_ok=True)
        shutil.copy2(OGG, dst)
        if hashlib.sha256(open(dst, "rb").read()).hexdigest() != h:
            fails.append(u"音频拷贝后哈希不一致")
        else:
            ok += 1
            lines.append(u"sha256 %s  %10d  %s" % (h, os.path.getsize(dst),
                                                  u"user\\Jasmine_Flower_Strings_mono.ogg"))
    io.open(os.path.join(BK, u"_sha1.txt"), "w", encoding="utf-8",
            newline=u"\n").write(u"\n".join(lines) + u"\n")
    print(u"改前件 %d 份 → %s" % (ok, BK))
    print(u"失败项 = %d" % len(fails))
    for f in fails:
        print(u"  !! " + f)
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())
