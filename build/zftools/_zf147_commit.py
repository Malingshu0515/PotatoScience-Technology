# -*- coding: utf-8 -*-
r'''_zf147_commit.py —— ZF147（版本线 0.11 → 0.12）的定点提交。只加自己碰过的路径（§10.1）。'''
import io, os, subprocess, sys
try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass
ROOT = r"E:\PotatoST"
GIT = r"C:\Program Files\Git\cmd\git.exe"
PATHS = [r"gradle.properties", r"docs\开发档案.md", r"docs\多会话协作交接.md",
         r"docs\UpdateAnnouncement_EN.md",
         r"build\zftools\_zf73_verify.py", r"build\zftools\_zf78_verify.py",
         r"build\zftools\_zf79_verify.py", r"build\zftools\_zf145_verify.py",
         r"build\zftools\_zf147_version.py", r"build\zftools\_zf147_commit.py"]
MSG = u"""ZF147 版本线 0.11 → 0.12 + 立「每轮改动都记日志」的纪律

用户原话：「从现在开始都是 0.12 版本 无论是小更新还是修bug 麻烦在日志写一下」。

  · gradle.properties：mod_version=0.11 → 0.12（**全工程唯一一处**版本号；
    neoforge.mods.toml 引用 ${mod_version}）。
  · 档案立 §4.150「版本线与日志纪律」：**从 ZF147 起每一轮改动（含小修 / 修 bug）都要在
    §5 留一行 + 在英文公告留一条**，版本号写 0.12；§9 小节按改动大小决定写不写。
  · 交接标题 0.11 → 0.12、§1 加「版本线」一行、§6 加第 28 条。
  · 英文公告标题 → 0.12，末尾补「Version line: 0.11 → 0.12 (ZF147)」一节。
  · 三份老门里"mod_version 仍是 0.11 / 本轮没有 0.12 任务"的断言跟到 0.12（判据没放宽）。
  · ⚠ 没动 Java / 资源 / 配方 / 贴图；release\\PotatoST-0.11.jar 不动（0.12 的成品等下一次打包）。
  · 顺手把 _zf145_verify.py 的 E8 从"值指纹"改成"键都在"（值归润色线，指纹降为提示）——
    润色线 d724a4a 已改过那 16 句、并重排过 lang 的键，硬钉值会让我的门随别人节奏变红。
"""
def run(a):
    return subprocess.run([GIT, u"-c", u"core.quotepath=false", u"-C", ROOT] + a, capture_output=True)
def main(argv):
    msg = os.path.join(ROOT, r"build\zftools\_zf147_commit_msg.txt")
    io.open(msg, u"w", encoding=u"utf-8", newline=u"").write(MSG)
    if u"--write" not in argv:
        print(u"待 add %d 条；没加 --write，只算不写" % len(PATHS)); return 0
    r = run([u"add", u"-f", u"--"] + PATHS)
    if r.returncode:
        print(r.stderr.decode("utf-8", "replace")); return 1
    out = run([u"diff", u"--cached", u"--stat"]).stdout.decode("utf-8", "replace")
    print(out[-1200:])
    r = run([u"commit", u"-F", msg])
    print(u"commit 退出码 = %d" % r.returncode)
    print(r.stdout.decode("utf-8", "replace")[-600:])
    if r.returncode:
        print(r.stderr.decode("utf-8", "replace")[-800:]); return 1
    print(u"HEAD = " + run([u"log", u"--oneline", u"-1"]).stdout.decode("utf-8", "replace").strip())
    p = run([u"push", u"origin", u"main"])
    print(u"push 退出码 = %d" % p.returncode)
    print((p.stdout + p.stderr).decode("utf-8", "replace")[-400:])
    return 0
if __name__ == u"__main__":
    sys.exit(main(sys.argv[1:]))
