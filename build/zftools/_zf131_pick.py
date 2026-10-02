# -*- coding: utf-8 -*-
"""_zf131_pick.py —— 最终挑选：**样本接缝差**与**末→首电平差**同时合格

到第六版为止的战况：
  · `0.086 / 10.790 / 300ms`：接缝差 0.0174、末→首 4.40%
  · `0.086 / 10.550 / 300ms`：接缝差 0.0136、末→首 3.13%（实测 1.98%）
  · `0.106 / 10.790 / 300ms`：接缝差 **0.0023**、末→首 6.21%
两条此消彼长，所以这一版把 (start, end, xfade) 的网格铺得更密、**同时报两条**，
挑一个"两条都 ≤ 阈值"的解：

    样本接缝差 ≤ 0.010   （远低于 §6.5 记的合金炉 0.0008 量级之上一点点，听不出"咔"）
    末→首电平差 ≤ 3.5%   （≈0.3 dB，低于素材本身的 4.49% 抖动）

挑不出就取加权和最小的那个，并**如实报出它没同时满足哪一条**。
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
SEAM_MAX = 0.010
WRAP_MAX = 0.035


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
    mean = rms(b)
    seam = abs(float(b[-1]) - float(b[0]))
    wrap = abs(rms(b[-seg:]) - rms(b[:seg])) / max(1e-9, mean)
    return seam, wrap, len(b) / bsr


def main():
    grid = [(0.086 + ds / 1000.0, 10.790 - de / 1000.0)
            for ds in range(0, 260, 10) for de in range(0, 420, 10)]
    xfs = (200.0, 300.0, 400.0, 600.0, 900.0)
    print(u"真编码测量 %d 组 × %d 档淡化 = %d 次 …" % (len(grid), len(xfs), len(grid) * len(xfs)))

    res = []
    for s, e in grid:
        for xf in xfs:
            got = measure(s, e, xf)
            if got is None:
                continue
            seam, wrap, dur = got
            res.append((seam, wrap, s, e, xf, dur))

    ok = [r for r in res if r[0] <= SEAM_MAX and r[1] <= WRAP_MAX]
    print(u"\n两条同时合格（接缝差 ≤ %.3f、末→首 ≤ %.1f%%）的解：%d 个"
          % (SEAM_MAX, WRAP_MAX * 100, len(ok)))
    if ok:
        ok.sort(key=lambda r: (r[0] + 2.0 * r[1]))
        print(u"   接缝差  末→首差  start   end   xfade  时长")
        for seam, wrap, s, e, xf, dur in ok[:8]:
            print(u"  %7.5f  %6.2f%%  %6.3f %6.3f %5.0f  %5.2f s"
                  % (seam, wrap * 100, s, e, xf, dur))
        seam, wrap, s, e, xf, dur = ok[0]
    else:
        res.sort(key=lambda r: r[0] + 2.0 * r[1])
        print(u"   （没有同时合格的，取加权和最小的）")
        for seam, wrap, s, e, xf, dur in res[:5]:
            print(u"  %7.5f  %6.2f%%  %6.3f %6.3f %5.0f  %5.2f s"
                  % (seam, wrap * 100, s, e, xf, dur))
        seam, wrap, s, e, xf, dur = res[0]

    print(u"\n==> 选定：--start %.3f --end %.3f --crossfade %.0f" % (s, e, xf))
    print(u"    接缝差 %.5f（阈值 %.3f）%s" % (seam, SEAM_MAX, u"OK" if seam <= SEAM_MAX else u"超标"))
    print(u"    末→首 %.2f%%（阈值 %.1f%%）%s" % (wrap * 100, WRAP_MAX * 100,
                                            u"OK" if wrap <= WRAP_MAX else u"超标"))

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
