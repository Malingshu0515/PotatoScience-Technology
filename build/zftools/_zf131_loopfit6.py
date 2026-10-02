# -*- coding: utf-8 -*-
"""_zf131_loopfit6.py —— 判据修正：量**末块 → 首块**这一对（循环真正跨过的那一步）

第五版的判据写错了位置：它比的是「成品开头 0.4 s」与「紧随其后的 0.4 s」——
这两段都在**交叉淡化已经抹平过**的区域里，当然接近；于是它给
`0.511 / 10.390 / 1000ms` 打了高分，而那个成品的
**末块 0.100 → 首块 0.081（差 19.4%）**：每绕一圈音量先塌一下，可闻。

循环真正跨过的那一步是 **成品末尾 → 成品开头**。所以这一版直接量：

    wrap = |RMS(末 0.5 s) − RMS(首 0.5 s)| / 全段 RMS

外加两条：接缝样本差、开头是否明显低于全段均值（首块 vs 均值）。
三条一起评，仍然**真编码**、真回读。
"""
import os
import subprocess
import sys

import numpy as np
import soundfile as sf

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

ROOT = r"E:\PotatoST"
SRC = os.path.join(ROOT, "build", u"用户素材", u"柴油发电机工作.mp3")
MAKESFX = os.path.join(ROOT, "build", "zftools", "MakeSfx.py")
FINAL = os.path.join(ROOT, r"src\main\resources\assets\potato_s_t\sounds",
                     "diesel_generator_running.ogg")
TMP = os.path.join(ROOT, "build", "zftools", "_zf131_cand.ogg")
SR = 44100


def rms(x):
    return float(np.sqrt((np.asarray(x, dtype="float64") ** 2).mean()))


def measure(start, end, xfade):
    cmd = [sys.executable, MAKESFX, SRC, TMP, "--loop",
           "--start", "%.4f" % start, "--end", "%.4f" % end,
           "--crossfade", "%.0f" % xfade, "--target-rms", "0.10"]
    r = subprocess.run(cmd, capture_output=True)
    if r.returncode != 0 or not os.path.exists(TMP):
        return None
    b, bsr = sf.read(TMP, dtype="float32")
    seg = int(0.5 * bsr)
    if len(b) < 4 * seg:
        return None
    seam = abs(float(b[-1]) - float(b[0]))
    mean = rms(b)
    head, tail = rms(b[:seg]), rms(b[-seg:])
    wrap = abs(tail - head) / max(1e-9, mean)          # ★ 循环真正跨过的那一步
    head_low = max(0.0, (mean - head) / mean)          # 开头比全段低多少
    return seam, wrap, head_low, len(b) / bsr


def main():
    # 头部/尾部候选都贴近素材两端（0~300 ms 内），避免把淡化窗口推到大电平差的地方
    grid = [(0.086 + ds / 1000.0, 10.790 - de / 1000.0)
            for ds in range(0, 320, 20) for de in range(0, 320, 20)]
    xfs = (300.0, 500.0, 700.0)
    print(u"真编码测量 %d 组 × %d 档淡化 = %d 次 …" % (len(grid), len(xfs), len(grid) * len(xfs)))

    res = []
    for s, e in grid:
        for xf in xfs:
            got = measure(s, e, xf)
            if got is None:
                continue
            seam, wrap, head_low, dur = got
            score = seam + 0.8 * wrap + 0.8 * head_low
            res.append((score, seam, wrap, head_low, s, e, xf, dur))

    res.sort()
    print(u"\n评分 = 接缝差 + 0.8×(末块→首块电平差) + 0.8×(首块低于均值)")
    print(u"   评分    接缝差  末→首差  首低均值  start   end   xfade  时长")
    for sc, seam, wrap, hl, s, e, xf, dur in res[:12]:
        print(u"  %7.5f %7.5f  %6.2f%%  %6.2f%%  %6.3f %6.3f %5.0f  %5.2f s"
              % (sc, seam, wrap * 100, hl * 100, s, e, xf, dur))

    sc, seam, wrap, hl, s, e, xf, dur = res[0]
    print(u"\n==> 修正判据后的最优：--start %.3f --end %.3f --crossfade %.0f" % (s, e, xf))
    print(u"    接缝差 %.5f  末→首电平差 %.2f%%  首块低于均值 %.2f%%  成品 %.2f s"
          % (seam, wrap * 100, hl * 100, dur))

    cmd = [sys.executable, MAKESFX, SRC, FINAL, "--loop",
           "--start", "%.4f" % s, "--end", "%.4f" % e,
           "--crossfade", "%.0f" % xf, "--target-rms", "0.10"]
    r = subprocess.run(cmd, capture_output=True)
    print(u"\n-- 最终 MakeSfx 输出 --")
    for ln in r.stdout.decode("utf-8", "replace").splitlines():
        if any(k in ln for k in (u"输出 :", u"接缝", u"有声起点", u"音量", u"循环", u"切片")):
            print(u"  " + ln)
    if os.path.exists(TMP):
        os.remove(TMP)
    return 0 if r.returncode == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
