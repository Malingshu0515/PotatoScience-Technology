# -*- coding: utf-8 -*-
"""ZF64：看用户给的电机音效素材包络，决定循环段与音量。
打印每 0.25s 的 RMS（看是不是稳态）、首尾 0.2s 的峰值（看接缝）、整段统计。
"""
import sys

import numpy as np
import soundfile as sf

SRC = sys.argv[1] if len(sys.argv) > 1 else ""
if not SRC:
    print("用法: python _zf64_envelope.py <src.ogg>")
    raise SystemExit(2)

data, sr = sf.read(SRC, always_2d=True, dtype="float32")
mono = data.mean(axis=1)
dur = len(mono) / float(sr)
print("file      :", SRC.replace("\\", "/").split("/")[-1])
print("spec      : %d Hz  %d 声道  %.3fs  %d samples" % (sr, data.shape[1], dur, len(mono)))
print("peak/RMS  : %.3f / %.4f" % (float(np.max(np.abs(mono))), float(np.sqrt((mono ** 2).mean()))))

win = int(sr * 0.25)
rows = []
for i in range(0, len(mono) - win + 1, win):
    seg = mono[i:i + win]
    rows.append((i / float(sr), float(np.sqrt((seg ** 2).mean())), float(np.max(np.abs(seg)))))
print("---- 0.25s 窗 RMS（看稳态与淡入淡出） ----")
for t, r, p in rows:
    print("  %5.2fs  RMS %.4f  peak %.3f  %s" % (t, r, p, "#" * int(r * 120)))

for label, seg in (("开头 0.20s", mono[:int(sr * 0.2)]), ("结尾 0.20s", mono[-int(sr * 0.2):])):
    print("%s : peak %.4f  RMS %.4f  首样本 %+.4f  末样本 %+.4f"
          % (label, float(np.max(np.abs(seg))), float(np.sqrt((seg ** 2).mean())),
             float(seg[0]), float(seg[-1])))

# 静音检查
loud = np.nonzero(np.abs(mono) > 0.005)[0]
if len(loud):
    print("有声区间  : %.3fs ~ %.3fs（首尾静音 %.3fs / %.3fs）"
          % (loud[0] / float(sr), loud[-1] / float(sr),
             loud[0] / float(sr), dur - loud[-1] / float(sr)))
else:
    print("!! 整段静音")
