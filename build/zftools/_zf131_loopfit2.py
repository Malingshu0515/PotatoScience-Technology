# -*- coding: utf-8 -*-
"""_zf131_loopfit2.py —— 在**真产物**上挑循环点（对候选逐个编码成 OGG 再回读测接缝）

第一版（`_zf131_loopfit.py`）用"整数样本"当代理，量出 0.00066，
但 MakeSfx 真跑出来是 0.0189 —— 因为 `MakeSfx.py` 取切片用的是
`s = int((start or 0.0) * sr)`（**截断**），我那个代理差 1 个样本。
对发动机这种噪声信号，1 个样本的相位差就足以让"首尾差"这个指标变化一个数量级
⇒ **代理不能当结论**（§4.55「先怀疑探针」那一族）。

这一版不改 MakeSfx，而是在**它真实产出的文件**上量：
  ① 先用与 MakeSfx **逐字一致**的取整方式粗筛 40 个候选；
  ② 对粗筛出来的前若干名，真的调 MakeSfx 编码 → 回读 OGG → 量 `abs(last-first)`；
  ③ 取真产物里最小的那个。
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
XFADE_MS = 400.0
THR = 0.005


def proxy_seam(mono, s, e, x):
    """与 MakeSfx 逐字一致的切片 + 交叉淡化（不做增益），返回代理接缝差"""
    m = mono[s:e]
    if len(m) <= 2 * x:
        return 9.99
    body = m[:-x].copy()
    nxt = m[-x:]
    w = np.linspace(1.0, 0.0, x, dtype="float32")
    body[:x] = nxt * w + body[:x] * (1.0 - w)
    return abs(float(body[-1]) - float(body[0]))


def real_seam(start, end):
    """真的调 MakeSfx 产出 OGG，回读量接缝"""
    cmd = [sys.executable, MAKESFX, SRC, TMP, "--loop",
           "--start", "%.4f" % start, "--end", "%.4f" % end,
           "--crossfade", "%.0f" % XFADE_MS, "--target-rms", "0.10"]
    r = subprocess.run(cmd, capture_output=True)
    if r.returncode != 0 or not os.path.exists(TMP):
        return 9.99, 0.0
    back, bsr = sf.read(TMP, dtype="float32")
    return abs(float(back[-1]) - float(back[0])), len(back) / bsr


def main():
    data, sr = sf.read(SRC, always_2d=True, dtype="float32")
    mono = data.mean(axis=1) if data.shape[1] > 1 else data[:, 0]
    loud = np.nonzero(np.abs(mono) > THR)[0]
    lo, hi = int(loud[0]), int(loud[-1])
    x = int(XFADE_MS / 1000.0 * sr)
    print(u"有声区间 %.3f ~ %.3f s；交叉淡化 %d 样本" % (lo / sr, hi / sr, x))

    # ① 粗筛：与 MakeSfx 逐字一致的取整
    cands = []
    for ds in range(0, 900, 5):
        s = int((lo / sr + ds / 1000.0) * sr)
        for de in range(0, 900, 5):
            e = int((hi / sr - de / 1000.0) * sr)
            if e - s < SR * 4:
                continue
            cands.append((proxy_seam(mono, s, e, x), s, e))
    cands.sort()
    print(u"粗筛 %d 组，前 6 名的代理值：%s"
          % (len(cands), u", ".join(u"%.5f" % c[0] for c in cands[:6])))

    # ② 对前若干名做真编码测量（去重：起点/终点太近的只留一个代表）
    tried, pick = [], []
    for _, s, e in cands:
        if any(abs(s - t[0]) < 2205 and abs(e - t[1]) < 2205 for t in tried):
            continue
        tried.append((s, e))
        pick.append((s, e))
        if len(pick) >= 8:
            break

    print(u"\n真产物测量（%d 个候选，每个都真编码一遍）：" % len(pick))
    print(u"  start    end      接缝差     时长")
    best = None
    for s, e in pick:
        d, dur = real_seam(s / sr, e / sr)
        print(u"  %6.3f  %6.3f   %8.5f   %5.2f s" % (s / sr, e / sr, d, dur))
        if best is None or d < best[0]:
            best = (d, s, e, dur)

    # 对照：默认切法
    d0, dur0 = real_seam(0.09, 10.79)
    print(u"\n  默认 0.090 / 10.790   %8.5f   %5.2f s" % (d0, dur0))
    print(u"  （ZF131 第一版交出去的就是这个）")

    d, s, e, dur = best
    print(u"\n==> 真产物最优：--start %.3f --end %.3f  接缝差 %.5f  成品 %.2f s"
          % (s / sr, e / sr, d, dur))

    # ③ 用它产出最终文件
    cmd = [sys.executable, MAKESFX, SRC, FINAL, "--loop",
           "--start", "%.4f" % (s / sr), "--end", "%.4f" % (e / sr),
           "--crossfade", "%.0f" % XFADE_MS, "--target-rms", "0.10"]
    r = subprocess.run(cmd, capture_output=True)
    out = r.stdout.decode("utf-8", "replace")
    print(u"\n-- 最终 MakeSfx 输出 --")
    for ln in out.splitlines():
        if any(k in ln for k in (u"输出", u"接缝", u"有声起点", u"音量", u"循环", u"切片")):
            print(u"  " + ln)
    if os.path.exists(TMP):
        os.remove(TMP)
    return 0 if r.returncode == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
