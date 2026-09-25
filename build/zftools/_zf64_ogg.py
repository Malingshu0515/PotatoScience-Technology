# -*- coding: utf-8 -*-
"""ZF64 音效探针：不解码，直接读 Ogg 容器 + Vorbis 头，回答三件事：
   1) 编码是不是 Vorbis；2) 声道数（是不是单声道）；3) 时长（末页 granule / 采样率）。
   用法: python _zf64_ogg.py <file.ogg> [more.ogg ...]
"""
import sys, struct, os

def analyse(path):
    data = open(path, 'rb').read()
    print("=" * 60)
    print("file      :", path)
    print("bytes     :", len(data))
    if data[:4] != b'OggS':
        print("  !! 不是 Ogg 容器，头 4 字节 =", data[:4])
        return
    print("container : OggS")

    pos = 0
    pages = 0
    last_granule = 0
    vorbis_id = None
    serials = set()
    while pos + 27 <= len(data):
        if data[pos:pos + 4] != b'OggS':
            print("  !! 第 %d 页起找不到 OggS（偏移 %d）" % (pages, pos))
            break
        ver = data[pos + 4]
        nsegs = data[pos + 26]
        seg_table = data[pos + 27:pos + 27 + nsegs]
        body = pos + 27 + nsegs
        body_len = sum(seg_table)
        granule = struct.unpack_from('<q', data, pos + 6)[0]
        serial = struct.unpack_from('<I', data, pos + 14)[0]
        serials.add(serial)
        flags = data[pos + 5]
        if granule >= 0:
            last_granule = granule
        if vorbis_id is None and body_len >= 30:
            pkt = data[body:body + body_len]
            if pkt[:1] == b'\x01' and pkt[1:7] == b'vorbis':
                vorbis_id = pkt
        pages += 1
        pos = body + body_len
        if flags & 0x04:      # EOS
            break

    print("pages     :", pages, " logical streams:", len(serials))
    if vorbis_id is None:
        print("  !! 没找到 Vorbis 识别头（可能是 Opus/FLAC 等）——看第一页正文头:")
        # 再定位一次第一包正文
        nsegs = data[26]
        body = 27 + nsegs
        print("     first packet head:", data[body:body + 16])
        return
    ver = struct.unpack_from('<I', vorbis_id, 7)[0]
    channels = vorbis_id[11]
    rate = struct.unpack_from('<I', vorbis_id, 12)[0]
    bitrate_max = struct.unpack_from('<i', vorbis_id, 16)[0]
    bitrate_nom = struct.unpack_from('<i', vorbis_id, 20)[0]
    print("codec     : Vorbis (v%d)" % ver)
    print("channels  :", channels, "  <== %s" % ("单声道 MONO" if channels == 1 else "多声道 NOT MONO"))
    print("sample    :", rate, "Hz")
    print("bitrate   : nominal %d / max %d bps  (实测约 %d kbps)" %
          (bitrate_nom, bitrate_max, (len(data) * 8 * max(rate, 1)) // max(last_granule, 1) // 1000))
    if rate:
        dur = last_granule / float(rate)
        print("granule   :", last_granule, " samples  ->  时长 %.3f 秒" % dur)
        print("loop hint : 每 %d tick 放一次可无缝续上（%.3fs x 20）" % (round(dur * 20), dur))

for p in sys.argv[1:]:
    if os.path.isfile(p):
        analyse(p)
    else:
        print("!! 文件不存在:", p)
