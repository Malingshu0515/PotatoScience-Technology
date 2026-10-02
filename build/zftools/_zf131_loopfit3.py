# -*- coding: utf-8 -*-
"""_zf131_loopfit3.py —— 连**交叉淡化长度**一起搜（在真产物上量）

`MakeSfx.py --loop` 默认 `--crossfade 400`（0.10 ZF64 合金炉那次的用法），
但 400 ms 只是当时够用，**不是规律**。对这段柴油机噪声，淡化窗口越长、
被"抹平"的接缝越长，首尾就越容易接上。

本脚本：粗筛 (start, end) → 对每个候选再试几档 crossfade → **每个组合都真编码一遍**
→ 回读 OGG 量 abs(last-first) → 取最小。收敛后写出最终文件。
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
THR = 0.005


def encode(start, end, xfade, dst):
    cmd = [sys.executable, MAKESFX, SRC, dst, "--loop",
           "--start", "%.4f" % start, "--end", "%.4f" % end,
           "--crossfade", "%.0f" % xfade, "--target-rms", "0.10"]
    r = subprocess.run(cmd, capture_output=True)
    if r.returncode != 0 or not os.path.exists(dst):
        return None
    b, bsr = sf.read(dst, dtype="float32")
    return abs(float(b[-1]) - float(b[0])), len(b) / bsr


def main():
    data, sr = sf.read(SRC, always_2d=True, dtype="float32")
    mono = data.mean(axis=1) if data.shape[1] > 1 else data[:, 0]
    loud = np.nonzero(np.abs(mono) > THR)[0]
    lo, hi = int(loud[0]), int(loud[-1])

    # 用 MakeSfx 逐字一致的取整做粗筛，取 8 个"起点后移"档（终点固定在最优那一带）
    cands = []
    for ds in range(0, 600, 3):
        s = int((lo / sr + ds / 1000.0) * sr)
        for de in range(600, 900, 3):
            e = int((hi / sr - de / 1000.0) * sr)
            if e - s < SR * 4:
                continue
            m = mono[s:e]
            x = int(400 / 1000.0 * sr)
            body = m[:-x].copy()
            nxt = m[-x:]
            w = np.linspace(1.0, 0.0, x, dtype="float32")
            body[:x] = nxt * w + body[:x] * (1.0 - w)
            cands.append((abs(float(body[-1]) - float(body[0])), s, e))
    cands.sort()
    picks, tried = [], []
    for _, s, e in cands:
        if any(abs(s - t[0]) < 2205 and abs(e - t[1]) < 2205 for t in tried):
            continue
        tried.append((s, e))
        picks.append((s, e))
        if len(picks) >= 6:
            break

    print(u"候选起点/终点（粗筛前 6 名），每档再配 4 种交叉淡化长度：")
    print(u"  start    end    xfade    接缝差     时长")
    best = None
    for s, e in picks:
        for xf in (400.0, 800.0, 1200.0, 1800.0):
            if xf / 1000.0 * SR >= (e - s) / 2:
                continue
            got = encode(s / sr, e / sr, xf, TMP)
            if got is None:
                continue
            d, dur = got
            print(u"  %6.3f  %6.3f  %5.0f   %8.5f   %5.2f s" % (s / sr, e / sr, xf, d, dur))
            if best is None or d < best[0]:
                best = (d, s, e, xf, dur)

    d, s, e, xf, dur = best
    print(u"\n==> 最优：--start %.3f --end %.3f --crossfade %.0f  接缝差 %.5f  成品 %.2f s"
          % (s / sr, e / sr, xf, d, dur))

    cmd = [sys.executable, MAKESFX, SRC, FINAL, "--loop",
           "--start", "%.4f" % (s / sr), "--end", "%.4f" % (e / sr),
           "--crossfade", "%.0f" % xf, "--target-rms", "0.10"]
    r = subprocess.run(cmd, capture_output=True)
    out = r.stdout.decode("utf-8", "replace")
    print(u"\n-- 最终 MakeSfx 输出 --")
    for ln in out.splitlines():
        if ln.startswith(u"  ") or any(k in ln for k in (u"输出", u"接缝", u"有声起点", u"音量")):
            print(u"  " + ln.strip())
    if os.path.exists(TMP):
        os.remove(TMP)
    return 0 if r.returncode == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
