# -*- coding: utf-8 -*-
r'''_zf141_commit.py —— ZF141 的提交（**只 add 自己点名的路径**，别人的东西一个都不碰）

本工程的规矩（§4.7 / §7）：树是**多条线共用**的，`git add -A` 会把别人没写完的东西一起提交。
⇒ 这里把"我这一轮碰过的路径"逐个列出来，add 完把 `git status` 剩下的原样打印出来给人看。

跑法：
    python build\zftools\_zf141_commit.py            # 只 add + 打印，不提交
    python build\zftools\_zf141_commit.py --commit   # add + commit
    python build\zftools\_zf141_commit.py --commit --push
'''
import io
import os
import subprocess
import sys

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

ROOT = r"E:\PotatoST"
GIT = r"C:\Program Files\Git\cmd\git.exe"
MSG_FILE = os.path.join(ROOT, r"build\zftools\_zf141_commit_msg.txt")

MINE = [
    # ---- 代码（4 个新类 + 两个改过的注册/档位文件）----
    r"src\main\java\com\potatost\mod\StarSteelTools.java",
    r"src\main\java\com\potatost\mod\StarSteelSwordItem.java",
    r"src\main\java\com\potatost\mod\StarSteelPickaxeItem.java",
    r"src\main\java\com\potatost\mod\StarSteelHoeItem.java",
    r"src\main\java\com\potatost\mod\ModTiers.java",
    r"src\main\java\com\potatost\mod\ModItems.java",
    # ---- 资源（4 贴图 / 3 模型 / 3 配方 / 4 语言）----
    r"src\main\resources\assets\potato_s_t\textures\item\star_steel_sword.png",
    r"src\main\resources\assets\potato_s_t\textures\item\star_steel_pickaxe.png",
    r"src\main\resources\assets\potato_s_t\textures\item\star_steel_hoe.png",
    r"src\main\resources\assets\potato_s_t\textures\item\star_steel_axe.png",
    r"src\main\resources\assets\potato_s_t\models\item\star_steel_sword.json",
    r"src\main\resources\assets\potato_s_t\models\item\star_steel_pickaxe.json",
    r"src\main\resources\assets\potato_s_t\models\item\star_steel_hoe.json",
    r"src\main\resources\data\potato_s_t\recipe\star_steel_sword.json",
    r"src\main\resources\data\potato_s_t\recipe\star_steel_pickaxe.json",
    r"src\main\resources\data\potato_s_t\recipe\star_steel_hoe.json",
    r"src\main\resources\assets\potato_s_t\lang\zh_cn.json",
    r"src\main\resources\assets\potato_s_t\lang\en_us.json",
    r"src\main\resources\assets\potato_s_t\lang\ja_jp.json",
    r"src\main\resources\assets\potato_s_t\lang\ru_ru.json",
    # ---- 文档 ----
    r"docs\开发档案.md",
    r"docs\多会话协作交接.md",
    r"docs\UpdateAnnouncement_EN.md",
    r"docs\贴图清单.md",
    r"build\用户素材\_来源凭据.json",
    # ---- 工具：探针归档 + 本轮脚本 + 门清单 ----
    r"build\zftools\check\Zf141Check.java",
    r"build\zftools\_zf104_gates.ps1",
    r"build\zftools\_zf104_gatecount.py",
    # ---- 被 `_zf141_gatefix.py` 跟平过键数（483→487）的 31 份常驻门 ----
    # ⚠ 这里**逐份点名**，不用"扫目录通配"——§4.132 那条（改名脚本扫通配误伤别人）的同源教训。
    r"build\zftools\_zf71_verify.py",
    r"build\zftools\_zf73_verify.py",
    r"build\zftools\_zf75_verify.py",
    r"build\zftools\_zf78_verify.py",
    r"build\zftools\_zf79_verify.py",
    r"build\zftools\_zf80_verify.py",
    r"build\zftools\_zf81_verify.py",
    r"build\zftools\_zf82_verify.py",
    r"build\zftools\_zf93_verify.py",
    r"build\zftools\_zf96_verify.py",
    r"build\zftools\_zf97_verify.py",
    r"build\zftools\_zf98_verify.py",
    r"build\zftools\_zf100_verify.py",
    r"build\zftools\_zf101_verify.py",
    r"build\zftools\_zf102_verify.py",
    r"build\zftools\_zf103_verify.py",
    r"build\zftools\_zf107_verify.py",
    r"build\zftools\_zf109_verify.py",
    r"build\zftools\_zf111_verify.py",
    r"build\zftools\_zf112_verify.py",
    r"build\zftools\_zf114_verify.py",
    r"build\zftools\_zf117_verify.py",
    r"build\zftools\_zf118_verify.py",
    r"build\zftools\_zf119_verify.py",
    r"build\zftools\_zf122_verify.py",
    r"build\zftools\_zf125_verify.py",
    r"build\zftools\_zf126_verify.py",
    r"build\zftools\_zf127_verify.py",
    r"build\zftools\_zf128_verify.py",
    r"build\zftools\_zf133_verify.py",
    r"build\zftools\_zf139_verify.py",
    # ⚠ C 段（配方数 + 成品键数）还改了两份，别漏
    r"build\zftools\_zf100_recipe_guard.py",
    r"build\zftools\_zf134_verify.py",
    # ---- 本轮自己的脚本与产物 ----
    r"build\zftools\_zf141_recon.py",
    r"build\zftools\_zf141_recon.txt",
    r"build\zftools\_zf141_mineblock.py",
    r"build\zftools\_zf141_ctor.py",
    r"build\zftools\_zf141_ctor.txt",
    r"build\zftools\_zf141_posthurt.py",
    r"build\zftools\_zf141_api.py",
    r"build\zftools\_zf141_api2.py",
    r"build\zftools\_zf141_backup.py",
    r"build\zftools\_zf141_tex.py",
    r"build\zftools\_zf141_lang.py",
    r"build\zftools\_zf141_gatefix.py",
    r"build\zftools\_zf141_docs.py",
    r"build\zftools\_zf141_verify.py",
    r"build\zftools\_zf141_falsify.py",
    r"build\zftools\_zf141_unprobe.py",
    r"build\zftools\_zf141_commit.py",
    r"build\zftools\_zf141_commit_msg.txt",
    r"build\zftools\_zf141_gatesnap.py",
    r"build\zftools\_zf141_gatesnap.txt",
    r"build\zftools\_zf141_probe.log",
    r"build\zftools\_zf141_probe_utf8.txt",
]

