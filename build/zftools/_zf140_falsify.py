# -*- coding: utf-8 -*-
u"""_zf140_falsify.py —— ZF140 的反证：**每条判据都要被咬一次才作数**

做法（本工程的老规矩）：往真文件里注入一个"看起来还挺合理"的缺陷 → 跑常驻校验 →
必须出现**指定的那条 FAIL** → 再把文件逐字节还原并核哈希。
咬不住的判据等于没写，这一轮就要在这里当场抓出来。

跑法：python build\\zftools\\_zf140_falsify.py
"""
import hashlib
import io
import os
import subprocess
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _zf140_img import read_png_np, write_rgba  # noqa: E402

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

ROOT = r"E:\PotatoST"
JAVA = os.path.join(ROOT, "src", "main", "java", "com", "potatost", "mod", "client",
                    "SkyboxRenderer.java")
HOLE = os.path.join(ROOT, "src", "main", "resources", "assets", "potato_s_t", "textures",
                    "skybox", "black_hole.png")
VERIFY = os.path.join(ROOT, "build", "zftools", "_zf140_verify.py")


def sha1(p):
    return hashlib.sha1(open(p, "rb").read()).hexdigest()


def run_verify():
    env = dict(os.environ)
    env["PYTHONIOENCODING"] = "utf-8"
    r = subprocess.run([sys.executable, VERIFY], stdout=subprocess.PIPE,
                       stderr=subprocess.STDOUT, env=env)
    return r.returncode, r.stdout.decode("utf-8", "replace")


# ---------------------------------------------------------------- 注入器
def java_patch(old, new):
    def apply():
        t = io.open(JAVA, "r", encoding="utf-8", newline="").read()
        n = t.count(old)
        assert n == 1, u"注入锚点命中 %d 次：%r" % (n, old)
        io.open(JAVA, "w", encoding="utf-8", newline="").write(t.replace(old, new, 1))
    return apply


def png_patch():
    def apply():
        img = read_png_np(HOLE)
        h, w = img.shape[:2]
        yy, xx = np.mgrid[0:h, 0:w]
        core = np.sqrt((xx - w / 2.0) ** 2 + (yy - h / 2.0) ** 2) <= 40
        img[core, 3] = 0                      # 把极点那一块抠空
        write_rgba(HOLE, img)
    return apply


CASES = [
    (u"K1 把 θ=atan(g·tmax) 改成线性的 g·tmax（透视的逆没了）",
     u"double theta = Math.atan(g * tmax);", u"double theta = g * tmax;", u"C1"),
    (u"K2 UV 的 V 写成减号（正对极点时上下颠倒）",
     u"out[n++] = (float) (0.5D + 0.5D * b);", u"out[n++] = (float) (0.5D - 0.5D * b);", u"C1"),
    (u"K3 UV 的 U 缩一半（图会被压扁）",
     u"out[n++] = (float) (0.5D + 0.5D * a);", u"out[n++] = (float) (0.5D + 0.25D * a);", u"C4"),
    (u"K4 写 4 个 float 而不是 5 个（顶点数据错位）",
     u"        out[n++] = (float) (0.5D + 0.5D * a);\n",
     u"        n++;\n", u"A16"),
    (u"K5 网格降到 4×4（球面被切成大平板）",
     u"private static final int HOLE_GRID = 16;", u"private static final int HOLE_GRID = 4;", u"C3"),
    (u"K6 盖片半径与球幕一样大（不再压在球幕之上）",
     u"private static final float HOLE_RADIUS = RADIUS * 0.995F;",
     u"private static final float HOLE_RADIUS = RADIUS * 1.5F;", u"A4"),
    (u"K7 干脆不画盖片了",
     u"        drawBlackHoles(matrix);\n\n", u"", u"A7"),
    (u"K8 把盖片挪到球幕**之前**画（会被球幕盖掉）",
     u"        BufferUploader.drawWithShader(buffer.buildOrThrow());\n\n        drawBlackHoles(matrix);",
     u"        drawBlackHoles(matrix);\n\n        BufferUploader.drawWithShader(buffer.buildOrThrow());",
     u"A8"),
    (u"K9 去掉 `index <= 0` 那道闸（原版星空也会长黑洞）",
     u"        if (index <= 0 || index >= SKIES.length) {",
     u"        if (index >= SKIES.length) {", u"A9"),
    (u"K10 贴图指向星图自己（黑洞变成一片星云）",
     u'"textures/skybox/black_hole.png"', u'"textures/skybox/sky_mystic.png"', u"A1"),
    (u"K11 纹理中心抠空（极点从黑洞里透出来）", None, None, u"B5"),
    (u"K12 去掉开机自检（真顶点就没人量了）",
     u"        verifyCaps();\n", u"", u"A20"),
    (u"K13 自检改成失败就抛异常（会把玩家的客户端炸掉）",
     u"            LOGGER.error(\"SkyboxRenderer: black-hole cap geometry BROKEN",
     u"            throw new IllegalStateException(\"SkyboxRenderer: black-hole cap geometry BROKEN",
     u"A20c"),
]

PNG_CASES = {10}          # 索引 10 = K11 走贴图注入


def main():
    ok, bad = 0, []
    java0 = open(JAVA, "rb").read()
    png0 = open(HOLE, "rb").read()
    h_java, h_png = sha1(JAVA), sha1(HOLE)
    print(u"改前哈希：SkyboxRenderer %s…  black_hole.png %s…\n" % (h_java[:12], h_png[:12]))

    for i, (title, old, new, want) in enumerate(CASES):
        print(u"—— %s" % title)
        try:
            if i in PNG_CASES:
                png_patch()()
            else:
                java_patch(old, new)()
            code, out = run_verify()
            hit = [ln.strip() for ln in out.splitlines() if u"[FAIL]" in ln]
            ids = [ln.split()[1] for ln in hit if len(ln.split()) > 1]
            got = code != 0 and want in ids
            print(u"   退出码 %d，FAIL 命中 %s" % (code, u"、".join(ids) if ids else u"（无）"))
            if got:
                ok += 1
            else:
                bad.append(u"%s：期望 %s 咬住，实际命中 %s（退出码 %d）"
                           % (title, want, ids or u"无", code))
        finally:
            io.open(JAVA, "wb").write(java0)
            io.open(HOLE, "wb").write(png0)
        assert sha1(JAVA) == h_java and sha1(HOLE) == h_png, u"还原失败！"

    print(u"\n还原核对：SkyboxRenderer %s  black_hole.png %s"
          % (u"一致" if sha1(JAVA) == h_java else u"不一致",
             u"一致" if sha1(HOLE) == h_png else u"不一致"))
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
