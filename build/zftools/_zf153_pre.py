# -*- coding: utf-8 -*-
u"""_zf153_pre.py —— ZF153 的改前件（§10：**先建备份，再动第一个字节**）

用户原话（本轮需求，逐字）：
    「加个振金剑材质在素材 无法破坏 拿在手里免疫凋零，缓慢，挖掘疲劳 24点伤害 1.4攻击速度
      1附魔权重 shift+右键猛击地面 击飞6x6除自己的所有生物 并对其造成n+12点伤害
      n为玩家基础伤害 和4s的失明 4s的缓慢效果 冷却6s」

⇒ 本轮要动的盘上文件：
  ① `ModTiers.java` —— 加"振金"这一档（**附魔权重 1** 就落在这里，`TieredItem` 直接取
     `tier.getEnchantmentValue()`，侦察③ 已从 sources.jar 核实）+ 剑的伤害/攻速两个参数；
  ② `ModItems.java` —— 注册 `vibranium_sword` + 创造页一行（§4.82：漏了就是"看不见、搜不到"）；
  ③ `PotatoST.java` —— 挂两处 game 总线监听（"拿在手里免疫三种效果" + 手持清理），
     以及临时探针 `Zf153Check.java`（挂完必摘，逐字节核对回这份备份）；
  ④ 五份 lang —— 物品名 + Shift 说明；
  ⑤ 45 份**写死了语言键数**的常驻校验（本轮 +键 ⇒ 必须一起重定靶，照 ZF150 的 retarget 做法）；
  ⑥ `build/用户素材/_来源凭据.json`（用户素材的出处账）+ `docs/贴图清单.md` / 开发档案 / 交接；
  ⑦ 旧成品 `release/PotatoST-0.12.jar` 与 `.sha1`（本工程是"同版本原地重打"，发布必须公布作废的旧 SHA1）。

⚠ 轮号先查过（§4.132）：`build\\zftools` 下 147~152 都被别的线占了、救援目录里 142~151 也都有
   `zfN_pre`，**没有 `_zf153_*`、没有 `zf153_pre`** ⇒ 本轮取 ZF153。
⚠ 本轮开工时**同一棵树上有另一条线（ZF151/152）正挂着探针在跑**（`PotatoST.java:78`
   `Zf151Check.register();`）⇒ 我这份备份里的 `PotatoST.java` 是**带他们探针那一版**；
   我的探针挂载脚本会**只碰自己那两行**，摘的时候只摘自己的。

跑法：
    python build\\zftools\\_zf153_pre.py
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
BK = r"C:\PotatoST救援\zf153_pre"
TOOLS = r"build\zftools"
MOD = r"src\main\java\com\potatost\mod"
ASSETS = r"src\main\resources\assets\potato_s_t"
LANG = ASSETS + r"\lang"

FILES = [
    MOD + r"\ModTiers.java",
    MOD + r"\ModItems.java",
    MOD + r"\PotatoST.java",
    MOD + r"\VibraniumSwordItem.java",          # 本轮新建（不存在 ⇒ 只记进"新增件"清单）
    LANG + r"\zh_cn.json",
    LANG + r"\en_us.json",
    LANG + r"\ja_jp.json",
    LANG + r"\ru_ru.json",
    LANG + r"\lzh.json",
    r"build\用户素材\_来源凭据.json",
    TOOLS + r"\Audit.ps1",
    TOOLS + r"\LangCheck.ps1",
    TOOLS + r"\RecipeCheck.ps1",
    TOOLS + r"\ModelCheck.py",
    TOOLS + r"\JsonCheck.py",
    TOOLS + r"\SoundCheck.py",
    TOOLS + r"\TextureCheck.py",
    TOOLS + r"\ToolLint.py",
    TOOLS + r"\check\GroupEnergyCheck.java",
    # 本轮要照着写的样板（不改，只留底当对照）
    MOD + r"\StarSteelSwordItem.java",
    MOD + r"\StarSteelAxeItem.java",
    MOD + r"\ShockwaveManager.java",
    MOD + r"\ModArmorItems.java",
    # 文档
    r"docs\开发档案.md",
    r"docs\多会话协作交接.md",
    r"docs\贴图清单.md",
    r"docs\协作日志.md",
    # 旧成品
    r"release\PotatoST-0.12.jar",
    r"release\PotatoST-0.12.jar.sha1",
]

# 本轮**新建**的路径：动手前一条都不该存在
NEW = [
    MOD + r"\VibraniumSwordItem.java",
    ASSETS + r"\models\item\vibranium_sword.json",
    ASSETS + r"\textures\item\vibranium_sword.png",
    TOOLS + r"\_zf153_texture.py",
    TOOLS + r"\_zf153_java.py",
    TOOLS + r"\_zf153_lang.py",
    TOOLS + r"\_zf153_retarget.py",
    TOOLS + r"\_zf153_verify.py",
    TOOLS + r"\_zf153_falsify.py",
    TOOLS + r"\_zf153_gates.py",
    TOOLS + r"\_zf153_probe.py",
    TOOLS + r"\_zf153_publish.py",
    TOOLS + r"\_zf153_docs.py",
    TOOLS + r"\_zf153_commit.py",
    TOOLS + r"\_zf153_commit_msg.txt",
    TOOLS + r"\check\Zf153Check.java",
]

# 我自己在"建备份之前"就建好的**只读侦察脚本**（不碰任何产物 ⇒ 单独记账，不混进 NEW）
MINE = [
    TOOLS + r"\_zf153_recon.py",
    TOOLS + r"\_zf153_recon.txt",
    TOOLS + r"\_zf153_recon2.py",
    TOOLS + r"\_zf153_recon2.txt",
    TOOLS + r"\_zf153_recon3.py",
    TOOLS + r"\_zf153_recon3.txt",
]

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

    # ① 备份（缺文件是**正常的**：本轮新建的那些还不存在，见 ③）
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

    # ② 回读证明
    bad = [rel for rel in todo
           if os.path.exists(os.path.join(ROOT, rel)) and os.path.exists(os.path.join(BK, rel))
           and sha1(os.path.join(ROOT, rel)) != sha1(os.path.join(BK, rel))]
    if bad:
        fails.append(u"回读不一致：%s" % u"、".join(bad))
    else:
        notes.append(u"回读证明：%d 份备份与盘上逐字节相同" % ok)

    # ③ 缺的那几份必须是"本轮新建件"
    unexpected = [rel for rel in missing if rel not in NEW]
    if unexpected:
        fails.append(u"这些**该有**的文件不在盘上：%s" % u"、".join(unexpected))
    else:
        notes.append(u"盘上缺的 %d 份全部是本轮新建件（符合预期）" % len(missing))

    # ④ 点名件
    POINT = [MOD + r"\ModTiers.java", MOD + r"\ModItems.java", MOD + r"\PotatoST.java",
             LANG + r"\zh_cn.json", r"release\PotatoST-0.12.jar"]
    miss = [rel for rel in POINT if not os.path.exists(os.path.join(BK, rel))]
    if miss:
        fails.append(u"点名件没抄到：%s" % u"、".join(miss))
    else:
        notes.append(u"点名件全在（档位 / 注册 / 探针挂载点 / 主语言 / 旧成品）")

    # ⑤ 新增件真的一条都不存在
    existed = [rel for rel in NEW if os.path.exists(os.path.join(ROOT, rel))]
    if existed:
        fails.append(u"这些「新增件」已经存在了：%s" % u"、".join(existed))
    else:
        notes.append(u"新增件 %d 条：动手前一条都不存在" % len(NEW))

    # ⑥ 我自己的侦察脚本单独记账
    mine_missing = [rel for rel in MINE if not os.path.exists(os.path.join(ROOT, rel))]
    if mine_missing:
        fails.append(u"侦察脚本不在：%s" % u"、".join(mine_missing))
    else:
        notes.append(u"侦察脚本 %d 份（只读，建备份之前就建好了，单独记账）" % len(MINE))

    # ⑦ 写账
    io.open(os.path.join(BK, u"_zf153_newfiles.txt"), "w", encoding="utf-8",
            newline=u"\n").write(u"本轮开始前这些路径应当不存在：\n" + u"\n".join(NEW) + u"\n")
    io.open(os.path.join(BK, u"_zf153_mine.txt"), "w", encoding="utf-8", newline=u"\n").write(
        u"我自己在建备份之前就建的**只读侦察脚本**（不改任何产物）：\n"
        + u"\n".join(u"%s  %s" % (sha1(os.path.join(ROOT, rel)), rel) for rel in MINE) + u"\n")
    io.open(os.path.join(BK, u"_sha1.txt"), "w", encoding="utf-8", newline=u"\n").write(
        u"\n".join(lines) + u"\n")
    io.open(os.path.join(BK, u"_说明.txt"), "w", encoding="utf-8", newline=u"\n").write(
        u"ZF153 改前件：**振金剑**（无法破坏 / 手持免疫凋零+缓慢+挖掘疲劳 / 24 伤害 / 1.4 攻速 /\n"
        u"附魔权重 1 / Shift+右键猛击地面：6x6 内除自己全部击飞 + n+12 伤害 + 失明 4s + 缓慢 4s /\n"
        u"冷却 6s）。\n"
        u"备份脚本：build/zftools/_zf153_pre.py\n"
        u"⚠ 本轮开工时另一条线（ZF151/152）的探针正挂在 PotatoST.java 上 ⇒ 这里的 PotatoST.java\n"
        u"   是**带他们探针那一版**；我的挂载只碰自己那两行。\n"
        u"⚠ 语言键数一变，45 份写死键数的常驻校验要一起重定靶（照 ZF150 的 retarget 做法）。\n")
    print(u"\n".join(u"  [OK] " + n for n in notes))
    print(u"改前件 %d 份 → %s" % (ok, BK))
    print(u"失败项 = %d" % len(fails))
    for f in fails:
        print(u"  !! " + f)
    return 1 if fails else 0


if __name__ == u"__main__":
    sys.exit(main())
