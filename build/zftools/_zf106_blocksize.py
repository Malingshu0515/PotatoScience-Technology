# -*- coding: utf-8 -*-
u"""_zf106_blocksize.py —— 只读诊断：判断这两张 64x32 预览是"真贴图"还是"被放大过的缩略图"

做法：把 64x32 的像素网格按 k×k 分块，若每块内部**完全同色**，说明原图其实只有 64/k × 32/k。
对取证很关键：如果 k>1，那我手上这份就不是能直接用的贴图（细节已经在缩放里丢了）。

另外把它按 8 档灰度打出来，看整体形状是不是标准盔甲层贴图（头在上、身体+手臂在下）。
"""
import struct
import sys
import zlib

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

OBJS = [
    (u"钛合金套装", r"C:\Users\Administrator\.dsh\attachments\v1\objects\84"
                     r"\84c0660b9d956c9af58f4c96242a92bcac9996f5fd09bb2cfc02d108e09a9d7a"),
    (u"星璨钢套装", r"C:\Users\Administrator\.dsh\attachments\v1\objects\02"
                     r"\02239356de18e07b8ceedf3802be7aa3e1152abfa5dfa7873bd968f26f2f7c12"),
]
RAMP = u" .:-=+*#%@"


def decode(path):
    d = open(path, "rb").read()
    pos, idat, dims, ct = 8, b"", None, None
    while pos < len(d):
        ln = struct.unpack_from(">I", d, pos)[0]
        ctype = d[pos + 4:pos + 8]
        if ctype == b"IHDR":
            w, h, depth, ct = struct.unpack_from(">IIBB", d, pos + 8)
            dims = (w, h)
        elif ctype == b"IDAT":
            idat += d[pos + 8:pos + 8 + ln]
        pos += 12 + ln
    ch = {2: 3, 4: 2, 6: 4}[ct]
    stride = dims[0] * ch
    raw = zlib.decompress(idat)
    p, prev, rows = 0, bytearray(stride), []
    for _y in range(dims[1]):
        f = raw[p]
        p += 1
        line = bytearray(raw[p:p + stride])
        p += stride
        if f == 1:
            for i in range(ch, stride):
                line[i] = (line[i] + line[i - ch]) & 0xFF
        elif f == 2:
            for i in range(stride):
                line[i] = (line[i] + prev[i]) & 0xFF
        elif f == 3:
            for i in range(stride):
                a = line[i - ch] if i >= ch else 0
                line[i] = (line[i] + ((a + prev[i]) >> 1)) & 0xFF
        elif f == 4:
            for i in range(stride):
                a = line[i - ch] if i >= ch else 0
                b = prev[i]
                c = prev[i - ch] if i >= ch else 0
                pa, pb, pc = abs(b - c), abs(a - c), abs(a + b - 2 * c)
                pr = a if (pa <= pb and pa <= pc) else (b if pb <= pc else c)
                line[i] = (line[i] + pr) & 0xFF
        rows.append(bytes(line))
        prev = line
    return dims[0], dims[1], ch, rows


def main():
    for name, path in OBJS:
        w, h, ch, rows = decode(path)
        print(u"\n================ %s  %dx%d ================" % (name, w, h))
        # ① 分块同色检测
        print(u"  分块同色检测（k = 块边长；'全同色' 说明原图只有 64/k × 32/k）：")
        for k in (1, 2, 4, 8, 16):
            if w % k or h % k:
                continue
            same = 0
            total = 0
            for by in range(0, h, k):
                for bx in range(0, w, k):
                    total += 1
                    first = rows[by][bx * ch:bx * ch + ch]
                    if all(rows[by + dy][(bx + dx) * ch:(bx + dx) * ch + ch] == first
                           for dy in range(k) for dx in range(k)):
                        same += 1
            print(u"    k=%2d：%d/%d 块内部同色（%.1f%%）" % (k, same, total, 100.0 * same / total))
        # ② 透明像素统计
        trans = sum(1 for y in range(h) for x in range(w) if rows[y][x * ch + 3] == 0)
        print(u"  透明像素：%d/%d（%.1f%%）" % (trans, w * h, 100.0 * trans / (w * h)))
        # ③ 灰度形状（每 2 列采样，反相：越亮越空）
        print(u"  形状（每 2 列采样；空格 = 透明）：")
        for y in range(h):
            line = []
            for x in range(0, w, 2):
                o = x * ch
                a = rows[y][o + 3]
                if a < 16:
                    line.append(u" ")
                else:
                    lum = (rows[y][o] * 299 + rows[y][o + 1] * 587 + rows[y][o + 2] * 114) // 1000
                    line.append(RAMP[min(9, (255 - lum) * 10 // 256)])
            print(u"  %2d|%s|" % (y, u"".join(line)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
