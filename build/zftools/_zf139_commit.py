# -*- coding: utf-8 -*-
u"""_zf139_commit.py —— ZF139 的提交（**只 add 自己点名的路径**，§10.1）

⚠ 树是共享的：`git add -A` 会把别的线正在改的东西一起提交（本轮开工时亲眼见到
另一条线的 `8ed549a` 把我当时在飞的 `ModArmorMaterials.java` 与四份 lang 一起扫了进去）。
所以这里**逐个路径点名**，并且提交前把 `git status --porcelain` 里"我清单之外的改动"
打出来给人看（不改、不提交）。

跑法：
    python build\\zftools\\_zf139_commit.py            # 只演（打印要 add 的清单与状态）
    python build\\zftools\\_zf139_commit.py --go       # 真提交（不 push）
"""
import io
import os
import subprocess
import sys

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

GIT = r"C:\Program Files\Git\cmd\git.exe"
ROOT = r"E:\PotatoST"

MSG = u"""0.11 ZF139：振金套加强（护甲 24 / 常驻抗性 I / 免摔落 / 10% 反伤「踢到了铁板」）

用户原话：「振金套你看看能不能略微加强一下 现在地位太尴尬了 比星璨麻烦很多 却大大不如晚上的星璨
简直就是个白板」。先把两套的实吃伤害按原版公式（CombatRules.getDamageAfterAbsorb +
LivingEntity.getDamageAfterMagicAbsorb）逐格算出来：振金改前的 20 护甲 / 12 韧性就是下界合金那一行
（10 点伤害吃 2.80），而星璨钢白天吃 2.00、夜晚只吃 1.20 —— 用户说「白板」是事实。
追问一轮后用户拍板：「用乙吧 再加一个套装效果；10%概率返还100%的伤害给攻击者
如果攻击者被反伤而死 死亡提示为「攻击者」踢到了铁板」。

改四条（都在「穿满四件」那一档）：
  ① 护甲值 3/8/6/3 → 4/9/7/4（各 +1，满套 24；韧性 12 / 击退抗性 0.4 / 附魔权重 2 一个不动）
     ⇒ 6/10/20 三档恒 16%，稳压白天星璨；
  ② 满套常驻抗性提升 I（不挑昼夜与维度；挂 PlayerTickEvent.Post，与星璨钢那套同一个口子）；
  ③ 满套免疫摔落伤害（取消 LivingFallEvent ⇒ causeFallDamage 直接 return false，
     连摔落音效都不放；没有走「按 #is_fall 取消伤害」那条会留音效的路）；
  ④ 满套 10% 反伤：反的是**这一击的原始伤害**（getOriginalDamage，进护甲前），
     挂 LivingDamageEvent.Post（不是「伤害之前」那个事件 —— 那个比无敌帧判定更早，
     会在根本没掉血的那一下掷骰子）；排除名单三条：反伤本身（递归保护）/ 弹射物（已被整条免疫）/
     爆炸（已减半），外加「getNewDamage() <= 0（被盾牌或伤害吸收全吃掉）」不掷骰。

反伤用了**本工程第一个自定义伤害类型** `potato_s_t:vibranium_reflect`
（data/potato_s_t/damage_type/vibranium_reflect.json，照原版 thorns.json 的格式与键序）：
effects=thorns ⇒ 挨这一下的人听到的是「打铁板」那一声；message_id ⇒ 死亡文案键
death.attack.potato_s_t.vibranium_reflect，中文「%1$s踢到了铁板」，而 %1$s 按
DamageSource.getLocalizedDeathMessage 的规则是**受害者** = 先动手那位，名字天然对。

连锁面：四语言 482 → 483 键（+1：死亡文案）⇒ 28 份往轮门 + 英文公告跟平；
贴图 / 模型 / 配方 / 进度一行没动。

证据：
  · 真服务端探针 Zf139Check **52 项全绿**（含 2000 次真受击反伤 175 次 ≈ 8.75%、
    四条排除名单各 400 次全 0 且配「同口径普通攻击 400 次反了 36 次」的灵敏度对照、
    死亡那一刻的 CombatTracker 文案键、无敌帧那一下 incoming+1 / post+0 的架构证据）；
  · _zf139_verify.py **95 项 0 失败**；反证刀 **K227~K250（24 把）**全部咬住；
  · 全门快照见 _zf139_gatesnap.txt（与改前 _zf139_gatesnap_before.txt 逐条比）。

⚠ 本轮轮号改了两次（ZF136 → ZF138 → **ZF139**）：ZF136 被另一条线的档案行占了、
ZF137 是他们的提交、ZF138 是他们在用的文件名。第二次改号时我的改名脚本用了通配，
误伤了他们**已经在用**的 _zf138_*.py（覆盖成他们自己的 _zf136_*.py 旧稿）；
已逐个查过（138 全在号码位置、没有数据值被误伤）并**逐字节还原**成 _zf136_*，
救不回的那部分写在交接 §6 第 22 条请他们核对。这就是 §4.111 的重演，已立 §4.132。

⚠ 本提交**只含我点名的路径**：ModArmorMaterials.java 与四份 lang 的改动早前已被
另一条线的 8ed549a 扫进去了（不是我提交的），这里不再重复 add。
"""

