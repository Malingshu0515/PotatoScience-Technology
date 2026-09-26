# -*- coding: utf-8 -*-
"""_zf134_falsify_angle.py —— 反证"任意角度"这条改动：把主轴写法的等价物塞回去，判据必须咬住

打三把刀（都只针对 B24/B25/B2 —— 角度那一套）：
  K-A1：把采样从"法线"改回"主轴 + 整数偏移"（等价于退回四方向）⇒ B24 必须红；
  K-A2：去掉归一化（直接用视线分量，长度 ≠ 1）⇒ 速度会随俯仰变化 ⇒ B25 必须红；
  K-A3：去掉"视线垂直时的 yaw 兜底" ⇒ B26 必须红。

⚠ 只改 B 组那一套会影响的功能，不动别的（避免一次注入牵动一片）。

跑法：python build\\zftools\\_zf134_falsify_angle.py
"""
import hashlib
import io
import os
import subprocess
import sys

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
ROOT = r"E:\PotatoST"
SHOCK = os.path.join(ROOT, r"src\main\java\com\potatost\mod\ShockwaveManager.java")
VERIFY = os.path.join(ROOT, r"build\zftools\_zf133_verify.py")

KNIVES = [
    ("K-A1", "采样退回主轴 + 整数偏移（等价于四方向）",
     "            double lat = lateral - HALF_WIDTH;      // -3 .. +2（偶数宽的对称铺法）",
     "                double lat = lateral - HALF_WIDTH;      // -3 .. +2（偶数宽的对称铺法）\n"
     "                double perpX0 = perpX; double perpZ0 = perpZ; perpX = 0; perpZ = 0;",
     "B24"),
    ("K-A2", "去掉归一化（方向长度 ≠ 1 ⇒ 速度随俯仰变）",
     "        double dirX = dx / len;\n        double dirZ = dz / len;",
     "        double dirX = dx;\n        double dirZ = dz;",
     "B25"),
    ("K-A3", "去掉视线垂直时的 yaw 兜底",
     "        if (len < 1.0E-4D) {",
     "        if (false) {",
     "B26"),
]


def sha(p):
    return hashlib.sha1(open(p, "rb").read()).hexdigest()


def run_verify():
    env = dict(os.environ, PYTHONIOENCODING="utf-8")
    r = subprocess.run([sys.executable, VERIFY], capture_output=True, env=env)
    out = r.stdout.decode("utf-8", "replace")
    return [l.strip() for l in out.split("\n") if "[FAIL]" in l]


def main():
    orig = io.open(SHOCK, encoding="utf-8").read()
    base = sha(SHOCK)
    b = run_verify()
    print("基线失败条数 =", len(b))
    assert not b, "基线不干净，反证无意义"

    results = []
    for kid, desc, old, new, expect in KNIVES:
        n = orig.count(old)
        if n != 1:
            print("[SKIP] %s 锚点 %d 次" % (kid, n))
            results.append((kid, desc, "ANCHOR x%d" % n, False))
            continue
        io.open(SHOCK, "w", encoding="utf-8", newline="\n").write(orig.replace(old, new, 1))
        fails = run_verify()
        hit = any(expect in f for f in fails)
        results.append((kid, desc, "红 %d 条，含 %s = %s" % (len(fails), expect, hit), hit))
        print("[%s] %s —— 红 %d 条，%s %s" % ("咬住" if hit else "**没咬住**", kid,
                                              len(fails), expect, "命中" if hit else "没命中"))
        for f in fails[:3]:
            print("        " + f[:140])
        io.open(SHOCK, "w", encoding="utf-8", newline="\n").write(orig)
        assert sha(SHOCK) == base, "还原不干净"

    print("还原后失败 =", len(run_verify()))
    caught = sum(1 for x in results if x[3])
    print("角度反证：%d / %d" % (caught, len(results)))
    return 0 if caught == len(results) else 1


sys.exit(main())
