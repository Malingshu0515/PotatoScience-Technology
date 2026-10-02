# -*- coding: utf-8 -*-
"""_zf131_loopfit4.py —— 双判据挑循环点：**接缝差** + **包络平坦度**

前两版只看接缝差。第三版挑出的 `0.188 / 10.064 / xfade 1800` 接缝差只有 0.0018，
漂亮 —— 但它的**包络**是 0.11 → 0.07 → 0.11：交叉淡化把那一段抹平的同时，
也把整段切成了"一半响一半轻"。8 秒绕一圈就是一次可闻的"呼吸"。
机器循环音要的是**稳态**（§8 那套："切稳态段"），所以两个判据都得看。

评分 = 接缝差 + W × 包络相对起伏
  包络起伏 = (max-min)/mean（对 0.25 s 窗口的 RMS 序列）
  W = 0.30（接缝差 0.003 与起伏 1% 大致等价；先按这个权重，改一行就能调）
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
W = 0.30


def measure(start, end, xfade):
    cmd = [sys.executable, MAKESFX, SRC, TMP, "--loop",
           "--start", "%.4f" % start, "--end", "%.4f" % end,
           "--crossfade", "%.0f" % xfade, "--target-rms", "0.10"]
    r = subprocess.run(cmd, capture_output=True)
    if r.returncode != 0 or not os.path.exists(TMP):
        return None
    b, bsr = sf.read(TMP, dtype="float32")
    seam = abs(float(b[-1]) - float(b[0]))
    win = max(1, int(bsr * 0.25))
    env = np.array([float(np.sqrt((b[i:i + win] ** 2).mean()))
                    for i in range(0, len(b) - win + 1, win)])
    ripple = float((env.max() - env.min()) / max(1e-9, env.mean()))
    return seam, ripple, len(b) / bsr


def main():
    grid = []
    # 起点：有声起点后 0~400 ms（20 ms 步进）；终点：有声终点前 600~900 ms（20 ms 步进）
    for ds in range(0, 420, 20):
        for de in range(600, 920, 20):
            grid.append((0.086 + ds / 1000.0, 10.790 - de / 1000.0))
    print(u"真编码测量 %d 组 × 2 档淡化 = %d 次 …" % (len(grid), len(grid) * 2))

    results = []
    for start, end in grid:
        for xf in (800.0, 1800.0):
            if xf / 1000.0 * SR >= (end - start) * SR / 2:
                continue
            got = measure(start, end, xf)
            if got is None:
                continue
            seam, ripple, dur = got
            results.append((seam + W * ripple, seam, ripple, start, end, xf, dur))

    results.sort()
    print(u"\n评分 = 接缝差 + %.2f × 包络起伏；前 10 名：" % W)
    print(u"   评分     接缝差   包络起伏   start    end    xfade   时长")
    for sc, seam, rip, s, e, xf, dur in results[:10]:
        print(u"  %7.5f  %7.5f   %6.2f%%   %6.3f  %6.3f  %5.0f   %5.2f s"
              % (sc, seam, rip * 100, s, e, xf, dur))

    # 对照：只看接缝差会选谁
    by_seam = sorted(results, key=lambda r: r[1])
    sc, seam, rip, s, e, xf, dur = by_seam[0]
    print(u"\n对照（只看接缝差会选）：接缝差 %.5f 但包络起伏 %.2f%% ⇒ %.3f / %.3f / %.0f"
          % (seam, rip * 100, s, e, xf))

    sc, seam, rip, s, e, xf, dur = results[0]
    print(u"\n==> 双判据最优：--start %.3f --end %.3f --crossfade %.0f" % (s, e, xf))
    print(u"    接缝差 %.5f   包络起伏 %.2f%%   成品 %.2f s" % (seam, rip * 100, dur))

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
