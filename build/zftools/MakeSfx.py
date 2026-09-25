# -*- coding: utf-8 -*-
"""MakeSfx.py —— 把外部音效（mp3/wav/…）做成 Minecraft 能用的单声道 Ogg Vorbis（0.10 新增）

为什么需要它：
  1. 原版 / 本项目的音效规格统一是 **单声道 44100 Hz Ogg Vorbis**（立体声在 MC 里不会被距离衰减，
     采样率不对则播放速度/音高会歪）；
  2. 网上抓来的素材（freesound 等）**前面常常带几百毫秒纯静音**——直接转的话，
     机器"完成"时玩家要愣等半秒才听见声音，必须掐头去尾；
  3. 掐完的头尾如果不做淡入淡出，会有"啪"的爆音；
  4. **循环音**（机器运行时的嗡嗡声）另有两个坑：不能带淡入淡出（每循环一圈就"泄一次气"），
     而且循环接缝必须做**交叉淡化**，否则每圈都"咔"一声。用 `--loop` 处理。

依赖：`pip install soundfile`（自带 libsndfile 1.2.x，能读 MP3、写 Vorbis），numpy 会一起装上。

用法：
    # 一次性音效（自动掐首尾静音 + 淡入淡出）
    python MakeSfx.py <输入> <输出.ogg> [--sr 44100] [--no-trim] [--fade-in 15] [--fade-out 40]

    # 循环音（按秒切出稳态段 + 接缝交叉淡化，默认不做淡入淡出）
    python MakeSfx.py <输入> <输出.ogg> --loop --start 0.45 --end 7.25 --crossfade 400

    # 响度对齐（循环音在代码里固定 volume=1.0，只能靠文件 RMS 对齐；本项目机器循环取 0.10）
    python MakeSfx.py <输入> <输出.ogg> --loop --start 0.45 --end 7.25 --target-rms 0.10

输出会打印转换前后的规格与包络，便于确认（一次性音效要确认"有声起点 = 0.00s"）。
"""
import sys

import numpy as np
import soundfile as sf

TRIM_THRESHOLD = 0.005     # 判定"有声"的幅度阈值
PRE_ROLL_SEC = 0.005       # 起点前保留一点，别把起音削掉
POST_ROLL_SEC = 0.060      # 终点后多留一点衰减尾巴


