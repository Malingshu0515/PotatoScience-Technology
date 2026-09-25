# -*- coding: utf-8 -*-
u"""_zf78_archive.py —— 把 ZF78 这一轮的新增/改动文件归档到 `C:\\PotatoST救援\\zf78_pre\\新增文件\\`

规矩（§10）：
  · 逐份**核哈希**（拷完再算一遍，不一致就报 FAIL）；
  · 每类文件都断言"至少拷到 N 份"（防 glob 写错、静默什么都没拷）；
  · 归档清单（含哈希）追加进 `MANIFEST.md`。
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
BK = r"C:\PotatoST救援\zf78_pre"
NEW = os.path.join(BK, u"新增文件")

# (分类, 相对路径 glob, 至少几份)
GROUPS = [
    (u"Java：本轮 7 个新类",
     [r"src\main\java\com\potatost\mod\Distillation*.java",
      r"src\main\java\com\potatost\mod\client\Distillation*.java"], 7),
    (u"Java：本轮改过的 8 个文件（改后状态）",
     [r"src\main\java\com\potatost\mod\ModFluids.java",
      r"src\main\java\com\potatost\mod\ModItems.java",
      r"src\main\java\com\potatost\mod\ModBlocks.java",
      r"src\main\java\com\potatost\mod\ModMenus.java",
      r"src\main\java\com\potatost\mod\PotatoST.java",
      r"src\main\java\com\potatost\mod\PotatoSTClient.java",
      r"src\main\java\com\potatost\mod\client\gui\parts\EnergyBarPart.java",
      r"src\main\java\com\potatost\mod\client\gui\parts\FluidTankPart.java"], 8),
    (u"Java：2026-09-24 追加改过的 3 个（倒流体扩了容器接口）",
     [r"src\main\java\com\potatost\mod\FluidContainerItem.java",
      r"src\main\java\com\potatost\mod\OilBucketItem.java",
      r"src\main\java\com\potatost\mod\HighPressureTankItem.java"], 3),
    (u"资源：方块状态 / 模型",
     [r"src\main\resources\assets\potato_s_t\blockstates\distillation_*.json",
      r"src\main\resources\assets\potato_s_t\models\block\distillation_*.json",
      r"src\main\resources\assets\potato_s_t\models\item\distillation_*.json",
      r"src\main\resources\assets\potato_s_t\models\item\bitumen.json"], 7),
    (u"资源：贴图（4 流体 × still/flow + 2 方块 × 顶/侧 + 沥青）",
     [r"src\main\resources\assets\potato_s_t\textures\block\distillation_*.png",
      r"src\main\resources\assets\potato_s_t\textures\block\diesel_*.png",
      r"src\main\resources\assets\potato_s_t\textures\block\naphtha_*.png",
      r"src\main\resources\assets\potato_s_t\textures\block\gasoline_*.png",
      r"src\main\resources\assets\potato_s_t\textures\block\lpg_*.png",
      r"src\main\resources\assets\potato_s_t\textures\item\bitumen.png"], 13),
    (u"资源：四语言",
     [r"src\main\resources\assets\potato_s_t\lang\*.json"], 4),
    (u"资源：标签（4 张流体 c: + 挖掘标签）",
     [r"src\main\resources\data\c\tags\fluid\diesel.json",
      r"src\main\resources\data\c\tags\fluid\naphtha.json",
      r"src\main\resources\data\c\tags\fluid\gasoline.json",
      r"src\main\resources\data\c\tags\fluid\lpg.json",
      r"src\main\resources\data\minecraft\tags\block\mineable\pickaxe.json"], 5),
    (u"工具：本轮脚本 + 门脚本 + 探针源",
     [r"build\zftools\_zf78_*.py",
      r"build\zftools\_zf78_gates.ps1",
      r"build\zftools\check\DistillationCheck.java"], 14),
    (u"工具：证据（探针报告 / 门日志 / 构建日志 / 凭据）",
     [r"build\zftools\_zf78_probe.txt",
      r"build\zftools\_zf78_gates.txt",
      r"build\zftools\_zf78_gates.txt.utf8.txt",
      r"build\zftools\_zf78_server.log",
      r"build\zftools\_zf78_server.log.utf8.txt",
      r"build\zftools\_zf78_compile.log.utf8.txt",
      r"build\zftools\_zf78_build2.log.utf8.txt",
      r"build\zftools\_zf78_bitumen_provenance.json"], 6),
    (u"文档",
     [r"docs\开发档案.md", r"docs\v0.11规划.md", r"docs\贴图清单.md",
      r"docs\UpdateAnnouncement_EN.md"], 4),
    (u"成品",
     [r"release\PotatoST-0.11.jar", r"release\PotatoST-0.11.jar.sha1"], 2),
]

fails = []
lines = []


def sha1(path):
    return hashlib.sha1(open(path, "rb").read()).hexdigest()


def main():
    total = 0
    size = 0
    for title, patterns, minimum in GROUPS:
        files = []
        for pat in patterns:
            files += [p for p in glob.glob(os.path.join(ROOT, pat)) if os.path.isfile(p)]
        files = sorted(set(files))
        if len(files) < minimum:
            fails.append(u"%s：只找到 %d 份（至少应有 %d）" % (title, len(files), minimum))
        print(u"== %s：%d 份 ==" % (title, len(files)))
        for src in files:
            rel = os.path.relpath(src, ROOT)
            dst = os.path.join(NEW, rel)
            os.makedirs(os.path.dirname(dst), exist_ok=True)
            before = sha1(src)
            shutil.copy2(src, dst)
            after = sha1(dst)
            if before != after:
                fails.append(u"%s：拷贝后哈希不一致" % rel)
            else:
                total += 1
                size += os.path.getsize(dst)
                lines.append(u"%s  %10d  %s" % (after, os.path.getsize(dst), rel))
        print(u"   ✓")
    print(u"\n归档 %d 份 / %.1f KB" % (total, size / 1024.0))

    # 清单追加进 MANIFEST（不覆盖原有内容）
    man = os.path.join(BK, "MANIFEST.md")
    t = io.open(man, encoding="utf-8").read()
    block = (u"\n## 归档清单（`新增文件\\`，%d 份，逐份核过哈希）\n\n```\n"
             % total) + u"\n".join(lines) + u"\n```\n"
    if u"## 归档清单" in t:
        t = t[:t.index(u"## 归档清单")] + block
    else:
        t += block
    io.open(man, "w", encoding="utf-8", newline=u"\n").write(t)
    print(u"MANIFEST.md 已更新")

    print(u"\n失败项 = %d" % len(fails))
    for f in fails:
        print(u"  !! " + f)
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())
