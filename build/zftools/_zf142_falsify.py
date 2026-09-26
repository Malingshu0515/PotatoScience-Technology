# -*- coding: utf-8 -*-
u"""_zf142_falsify.py —— ZF142 的反证：**每条判据都要被咬一次才作数**

做法同 ZF140：往真文件里注入一个"看起来还挺合理"的缺陷 → 跑常驻校验 →
必须出现**指定的那条 FAIL** → 再把文件逐字节还原并核哈希。

跑法：python build\\zftools\\_zf142_falsify.py
"""
import hashlib
import os
import subprocess
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import _zf142_poleblur as PB  # noqa: E402

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

ROOT = r"E:\PotatoST"
VERIFY = os.path.join(ROOT, r"build\zftools\_zf142_verify.py")
SKY = PB.SKY
VICTIM = os.path.join(SKY, "sky_mystic.png")
PRE = r"C:\PotatoST救援\zf142_pre\src\main\resources\assets\potato_s_t\textures\skybox"


def sha1(p):
    return hashlib.sha1(open(p, "rb").read()).hexdigest()


def run_verify():
    env = dict(os.environ)
    env["PYTHONIOENCODING"] = "utf-8"
    r = subprocess.run([sys.executable, VERIFY], stdout=subprocess.PIPE,
                       stderr=subprocess.STDOUT, env=env)
    return r.returncode, r.stdout.decode("utf-8", "replace")


# ---------------------------------------------------------------- 注入器
def inj_pixel_outside():
    u"""带外手改一个像素（模拟"顺手修了一下"）"""
    w, h, idx, plte = PB.read_pal_png(VICTIM)
    idx[400, 7] = (int(idx[400, 7]) + 1) % 256
    PB.write_pal_png(VICTIM, idx, plte)


def inj_refilter(par=(160, 64.0, 0.7)):
    u"""换成更强的参数重滤一遍（图还是"糊过的"，但不是本轮定的那条）"""
    w, h, idx, plte = PB.read_pal_png(VICTIM)
    new, _, _ = PB.filter_sky(idx, plte, par[0], par[1], par[2])
    PB.write_pal_png(VICTIM, new, plte)


def inj_unblur():
    u"""把极带改回留底的样子（等于这条滤波没做）"""
    w, h, idx, plte = PB.read_pal_png(VICTIM)
    _, _, idx0, _ = PB.read_pal_png(os.path.join(PRE, "sky_mystic.png"))
    PB.write_pal_png(VICTIM, idx0, plte)


def inj_palette():
    u"""动调色板里的一个色（图看着几乎没变，但"索引表"变了）"""
    w, h, idx, plte = PB.read_pal_png(VICTIM)
    plte = plte.copy()
    plte[9] = (255 - plte[9][0], plte[9][1], plte[9][2])
    PB.write_pal_png(VICTIM, idx, plte)


CASES = [
    (u"K1 带外手改一个像素", inj_pixel_outside, u"A3"),
    (u"K2 换成更强的参数重滤（160,64,0.7）", inj_refilter, u"A4"),
    (u"K3 极带改回原样（等于没糊）", inj_unblur, u"A4"),
    (u"K4 动调色板里一个色", inj_palette, u"A2"),
    (u"K5 把校验器里的参数改成 r0=0（等于没糊）", None, u"A4"),
]


def main():
    ok, bad = 0, []
    base = open(VICTIM, "rb").read()
    h0 = sha1(VICTIM)
    v0 = open(VERIFY, "rb").read()
    hv0 = sha1(VERIFY)
    print(u"改前：sky_mystic.png %s…   校验器 %s…" % (h0[:12], hv0[:12]))

    for title, fn, want in CASES:
        print(u"—— %s" % title)
        try:
            if fn is None:
                t = open(VERIFY, "r", encoding="utf-8", newline="").read()
                old = u"PARAMS = (96, 16.0, 1.0)"
                assert t.count(old) == 1, u"参数锚点命中 %d 次" % t.count(old)
                open(VERIFY, "w", encoding="utf-8", newline="").write(
                    t.replace(old, u"PARAMS = (96, 0.0, 1.0)", 1))
            else:
                fn()
            code, out = run_verify()
            ids = [l.strip().split()[1] for l in out.splitlines() if u"[FAIL]" in l]
            got = code != 0 and want in ids
            print(u"   退出码 %d，FAIL 命中 %s" % (code, u"、".join(ids) if ids else u"（无）"))
            if got:
                ok += 1
            else:
                bad.append(u"%s：期望 %s 咬住，实际命中 %s（退出码 %d）"
                           % (title, want, ids or u"无", code))
        finally:
            open(VICTIM, "wb").write(base)
            open(VERIFY, "wb").write(v0)
        assert sha1(VICTIM) == h0 and sha1(VERIFY) == hv0, u"还原失败！"

    print(u"\n还原核对：sky_mystic.png %s / 校验器 %s"
          % (u"一致" if sha1(VICTIM) == h0 else u"不一致",
             u"一致" if sha1(VERIFY) == hv0 else u"不一致"))
    code, _ = run_verify()
    print(u"全部还原后再跑一遍常驻校验：退出码 %d（必须 0）" % code)
    if code != 0:
        bad.append(u"还原后常驻校验仍不通过")
    print(u"\n咬住 %d/%d" % (ok, len(CASES)))
    for b in bad:
        print(u"  !! " + b)
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
