# -*- coding: utf-8 -*-
r"""_zf141_backup.py —— §10：**改第一个字节之前**先把改前件逐字节备份到救援盘。

备份根：`C:\PotatoST救援\zf141_pre`（与 zf72 起的每一次同一个根；桌面根早已被删，见 §10）

本轮（ZF141：星璨钢工具补齐）会碰到的路径分三类：
  · **要改的**：ModTiers / ModItems / PotatoST（探针挂载点）/ 四份 lang / 斧子贴图（换新图）
    / 凭据 / 四份文档 / 门清单 / 门计数器；
  · **可能会被"跟平数字"改到的**：build/zftools 下所有常驻门脚本（键数 487 那一串）；
  · **新建的**（盘上还没有）：三把工具的三个 java + 三个配方 + 三个模型 + 三张贴图
    + Zf141Check.java + 本轮的脚本 —— 这些备份时记为 MISSING，收尾时单独列进 `_zf141_newfiles.txt`。

自证：每一份拷完**回读**，逐份比 sha1；有一份对不上就当场报错（宁可不改）。
跑法：python build\zftools\_zf141_backup.py
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
PRE = os.path.join(r"C:\PotatoST救援", "zf141_pre")
ZFTOOLS = os.path.join(ROOT, "build", "zftools")

# ---- ① 明确要改的 ----
NAMED = [
    r"src\main\java\com\potatost\mod\ModTiers.java",
    r"src\main\java\com\potatost\mod\ModItems.java",
    r"src\main\java\com\potatost\mod\PotatoST.java",
    r"src\main\resources\assets\potato_s_t\textures\item\star_steel_axe.png",
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

# ---- ② 可能会被"跟平活体数字"改到的常驻门（全量，别挑）----
GATE_PAT = ("_verify.py", "_check.py", "_chain.py", "_falsify.py",
            "_gatesnap.py", "_fluidcheck.py", "_langcheck.py")


def collect_gates():
    out = []
    if not os.path.isdir(ZFTOOLS):
        return out
    for name in sorted(os.listdir(ZFTOOLS)):
        if not name.endswith(".py"):
            continue
        if any(name.endswith(p) for p in GATE_PAT):
            out.append(os.path.join("build", "zftools", name))
    return out


def sha1(p):
    return hashlib.sha1(open(p, "rb").read()).hexdigest()


def main():
    files = list(NAMED) + collect_gates()
    # 去重、保持稳定顺序
    seen, ordered = set(), []
    for f in files:
        k = f.lower()
        if k in seen:
            continue
        seen.add(k)
        ordered.append(f)

    ok, missing, bad = [], [], []
    manifest = []
    for rel in ordered:
        src = os.path.join(ROOT, rel)
        dst = os.path.join(PRE, rel)
        if not os.path.isfile(src):
            missing.append(rel)
            manifest.append(u"MISSING\t%s" % rel)
            continue
        os.makedirs(os.path.dirname(dst), exist_ok=True)
        shutil.copy2(src, dst)
        # **回读**：拷完再读一遍，逐份比哈希（不靠 copy 的返回值）
        if sha1(src) != sha1(dst):
            bad.append(rel)
            continue
        ok.append(rel)
        manifest.append(u"%s\t%s\t%d" % (sha1(src), rel, os.path.getsize(src)))

    # 清单落盘（含改前件的哈希，收尾时用来证明"只改了该改的"）
    io.open(os.path.join(PRE, "_sha1.txt"), "w", encoding="utf-8",
            newline="\n").write(u"\n".join(manifest) + u"\n")

    print(u"备份根：%s" % PRE)
    print(u"  已核哈希 %d 份" % len(ok))
    print(u"  盘上还没有（记为 MISSING）%d 份" % len(missing))
    for m in missing:
        print(u"      MISSING  %s" % m)
    print(u"  回读不一致 %d 份" % len(bad))
    for b in bad:
        print(u"      !! %s" % b)
    print(u"")
    print(u"失败项 = %d" % len(bad))
    return 1 if bad else 0


if __name__ == u"__main__":
    sys.exit(main())
