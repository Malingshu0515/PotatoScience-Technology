# -*- coding: utf-8 -*-
u"""_zf142_commit.py —— ZF142 的提交（**只提交本轮自己的文件**）

⚠ 并发环境：盘上同时有别的线**未提交**的改动 ⇒ **不许 `git add -A`**，只提交下面这张点名清单。

跑法：python build\\zftools\\_zf142_commit.py [--write]
"""
import io
import os
import subprocess
import sys

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

ROOT = r"E:\PotatoST"
GIT = r"C:\Users\Administrator\AppData\Local\GitHubDesktop\app-3.6.5\resources\app\git\cmd\git.exe"
SKY = "src/main/resources/assets/potato_s_t/textures/skybox/"

FILES = [
    SKY + "sky_verdant.png",
    SKY + "sky_mystic.png",
    SKY + "sky_ember.png",
    SKY + "sky_tarantula.png",
    "build/zftools/_zf140_verify.py",      # B9 改写成「只动极带」
    "build/zftools/_zf140_sim.py",         # 缓存名带 sha1（改了图之后模拟器不再拿旧数据）
    "build/zftools/_zf140_img.py",
    "build/zftools/_zf142_pre.py",
    "build/zftools/_zf142_poleblur.py",
    "build/zftools/_zf142_look.py",
    "build/zftools/_zf142_probe.py",
    "build/zftools/_zf142_ingame.py",
    "build/zftools/_zf142_verify.py",
    "build/zftools/_zf142_falsify.py",
    "build/zftools/_zf142_gates.py",
    "build/zftools/_zf142_docs.py",
    "build/zftools/_zf142_quotefix.py",
    "build/zftools/_zf142_quotefind.py",
    "build/zftools/_zf142_commit.py",
    "build/zftools/_zf142_out/cmp_sky_mystic.png",
    "build/zftools/_zf142_out/ingame_sky_mystic.png",
    "build/zftools/_zf142_out/probe_sky_mystic.png",
    "build/zftools/_zf142_out/metric_before.txt",
    "build/zftools/_zf142_out/metric_after.txt",
    "build/zftools/_zf142_gates.txt",
    "build/zftools/_zf142_build.log",
    "docs/\u5f00\u53d1\u6863\u6848.md",
    "docs/\u8d34\u56fe\u6e05\u5355.md",
]

MSG = u"""0.11 ZF142：四张星图的极带加一点点横向模糊（极滤波）

用户原话（接在 ZF140 汇报里"条纹只是被盖住、没治好"那段之后）：「可以尝试加一点点模糊」

- 先判因：拿"沿 u 均匀糊 32 个纹素"做实验，细条纹只降 10% => 病根不是采样混叠，
  是星图自己的纤维被径向拉长；原本打算用的"物理律 0.22/tanθ"全图只改 1.0/255，等于没做
- 参数：y0=96 行（33.8°）、极点半径 r0=16 纹素、线性衰减到 0（四档里最轻的一档）
- 只动极带：调色板原样保留、带外 324 行索引逐字节不动，每张只改 186 行
- 疗效：极区细条纹 20.2/17.7/13.9/23.8 -> 15.4/14.2/5.5/19.0（降 24%/20%/60%/20%）
- 体积 1.29 MB -> 1.07 MB（成品 jar 也小 220 KB）
- 证据：_zf142_verify.py 33 项 0 失败、反证 K1~K5 五把刀全咬住、
  _zf140_verify.py 58 项 0 失败、九道门全绿
"""


def run(args):
    return subprocess.run([GIT, "-C", ROOT] + args, stdout=subprocess.PIPE,
                          stderr=subprocess.STDOUT).stdout.decode("utf-8", "replace")


def main(argv):
    write = "--write" in argv
    missing, dirty, clean = [], [], []
    for f in FILES:
        p = os.path.join(ROOT, f.replace("/", os.sep))
        if not os.path.exists(p):
            missing.append(f)
            continue
        st = run(["status", "--porcelain", "--", f]).strip()
        (dirty if st else clean).append((f, st))

    print(u"清单 %d 份：缺 %d / 有改动 %d / 无改动 %d"
          % (len(FILES), len(missing), len(dirty), len(clean)))
    for f in missing:
        print(u"  [缺] %s" % f)
    for f, st in dirty:
        print(u"  %s  %s" % (st[:2], f))
    for f, _ in clean:
        print(u"  [无改动] %s" % f)

    mine = set(FILES)
    others = [l for l in run(["status", "--porcelain"]).strip().split("\n")
              if l.strip() and l[3:].replace("\\", "/").strip('"') not in mine]
    print(u"\n盘上**别的线**的在途改动 %d 条（本轮一律不碰）：" % len(others))
    for l in others[:8]:
        print(u"  " + l[:105])

    if missing:
        print(u"[STOP] 清单里有文件不存在。")
        return 1
    if not write:
        print(u"\n--- 只体检（没提交）；加 --write 才真提交 ---")
        return 0
    for f in FILES:
        out = run(["add", "--", f])
        if out.strip():
            print(u"  git add %s -> %s" % (f, out.strip()))
    mf = os.path.join(ROOT, "build", "zftools", "_zf142_commit_msg.txt")
    io.open(mf, "w", encoding="utf-8", newline="\n").write(MSG)
    print(run(["commit", "-F", mf]))
    print(run(["log", "--oneline", "-1"]))
    print(run(["show", "--stat", "--oneline", "HEAD"])[-1200:])
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
