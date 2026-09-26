# -*- coding: utf-8 -*-
u"""_zf140_commit.py —— ZF140 的提交（**只提交本轮自己的文件**）

⚠ 并发环境：盘上同时有别的线**未提交**的改动（`Zf141Check.java`、各 BlockEntity、lang、
`TextureCheck.py`…）。所以**不许 `git add -A`** —— 只提交下面这张点名清单。
清单里少一份 = 提交不完整；多一份 = 把别人的在途改动卷进来了。两个都要避免。

跑法：
    python build\\zftools\\_zf140_commit.py           # 只看（列出清单与状态）
    python build\\zftools\\_zf140_commit.py --write    # 真提交（不 push）
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

FILES = [
    # —— 代码（唯一一处） ——
    "src/main/java/com/potatost/mod/client/SkyboxRenderer.java",
    # —— 贴图 ——
    "src/main/resources/assets/potato_s_t/textures/skybox/black_hole.png",
    # —— 素材与凭据 ——
    "build/\u7528\u6237\u7d20\u6750/\u9ed1\u6d1e.jpg",
    "build/\u7528\u6237\u7d20\u6750/_\u6765\u6e90\u51ed\u636e.json",
    # —— 本轮的工具（全链） ——
    "build/zftools/_zf140_pre.py",
    "build/zftools/_zf140_jpeg_dump.ps1",
    "build/zftools/_zf140_intake.py",
    "build/zftools/_zf140_cutout.py",
    "build/zftools/_zf140_img.py",
    "build/zftools/_zf140_sim.py",
    "build/zftools/_zf140_cmp.py",
    "build/zftools/_zf140_mapping.py",
    "build/zftools/_zf140_java.py",
    "build/zftools/_zf140_java2.py",
    "build/zftools/_zf140_worldprobe.py",
    "build/zftools/_zf140_verify.py",
    "build/zftools/_zf140_falsify.py",
    "build/zftools/_zf140_gates.py",
    "build/zftools/_zf140_publish.py",
    "build/zftools/_zf140_docs.py",
    "build/zftools/_zf140_docs2.py",
    "build/zftools/_zf140_commit.py",
    # —— 证据（出图 + 门快照 + 自检日志） ——
    "build/zftools/_zf140_out/pole_check.png",
    "build/zftools/_zf140_out/cmp_theta_s0.png",
    "build/zftools/_zf140_out/cutout_check.png",
    "build/zftools/_zf140_out/black_hole.png",
    "build/zftools/_zf140_gates.txt",
    "build/zftools/_zf140_client.log",
    "build/zftools/_zf140_build.log",
    # —— 文档 ——
    "docs/\u5f00\u53d1\u6863\u6848.md",
    "docs/\u8d34\u56fe\u6e05\u5355.md",
    # —— 顺手修好的门（此前一直红着：语法错） ——
    "build/zftools/_zf133_docs.py",
    # —— 成品 ——
    "release/PotatoST-0.11.jar",
    "release/PotatoST-0.11.jar.sha1",
]

MSG = u"""0.11 ZF140：四张星图的极点补黑洞（盖片）

用户原话：「因为图片问题 天空盒一个点会看到明显的拉伸现象 解决不了 那正好在那个地方
（四张星图都需要）补个黑洞 图给你了 估计得抠一下 只剩黑洞本体 然后放到拉伸的地方」

- 病根：天空盒走等距圆柱投影，两极天生是塌的（贴图最上面一行要摊满 360° 方位角）
- 做法：南北极各一张「盖片」——独立 640x640 RGBA 贴图 + 自己的 16x16 网格，
  分辨率与 1024x512 的星图解耦；四张星图共用一张图；原版星空不受影响
- 几何：顶点摆在 theta = atan(|(a,b)| * tan(theta_max))（透视的逆）、UV 取 0.5+0.5(a,b)
  => 正对极点看过去就是原图（恒等误差 2.2e-16 / 分格误差 0.29 px / 与原图差 0.68/255）
- 抠图：背景 = 「亮度 <=20 且从四边连得出去」，剩下最大连通域即本体（自带填实：阴影留着）
- 开机自检：init() 里量真顶点数组并打进日志（max error 3.8e-8）
- 证据：常驻校验 54 项 0 失败；反证 K1~K13 十三把刀全咬住；九道门全绿；runClient 自检通过
- 顺带：修好 _zf133_docs.py 的语法错（ToolLint 门此前红着）
"""


def run(args, **kw):
    return subprocess.run([GIT, "-C", ROOT] + args, stdout=subprocess.PIPE,
                          stderr=subprocess.STDOUT, **kw).stdout.decode("utf-8", "replace")


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

    others = run(["status", "--porcelain"]).strip().split("\n")
    mine = set(FILES)
    theirs = [l for l in others if l.strip() and l[3:].replace("\\", "/").strip('"') not in mine]
    print(u"\n盘上**别的线**的在途改动 %d 条（本轮一律不碰）：" % len(theirs))
    for l in theirs[:12]:
        print(u"  " + l[:110])
    if len(theirs) > 12:
        print(u"  … 还有 %d 条" % (len(theirs) - 12))

    if missing:
        print(u"[STOP] 清单里有文件不存在 —— 先搞清楚再提交。")
        return 1
    if not write:
        print(u"\n--- 只体检（没提交）；加 --write 才真提交 ---")
        return 0

    # ⚠ 逐个 add，不用 -A：盘上还有别人的在途改动
    for f in FILES:
        out = run(["add", "--", f])
        if out.strip():
            print(u"  git add %s -> %s" % (f, out.strip()))
    msgfile = os.path.join(ROOT, "build", "zftools", "_zf140_commit_msg.txt")
    io.open(msgfile, "w", encoding="utf-8", newline="\n").write(MSG)
    out = run(["commit", "-F", msgfile])
    print(out)
    print(run(["log", "--oneline", "-1"]))
    print(run(["show", "--stat", "--oneline", "HEAD"]))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