MSG = u"""0.11 ZF141：星璨钢工具补齐（剑 16 / 镐 13 / 锄 12 + 夜晚不磨损 + 原版图纸配方 + 斧子换贴图）

用户原话：「还有几个星璨钢的工具你自己写一下呗（耐久 挖掘等级 技能...）剑和斧子差不多强度
其他的略低（要不要技能都无所谓）你参考一下斧子和星璨钢套 你随便搞 配方就是原版工具一样
（原材料换成星璨钢）」+「贴图在用户素材 刚才忘说了」。

① 剑 / 镐 / 锄与斧子**共用同一档位**（1192 耐久 / 速度 9.0 / 加成 8.0 / 钻石级 / 附魔 22），
   伤害剑 16.0、镐 13.0、锄 12.0（斧子 17.0 一个字没动）；技能「与夜同频」=
   夜晚采掘与攻击都不磨损（判据转调斧子的 isNight，不复制第二份）。
② 1.21.1 的 mineBlock 写在 Item 上、读 DataComponents.TOOL（剑的 damagePerBlock 是 2）
   ⇒ 白天走 super.mineBlock，没有照抄斧子那三行硬编码 hurtAndBreak(1)（§4.139）。
③ 锄的攻速有意取 1.0 次/秒（原版那套刻度配上 +8 的档位加成会得到 24 DPS 的最强武器）。
④ 配方 = 原版图纸只换材料（探针在真合成网格里摆了一遍，并用「同图纸换钻石出原版工具」做正对照）。
⑤ 斧子贴图换成用户新给的图；顺手修好 _zf133_verify.py 里那条已经静默跳过的贴图判据（§4.144）。
⑥ 四语言 483 → 487 键，32 份门跟平；新增 §4.139~§4.145 七条雷区。

证据：探针 70 项全绿 / _zf141_verify.py 99 项 0 失败 / 反证刀 K251~K275 二十五把全咬住。

⚠ **如实记两笔**（共树带来的，不是本轮的改动）：
① 四份 lang 的 diff 里**带着另一条线在途的改动**：整份从 4 空格缩进重排成 2 空格，
   外加 4 条套装/死亡说明的**新文案**（`star_steel_set` / `vibranium_set` /
   `titanium_alloy_set` / `death.attack.potato_s_t.vibranium_reflect`）。本轮**必须**动这四个文件
   （要加 4 个键），所以只能连它们一起带上 —— 按实测：新增 4 键、丢失 0 键、改值恰好那 4 条。
   （同一棵树上前例：8ed549a 那次也是把我在途的 lang 改动一起扫进去的。）
② `build/用户素材/` 里 17 个文件在工作区被删（`git status` 是 `D`），**不是本轮删的**；
   它让 `_zf79/_zf92/_zf93/_zf119` 四道门由绿转红（根因同一个），已记进交接 §6 第 23 条 ⑧。
   另：`release\PotatoST-0.11.jar` 在收尾时已被**别的线重新打包**（SHA1 303c5d46… → 276e9eff…），
   那份成品里 zh_cn 是 487 键 ⇒ `_zf93_verify.py` 的 `RELEASE_KEYS` 已跟到 487。
"""


