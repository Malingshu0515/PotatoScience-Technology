# -*- coding: utf-8 -*-
u"""_zf158_commit.py —— ZF158 提交（**只提交自己点名的路径**，绝不 `git add -A`）。

跑法：python build\\zftools\\_zf158_commit.py [--write] [--push]
"""
import io
import os
import subprocess
import sys

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding=u"utf-8", errors="replace")

ROOT = r"E:\PotatoST"
ZT = os.path.join(ROOT, "build", "zftools")
MSG = os.path.join(ZT, u"_zf158_commit_msg.txt")

MINE = [
    r"src\main\resources\data\potato_s_t\recipe\thermal_metal.json",
    r"build\zftools\_zf45_recipes.py",
    r"docs\开发档案.md",
    r"docs\多会话协作交接.md",
    r"docs\UpdateAnnouncement_EN.md",
    r"build\zftools\_zf149_verify.py",
    r"build\zftools\_zf156_pkg.py",
    r"build\zftools\_zf158_gatesnap.txt",
    r"build\zftools\_zf158_recon.txt",
]

MSG_TEXT = u"""ZF158 0.13：热力金属换成「铜板夹银锭」+ 配方生成器表跟平两笔旧账（0.13）

用户原话：「热力金属改成铜板夹银锭（铜板银锭互相调换一下位置）」。

① 图纸：`SSS/CCC/SSS`（银在外）→ **`CCC/SSS/CCC`（铜在外）** = 铜板 ×6 + 银锭 ×3 → 热力金属 ×1。
   两个 key 一个字没改（`C` = `#c:plates/copper`、`S` = `#c:ingots/silver`）⇒ ZF156 的跨 mod 兼容不倒退。
② 照规矩**改生成器表再 `--write`**（`_zf45_recipes.py` 自称是那 35 份 JSON 的唯一来源），
   顺手跟平两笔"只改了盘、没改表"的旧账：
   · ZF156：表里 13 行 15 处 `("item", "potato_s_t:<金属>_plate")` → `("tag", "c:plates/<金属>")`；
   · ZF155：`SMITHING_TEMPLATE` 下界合金升级模板 → 通用升级模板。
   ⚠ 跟平前实测到出血：跑一次 `--write` 把 ZF155 的 4 份振金护甲模板**当场 revert**（已从 zf158_pre 逐字节还原）。
③ 验收：跟平后 `--write` 重出，**除 `thermal_metal.json` 一份不动**（拿改前备份整目录对账）= 表与盘的机器证明；
   `_zf45_recipes.py` 校验模式 47 条 0 失败；新常驻门 `_zf158_verify.py` **20 项 0 失败**，
   其中 B5 把"可复现"固化了：复制生成器 → 输出目录改到临时夹 → 重出 → 与盘逐字节比。
④ 重打成品：`release\\PotatoST-0.13.jar` = 5,881,011 字节 / sha1
   c7dcd4306a9b6ef25d8d54a61d77a1b36e6c9498；哈希三处联动已跟平。
   ⚠ 这一版**还带上了另一条线在途的贴图**（4 张钛合金护甲图 + 重画的热力金属图，未提交，账记在 §4.166⑤）。
⑤ 全门快照：绿 23 → 24（多的那条是本轮新门）、红 45 → 45（一条没多一条没少）。
"""


def main(argv):
    write = u"--write" in argv
    push = u"--push" in argv
    paths = list(MINE)
    for fn in sorted(os.listdir(ZT)):
        if fn.startswith(u"_zf158_") and (fn.endswith(u".py") or fn.endswith(u".txt")):
            paths.append(os.path.join(r"build\zftools", fn))
    paths = sorted(set(paths))
    print(u"要 add 的路径 %d 条：" % len(paths))
    for p in paths:
        print(u"   " + p)
    if not write:
        print(u"（没加 --write：只列清单）")
        return 0

    io.open(MSG, "w", encoding="utf-8", newline="\n").write(MSG_TEXT)
    r = subprocess.run(["git", "add", "--"] + paths, cwd=ROOT, stdout=subprocess.PIPE,
                       stderr=subprocess.STDOUT)
    print(r.stdout.decode("utf-8", "replace")[-400:])
    staged = [p for p in subprocess.run(["git", "diff", "--cached", "--name-only", "-z"],
                                        cwd=ROOT, stdout=subprocess.PIPE)
              .stdout.decode("utf-8", "replace").split(u"\0") if p]
    allowed = set(p.replace(u"\\", u"/") for p in paths)
    bad = [s for s in staged if s.replace(u"\\", u"/") not in allowed]
    if bad:
        print(u"!! 暂存区里有不在清单里的路径（停手）：")
        for b in bad[:20]:
            print(u"   " + b)
        return 2
    print(u"暂存区核对：%d 条，全部在清单里" % len(staged))
    r = subprocess.run(["git", "commit", "-F", MSG], cwd=ROOT, stdout=subprocess.PIPE,
                       stderr=subprocess.STDOUT)
    print(r.stdout.decode("utf-8", "replace")[-900:])
    if r.returncode != 0:
        return 1
    if push:
        for attempt in range(4):
            r = subprocess.run(["git", "push", "origin", "HEAD"], cwd=ROOT,
                               stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
            out = r.stdout.decode("utf-8", "replace")
            print(u"push 第 %d 次 rc=%d\n%s" % (attempt + 1, r.returncode, out[-300:]))
            if r.returncode == 0:
                break
        else:
            print(u"!! push 四次都没成")
            return 1
    return 0


if __name__ == u"__main__":
    sys.exit(main(sys.argv[1:]))
