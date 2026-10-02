# -*- coding: utf-8 -*-
u"""_zf155_commit.py —— ZF155 提交（**只 add 我自己的路径**，绝不 `git add -A`）。

三道自检：
  ① 被我跟平的那批门：`git diff -U0` 里**每一处改动都必须只是 587→594 / 589→596**，
     别的门文件我不碰（防"手滑顺手 reformat 了别人的门"）；
  ② 待提交清单逐条打印（人可核对）；
  ③ 提交前重跑 `_zf155_verify.py`，必须全绿。

跑法：python build\\zftools\\_zf155_commit.py [--write]
"""
import io
import os
import re
import subprocess
import sys

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

ROOT = r"E:\PotatoST"
GIT = r"C:\Program Files\Git\cmd\git.exe"
ZT = os.path.join(ROOT, "build", "zftools")
MSG = os.path.join(ZT, u"_zf155_commit_msg.txt")

MINE = [
    # 源码
    u"src/main/java/com/potatost/mod/ModItems.java",
    u"src/main/java/com/potatost/mod/UniversalUpgradeTemplate.java",
    # 资源
    u"src/main/resources/assets/potato_s_t/lang/zh_cn.json",
    u"src/main/resources/assets/potato_s_t/lang/en_us.json",
    u"src/main/resources/assets/potato_s_t/lang/ja_jp.json",
    u"src/main/resources/assets/potato_s_t/lang/ru_ru.json",
    u"src/main/resources/assets/potato_s_t/lang/lzh.json",
    u"src/main/resources/assets/potato_s_t/models/item/universal_upgrade_template.json",
    u"src/main/resources/assets/potato_s_t/textures/item/universal_upgrade_template.png",
    u"src/main/resources/data/potato_s_t/recipe/universal_upgrade_template.json",
    u"src/main/resources/data/potato_s_t/recipe/vibranium_sword_smithing.json",
    u"src/main/resources/data/potato_s_t/recipe/vibranium_helmet_smithing.json",
    u"src/main/resources/data/potato_s_t/recipe/vibranium_chestplate_smithing.json",
    u"src/main/resources/data/potato_s_t/recipe/vibranium_leggings_smithing.json",
    u"src/main/resources/data/potato_s_t/recipe/vibranium_boots_smithing.json",
    # 文档
    u"docs/开发档案.md",
    u"docs/多会话协作交接.md",
    u"docs/UpdateAnnouncement_EN.md",
    # 本轮脚本与产物
    u"build/zftools/_zf155_assets.py",
    u"build/zftools/_zf155_pre.py",
    u"build/zftools/_zf155_recon.py",
    u"build/zftools/_zf155_recon.txt",
    u"build/zftools/_zf155_recon2.py",
    u"build/zftools/_zf155_recon2.txt",
    u"build/zftools/_zf155_recon3.py",
    u"build/zftools/_zf155_recon3.txt",
    u"build/zftools/_zf155_preview.py",
    u"build/zftools/_zf155_preview.png",
    u"build/zftools/_zf155_probe_mount.py",
    u"build/zftools/_zf155_unprobe.py",
    u"build/zftools/_zf155_probe_utf8.txt",
    u"build/zftools/_zf155_probe.log",
    u"build/zftools/_zf155_verify.py",
    u"build/zftools/_zf155_falsify.py",
    u"build/zftools/_zf155_falsify_probe.py",
    u"build/zftools/_zf155_falsify_probe.log",
    u"build/zftools/_zf155_docs.py",
    u"build/zftools/_zf155_retarget.py",
    u"build/zftools/_zf155_retarget2.py",
    u"build/zftools/_zf155_retarget2_scan.py",
    u"build/zftools/_zf155_docs2.py",
    u"build/zftools/_zf155_docs3.py",
    u"build/zftools/_zf155_pkg.py",
    u"build/zftools/_zf155_fixhand.py",
    u"build/zftools/_zf155_annjar.py",
    u"build/zftools/_zf155_gatelist.py",
    u"build/zftools/_zf155_countpeek.py",
    u"build/zftools/_zf155_countpeek2.py",
    u"build/zftools/_zf155_peek3.py",
    u"build/zftools/_zf155_status.py",
    u"build/zftools/_zf155_mkgatesnap.py",
    u"build/zftools/_zf155_gatesnap.py",
    u"build/zftools/_zf155_gatesnap.txt",
    u"build/zftools/check/Zf155Check.java",
    # 成品靶子（打包轮必须跟平：里面同时有 ZF153 那条线**尚未提交**的同批数字改动）
    u"build/zftools/_zf149_jar.py",
    u"build/zftools/_zf149_verify.py",
]
# 被我跟平（写死旧键数）的那批门 —— 由 _zf155_retarget.py 现场产出，这里按盘上实况取
RETARGET_MARK = u"_zf155_retarget.py"


