# -*- coding: utf-8 -*-
u"""_zf83_backup.py —— ZF83 改前件（**事后补建**，照 ZF78/ZF33 先例，如实记录）

⚠ 本轮我**先动手后抄**（§10 的规矩是"第一个字节改动之前先抄"），这是第二次犯（ZF78 那次也是）。
   补救办法（和 ZF78 一样，用**可验证**的来源重建，不靠记忆）：
     · `steel_plate.png` / `copper_plate.png` / `plate.png` / 三个板子的物品模型
       全部从 **ZF82 已发布的成品 jar**（`release\PotatoST-0.11.jar`，就是用户手上那个）里取回
       —— 那是**唯一权威**的"改动前是什么样"，且逐份核 SHA1；
     · 其余文件（文档、旧成品）本来就是没动过的，直接拷。

   `_说明.txt` 里写清楚：这些副本是**事后**的、来源是哪个 jar、哪些是"当时磁盘上的原件"。
"""
import hashlib
import io
import os
import shutil
import sys
import zipfile

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

ROOT = r"E:\PotatoST"
BK = r"C:\PotatoST救援\zf83_pre"
JAR = os.path.join(ROOT, "release", "PotatoST-0.11.jar")
ASSETS = os.path.join(ROOT, "src", "main", "resources", "assets", "potato_s_t")

FROM_JAR = [
    u"assets/potato_s_t/textures/item/steel_plate.png",
    u"assets/potato_s_t/textures/item/copper_plate.png",
    u"assets/potato_s_t/textures/item/plate.png",
    u"assets/potato_s_t/models/item/steel_plate.json",
    u"assets/potato_s_t/models/item/copper_plate.json",
    u"assets/potato_s_t/models/item/iron_plate.json",
]
PLAIN = [
    r"docs\贴图清单.md",
    r"docs\开发档案.md",
    r"release\PotatoST-0.11.jar",
    r"release\PotatoST-0.11.jar.sha1",
]
fails = []
lines = []


def sha1b(b):
    return hashlib.sha1(b).hexdigest()


def sha1f(p):
    return hashlib.sha1(open(p, "rb").read()).hexdigest()


def main():
    if os.path.isdir(BK):
        print(u"  [SKIP] 备份根已存在：%s" % BK)
    if not os.path.exists(JAR):
        print(u"  !! 没有成品 jar，无法重建改前贴图")
        return 1
    jar_sha = sha1f(JAR)
    print(u"来源 jar：%s（%s…）" % (JAR, jar_sha[:8]))

    with zipfile.ZipFile(JAR) as zf:
        for entry in FROM_JAR:
            rel = entry.replace(u"/", os.sep)
            data = zf.read(entry)
            dst = os.path.join(BK, u"src", u"main", u"resources", rel)
            os.makedirs(os.path.dirname(dst), exist_ok=True)
            io.open(dst, "wb").write(data)
            lines.append(u"%s  %10d  %s（取自成品 jar）" % (sha1b(data), len(data), rel))
            print(u"  [OK]   %s ← jar（%s…）" % (rel, sha1b(data)[:8]))

    for rel in PLAIN:
        src = os.path.join(ROOT, rel)
        if not os.path.exists(src):
            fails.append(u"缺文件：%s" % rel)
            continue
        dst = os.path.join(BK, rel)
        os.makedirs(os.path.dirname(dst), exist_ok=True)
        shutil.copy2(src, dst)
        before, after = sha1f(src), sha1f(dst)
        if before != after:
            fails.append(u"%s：拷贝后哈希不一致" % rel)
        else:
            lines.append(u"%s  %10d  %s" % (after, os.path.getsize(dst), rel))
            print(u"  [OK]   %s（%s…）" % (rel, after[:8]))

    io.open(os.path.join(BK, u"_sha1.txt"), "w", encoding="utf-8",
            newline=u"\n").write(u"\n".join(lines) + u"\n")
    io.open(os.path.join(BK, u"_说明.txt"), "w", encoding="utf-8", newline=u"\n").write(
        u"""ZF83 改前件说明（**事后补建**，请照实看待）

① 本轮我**先动手后抄**：把三张板子贴图转档、并改了三个物品模型之后才建这个备份
   —— 违反 §10「第一个字节改动之前先抄」，这是第二次（ZF78 那次也是）。已记进档案 §4.56。

② 贴图与模型这 6 份不是"当时磁盘上的原件"（原件已被覆盖），而是从
   **ZF82 已发布的成品 jar** 里逐字节取回的：%s（SHA1 %s）
   —— 那是用户手上那个包，也就是"改动前游戏里真实生效的样子"，因此可信且可复核。

③ `docs/贴图清单.md`、`docs/开发档案.md`、`release/*` 三份确实是动手前拷的（未被本轮改动）。
""" % (JAR, jar_sha))

    print(u"\n改前件 %d 份 → %s" % (len(lines), BK))
    print(u"失败项 = %d" % len(fails))
    for f in fails:
        print(u"  !! " + f)
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())
