# -*- coding: utf-8 -*-
u"""_zf108_falsify.py —— 【反证刀】证明 `_zf108_verify.py` 真的会失败（0.11 ZF108）

§4.17 的口径：**"能失败的检查"才算检查**。本轮是"画图 + 改 UV"，所以刀也分两类：
  · 改**模型/材质/文档**的文本（K92/K93/K94/K97/K98）；
  · 重新**写出难看的贴图**（K95/K96）—— 这两把是专门喂给"防糊化"那两条断言的
    （色数 ≤ 8、用色 ∈ 家族调色板、机体图上下镜像对称）。

每把刀：改 → 跑校验器（必须 FAIL）→ **逐字还原** → 再跑（必须回到全绿）。
开跑前先验基线是绿的；跑门带 180 秒超时（§4.77：卡死和抓到在退出码上长得一样，要分开）。
⚠ 备份目录名带进程号（并行流程会清 `_zf10*_bak`）。
"""
import hashlib
import io
import os
import random
import shutil
import subprocess
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from PngRecolor import write_png   # noqa: E402

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

ROOT = r"E:\PotatoST"
ZT = os.path.join(ROOT, "build", "zftools")
TEXB = os.path.join(ROOT, r"src\main\resources\assets\potato_s_t\textures\block")
MDIR = os.path.join(ROOT, r"src\main\resources\assets\potato_s_t\models\block")
DOCS = os.path.join(ROOT, "docs")
BAK = os.path.join(ZT, "_zf108_falsify_bak_%d" % os.getpid())
VERIFY = os.path.join(ZT, "_zf108_verify.py")

fails = []


def sha(p):
    return hashlib.sha256(open(p, "rb").read()).hexdigest()


def read(p):
    return io.open(p, encoding="utf-8").read()


def write(p, t):
    io.open(p, "w", encoding="utf-8", newline=u"").write(t)


def text_sub(path, old, new, count=1):
    t = read(path)
    if t.count(old) != count:
        return False
    write(path, t.replace(old, new, count))
    return True


def noise_png(path, seed=7):
    u"""写一张 16×16 的"糊图"（随机色，模拟旧那种 228 色的噪声图）"""
    rnd = random.Random(seed)
    buf = bytearray()
    for _ in range(16 * 16):
        buf += bytes((rnd.randrange(256), rnd.randrange(256), rnd.randrange(256), 255))
    write_png(path, 16, 16, bytes(buf))
    return True


def asym_png(path):
    u"""写一张 16×16 但**上下不对称**的图（专门破"镜像对称"那条断言）"""
    base = (0x4a, 0x4a, 0x52, 255)
    hi = (0x9a, 0xa2, 0xac, 255)
    buf = bytearray()
    for y in range(16):
        for x in range(16):
            buf += bytes(hi if (y == 0 and x < 8) else base)
    write_png(path, 16, 16, bytes(buf))
    return True


KNIVES = [
    (u"K92 把 north.obj 的 vt 退回旧的 4×4 小格",
     lambda: text_sub(os.path.join(MDIR, u"alloy_smelter_north.obj"),
                      u"vt 1.0000 1.0000", u"vt 0.2500 1.0000", count=84)),
    (u"K93 改一行 `v ` 顶点（证明『只有 vt 许变』那条会咬）",
     lambda: text_sub(os.path.join(MDIR, u"alloy_smelter_east.obj"),
                      u"\nv 0.0000 2.0000 0.5632\n",
                      u"\nv 0.0001 2.0000 0.5632\n", count=1)),
    (u"K94 把 MTL 的 map_Kd 退回借来的 heat_resistant_metal_block",
     lambda: text_sub(os.path.join(MDIR, u"alloy_smelter.mtl"),
                      u"map_Kd potato_s_t:block/alloy_smelter_formed",
                      u"map_Kd potato_s_t:block/heat_resistant_metal_block")),
    (u"K95 把机体图写成上下不对称（破镜像对称那条）",
     lambda: asym_png(os.path.join(TEXB, u"alloy_smelter_formed.png"))),
    (u"K96 把主控图写成 16×16 随机噪声（= 又画糊了）",
     lambda: noise_png(os.path.join(TEXB, u"alloy_smelter.png"))),
    (u"K97 把贴图清单里合金炉那行的新贴图名抹掉（两处都要抹，不然还有一处提到它）",
     lambda: text_sub(os.path.join(DOCS, u"贴图清单.md"),
                      u"`alloy_smelter_formed.png`", u"`alloy_smelter.png`", count=2)),
    (u"K98 把主控模型抄错贴图（指向 wiring_block）",
     lambda: text_sub(os.path.join(MDIR, u"alloy_smelter.json"),
                      u'"all": "potato_s_t:block/alloy_smelter"',
                      u'"all": "potato_s_t:block/wiring_block"')),
]