def git(*args, **kw):
    r = subprocess.run([GIT, u"-c", u"core.quotepath=false"] + list(args), cwd=ROOT,
                       stdout=subprocess.PIPE, stderr=subprocess.STDOUT, **kw)
    return r.returncode, r.stdout.decode("utf-8", "replace")


def retargeted_gates():
    """被本轮 retarget 改过的门 = git 里改了、且 diff **只含** 587→594 / 589→596 的那些。

    ⚠ 多线共树：`build/zftools` 下还有别人**在途未提交**的改动（本轮实测：
      `_zf141_recon.py` 的模块级文件句柄、`_zf45_recipes.py` 的 ZF144 无序配方表）。
      这些**不许顺手带上车** —— 所以判据是「自动带上的门，diff 必须只是键数」；
      我自己在 MINE 里点名的文件不受这条限制（它们本来就是我的活）。
    """
    rc, out = git(u"diff", u"--name-only")
    cand = [l.strip() for l in out.split(u"\n")
            if l.strip().startswith(u"build/zftools/_zf") and l.strip().endswith(u".py")]
    good, bad, foreign = [], [], []
    for p in cand:
        rc, d = git(u"diff", u"-U0", u"--", p)
        added = [l for l in d.split(u"\n") if l.startswith(u"+") and not l.startswith(u"+++")]
        removed = [l for l in d.split(u"\n") if l.startswith(u"-") and not l.startswith(u"---")]
        ok = bool(added) and all((u"594" in a or u"596" in a) for a in added) \
            and all((u"587" in r or u"589" in r) for r in removed)
        if p in MINE:
            good.append(p) if ok else foreign.append((p, added[:1], removed[:1]))
        elif ok:
            good.append(p)
        else:
            bad.append((p, added[:1], removed[:1]))
    return good, bad, foreign


def main(argv):
    write = u"--write" in argv

    print(u"① 跟平门的 diff 体检")
    good, bad, foreign = retargeted_gates()
    print(u"   自动带上车的门 %d 份（diff 只含键数）；**别人的在途改动（不带）** %d 份；"
          u"我自己的门（diff 不止键数，正常）%d 份" % (len(good), len(bad), len(foreign)))
    for p, a, r in bad:
        print(u"   -- 不带上车：%s\n       +%s\n       -%s" % (p, a, r))
    for p, a, r in foreign:
        print(u"   == 我的门：%s（另有非键数改动，见 MINE）" % p)

    files = list(MINE) + list(good)
    files = sorted(set(files))
    existing = [f for f in files if os.path.exists(os.path.join(ROOT, f))]
    missing = [f for f in files if f not in existing]
    print(u"\n② 待提交 %d 份（不存在 %d 份）" % (len(existing), len(missing)))
    for f in existing:
        print(u"     " + f)
    for f in missing:
        print(u"   !! 不在盘上：" + f)

    print(u"\n③ 提交前重跑 _zf155_verify.py")
    r = subprocess.run([sys.executable, os.path.join(ZT, u"_zf155_verify.py")], cwd=ROOT,
                       stdout=subprocess.PIPE, stderr=subprocess.STDOUT, timeout=600)
    out = r.stdout.decode("utf-8", "replace")
    tail = [l for l in out.split(u"\n") if u"====" in l]
    print(u"   rc=%d %s" % (r.returncode, tail[-1].strip() if tail else u""))
    green = r.returncode == 0

    if not write:
        print(u"\n（没加 --write：只算不写）")
        return 0 if (green and not missing) else 1
    if missing or not green:
        print(u"\n!! 自检没过，不提交")
        return 1

    rc, out = git(u"add", u"--", *existing)
    print(u"\n④ git add rc=%d" % rc)
    if out.strip():
        print(u"   " + out.strip()[:600])
    rc, out = git(u"status", u"--porcelain", u"--", *existing[:6])
    print(u"   抽看 6 份状态：%s" % out.strip().replace(u"\n", u" | ")[:300])
    rc, out = git(u"commit", u"-F", MSG)
    print(u"\n⑤ commit rc=%d\n%s" % (rc, out.strip()[:1500]))
    return 0 if rc == 0 else 1


if __name__ == u"__main__":
    sys.exit(main(sys.argv[1:]))
