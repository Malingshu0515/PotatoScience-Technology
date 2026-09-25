# -*- coding: utf-8 -*-
r"""_zf119_intake.py —— ZF119 收件体检：`振金锭.png`（只读 + 抄一份进项目）

用户原话：「加个振金锭（目前没配方）这是振金锭贴图 做成动态贴图 3t播放一帧」

本轮候选只有这一件，来源是**会话附件**（不是往常的 `build\用户素材\` 手放），
附件那份是**规范化副本**（可能被缩放过）⇒ 先体检，再决定怎么落地：

  ① 真格式（PNG / JPEG / WebP —— 本工程被"名字叫 .png 实际是 webp/jpg"坑过 3 次）；
  ② 尺寸 / 位深 / 颜色类型 / alpha 分布；
  ③ **是不是一条竖直的动画帧带**：逐行统计"这一行有没有不透明像素"，
     找出全透明的分隔行 ⇒ 推出**每帧多高、共几帧**（动画贴图在 MC 里 =
     宽 × (宽 × 帧数) 的竖直长条 + 同名 `.mcmeta`）；
  ④ 打一份字符画（每帧一张），肉眼核一下"每帧只差那条高光"。
"""
import hashlib
import io
import os
import struct
import sys
import zlib

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

ATT = (r"C:\Users\Administrator\.dsh\attachments\v1\objects\a8"
       r"\a8c784271dd33ae7e3117d561badd8d550b29a070ffb1c2a20475f30e6b55a45")
USERART = r"E:\PotatoST\build\用户素材"
KEEP = os.path.join(USERART, u"振金锭.png")
TOOLS = r"E:\PotatoST\build\zftools"
OUT = os.path.join(TOOLS, u"_zf119_intake.txt")
RAMP = u" .:-=+*#%@"

lines = []


def say(s):
    print(s)
    lines.append(s)


def read_png(path):
    u"""最小 PNG 解码（8 位 RGBA / 调色板 / 灰度都认；本工程老规矩：不引第三方库）"""
    b = open(path, "rb").read()
    if b[:8] != b"\x89PNG\r\n\x1a\n":
        raise ValueError(u"不是 PNG（前 8 字节 %r）" % b[:8])
    pos, idat, pal, trns = 8, b"", None, None
    w = h = depth = ctype = None
    while pos < len(b):
        (ln,) = struct.unpack(">I", b[pos:pos + 4])
        typ = b[pos + 4:pos + 8]
        data = b[pos + 8:pos + 8 + ln]
        if typ == b"IHDR":
            w, h, depth, ctype = struct.unpack(">IIBB", data[:10])[:4]
            interlace = data[12]
            if interlace != 0:
                raise ValueError(u"隔行扫描 PNG，不支持")
        elif typ == b"PLTE":
            pal = [tuple(data[i:i + 3]) for i in range(0, len(data), 3)]
        elif typ == b"tRNS":
            trns = data
        elif typ == b"IDAT":
            idat += data
        elif typ == b"IEND":
            break
        pos += 12 + ln
    raw = zlib.decompress(idat)
    ch = {0: 1, 2: 3, 3: 1, 4: 2, 6: 4}[ctype]
    stride = w * ch
    out, prev = [], bytearray(stride)
    p = 0
    for _y in range(h):
        f = raw[p]
        p += 1
        row = bytearray(raw[p:p + stride])
        p += stride
        for i in range(stride):
            a = row[i - ch] if i >= ch else 0
            bb = prev[i]
            c = prev[i - ch] if i >= ch else 0
            if f == 1:
                row[i] = (row[i] + a) & 0xFF
            elif f == 2:
                row[i] = (row[i] + bb) & 0xFF
            elif f == 3:
                row[i] = (row[i] + ((a + bb) >> 1)) & 0xFF
            elif f == 4:
                pp = a + bb - c
                pa, pb, pc = abs(pp - a), abs(pp - bb), abs(pp - c)
                pr = a if (pa <= pb and pa <= pc) else (bb if pb <= pc else c)
                row[i] = (row[i] + pr) & 0xFF
        out.append(bytes(row))
        prev = row
    rgba = []
    for y in range(h):
        row = out[y]
        for x in range(w):
            if ctype == 6:
                i = x * 4
                rgba.append((row[i], row[i + 1], row[i + 2], row[i + 3]))
            elif ctype == 2:
                i = x * 3
                rgba.append((row[i], row[i + 1], row[i + 2], 255))
            elif ctype == 3:
                idx = row[x]
                r, g, bl = pal[idx]
                al = trns[idx] if (trns and idx < len(trns)) else 255
                rgba.append((r, g, bl, al))
            elif ctype == 0:
                v = row[x]
                rgba.append((v, v, v, 255))
            elif ctype == 4:
                i = x * 2
                rgba.append((row[i], row[i], row[i], row[i + 1]))
    return w, h, depth, ctype, rgba


