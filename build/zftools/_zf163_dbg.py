# -*- coding: utf-8 -*-
r"""_zf163_dbg.py —— 两个实现为什么一个过、一个红？（同一个进程里并排跑）"""
import math, os, sys
sys.stdout.reconfigure(encoding='utf-8')
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from PngRecolor import read_png

T = r'E:\PotatoST\src\main\resources\assets\potato_s_t\textures\block'


def impl_apply(px, f, A=2, TT=32):
    bad = 0
    def col(fr, x):
        return [bytes(px[((fr * 16) + y) * 64 + x * 4:((fr * 16) + y) * 64 + x * 4 + 4]) for y in range(16)]
    base = [col(0, x) for x in range(16)]
    for t in range(TT):
        for x in range(16):
            dy = int(round(A * math.sin(2 * math.pi * (x / 16.0 - t / float(TT)))))
            if col(t, x) != [base[x][(y - dy) % 16] for y in range(16)]:
                bad += 1
    return bad


def impl_gate(rgba, fl, A=2, FS=32):
    bad = 0

    def col_of(rgba, fr, x):
        return [bytes(rgba[((fr * 16) + y) * 64 + x * 4: ((fr * 16) + y) * 64 + x * 4 + 4]) for y in range(16)]
    base = [col_of(rgba, 0, x) for x in range(16)]
    for t in range(32):
        for x in range(16):
            dy = int(round(A * math.sin(2 * math.pi * (x / 16.0 - t / float(FS)))))
            if col_of(rgba, t, x) != [base[x][(y - dy) % 16] for y in range(16)]:
                bad += 1
    return bad


for fl in ['nitrogen', 'crude_oil']:
    w, h, px = read_png(os.path.join(T, fl + '_still.png'))
    print(u'%s: %dx%d' % (fl, w, h))
    print(u'   apply 版不符 = %d   gate 版不符 = %d' % (impl_apply(px, fl), impl_gate(px, fl)))
    # 实际位移到底是什么
    def col(fr, x):
        return [bytes(px[((fr * 16) + y) * 64 + x * 4:((fr * 16) + y) * 64 + x * 4 + 4]) for y in range(16)]
    base = [col(0, x) for x in range(16)]
    for t in (1, 2, 16):
        line = []
        for x in (0, 4, 8, 12):
            got = col(t, x)
            cands = [s for s in range(-8, 9) if got == [base[x][(y - s) % 16] for y in range(16)]]
            want = int(round(2 * math.sin(2 * math.pi * (x / 16.0 - t / 32.0))))
            line.append(u'x=%d 公式=%d 实际候选=%s' % (x, want, cands))
        print(u'   t=%-3d %s' % (t, u' | '.join(line)))
