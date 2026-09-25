# -*- coding: utf-8 -*-
u"""_zf97_backup.py —— ZF97 **动手前**的改前件（§10）

本轮（用户两条消息给的规格）：

  ① **空气分离器**：gui 只有两个储罐（**不接受被灌入、只能泵出**）+ 一个工作指示灯；
     储能 5000 FE、耗能 200 FE/t、**30 s 产出 8 mB 氮气 + 2 mB 氧气**；
     配方【】【散热装置】【电容】/【高压气罐】【加热装置】【高压气罐】/【电容】【流体管道】【】
  ② **氨气组成室**：gui 左侧原料储罐 + 一个催化剂槽（槽位上标「催化剂(铁粉)」）、右侧输出；
     **每 t 耗 1 mB 氮气 + 1 mB 氢气、200 FE/t、产 1 mB 氨气**，催化剂不消耗；
     原料罐下方各一个高压气罐槽（气罐 → 储罐 50 mB/t），输出罐的槽反向（氨气 50 mB/t → 气罐）；
     泵只能泵入氮气/氢气、泵出氨气；
     配方【流体管道】【高压气罐】【流体管道】/【铁板】【高压气罐】【铁板】/【加热装置】【高压气罐】【加热装置】

⇒ 本轮要动的东西比往轮多一个量级：**两种新流体**（氮气 / 氨气）会牵到
`ModFluids`、客户端贴图注册、`isGas` 正向白名单、`c:` 流体标签、
灌装机的 JEI 气体列表，以及**每一条数流体个数的往轮断言**。

会动到的（纳入快照）：
  · Java 9 个：ModFluids / PotatoSTClient / ModBlocks / ModMenus / PotatoST /
    ModItems / MachineRecipes / client\jei\PotatoSTJeiPlugin / client\gui\parts\StatusLampPart
  · 四份 lang + `data\c\tags\fluid\gaseous.json`
  · **12 份往轮校验**（活体数字：流体数 8→10、键数 284→N、定形配方 36→38、JEI 9→11、
    `c:gaseous` 名单、isGas 正向列举 6→10）+ `_zf78_falsify.py` + `_zf96_gates.ps1`
  · 工具件 `PngRecolor.py`（本轮要用它生成 4 张流体贴图 + 2 张机器贴图）
  · 三份文档 + 旧成品 jar 与 `.sha1`
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
BK = r"C:\PotatoST救援\zf97_pre"
JAVA = r"src\main\java\com\potatost\mod"
RES = r"src\main\resources"
FILES = [
    # ---- 要改的既有 Java ----
    JAVA + r"\ModFluids.java",
    JAVA + r"\PotatoSTClient.java",
    JAVA + r"\ModBlocks.java",
    JAVA + r"\ModMenus.java",
    JAVA + r"\PotatoST.java",
    JAVA + r"\ModItems.java",
    JAVA + r"\MachineRecipes.java",
    JAVA + r"\client\jei\PotatoSTJeiPlugin.java",
    JAVA + r"\client\gui\parts\StatusLampPart.java",
    # ---- 资源：四份语言 + 气体标签 ----
    RES + r"\assets\potato_s_t\lang\zh_cn.json",
    RES + r"\assets\potato_s_t\lang\en_us.json",
    RES + r"\assets\potato_s_t\lang\ja_jp.json",
    RES + r"\assets\potato_s_t\lang\ru_ru.json",
    RES + r"\data\c\tags\fluid\gaseous.json",
    # ---- 往轮校验脚本（活体数字 + 流体名单）----
    r"build\zftools\_zf71_verify.py",
    r"build\zftools\_zf73_repro.py",
    r"build\zftools\_zf73_verify.py",
    r"build\zftools\_zf74_verify.py",
    r"build\zftools\_zf75_verify.py",
    r"build\zftools\_zf78_verify.py",
    r"build\zftools\_zf79_verify.py",
    r"build\zftools\_zf80_verify.py",
    r"build\zftools\_zf81_verify.py",
    r"build\zftools\_zf82_verify.py",
    r"build\zftools\_zf93_verify.py",
    r"build\zftools\_zf95_verify.py",
    r"build\zftools\_zf96_verify.py",
    r"build\zftools\_zf78_falsify.py",
    r"build\zftools\_zf96_gates.ps1",
    r"build\zftools\PngRecolor.py",
    # ---- 文档 ----
    r"docs\开发档案.md",
    r"docs\贴图清单.md",
    r"docs\UpdateAnnouncement_EN.md",
    # ---- 旧成品 ----
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
    lines, ok = [], 0
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
    # 改前配方目录清单（本轮只会新增，不会改旧的）
    rdir = os.path.join(ROOT, r"src\main\resources\data\potato_s_t\recipe")
    names = sorted(n for n in os.listdir(rdir) if n.endswith(".json"))
    dst = os.path.join(BK, "recipe_before.txt")
    io.open(dst, "w", encoding="utf-8", newline=u"\n").write(u"\n".join(names) + u"\n")
    ok += 1
    lines.append(u"%s  %10d  %s" % (sha1(dst), os.path.getsize(dst), u"recipe_before.txt（%d 份）" % len(names)))
    # 改前贴图清单（本轮要新增 4 张流体 + 4 张机器，旧的一张都不许动）
    tdir = os.path.join(ROOT, r"src\main\resources\assets\potato_s_t\textures")
    tex = []
    for sub in ("block", "item"):
        for n in sorted(os.listdir(os.path.join(tdir, sub))):
            tex.append(u"%s/%s  %s" % (sub, n, sha1(os.path.join(tdir, sub, n))))
    dst = os.path.join(BK, "textures_before.txt")
    io.open(dst, "w", encoding="utf-8", newline=u"\n").write(u"\n".join(tex) + u"\n")
    ok += 1
    lines.append(u"%s  %10d  %s" % (sha1(dst), os.path.getsize(dst), u"textures_before.txt（%d 张）" % len(tex)))
    # 改前流体标签目录清单（本轮要加两份标签 + 改 gaseous）
    fdir = os.path.join(ROOT, r"src\main\resources\data\c\tags\fluid")
    fl = sorted(os.listdir(fdir))
    dst = os.path.join(BK, "fluid_tags_before.txt")
    io.open(dst, "w", encoding="utf-8", newline=u"\n").write(u"\n".join(fl) + u"\n")
    ok += 1
    lines.append(u"%s  %10d  %s" % (sha1(dst), os.path.getsize(dst), u"fluid_tags_before.txt（%d 份）" % len(fl)))
    io.open(os.path.join(BK, u"_sha1.txt"), "w", encoding="utf-8",
            newline=u"\n").write(u"\n".join(lines) + u"\n")
    print(u"改前件 %d 份 → %s" % (ok, BK))
    print(u"  配方目录改前 %d 份；贴图目录改前 %d 张；流体标签改前 %d 份" % (len(names), len(tex), len(fl)))
    print(u"失败项 = %d" % len(fails))
    for f in fails:
        print(u"  !! " + f)
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())