# ---- 我自己的路径（逐个点名）----
PATHS = [
    u"src/main/java/com/potatost/mod/ModVibraniumSet.java",
    u"src/main/java/com/potatost/mod/ModArmorItems.java",
    u"src/main/resources/data/potato_s_t/damage_type/vibranium_reflect.json",
    u"build/zftools/check/Zf139Check.java",
    u"build/zftools/_zf104_gates.ps1",
    u"build/zftools/_zf104_gatecount.py",
    u"build/zftools/_zf120_verify.py",
    u"docs/开发档案.md",
    u"docs/多会话协作交接.md",
    u"docs/UpdateAnnouncement_EN.md",
    # 本轮自己写的脚本与产物
    u"build/zftools/_zf139_backup.py",
    u"build/zftools/_zf139_calc.py",
    u"build/zftools/_zf139_calc.txt",
    u"build/zftools/_zf139_falsify.py",
    u"build/zftools/_zf139_gatefix.py",
    u"build/zftools/_zf139_gatesnap.py",
    u"build/zftools/_zf139_gatesnap_before.txt",
    u"build/zftools/_zf139_gatesnap.txt",
    u"build/zftools/_zf139_lang.py",
    u"build/zftools/_zf139_langdump.py",
    u"build/zftools/_zf139_langdump.txt",
    u"build/zftools/_zf139_probe.log",
    u"build/zftools/_zf139_probe_utf8.txt",
    u"build/zftools/_zf139_rename.py",
    u"build/zftools/_zf139_rename_incident.py",
    u"build/zftools/_zf139_unprobe.py",
    u"build/zftools/_zf139_verify.py",
    u"build/zftools/_zf139_anchors.py",
    u"build/zftools/_zf139_anchors.txt",
    u"build/zftools/_zf139_docs.py",
    u"build/zftools/_zf139_commit.py",
    u"build/zftools/_zf139_commit_msg.txt",
]
# 键数跟平动到的那 28 份往轮门（gatefix 的清单）
RETARGET = [u"_zf71_verify.py", u"_zf73_verify.py", u"_zf75_verify.py", u"_zf78_verify.py",
            u"_zf79_verify.py", u"_zf80_verify.py", u"_zf81_verify.py", u"_zf82_verify.py",
            u"_zf93_verify.py", u"_zf96_verify.py", u"_zf97_verify.py", u"_zf98_verify.py",
            u"_zf100_verify.py", u"_zf101_verify.py", u"_zf102_verify.py", u"_zf103_verify.py",
            u"_zf107_verify.py", u"_zf109_verify.py", u"_zf111_verify.py", u"_zf112_verify.py",
            u"_zf114_verify.py", u"_zf117_verify.py", u"_zf118_verify.py", u"_zf122_verify.py",
            u"_zf125_verify.py", u"_zf126_verify.py", u"_zf127_verify.py", u"_zf128_verify.py"]


def git(*args, **kw):
    r = subprocess.run([GIT, u"-c", u"core.quotepath=false"] + list(args),
                       cwd=ROOT, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                       env=dict(os.environ, PYTHONIOENCODING=u"utf-8"))
    return r.returncode, r.stdout.decode("utf-8", "replace")


def main(argv):
    go = u"--go" in argv
    io.open(os.path.join(ROOT, u"build", u"zftools", u"_zf139_commit_msg.txt"),
            u"w", encoding=u"utf-8", newline=u"\n").write(MSG)

    rc, out = git(u"status", u"--porcelain")
    print(u"===== 当前工作树（前 40 行）=====")
    print(u"\n".join(out.split(u"\n")[:40]))

    todo = PATHS + [u"build/zftools/" + n for n in RETARGET]
    missing = [p for p in todo if not os.path.exists(os.path.join(ROOT, p.replace(u"/", os.sep)))]
    if missing:
        print(u"")
        print(u"⚠ 清单里这些路径不在盘上（会被 git add 报错）：")
        for m in missing:
            print(u"   " + m)

    if not go:
        print(u"")
        print(u"（没加 --go，只演。要 add 的路径 %d 条）" % len(todo))
        return 0

    rc, out = git(u"add", u"--", *todo)
    print(out.strip())
    if rc != 0:
        print(u"  !! git add 失败")
        return 1
    rc, out = git(u"commit", u"-F", os.path.join(u"build", u"zftools",
                                                 u"_zf139_commit_msg.txt"))
    print(out.strip())
    if rc != 0:
        print(u"  !! git commit 失败")
        return 1
    rc, out = git(u"log", u"--oneline", u"-3")
    print(u"---- 最近 3 笔 ----")
    print(out.strip())
    rc, out = git(u"status", u"--porcelain")
    n = len([l for l in out.split(u"\n") if l.strip()])
    print(u"---- 提交后工作树剩余条目：%d（别的线的改动，我没碰）----" % n)
    return 0


if __name__ == u"__main__":
    sys.exit(main(sys.argv[1:]))
