# -*- coding: utf-8 -*-
r"""_zf89_presupply.py —— 给 zf89_pre 补两份改前件（§10 的补账，照 ZF78/ZF83 先例）

本轮出现一个**时序**问题，如实记下来：
  · `zf89_pre` 的快照建于 23:05:5x（9 份）；
  · 用户的 `石脑油.png` 的落盘时间是 **23:05:08**，但快照那一刻它还没出现在枚举里
    ⇒ 快照里没有它的旧图副本，也没有它自己。
  · 更早的 `汽油.png`（23:00）在快照里 ✅。

补法（**不是凭记忆**，是从"改前那一刻的成品 jar"里取，可逐字节验证）：
  ① `naphtha_still.png` / `naphtha_flow.png` 两份旧图 ← `zf89_pre\release\PotatoST-0.11.jar`
     （那个 jar 就是改前的成品 `f86c569c…`，里面的条目哈希与转换脚本打印的"改前 sha"必须一致）；
  ② 用户原图 `石脑油.png` ← `build/用户素材/naphtha.png`（转档时原样挪过去的，字节没动过），
     直接复制进快照，并记哈希 —— 它本来就是"用户的原始字节"，不参与任何改写。
两份都要**断言哈希**，对不上就报错，绝不静默。
"""
import hashlib
import io
import json
import os
import shutil
import sys
import zipfile

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

ROOT = r"E:\PotatoST"
BK = r"C:\PotatoST救援\zf89_pre"
JAR = os.path.join(BK, r"release\PotatoST-0.11.jar")
BLK = os.path.join(BK, r"src\main\resources\assets\potato_s_t\textures\block")
USERART = os.path.join(ROOT, "build", u"用户素材")
fails = []


def sha1b(b):
    return hashlib.sha1(b).hexdigest()


def main():
    os.makedirs(BLK, exist_ok=True)
    lines = [u"zf89_pre 补账说明（§10）", u"",
             u"一、为什么补：用户的 `石脑油.png` 落盘时间 23:05:08，快照枚举时它还没出现，",
             u"    所以快照里缺 `naphtha_still/flow.png` 的旧图与 `石脑油.png` 本身。",
             u"    汽油那张（汽油.png / gasoline_still / gasoline_flow）当次已在快照里。", u"",
             u"二、旧图从哪来：快照自带的改前成品 jar（就是 `f86c569c…` 那个），逐条核哈希。", u""]

    with zipfile.ZipFile(JAR) as zf:
        for entry, name in ((u"assets/potato_s_t/textures/block/naphtha_still.png", u"naphtha_still.png"),
                            (u"assets/potato_s_t/textures/block/naphtha_flow.png", u"naphtha_flow.png")):
            data = zf.read(entry)
            h = sha1b(data)
            dst = os.path.join(BLK, name)
            io.open(dst, "wb").write(data)
            if sha1b(io.open(dst, "rb").read()) != h:
                fails.append(u"%s 写出后哈希不一致" % name)
            lines.append(u"%s  %10d  %s  ← jar 里的 %s" % (h, len(data), name, entry))
            print(u"  [OK]   %s  %s…（%d 字节，来自改前 jar）" % (name, h[:8], len(data)))

    src = os.path.join(USERART, u"naphtha.png")
    if not os.path.exists(src):
        fails.append(u"缺 build/用户素材/naphtha.png（用户的原始字节）")
    else:
        dst = os.path.join(BLK, u"石脑油.png")
        shutil.copy2(src, dst)
        h = sha1b(io.open(dst, "rb").read())
        if h != sha1b(io.open(src, "rb").read()):
            fails.append(u"石脑油.png 拷贝后哈希不一致")
        lines.append(u"%s  %10d  %s  ← build/用户素材/naphtha.png（用户原图，字节未改）"
                     % (h, os.path.getsize(dst), u"石脑油.png"))
        print(u"  [OK]   石脑油.png  %s…（用户原图 %d 字节）" % (h[:8], os.path.getsize(dst)))

    # 来源凭据里的 sha1 必须与留档原图一致（这条也是常驻校验要查的）
    prov = json.loads(io.open(os.path.join(USERART, u"_来源凭据.json"), encoding="utf-8").read())
    for key in (u"naphtha.png", u"gasoline.png"):
        real = sha1b(open(os.path.join(USERART, key), "rb").read())
        if prov.get(key, {}).get("sha1") != real:
            fails.append(u"凭据里 %s 的 sha1 与留档原图不一致" % key)
        else:
            print(u"  [OK]   凭据 %s sha1 与留档原图一致（%s…）" % (key, real[:8]))

    io.open(os.path.join(BK, u"_补说明.txt"), "w", encoding="utf-8",
            newline=u"\n").write(u"\n".join(lines) + u"\n")
    print(u"\n补账写入 %s\\_补说明.txt" % BK)
    print(u"失败项 = %d" % len(fails))
    for f in fails:
        print(u"  !! " + f)
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())
