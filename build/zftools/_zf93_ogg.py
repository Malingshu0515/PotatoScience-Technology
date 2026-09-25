# -*- coding: utf-8 -*-
r"""_zf93_ogg.py —— 读用户给的 .ogg（只读）：规格 + 时长 + 包络，用来填 jukebox_song 的 length_in_seconds

为什么单独写一个：`sounds.json` 里唱片要 `"stream": true`，而 `data/.../jukebox_song/<id>.json`
里的 `length_in_seconds` 必须**跟音频真实时长对得上**（原版唱片机就是按它算停播/比较器输出的）。
本机没有 ffprobe，但有 `soundfile`（libsndfile）——那就用它，**同时**自己按 Ogg 的 granule 位置
算一遍时长，两条路对上才算数（§4.30：能失败的检查先怀疑自己的期望）。

用法:
    python _zf93_ogg.py <file.ogg> [more.ogg]
"""
import io
import os
import struct
import sys

import numpy as np
import soundfile as sf

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass


def ogg_granule_duration(path):
    """自己解 Ogg 页头：最后一个页的 granule / 采样率（不依赖 soundfile）。"""
    data = io.open(path, "rb").read()
    if data[:4] != b"OggS":
        return None, None
    pos = 0
    last_granule = 0
    rate = None
    while pos < len(data):
        if data[pos:pos + 4] != b"OggS":
            break
        seg = data[pos + 26]
        seg_table = data[pos + 27:pos + 27 + seg]
        body = pos + 27 + seg
        n = sum(seg_table)
        granule = struct.unpack("<q", data[pos + 6:pos + 14])[0]
        if granule > 0:
            last_granule = granule
        # identification header
        if data[body:body + 7] == b"\x01vorbis" and rate is None:
            rate = struct.unpack("<I", data[body + 12:body + 16])[0]
        pos = body + n
    return last_granule, rate


def main(argv):
    for path in argv:
        print(u"\n=== %s ===" % os.path.basename(path))
        info = sf.info(path)
        print(u"soundfile: 格式=%s 子类型=%s 声道=%d 采样率=%d 帧=%d 时长=%.6f s"
              % (info.format, info.subtype, info.channels, info.samplerate, info.frames, info.duration))
        g, rate = ogg_granule_duration(path)
        print(u"自解 Ogg 页: 末页 granule=%s 采样率=%s ⇒ 时长=%s"
              % (g, rate, (u"%.6f s" % (g / float(rate))) if (g and rate) else u"—"))
        data, sr = sf.read(path, always_2d=True)
        mono = data.mean(axis=1) if data.shape[1] > 1 else data[:, 0]
        print(u"  样本数=%d 时长=%.6f s  RMS=%.4f  峰值=%.4f  首尾 0.1s 峰值=%.4f / %.4f"
              % (len(mono), len(mono) / float(sr), float(np.sqrt((mono ** 2).mean())),
                 float(np.max(np.abs(mono))),
                 float(np.max(np.abs(mono[:int(sr * 0.1)]))),
                 float(np.max(np.abs(mono[-int(sr * 0.1):])))))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
