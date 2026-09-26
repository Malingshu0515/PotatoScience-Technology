# -*- coding: utf-8 -*-
r'''_zf144_backup.py —— §10：动第一个字节之前先把改前件逐字节备份到救援盘。

备份根：`C:\PotatoST救援\zf144_pre`

本轮（ZF144：星璨钢锹 + 剑的「星辉斩」）会碰到的路径：
  · **要改的**：`StarSteelSwordItem` / `StarSteelTools` / `ModTiers` / `ModItems` / `PotatoST`（探针挂载点）
    / 四份 lang / 凭据 / 四份文档 / 门清单与计数器 / TextureCheck；
  · **可能会被"跟平活体数字"改到的**：build/zftools 下所有常驻门脚本（键数 487→492、配方 72→73）；
  · **新建的**（盘上还没有）：锹的物品类 / 一个 damage_type / 一张配方 / 一个模型 / 一张贴图
    + Zf144Check.java + 本轮脚本 —— 这些备份时记为 MISSING。

自证：每一份拷完**回读**，逐份比 sha1；有一份对不上就当场报错。
跑法：python build\zftools\_zf144_backup.py
'''
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
PRE = os.path.join(r"C:\PotatoST救援", "zf144_pre")
ZFTOOLS = os.path.join(ROOT, "build", "zftools")

NAMED = [
    r"src\main\java\com\potatost\mod\StarSteelSwordItem.java",
    r"src\main\java\com\potatost\mod\StarSteelTools.java",
    r"src\main\java\com\potatost\mod\ModTiers.java",
    r"src\main\java\com\potatost\mod\ModItems.java",
    r"src\main\java\com\potatost\mod\PotatoST.java",
    r"src\main\resources\assets\potato_s_t\lang\zh_cn.json",
    r"src\main\resources\assets\potato_s_t\lang\en_us.json",
    r"src\main\resources\assets\potato_s_t\lang\ja_jp.json",
    r"src\main\resources\assets\potato_s_t\lang\ru_ru.json",
    r"build\用户素材\_来源凭据.json",
    r"docs\开发档案.md",
    r"docs\多会话协作交接.md",
    r"docs\贴图清单.md",
    r"docs\UpdateAnnouncement_EN.md",
    r"build\zftools\_zf104_gates.ps1",
    r"build\zftools\_zf104_gatecount.py",
    r"build\zftools\TextureCheck.py",
]

GATE_PAT = ("_verify.py", "_check.py", "_chain.py", "_falsify.py",
            "_gatesnap.py", "_fluidcheck.py", "_langcheck.py", "_repro.py")


def collect_gates():
    out = []
    if not os.path.isdir(ZFTOOLS):
        return out
    for name in sorted(os.listdir(ZFTOOLS)):
        if name.endswith(".py") and any(name.endswith(p) for p in GATE_PAT):
            out.append(os.path.join("build", "zftools", name))
    return out


def sha1(p):
    return hashlib.sha1(open(p, "rb").read()).hexdigest()


def main():
    files = list(NAMED) + collect_gates()
    seen, ordered = set(), []
    for f in files:
        k = f.lower()
        if k in seen:
            continue
        seen.add(k)
        ordered.append(f)

    ok, missing, bad, manifest = [], [], [], []
    for rel in ordered:
        src = os.path.join(ROOT, rel)
        dst = os.path.join(PRE, rel)
        if not os.path.isfile(src):
            missing.append(rel)
            manifest.append(u"MISSING\t%s" % rel)
            continue
        os.makedirs(os.path.dirname(dst), exist_ok=True)
        shutil.copy2(src, dst)
        if sha1(src) != sha1(dst):
            bad.append(rel)
            continue
        ok.append(rel)
        manifest.append(u"%s\t%s\t%d" % (sha1(src), rel, os.path.getsize(src)))

    io.open(os.path.join(PRE, "_sha1.txt"), "w", encoding="utf-8",
            newline="\n").write(u"\n".join(manifest) + u"\n")

    print(u"备份根：%s" % PRE)
    print(u"  已核哈希 %d 份" % len(ok))
    print(u"  盘上还没有（MISSING）%d 份：%s" % (len(missing), missing[:6]))
    print(u"  回读不一致 %d 份：%s" % (len(bad), bad))
    print(u"")
    print(u"失败项 = %d" % len(bad))
    return 1 if bad else 0


if __name__ == u"__main__":
    sys.exit(main())
