# -*- coding: utf-8 -*-
"""_zf131_loopfit.py —— 给柴油发电机那段音频**找最佳循环点**（只读源 + 写诊断）

为什么需要它：`MakeSfx.py --loop` 的接缝质量取决于**素材本身首尾是否连续**。
合金炉那次素材首尾本来就淡到接近 0（接缝差 0.0008），所以默认切法就够了。
这段柴油机素材不是：默认 `--start 0.09 --end 10.79` 切出来**接缝差 0.1061**，
按 §6.5 第 2 条那套判据，这会在每绕一圈时"咔"一声 —— 不能就这么交。

做法：在"整段可用区间"里扫 (start, end) 组合，对每一组算出成品**接缝首尾差**，
挑最小的那组。评估方式与 MakeSfx.py 完全一致（末尾 X ms 与开头等功率交叉淡化后
再比 last 与 first 两个样本），所以扫出来的就是 MakeSfx 真会产出的结果。
"""
import sys

import numpy as np
import soundfile as sf

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

SRC = r"E:\PotatoST\build\用户素材\柴油发电机工作.mp3"
SR = 44100
XFADE_MS = 400.0
THR = 0.005


def seam_diff(mono, x):
    """复刻 MakeSfx.py 的循环处理，返回 (接缝首尾差, 成品长度秒)"""
    if len(mono) <= 2 * x:
        return 9.99, 0.0
    body = mono[:-x].copy()
    nxt = mono[-x:]
    w = np.linspace(1.0, 0.0, x, dtype="float32")
    body[:x] = nxt * w + body[:x] * (1.0 - w)
    return abs(float(body[-1]) - float(body[0])), len(body) / SR


def main():
    data, sr = sf.read(SRC, always_2d=True, dtype="float32")
    mono_all = data.mean(axis=1) if data.shape[1] > 1 else data[:, 0]
    loud = np.nonzero(np.abs(mono_all) > THR)[0]
    lo, hi = int(loud[0]), int(loud[-1])
    print("源：%.3f s ~ %.3f s（有声区间）" % (lo / sr, hi / sr))

    x = int(XFADE_MS / 1000.0 * sr)
    print("交叉淡化 %d 样本（%.0f ms）\n" % (x, XFADE_MS))

    # 起点候选：有声起点往后 0 ~ 1200 ms（步进 5 ms）
    # 终点候选：有声终点往前 0 ~ 1200 ms（步进 5 ms）
    best = None
    rows = []
    for ds in range(0, 1200, 5):
        s = lo + int(ds / 1000.0 * sr)
        for de in range(0, 1200, 5):
            e = hi - int(de / 1000.0 * sr)
            if e - s < SR * 4:          # 至少 4 秒，太短不像机器声
                continue
            d, dur = seam_diff(mono_all[s:e], x)
            rows.append((d, ds, de, dur))
            if best is None or d < best[0]:
                best = (d, ds, de, dur)

    rows.sort()
    print("接缝差最小的 12 组：")
    print("  接缝差     起点后移   终点前移   成品时长")
    for d, ds, de, dur in rows[:12]:
        print("  %8.5f   %5d ms   %5d ms   %6.2f s" % (d, ds, de, dur))

    print("\n默认切法（0.09 / 10.79）对照：")
    s = int(0.09 * sr)
    e = int(10.79 * sr)
    d, dur = seam_diff(mono_all[s:e], x)
    print("  接缝差 %8.5f   成品 %6.2f s" % (d, dur))

    d, ds, de, dur = best
    print("\n==> 推荐：--start %.3f --end %.3f（接缝差 %.5f，成品 %.2f s）"
          % ((lo + int(ds / 1000.0 * sr)) / sr, (hi - int(de / 1000.0 * sr)) / sr, d, dur))
    return 0


if __name__ == "__main__":
    sys.exit(main())
