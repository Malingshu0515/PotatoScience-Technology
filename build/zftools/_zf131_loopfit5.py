# -*- coding: utf-8 -*-
"""_zf131_loopfit5.py —— 第三判据：**循环点的电平连续性**

第四版挑出的 `0.286 / 9.930 / xfade 800` 接缝差只有 0.0003，但它的 0.5 s 块 RMS 是
`0.08 0.09 0.10 0.10 …` —— **循环起点那一块比其余低 ~20%**，每绕一圈就"掉一下音量"。
两个判据（接缝差 + 全段包络 std）都盖不住它，因为那个凹陷只占整段的一小块。

所以这一版直接量**循环点附近的电平连续性**：

  dip = |RMS(循环开头 0.4 s) − RMS(紧随其后的 0.4 s)| / 全段 RMS

这一条直接对应"绕回去时会不会听见音量跳一下"。三条一起评：
  评分 = 接缝差 + 0.5×dip + 0.3×全段起伏
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
    seam = abs(float(b[-1]) - float(b[0]))
    seg = int(0.4 * bsr)
    if len(b) < 4 * seg:
        return None
    overall = rms(b)
    # 循环点电平连续性：开头 0.4 s 与 紧随其后 0.4 s
    dip = abs(rms(b[:seg]) - rms(b[seg:2 * seg])) / max(1e-9, overall)
    # 结尾那 0.4 s 与它前面 0.4 s（循环是从结尾绕回开头，这一对同样要连续）
    dip_end = abs(rms(b[-seg:]) - rms(b[-2 * seg:-seg])) / max(1e-9, overall)
    win = max(1, int(bsr * 0.5))
    env = np.array([rms(b[i:i + win]) for i in range(0, len(b) - win + 1, win)])
    ripple = float((env.max() - env.min()) / max(1e-9, env.mean()))
    return seam, dip, dip_end, ripple, len(b) / bsr


def main():
    grid = []
    for ds in range(0, 500, 25):
        for de in range(0, 500, 25):
            grid.append((0.086 + ds / 1000.0, 10.790 - de / 1000.0))
    xfs = (600.0, 1000.0, 1400.0)
    print(u"真编码测量 %d 组 × %d 档淡化 = %d 次 …" % (len(grid), len(xfs), len(grid) * len(xfs)))

    res = []
    for s, e in grid:
        for xf in xfs:
            got = measure(s, e, xf)
            if got is None:
                continue
            seam, dip, dip_end, ripple, dur = got
            score = seam + 0.5 * dip + 0.5 * dip_end + 0.3 * ripple
            res.append((score, seam, dip, dip_end, ripple, s, e, xf, dur))

    res.sort()
    print(u"\n评分 = 接缝差 + 0.5×(起点电平跳变) + 0.5×(终点电平跳变) + 0.3×全段起伏")
    print(u"   评分    接缝差  起点跳变 终点跳变 全段起伏  start   end   xfade  时长")
    for sc, seam, dip, de_, rip, s, e, xf, dur in res[:12]:
        print(u"  %7.5f %7.5f  %6.2f%% %6.2f%% %6.2f%%  %6.3f %6.3f %5.0f  %5.2f s"
              % (sc, seam, dip * 100, de_ * 100, rip * 100, s, e, xf, dur))

    sc, seam, dip, de_, rip, s, e, xf, dur = res[0]
    print(u"\n==> 三判据最优：--start %.3f --end %.3f --crossfade %.0f" % (s, e, xf))
    print(u"    接缝差 %.5f  起点电平跳变 %.2f%%  终点 %.2f%%  全段起伏 %.2f%%  成品 %.2f s"
          % (seam, dip * 100, de_ * 100, rip * 100, dur))

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
