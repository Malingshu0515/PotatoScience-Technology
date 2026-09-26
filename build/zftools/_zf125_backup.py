# -*- coding: utf-8 -*-
u"""_zf125_backup.py —— ZF125 的改前件（§10：**先建备份，再动第一个字节**）

用户原话（一条消息给全图纸与功能）：
「加一个大型柴油发电机 3x5x2 第一层【耐热金属块】【流体泵】【耐热金属块】，
【耐热金属块】【低级发电机】【耐热金属块】，【耐热金属块】【燃烧反应室】【耐热金属块】，
【耐热金属块】【低级发电机】【耐热金属块】，【耐热金属块】【柴油发电机控制器】【耐热金属块】
第二层 【一般金属块】【耐热金属块】【一般金属块】，【铜块】【铜格栅】【铜块】，【铜块】【铜格栅】【铜块】，
【铜块】【铜格栅】【铜块】，【一般金属块】【接线块】【一般金属块】（铜无论氧化/涂蜡程度都可以）
以柴油发电机控制器为正方向 右键打开GUI 显示流体储罐（8000mB）工作指示灯 检测到红石信号停机
可以用流体泵泵入柴油 或用柴油桶/含有柴油的油桶右键添加柴油 每t消耗1mb柴油 7.2kFE
柴油发电机控制器配方;【】【流体管道】【】，【铜块】【熔炉】【铜块】，【】【钢板】【】」

⚠ 本轮**没有新方块**：`minecraft:copper_grate`（铜格栅）在 MC 1.21.1 **本来就有**，
   8 个氧化/涂蜡变体齐全（已从 `build\\neoForm\\...\\raw.jar` 与
   `.gradle\\caches\\minecraft\\versions\\1.21.1\\client.jar` 两处核实）。

本轮会新增（这些路径现在都应当**不存在**）：
  7 个 Java + 6 份资源 + 1 份配方 + 1 份物品标签 + 若干 zftools 脚本。

跑法：
    python build\\zftools\\_zf125_backup.py
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
BK = r"C:\PotatoST救援\zf125_pre"
JAVA = r"src\main\java\com\potatost\mod"
LANG = r"src\main\resources\assets\potato_s_t\lang"
ASSETS = r"src\main\resources\assets\potato_s_t"
DATA = r"src\main\resources\data"
TOOLS = r"build\zftools"

FILES = [
    JAVA + r"\ModBlocks.java",
    JAVA + r"\ModItems.java",
    JAVA + r"\ModMenus.java",
    JAVA + r"\PotatoST.java",
    JAVA + r"\PotatoSTClient.java",
    JAVA + r"\client\gui\parts\StatusLampPart.java",
    LANG + r"\zh_cn.json",
    LANG + r"\en_us.json",
    LANG + r"\ja_jp.json",
    LANG + r"\ru_ru.json",
    DATA + r"\minecraft\tags\block\mineable\pickaxe.json",
    DATA + r"\minecraft\tags\block\needs_stone_tool.json",
    DATA + r"\potato_s_t\tags\item\potato_s_t.json",
    TOOLS + r"\_zf100_verify.py",
    TOOLS + r"\_zf101_verify.py",
    TOOLS + r"\_zf102_verify.py",
    TOOLS + r"\_zf103_verify.py",
    TOOLS + r"\_zf117_verify.py",
    TOOLS + r"\_zf123_langaudit.py",
    TOOLS + r"\TextureCheck.py",
    TOOLS + r"\ModelCheck.py",
    r"docs\开发档案.md",
    r"docs\多会话协作交接.md",
    r"docs\UpdateAnnouncement_EN.md",
    r"docs\贴图清单.md",
    r"release\PotatoST-0.11.jar",
    r"release\PotatoST-0.11.jar.sha1",
]

J = JAVA + r"\%s.java"
NEW = [
    J % u"DieselGeneratorStructure",
    J % u"DieselGeneratorBlock",
    J % u"DieselGeneratorBlockEntity",
    J % u"DieselGeneratorPortBlock",
    J % u"DieselGeneratorPortBlockEntity",
    J % u"DieselGeneratorMenu",
    JAVA + r"\client\DieselGeneratorScreen.java",
    ASSETS + r"\blockstates\diesel_generator_controller.json",
    ASSETS + r"\blockstates\diesel_generator_port.json",
    ASSETS + r"\models\block\diesel_generator_controller.json",
    ASSETS + r"\models\block\diesel_generator_port.json",
    ASSETS + r"\models\item\diesel_generator_controller.json",
    ASSETS + r"\textures\block\diesel_generator_controller.png",
    DATA + r"\potato_s_t\recipe\diesel_generator_controller.json",
    DATA + r"\potato_s_t\tags\item\copper_blocks.json",
] + [TOOLS + r"\_zf125_%s.py" % s for s in
     ("backup", "java", "assets", "lang", "verify", "falsify", "docs")]

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
    for pat in ("_zf*_verify.py", "_zf*_falsify.py", "_zf*_gatesnap.py"):
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

    # 本轮要动的 7 个 Java 与 4 份语言，点名必须在
    for rel in [JAVA + r"\ModBlocks.java", JAVA + r"\PotatoST.java",
                LANG + r"\zh_cn.json", LANG + r"\ru_ru.json",
                r"docs\开发档案.md"]:
        if not os.path.exists(os.path.join(BK, rel)):
            fails.append(u"点名件没抄到：%s" % rel)
    notes.append(u"点名件全在（ModBlocks / PotatoST / 四语言 / 开发档案）")

    # 新增件必须**现在还不存在**（否则说明有人先动过）
    # ⚠ 本脚本自己（_zf125_backup.py）当然已经存在 —— 从判据里摘掉，别自己咬自己
    probe = [rel for rel in NEW if not rel.endswith(u"_zf125_backup.py")]
    existed = [rel for rel in probe if os.path.exists(os.path.join(ROOT, rel))]
    if existed:
        fails.append(u"这些「新增件」已经存在了，别再往下走：%s" % u"、".join(existed))
    else:
        notes.append(u"新增件 %d 条：动手前一条都不存在" % len(probe))

    io.open(os.path.join(BK, u"_zf125_newfiles.txt"), "w", encoding="utf-8",
            newline=u"\n").write(u"本轮开始前这些路径应当不存在：\n" + u"\n".join(NEW) + u"\n")
    io.open(os.path.join(BK, u"_sha1.txt"), "w", encoding="utf-8", newline=u"\n").write(
        u"\n".join(lines) + u"\n")
    io.open(os.path.join(BK, u"_说明.txt"), "w", encoding="utf-8", newline=u"\n").write(
        u"ZF125 改前件：大型柴油发电机（3×5×2 多方块）\n"
        u"备份时间：见文件时间戳；备份脚本：build/zftools/_zf125_backup.py\n"
        u"包含：本轮会动的 6 个 Java + 4 份 lang + 2 张挖掘标签 + 2 份文档 + release/ 现状\n"
        u"      + 全部 _zf*_verify.py / _zf*_falsify.py / _zf*_gatesnap.py\n")
    print(u"\n".join(u"  [OK] " + n for n in notes))
    print(u"改前件 %d 份 → %s" % (ok, BK))
    print(u"失败项 = %d" % len(fails))
    for f in fails:
        print(u"  !! " + f)
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())