TARGETS = [os.path.join(MDIR, n) for n in
           (u"alloy_smelter_north.obj", u"alloy_smelter_east.obj", u"alloy_smelter_south.obj",
            u"alloy_smelter_west.obj", u"alloy_smelter.mtl", u"alloy_smelter.json")]
TARGETS += [os.path.join(TEXB, n) for n in (u"alloy_smelter.png", u"alloy_smelter_formed.png")]
TARGETS += [os.path.join(DOCS, u"贴图清单.md")]


def run_gate():
    try:
        p = subprocess.run([sys.executable, VERIFY], stdout=subprocess.PIPE,
                           stderr=subprocess.STDOUT, timeout=180)
    except subprocess.TimeoutExpired:
        return -9, u"**校验器挂死（180 秒超时）** —— 坏数据下必须报错，不许卡死"
    return p.returncode, p.stdout.decode("utf-8", "replace")


def main():
    only = sys.argv[1:] or None
    if os.path.isdir(BAK):
        shutil.rmtree(BAK)
    os.makedirs(BAK)
    print(u"================ 基线 ================")
    rc, out = run_gate()
    print(u"  校验器退出码 %s（必须 0）" % rc)
    if rc != 0:
        for l in [l for l in out.split(u"\n") if l.strip().startswith(u"!!")][:6]:
            print(u"    %s" % l.strip()[:120])
        print(u"  [STOP] 基线就不是绿的 —— 不许挥刀")
        return 1

    manifest = []
    print(u"")
    print(u"================ 备份（逐份核副本自己的哈希）================")
    for t in TARGETS:
        if not os.path.isfile(t):
            fails.append(u"缺文件：%s" % t)
            continue
        dst = os.path.join(BAK, os.path.basename(t) + u"." + hashlib.md5(
            t.encode("utf-8")).hexdigest()[:8])
        shutil.copy2(t, dst)
        ok = sha(t) == sha(dst)
        manifest.append((t, dst, sha(dst)))
        print(u"  [%s] %-34s %s" % (u"OK" if ok else u"FAIL", os.path.basename(dst), sha(dst)[:16]))
        if not ok:
            fails.append(u"备份哈希不符：%s" % t)

    def restore():
        for t, dst, h in manifest:
            if not os.path.isfile(dst):
                fails.append(u"备份副本不见了：%s" % dst)
                continue
            shutil.copy2(dst, t)
            if sha(t) != h:
                fails.append(u"还原后哈希不符：%s" % t)

    print(u"")
    print(u"================ 逐刀 ================")
    for name, mutate in KNIVES:
        if only and not any(o in name for o in only):
            continue
        before = {t: sha(t) for t, _d, _h in manifest}
        try:
            acted = mutate()
        except Exception as e:
            acted = False
            print(u"  [SKIP] %s —— 变更抛异常 %s" % (name, e))
        if not acted:
            print(u"  [SKIP] %s —— 锚点没命中" % name)
            fails.append(u"锚点不唯一：%s" % name)
            restore()
            continue
        rc, out = run_gate()
        caught = rc != 0
        print(u"  [%s] %s" % (u"OK" if caught else u"FAIL", name))
        print(u"         ↳ 校验器退出码 %s（必须非 0）" % rc)
        for l in [l for l in out.split(u"\n") if l.strip().startswith(u"!!")][:3]:
            print(u"         ↳ %s" % l.strip()[:120])
        if not caught:
            fails.append(name)
        restore()
        rc2, _ = run_gate()
        back = all(sha(t) == h for t, h in before.items())
        print(u"         ↳ 还原后哈希一致 %s，校验器回到全绿 %s"
              % (u"✓" if back else u"✗", u"✓" if rc2 == 0 else u"✗"))
        if not (back and rc2 == 0):
            fails.append(u"还原失败：%s" % name)
        print(u"")

    print(u"================ 收尾 ================")
    for t, _dst, h in manifest:
        same = sha(t) == h
        print(u"  [%s] %s 回到备份哈希" % (u"OK" if same else u"FAIL", os.path.basename(t)))
        if not same:
            fails.append(u"收尾哈希不符：%s" % t)
    print(u"")
    print(u"失败项 = %d" % len(fails))
    for f in fails:
        print(u"  !! " + f)
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())