def main(argv):
    if len(argv) < 2:
        print(__doc__)
        return 2

    src, dst = argv[0], argv[1]
    rest = argv[2:]

    out_sr = 44100
    do_trim = True
    loop = False
    start = None
    end = None
    crossfade_ms = None
    target_rms = None
    fade_in_ms = 15.0
    fade_out_ms = 40.0

    for i, arg in enumerate(rest):
        if arg == "--sr":
            out_sr = int(rest[i + 1])
        elif arg == "--no-trim":
            do_trim = False
        elif arg == "--loop":
            loop = True
        elif arg == "--start":
            start = float(rest[i + 1])
        elif arg == "--end":
            end = float(rest[i + 1])
        elif arg == "--crossfade":
            crossfade_ms = float(rest[i + 1])
        elif arg == "--target-rms":
            target_rms = float(rest[i + 1])
        elif arg == "--fade-in":
            fade_in_ms = float(rest[i + 1])
        elif arg == "--fade-out":
            fade_out_ms = float(rest[i + 1])

    if loop:
        # 循环音绝不能带淡入淡出：每绕一圈都会听见一次音量塌陷
        fade_in_ms, fade_out_ms = 0.0, 0.0
        if crossfade_ms is None:
            crossfade_ms = 400.0

    data, sr = sf.read(src, always_2d=True, dtype="float32")
    print("输入 : {0}  {1} Hz  {2} 声道  {3:.2f}s  峰值 {4:.3f}  RMS {5:.4f}".format(
        src.replace("\\", "/").split("/")[-1], sr, data.shape[1], len(data) / sr,
        float(np.max(np.abs(data))), float(np.sqrt((data ** 2).mean()))))

    # 多声道先 downmix（MC 里要能距离衰减就必须是单声道）
    mono = data.mean(axis=1) if data.shape[1] > 1 else data[:, 0]

    if start is not None or end is not None:
        s = int((start or 0.0) * sr)
        e = int(end * sr) if end is not None else len(mono)
        print("切片 : {0:.2f}s ~ {1:.2f}s（显式指定，不做静音裁剪）".format(s / sr, e / sr))
        mono = mono[s:e]
    elif do_trim:
        loud = np.nonzero(np.abs(mono) > TRIM_THRESHOLD)[0]
        if len(loud) == 0:
            print("!! 整段都是静音，放弃裁剪")
        else:
            a = max(0, int(loud[0] - PRE_ROLL_SEC * sr))
            b = min(len(mono), int(loud[-1] + POST_ROLL_SEC * sr))
            print("裁剪 : 去掉开头 {0:.3f}s、结尾 {1:.3f}s 的静音".format(a / sr, (len(mono) - b) / sr))
            mono = mono[a:b]

    if loop and crossfade_ms and crossfade_ms > 0:
        x = int(crossfade_ms / 1000.0 * sr)
        if x <= 0 or len(mono) <= 2 * x:
            print("!! 交叉淡化长度不合理，按不做处理")
        else:
            # 做法：循环本体取 [开头, 末尾-X)，再用"紧跟在循环点之后的那 X 毫秒"
            # 与本体开头做等功率交叉淡化 —— 这样本体最后一个样本之后接的第一个样本
            # 正好是它时间上的后继，接缝处波形连续，不会"咔"。
            body = mono[:-x].copy()
            nxt = mono[-x:]
            w = np.linspace(1.0, 0.0, x, dtype="float32")
            body[:x] = nxt * w + body[:x] * (1.0 - w)
            mono = body
            print("循环 : 末尾 {0:.0f}ms 与开头交叉淡化，成品 {1:.2f}s 无缝".format(
                crossfade_ms, len(mono) / sr))

    fi, fo = int(fade_in_ms / 1000.0 * sr), int(fade_out_ms / 1000.0 * sr)
    if fi > 0:
        mono[:fi] *= np.linspace(0.0, 1.0, fi, dtype="float32")
    if fo > 0:
        mono[-fo:] *= np.linspace(1.0, 0.0, fo, dtype="float32")

    if target_rms is not None:
        cur = float(np.sqrt((mono ** 2).mean()))
        peak = float(np.max(np.abs(mono)))
        if cur > 0.0 and peak > 0.0:
            gain = target_rms / cur
            if peak * gain > 0.98:
                gain = 0.98 / peak
                print("音量 : 按目标 RMS 会削波，改用峰值保护，增益 {0:.3f}".format(gain))
            else:
                print("音量 : RMS {0:.4f} -> {1:.4f}（增益 {2:.3f}）".format(cur, cur * gain, gain))
            mono = mono * gain

    if sr != out_sr:
        n_out = int(round(len(mono) * out_sr / float(sr)))
        mono = np.interp(
            np.linspace(0.0, len(mono) - 1.0, n_out),
            np.arange(len(mono), dtype="float64"),
            mono.astype("float64"),
        ).astype("float32")
        print("重采样: {0} Hz -> {1} Hz".format(sr, out_sr))
        sr = out_sr

    sf.write(dst, mono, sr, format="OGG", subtype="VORBIS")

    # 回读验证：规格 + 包络 + 首尾样本差（循环接缝是否连续）
    info = sf.info(dst)
    back, back_sr = sf.read(dst, dtype="float32")
    win = max(1, int(back_sr * 0.05))
    env = [float(np.sqrt((back[i:i + win] ** 2).mean())) for i in range(0, len(back) - win + 1, win)]
    loud = np.nonzero(np.abs(back) > TRIM_THRESHOLD)[0]
    print("输出 : {0}  {1}  {2} Hz  {3} 声道  {4:.2f}s  峰值 {5:.3f}  RMS {6:.4f}".format(
        dst.replace("\\", "/").split("/")[-1], info.format + "/" + info.subtype, back_sr,
        info.channels, info.duration, float(np.max(np.abs(back))),
        float(np.sqrt((back ** 2).mean()))))
    print("       有声起点 {0:.3f}s".format(float(loud[0]) / back_sr if len(loud) else -1.0))
    print("       接缝首尾差 {0:.4f}（循环音越接近 0 越好）".format(abs(float(back[-1]) - float(back[0]))))
    print("       包络 " + " ".join("%.2f" % v for v in env))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