def run(args, check=True):
    r = subprocess.run([GIT, u"-c", u"core.quotepath=false"] + args,
                       cwd=ROOT, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    out = r.stdout.decode("utf-8", "replace")
    if check and r.returncode != 0:
        print(out)
        raise SystemExit(u"git %s 失败（%d）" % (u" ".join(args), r.returncode))
    return out


def main(argv):
    # ⚠ 这里**不再**用 `git status` 现问"哪些 `_zf*_verify.py` 被改过"——那种"扫一遍"
    #   会把别人在途的改动一起 add 进来（§4.132：改名脚本扫通配误伤别人的同源教训）。
    #   名单逐份写在 MINE 里。
    mine = sorted(set(MINE))
    miss = []
    for p in mine:
        if not os.path.exists(os.path.join(ROOT, p)):
            miss.append(p)
            continue
        run([u"add", u"--", p])
        print(u"  + %s" % p)
    if miss:
        print(u"  ⚠ 盘上不存在的路径（已跳过）：%s" % miss)

    print(u"")
    print(u"==== 暂存区里有什么（git diff --cached --stat 的尾部）====")
    print(run([u"diff", u"--cached", u"--stat"]).strip()[-1500:])

    print(u"")
    print(u"==== 没被 add 的（**别人的东西，原样不动**）====")
    left = run([u"status", u"--porcelain"]).split(u"\n")
    staged = set(p for p in mine)
    others = []
    for line in left:
        if not line.strip():
            continue
        code, path = line[:2], line[3:].strip()
        if code.strip() in (u"M", u"D", u"??", u"MM", u"A"):
            if path.replace(u"/", os.sep) not in staged:
                others.append(line)
    print(u"\n".join(others[:40]))
    print(u"  …… 共 %d 条（不属本轮，留给你/别的线）" % len(others))

    if u"--commit" in argv:
        io.open(MSG_FILE, u"w", encoding=u"utf-8", newline=u"\n").write(MSG)
        print(u"")
        print(run([u"commit", u"-F", MSG_FILE]))
        print(run([u"log", u"--oneline", u"-1"]).strip())
    if u"--push" in argv:
        print(run([u"push", u"origin", u"HEAD"]))
        print(run([u"log", u"--oneline", u"-1", u"origin/main"]).strip())
    return 0


if __name__ == u"__main__":
    sys.exit(main(sys.argv[1:]))
