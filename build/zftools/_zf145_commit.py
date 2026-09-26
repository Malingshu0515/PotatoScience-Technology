# -*- coding: utf-8 -*-
r'''_zf145_commit.py —— 只提交**本轮自己碰过的路径**（§10.1：绝不 `git add -A`）

本轮碰过的：
  · 8 个新进度 JSON + 1 个伤害类型标签（新建）
  · 四份 lang
  · 三份文档
  · 30 + 5 份常驻门（`_zf*_verify.py`，都是"跟平活体数字"，逐份记在 `_zf145_gatefix.py`）
  · `build\zftools\_zf145_*` 与归档探针 `check\Zf145Check.java`

⚠ 同一棵树上有别的会话**正在改**的东西（`TextureCheck.py` / `_zf141_recon.*` / `ModSounds.java` /
  `build\用户素材\` 的 17 个删除 …）—— 一律不碰。

跑法：python build\zftools\_zf145_commit.py [--write]
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

PATHS = [
    # ---- 新建的数据 ----
    r"src\main\resources\data\potato_s_t\advancement\vibranium.json",
    r"src\main\resources\data\potato_s_t\advancement\vibranium_armor.json",
    r"src\main\resources\data\potato_s_t\advancement\titanium_armor.json",
    r"src\main\resources\data\potato_s_t\advancement\star_steel_tools.json",
    r"src\main\resources\data\potato_s_t\advancement\star_steel_slash.json",
    r"src\main\resources\data\potato_s_t\advancement\star_chart_tome.json",
    r"src\main\resources\data\potato_s_t\advancement\diesel_generator.json",
    r"src\main\resources\data\potato_s_t\advancement\silver_wire.json",
    r"src\main\resources\data\potato_s_t\tags\damage_type\star_steel_slash.json",
    # ---- 语言 ----
    r"src\main\resources\assets\potato_s_t\lang\zh_cn.json",
    r"src\main\resources\assets\potato_s_t\lang\en_us.json",
    r"src\main\resources\assets\potato_s_t\lang\ja_jp.json",
    r"src\main\resources\assets\potato_s_t\lang\ru_ru.json",
    # ---- 文档 ----
    r"docs\开发档案.md",
    r"docs\多会话协作交接.md",
    r"docs\UpdateAnnouncement_EN.md",
    # ---- 跟平的常驻门（`_zf145_gatefix.py` 逐份记了命中次数）----
    r"build\zftools\_zf71_verify.py", r"build\zftools\_zf73_verify.py",
    r"build\zftools\_zf75_verify.py", r"build\zftools\_zf78_verify.py",
    r"build\zftools\_zf79_verify.py", r"build\zftools\_zf80_verify.py",
    r"build\zftools\_zf81_verify.py", r"build\zftools\_zf82_verify.py",
    r"build\zftools\_zf93_verify.py", r"build\zftools\_zf96_verify.py",
    r"build\zftools\_zf97_verify.py", r"build\zftools\_zf98_verify.py",
    r"build\zftools\_zf100_verify.py", r"build\zftools\_zf101_verify.py",
    r"build\zftools\_zf102_verify.py", r"build\zftools\_zf103_verify.py",
    r"build\zftools\_zf107_verify.py", r"build\zftools\_zf109_verify.py",
    r"build\zftools\_zf111_verify.py", r"build\zftools\_zf112_verify.py",
    r"build\zftools\_zf114_verify.py", r"build\zftools\_zf117_verify.py",
    r"build\zftools\_zf118_verify.py", r"build\zftools\_zf119_verify.py",
    r"build\zftools\_zf122_verify.py", r"build\zftools\_zf125_verify.py",
    r"build\zftools\_zf126_verify.py", r"build\zftools\_zf127_verify.py",
    r"build\zftools\_zf128_verify.py", r"build\zftools\_zf139_verify.py",
    r"build\zftools\_zf141_verify.py",
    # ---- 本轮的工具与产物 ----
    r"build\zftools\_zf145_pre.py", r"build\zftools\_zf145_recon.py",
    r"build\zftools\_zf145_recon.txt", r"build\zftools\_zf145_recon2.py",
    r"build\zftools\_zf145_recon2.txt", r"build\zftools\_zf145_recon3.py",
    r"build\zftools\_zf145_recon3.txt", r"build\zftools\_zf145_recon4.py",
    r"build\zftools\_zf145_recon4.txt", r"build\zftools\_zf145_recon5.py",
    r"build\zftools\_zf145_recon5.txt", r"build\zftools\_zf145_recon6.py",
    r"build\zftools\_zf145_recon6.txt", r"build\zftools\_zf145_recon7.py",
    r"build\zftools\_zf145_recon7.txt", r"build\zftools\_zf145_recon8.py",
    r"build\zftools\_zf145_recon8.txt", r"build\zftools\_zf145_recon9.py",
    r"build\zftools\_zf145_recon9.txt", r"build\zftools\_zf145_recon10.py",
    r"build\zftools\_zf145_apply.py", r"build\zftools\_zf145_lang.py",
    r"build\zftools\_zf145_gatefix.py", r"build\zftools\_zf145_verify.py",
    r"build\zftools\_zf145_falsify.py", r"build\zftools\_zf145_docs.py",
    r"build\zftools\_zf145_probe_mount.py", r"build\zftools\_zf145_unprobe.py",
    r"build\zftools\_zf145_oldsha.py", r"build\zftools\_zf145_oldsha.txt",
    r"build\zftools\_zf145_oldsha_ins.py", r"build\zftools\_zf145_newsha.py",
    r"build\zftools\_zf145_lines492.py", r"build\zftools\_zf145_lines492.txt",
    r"build\zftools\_zf145_peek.py", r"build\zftools\_zf145_grab.py",
    r"build\zftools\_zf145_fmt.py", r"build\zftools\_zf145_nl.py",
    r"build\zftools\_zf145_probe.log", r"build\zftools\_zf145_probe_utf8.txt",
    r"build\zftools\_zf145_commit.py", r"build\zftools\_zf145_commit_msg.txt",
    r"build\zftools\check\Zf145Check.java",
]

MSG = u"""ZF145 成就树补线：8 条新进度 + 星辉斩的伤害类型标签（四语言 492 → 508 键）

用户原话：「是时候更新一下成就啦宝宝」。

ZF117 那条线把树补到 35 条之后，新加的内容一条进度都没有（振金、星仪图之章、
大型柴油发电机、银线、星璨钢五件工具、剑的星辉斩）。本轮补 8 条，老节点的字节一个没动：

  vibranium        炼出振金（goal，挂 star_steel）
  vibranium_armor  振金套装（challenge，四件各占一个组 = 真「与」）
  titanium_armor   钛合金套装（goal，一条老空洞）
  star_steel_tools 星璨钢工具五件（goal，五条判据塞进同一个组 = 真「或」）
  star_steel_slash 星辉斩（challenge，**击杀型**：player_killed_entity + 伤害类型标签）
  star_chart_tome  星仪图之章（task，挂根）
  diesel_generator 大型柴油发电机（goal，挂 stronger_power）
  silver_wire      银线（task，挂 wiring）

星辉斩是**本工程第一条不判物品**的进度：killing_blow 只能按标签筛伤害类型
（DamageSourcePredicate.CODEC 的 tags），所以新增 tags/damage_type/star_steel_slash.json，
标签名与 ZF144 那个伤害类型同名（不同注册表，原版 is_projectile 同款做法）。

活体数字：四语言 492 → 508 键、进度 35 → 43 条；Java / 配方 / 贴图一行没动。
本轮没打包 ⇒ RELEASE_KEYS 保持 487。

证据：
  · 真服务端探针 Zf145Check（已归档 check/）：111 项全绿 —— 含"先反后正"的击杀对照
    （原版 player_attack 打死僵尸 ⇒ 不亮；用星辉斩的伤害类型打死 ⇒ 才亮）、
    三套盔甲只给三件不许亮、只给一把锹就点亮工具那条。
  · 常驻校验 _zf145_verify.py 178 项 0 失败；反证刀 _zf145_falsify.py 20 刀 20 咬住、
    逐刀还原后基线回到原样。
  · 顺手收口三处本线老账：_zf139 的 damage_type 份数与键序链（ZF144 顶的）、
    _zf117 的 D5/G3 活体数字；并补掉 _zf107 的 mod_ids() 扫不到 registerVibranium 的盲区
    （ZF120 起埋着，ZF145 第一次点名振金甲时暴露）—— 立成档案 §4.148/§4.149。
"""


def run(args, **kw):
    return subprocess.run([GIT, u"-c", u"core.quotepath=false", u"-C", ROOT] + args,
                          capture_output=True, **kw)


def main(argv):
    write = u"--write" in argv
    msg_path = os.path.join(ROOT, r"build\zftools\_zf145_commit_msg.txt")
    io.open(msg_path, u"w", encoding=u"utf-8", newline=u"").write(MSG)

    missing = [p for p in PATHS if not os.path.exists(os.path.join(ROOT, p))]
    if missing:
        print(u"  [警告] 这些路径不在盘上（多半是没生成到的临时件）：")
        for m in missing:
            print(u"     " + m)
    add = [p for p in PATHS if os.path.exists(os.path.join(ROOT, p))]

    if not write:
        print(u"待 add：%d 条路径（用 -f，防 .gitignore 挡掉）" % len(add))
        print(u"（没加 --write，只算不写）")
        return 0

    r = run([u"add", u"-f", u"--"] + add)
    print(u"git add 退出码 = %d" % r.returncode)
    if r.returncode:
        print(r.stderr.decode("utf-8", "replace"))
        return 1
    r = run([u"status", u"--short"])
    out = r.stdout.decode("utf-8", "replace")
    staged = [l for l in out.split(u"\n") if l[:2].strip() and l[0] not in u" ?"]
    print(u"已暂存 %d 条（下面只列前 8 条与最后 3 条）：" % len(staged))
    for l in staged[:8]:
        print(u"  " + l)
    print(u"  …")
    for l in staged[-3:]:
        print(u"  " + l)

    r = run([u"commit", u"-F", msg_path])
    print(u"\ngit commit 退出码 = %d" % r.returncode)
    print(r.stdout.decode("utf-8", "replace")[-1500:])
    if r.returncode:
        print(r.stderr.decode("utf-8", "replace")[-1500:])
        return 1
    r = run([u"log", u"--oneline", u"-1"])
    print(u"HEAD = " + r.stdout.decode("utf-8", "replace").strip())
    r = run([u"status", u"--short", u"--branch"])
    print(r.stdout.decode("utf-8", "replace").split(u"\n")[0])
    return 0


if __name__ == u"__main__":
    sys.exit(main(sys.argv[1:]))