def main():
    say(u"# ZF119 收件体检：振金锭.png")
    say(u"")
    sha = hashlib.sha1(open(ATT, "rb").read()).hexdigest()
    size = os.path.getsize(ATT)
    say(u"附件：%s" % ATT)
    say(u"      %d B  sha1 %s" % (size, sha))
    head = open(ATT, "rb").read(16)
    say(u"文件头：%s" % head.hex(" "))
    if head[:3] == b"\xff\xd8\xff":
        say(u"⚠ 真格式 = **JPEG**（不透明，没有 alpha）")
    elif head[:4] == b"RIFF" and head[8:12] == b"WEBP":
        say(u"⚠ 真格式 = **WebP**（本工程第 4 次）")
    elif head[:8] == b"\x89PNG\r\n\x1a\n":
        say(u"真格式 = PNG")
    else:
        say(u"⚠ 认不出的格式")
    w, h, depth, ctype, rgba = read_png(ATT)
    say(u"尺寸：%d × %d  位深 %d  颜色类型 %d（6=RGBA）" % (w, h, depth, ctype))
    alphas = {}
    for px in rgba:
        alphas[px[3]] = alphas.get(px[3], 0) + 1
    zero = alphas.get(0, 0)
    full = alphas.get(255, 0)
    semi = sum(v for k, v in alphas.items() if 0 < k < 255)
    say(u"alpha：全透明 %d 像素（%.1f%%）、不透明 %d、半透明 %d"
        % (zero, 100.0 * zero / (w * h), full, semi))
    say(u"用色数：%d 种（含 alpha 组合）" % len(set(rgba)))
    # 逐行：有没有不透明像素
    rows = []
    for y in range(h):
        n = sum(1 for x in range(w) if rgba[y * w + x][3] > 0)
        rows.append(n)
    say(u"")
    say(u"逐行不透明像素数（每行一个数，0 = 全透明的分隔行）：")
    say(u"    " + u" ".join(u"%d" % n for n in rows))
    # 找连续的非空行段
    bands, cur = [], None
    for y, n in enumerate(rows):
        if n > 0 and cur is None:
            cur = y
        elif n == 0 and cur is not None:
            bands.append((cur, y - 1))
            cur = None
    if cur is not None:
        bands.append((cur, h - 1))
    say(u"")
    say(u"非空行段（%d 段）：" % len(bands))
    for (a, b2) in bands:
        say(u"    y=%3d..%-3d  高 %d" % (a, b2, b2 - a + 1))
    if bands:
        hs = [b2 - a + 1 for (a, b2) in bands]
        say(u"段高：%s（唯一值 %s）" % (hs, sorted(set(hs))))
        say(u"⇒ 若每段 = 一帧：**帧高 %d**，帧数 **%d**，宽 %d" % (hs[0], len(bands), w))
        say(u"⇒ MC 动画贴图要求「宽 × (宽 × 帧数)」⇒ 期望高 = %d × %d = **%d**（实际 %d）%s"
            % (w, len(bands), w * len(bands), h,
               u" ✔" if w * len(bands) == h else u" ✘ 对不上"))
    # 每帧一张字符画
    say(u"")
    say(u"字符画（每段一帧，用亮度上色阶）：")
    for k, (a, b2) in enumerate(bands):
        say(u"---- 第 %d 帧（y=%d..%d）----" % (k, a, b2))
        for y in range(a, b2 + 1):
            line = []
            for x in range(w):
                r, g, bl, al = rgba[y * w + x]
                if al == 0:
                    line.append(u" ")
                else:
                    lum = (r * 299 + g * 587 + bl * 114) // 1000
                    line.append(RAMP[min(9, lum * 10 // 256)])
            say(u"    |" + u"".join(line) + u"|")
    # 抄一份进项目（原字节）
    os.makedirs(USERART, exist_ok=True)
    data = open(ATT, "rb").read()
    open(KEEP, "wb").write(data)
    say(u"")
    say(u"已抄进项目：%s（%d B，sha1 %s）"
        % (KEEP, os.path.getsize(KEEP), hashlib.sha1(open(KEEP, "rb").read()).hexdigest()))
    io.open(OUT, "w", encoding="utf-8", newline=u"\n").write(u"\n".join(lines) + u"\n")
    print(u"报告 → %s" % OUT)
    return 0


if __name__ == "__main__":
    sys.exit(main())
