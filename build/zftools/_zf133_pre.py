# -*- coding: utf-8 -*-
"""_zf133_pre.py —— ZF133 改前备份（§10 那条规定动作）

备份哪些件、凭什么挑的（**改前件必须逐个核 sha256**）：

  A 组 **我要改的共享文件**（多线汇合点，改前必须留底）：
      src/main/java/com/potatost/mod/ModItems.java
      src/main/java/com/potatost/mod/ModTiers.java
      src/main/java/com/potatost/mod/PotatoST.java
      src/main/java/com/potatost/mod/PotatoSTClient.java
      src/main/resources/assets/potato_s_t/lang/{zh_cn,en_us,ja_jp,ru_ru}.json
      docs/开发档案.md
      docs/贴图清单.md
      build/zftools/TextureCheck.py          ← 第 8 道门（"还在借原版贴图"的活体数字在里面）

  B 组 **我要新建的件**（改前 = 不存在，登记"不存在"本身也是一份凭据）：
      StarSteelAxeItem.java / ShockwaveManager.java / client/ShockwaveClientState.java
      client/ShockwaveRenderer.java / ShockwaveNetworking.java
      assets/.../textures/item/star_steel_axe.png
      assets/.../models/item/star_steel_axe.json

`_sha256.txt` 里 B 组写成 `MISSING (改前不存在)` —— 这样"本轮新建"这件事
是可核的（不是我事后自己说的）。

跑法：python build/zftools/_zf133_pre.py
"""
import hashlib
import io
import os
import shutil
import sys

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

ROOT = r"E:\PotatoST"
DEST = r"C:\PotatoST救援\zf133_pre"

A = [
    "src/main/java/com/potatost/mod/ModItems.java",
    "src/main/java/com/potatost/mod/ModTiers.java",
    "src/main/java/com/potatost/mod/PotatoST.java",
    "src/main/java/com/potatost/mod/PotatoSTClient.java",
    "src/main/resources/assets/potato_s_t/lang/zh_cn.json",
    "src/main/resources/assets/potato_s_t/lang/en_us.json",
    "src/main/resources/assets/potato_s_t/lang/ja_jp.json",
    "src/main/resources/assets/potato_s_t/lang/ru_ru.json",
    "docs/开发档案.md",
    "docs/贴图清单.md",
    "build/zftools/TextureCheck.py",
]

B = [
    "src/main/java/com/potatost/mod/StarSteelAxeItem.java",
    "src/main/java/com/potatost/mod/ShockwaveManager.java",
    "src/main/java/com/potatost/mod/ShockwaveNetworking.java",
    "src/main/java/com/potatost/mod/client/ShockwaveClientState.java",
    "src/main/java/com/potatost/mod/client/ShockwaveRenderer.java",
    "src/main/resources/assets/potato_s_t/textures/item/star_steel_axe.png",
    "src/main/resources/assets/potato_s_t/models/item/star_steel_axe.json",
]


def sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def main():
    if os.path.isdir(DEST):
        print("目录已存在：%s （先核对再决定要不要覆盖）" % DEST)
    os.makedirs(DEST, exist_ok=True)
    lines = []

    # ---- A 组：复制 + 核哈希 ----
    for rel in A:
        src = os.path.join(ROOT, rel.replace("/", os.sep))
        dst = os.path.join(DEST, rel.replace("/", os.sep))
        assert os.path.isfile(src), "改前件不在：" + src
        os.makedirs(os.path.dirname(dst), exist_ok=True)
        shutil.copy2(src, dst)
        s1, s2 = sha256(src), sha256(dst)
        assert s1 == s2, "拷完哈希不一致：" + rel
        lines.append("%s  %s  %d bytes" % (s1, rel, os.path.getsize(src)))
        print("[OK ] %s  %s" % (s1[:16], rel))

    # ---- B 组：登记"改前不存在" ----
    for rel in B:
        src = os.path.join(ROOT, rel.replace("/", os.sep))
        mark = "MISSING (改前不存在)" if not os.path.isfile(src) else "!! 已存在，需重新判断"
        lines.append("%-24s %s" % (mark, rel))
        print("[%s] %s" % ("NEW " if not os.path.isfile(src) else "WARN", rel))

    io.open(os.path.join(DEST, "_sha256.txt"), "w", encoding="utf-8",
            newline="\n").write("\n".join(lines) + "\n")
    print("-" * 60)
    print("备份完成：%s（A 组 %d 件 + B 组 %d 件登记）" % (DEST, len(A), len(B)))


main()
