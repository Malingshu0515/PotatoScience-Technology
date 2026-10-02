# -*- coding: utf-8 -*-
u"""_zf167_pre.py —— ZF167 的改前件（§10：**先建备份，再动第一个字节**）

用户原话（本轮需求，逐字）：
    「先加个空铝罐配方；【】【铝粒】【】，【】【铝板】【】，【】【】【】合成2个空铝罐
      熔炉/高炉烧制一个空铝罐产出5个铝粒；再加一个饮料罐装机（配方；【】【铁锭】【】，
      【拉杆】【银版】【铁活版门】，【轻质压力板】【高压气罐】【流体管道】）
      一个碳酸储罐（100MB）一个水储罐（1000mb）一个乙醇储罐（100mb 目前本mod没有乙醇
      做个兼容别的mod的乙醇）三个输入槽 一个输出槽 耗电600fe/t 先做一个配方试试水
      1.10mb碳酸+500mb水+2糖+1可可豆+1空铝罐 5s产出1罐可乐
      可乐是食物 但是食用音效用蜂蜜瓶的 食用后给予120s的急迫 3s的生命恢复1
      恢复3点饥饿值 9点饱和度 （食用后返还一个空铝罐）」

⇒ 本轮要动的盘上文件：
  ① **物品**：`ModItems.java`（空铝罐 / 可乐 + 创造页两行）、新 `ColaItem.java`
     （食物 + 蜂蜜瓶音效 + 吃完返还空铝罐）；
  ② **机器**：新 `BeverageCanningMachine{Block,BlockEntity,Menu}.java` +
     `client/BeverageCanningMachineScreen.java` + 新 `CanningMachineRecipes.java`；
  ③ **注册**：`ModBlocks.java`（方块 + 物品 + 方块实体）、`ModMenus.java`（菜单）、
     `PotatoST.java`（三种能力 + 探针挂载点）、`PotatoSTClient.java`（界面）、
     `client/jei/PotatoSTJeiPlugin.java` + `MachineRecipes.java`（JEI 那一条展示）；
  ④ **资源**：五份 lang、机器方块模型/blockstate/两张贴图、两个物品模型、
     四份配方 JSON（空铝罐 / 熔炉 / 高炉 / 机器本体）+ `data/c/tags/fluid/ethanol.json`；
  ⑤ 全部常驻门（改前件留底；活体数字本轮要跟平）+ 九道门本体 + 三份文档 + 旧成品。

⚠ 轮号先查过（§4.132）：`_zf167_*` 只有我自己那份侦察脚本、救援目录里没有 `zf167_pre`
   （场上已被占到 ZF166）。
跑法：python build\\zftools\\_zf167_pre.py
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
BK = r"C:\PotatoST救援\zf167_pre"
TOOLS = r"build\zftools"
MOD = r"src\main\java\com\potatost\mod"
ASSETS = r"src\main\resources\assets\potato_s_t"
LANG = ASSETS + r"\lang"

FILES = [
    MOD + r"\ModItems.java",
    MOD + r"\ModBlocks.java",
    MOD + r"\ModMenus.java",
    MOD + r"\PotatoST.java",
    MOD + r"\PotatoSTClient.java",
    MOD + r"\MachineRecipes.java",
    MOD + r"\client\jei\PotatoSTJeiPlugin.java",
    # 照抄的样板（不改，留底当对照）
    MOD + r"\MicroCrusherBlockEntity.java",
    MOD + r"\MicroCrusherBlock.java",
    MOD + r"\MicroCrusherMenu.java",
    MOD + r"\MicroCrusherRecipes.java",
    MOD + r"\FillingMachineBlockEntity.java",
    MOD + r"\MachineDrops.java",
    LANG + r"\zh_cn.json",
    LANG + r"\en_us.json",
    LANG + r"\ja_jp.json",
    LANG + r"\ru_ru.json",
    LANG + r"\lzh.json",
    ASSETS + r"\blockstates\micro_crusher.json",
    ASSETS + r"\models\block\micro_crusher.json",
    ASSETS + r"\models\item\micro_crusher.json",
    TOOLS + r"\Audit.ps1",
    TOOLS + r"\LangCheck.ps1",
    TOOLS + r"\RecipeCheck.ps1",
    TOOLS + r"\ModelCheck.py",
    TOOLS + r"\JsonCheck.py",
    TOOLS + r"\SoundCheck.py",
    TOOLS + r"\TextureCheck.py",
    TOOLS + r"\ToolLint.py",
    TOOLS + r"\check\GroupEnergyCheck.java",
    r"docs\开发档案.md",
    r"docs\多会话协作交接.md",
    r"docs\贴图清单.md",
    r"docs\UpdateAnnouncement_EN.md",
    r"release\PotatoST-0.12.jar",
    r"release\PotatoST-0.12.jar.sha1",
]

NEW = [
    MOD + r"\ColaItem.java",
    MOD + r"\CanningMachineRecipes.java",
    MOD + r"\BeverageCanningMachineBlock.java",
    MOD + r"\BeverageCanningMachineBlockEntity.java",
    MOD + r"\BeverageCanningMachineMenu.java",
    MOD + r"\client\BeverageCanningMachineScreen.java",
    ASSETS + r"\blockstates\beverage_canning_machine.json",
    ASSETS + r"\models\block\beverage_canning_machine.json",
    ASSETS + r"\models\item\beverage_canning_machine.json",
    ASSETS + r"\models\item\empty_aluminum_can.json",
    ASSETS + r"\models\item\cola.json",
    ASSETS + r"\textures\block\beverage_canning_machine_top.png",
    ASSETS + r"\textures\block\beverage_canning_machine_side.png",
    r"src\main\resources\data\potato_s_t\recipe\empty_aluminum_can.json",
    r"src\main\resources\data\potato_s_t\recipe\empty_aluminum_can_from_smelting.json",
    r"src\main\resources\data\potato_s_t\recipe\empty_aluminum_can_from_blasting.json",
    r"src\main\resources\data\potato_s_t\recipe\beverage_canning_machine.json",
    r"src\main\resources\data\c\tags\fluid\ethanol.json",
    TOOLS + r"\_zf167_verify.py",
    TOOLS + r"\_zf167_falsify.py",
    TOOLS + r"\_zf167_gates.py",
    TOOLS + r"\_zf167_probe.py",
    TOOLS + r"\_zf167_publish.py",
    TOOLS + r"\_zf167_docs.py",
    TOOLS + r"\_zf167_texture.py",
    TOOLS + r"\_zf167_commit.py",
    TOOLS + r"\_zf167_commit_msg.txt",
    TOOLS + r"\check\Zf167Check.java",
]

MINE = [TOOLS + r"\_zf167_recon_ethanol.py"]

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
    for pat in ("_zf*_verify.py", "_zf*_falsify*.py", "_zf*_gates.py", "_rzh_*.py"):
        for p in sorted(glob.glob(os.path.join(ROOT, TOOLS, pat))):
            rel = os.path.relpath(p, ROOT)
            if rel not in todo:
                todo.append(rel)

    missing = []
    for rel in todo:
        src = os.path.join(ROOT, rel)
        if not os.path.exists(src):
            missing.append(rel)
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

    unexpected = [rel for rel in missing if rel not in NEW]
    if unexpected:
        fails.append(u"这些**该有**的文件不在盘上：%s" % u"、".join(unexpected))
    else:
        notes.append(u"盘上缺的 %d 份全部是本轮新建件（符合预期）" % len(missing))

    existed = [rel for rel in NEW if os.path.exists(os.path.join(ROOT, rel))]
    if existed:
        fails.append(u"这些「新增件」已经存在了：%s" % u"、".join(existed))
    else:
        notes.append(u"新增件 %d 条：动手前一条都不存在" % len(NEW))

    if not os.path.exists(os.path.join(ROOT, MINE[0])):
        fails.append(u"侦察脚本不在：%s" % MINE[0])
    else:
        notes.append(u"侦察脚本 1 份（只读，动手前建的，单独记账）")

    io.open(os.path.join(BK, u"_zf167_newfiles.txt"), "w", encoding="utf-8",
            newline=u"\n").write(u"本轮开始前这些路径应当不存在：\n" + u"\n".join(NEW) + u"\n")
    io.open(os.path.join(BK, u"_sha1.txt"), "w", encoding="utf-8", newline=u"\n").write(
        u"\n".join(lines) + u"\n")
    io.open(os.path.join(BK, u"_说明.txt"), "w", encoding="utf-8", newline=u"\n").write(
        u"ZF167 改前件：空铝罐 + 可乐 + 饮料罐装机（0.13）。\n"
        u"备份脚本：build/zftools/_zf167_pre.py\n"
        u"⚠ 碳酸用本 mod 已有的 potato_s_t:carbonic_acid（酸性反应室那条配方产的，ZF101）；\n"
        u"   乙醇本 mod 没有 ⇒ 机器那只罐收 **c:ethanol** 流体标签（沉浸工程自己在盘上的 jar 里\n"
        u"   就是 data/c/tags/fluid/ethanol.json + immersiveengineering:ethanol，见 _zf167_recon_ethanol.py）。\n"
        u"⚠ 「轻质压力板」本 mod 没有压力板 ⇒ 取原版 minecraft:light_weighted_pressure_plate（已挂待确认）。\n")
    print(u"\n".join(u"  [OK] " + n for n in notes))
    print(u"改前件 %d 份 → %s" % (ok, BK))
    print(u"失败项 = %d" % len(fails))
    for f in fails:
        print(u"  !! " + f)
    return 1 if fails else 0


if __name__ == u"__main__":
    sys.exit(main())
