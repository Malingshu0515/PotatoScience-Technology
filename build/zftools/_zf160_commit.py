# -*- coding: utf-8 -*-
u"""_zf160_commit.py —— ZF160 提交（**只提交自己点名的路径**，绝不 `git add -A`）。

跑法：python build\\zftools\\_zf160_commit.py [--write] [--push]
"""
import io
import os
import subprocess
import sys

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding=u"utf-8", errors="replace")

ROOT = r"E:\PotatoST"
ZT = os.path.join(ROOT, "build", "zftools")
MSG = os.path.join(ZT, u"_zf160_commit_msg.txt")

MINE = [
    r"src\main\resources\data\potato_s_t\worldgen\configured_feature\ore_silver.json",
    r"src\main\resources\data\potato_s_t\worldgen\placed_feature\ore_silver_placed.json",
    r"src\main\resources\data\potato_s_t\worldgen\placed_feature\ore_aluminum_placed.json",
    r"docs\开发档案.md",
    r"docs\多会话协作交接.md",
    r"docs\UpdateAnnouncement_EN.md",
    r"build\zftools\_zf149_jar.py",
    r"build\zftools\_zf149_verify.py",
    r"build\zftools\_zf156_jarcheck.py",
    r"build\zftools\_zf156_pkg.py",
    r"build\zftools\_zf160_pot_sha.txt",
    r"build\zftools\_zf160_probe_utf8.txt",
    r"build\zftools\_zf160_recon.txt",
    r"build\zftools\_zf160_gatesnap.txt",
    r"build\zftools\check\Zf160Check.java",
]

MSG_TEXT = u"""ZF160 0.13：银矿矿脉调大（size 3→10 / 次数 9→12）、铝的权重调小（12→10）（0.13）

用户原话：「银矿矿脉可以稍微调大一点 大概和铜差不多（或者生成权重大一点也可以）然后铝的权重调小1~2」。

① 取证（`_zf160_recon.txt`）：本模组 9 种矿里银是最小的（size 3；铝 11、锰 12、铀 10…），
   原版铜是小脉 size 10 / 每区块 16 次（另有 size 20 的大脉）。
② 只动三个数：银 size 3→10（对齐原版铜小脉）、银 count 9→12（用户说"或者生成权重大一点也可以"，
   顺手提一档，仍低于铜的 16）、铝 count 12→10（"调小 1~2"取了 2）。
   高度区间 / 步数 / targets / 其余 7 种矿一个没动。
③ 探针 `Zf160Check`（真开服、**注册表现查**）7 项 ALL OK：银 size/count、银 targets、
   铝 count 且 size 仍 11、九种矿逐条对上改后表、九条高度区间逐条没动、负对照。
   ⚠ 探针改为在 ServerStartedEvent **立即**验：另一条线的 Zf159Check 在启动期就 halt，
   "等 20 tick"的版本一个 tick 都等不到（§4.168①）。
   ⚠ 本轮**没有动 PotatoST.java**（汇合点被别人的探针占着）：探针自带 @EventBusSubscriber 自动注册，
   挂载=拷一个文件、卸载=删掉（§4.168②），卸载自检基准换成"挂载那一刻的 sha1 快照"。
④ 常驻 `_zf160_verify.py` 16 项 0 失败（含 A5"把新旧两份 JSON 里那三个数换成占位符后逐字相同"）。
⑤ 撞号：本轮取的 §4.167 与另一条线（ZF159）撞了 ⇒ 当场改成 §4.168（只改自己的三处引用）。
⑥ 重打成品：release\\PotatoST-0.13.jar = 5,886,943 字节 /
   sha1 b3688162332a3e5e8a65000d40b09e53f0e578e1。
   ⚠ 这一版还带上了另一条线**在途**的 3 份 generator_fuel 配方 + 1 个 class + 3 张 c:dusts 标签
   （class 360→365、配方 91→94）⇒ `_zf149_jar.py` / `_zf149_verify.py` / `_zf156_jarcheck.py` /
   英文公告 四处活体数字一起跟平（判据没放宽，只是跟到发布那一刻的实测值）。
⑦ 全门快照：绿 24 → 25（多的那条是本轮新门）、红 45 → 45（一条没多、一条没少）。
"""


def main(argv):
    write = u"--write" in argv
    push = u"--push" in argv
    paths = list(MINE)
    for fn in sorted(os.listdir(ZT)):
        if fn.startswith(u"_zf160_") and (fn.endswith(u".py") or fn.endswith(u".txt")):
            paths.append(os.path.join(r"build\zftools", fn))
    paths = sorted(set(paths))
    # ⚠ `git add` 只要有一个 pathspec 不存在就**整条命令失败**（一条都不会 add）——
    #   本轮就踩了：`_zf160_pot_sha.txt` 因为挂载脚本第二次走幂等分支没写出来 ⇒ 暂存区空 ⇒
    #   commit 报 "no changes added"。所以先过滤掉不存在的，并**打印出来**。
    missing = [p for p in paths if not os.path.exists(os.path.join(ROOT, p))]
    if missing:
        print(u"⚠ 清单里不存在、已跳过 %d 条：" % len(missing))
        for m in missing:
            print(u"   " + m)
    paths = [p for p in paths if p not in missing]
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
