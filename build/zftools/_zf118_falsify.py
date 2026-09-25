# -*- coding: utf-8 -*-
u"""_zf118_falsify.py —— ZF118 的反证刀（K150~K156，7 把）

口径同前：先确认基线绿 → 改一处语义 ⇒ 门必须 FAIL 且**咬住指定的那条检查** ⇒
逐字节还原 ⇒ 收尾回到全绿。一把刀 180 秒超时（§4.77）。

刀面覆盖这一轮说出口的每一句话：
  图纸（pattern 被换 / 按位置核不出）、材料（中心那颗星 / 四角的岩浆块）、产物数量、
  账目（配方文件被删）、**生成器表与盘脱钩**（改了表不重跑）、文档（公告退回 no recipe yet）。
"""
import hashlib
import io
import os
import subprocess
import sys

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

ROOT = r"E:\PotatoST"
ZT = os.path.join(ROOT, r"build\zftools")
RDIR = os.path.join(ROOT, r"src\main\resources\data\potato_s_t\recipe")
GEN = os.path.join(ZT, u"_zf45_recipes.py")
ANN = os.path.join(ROOT, r"docs\UpdateAnnouncement_EN.md")
VERIFY = os.path.join(ZT, u"_zf118_verify.py")

REC = os.path.join(RDIR, "starfall_pendant.json")
PAT_OLD = u'  "pattern": [\n    "MSM",\n    "SNS",\n    "MSM"\n  ],'
PAT_NEW = u'  "pattern": [\n    "SMS",\n    "MNM",\n    "SMS"\n  ],'

KNIVES = [
    dict(id="K150", why=u"图纸的行列被换掉（pattern 不再是那张图）", path=REC,
         old=PAT_OLD, new=PAT_NEW, expect=u"A4 pattern 逐格"),
    dict(id="K151", why=u"中心那颗星换成下界砖", path=REC,
         old=u'"item": "minecraft:nether_star"', new=u'"item": "minecraft:nether_brick"',
         expect=u"A7 N = 下界之星"),
    dict(id="K152", why=u"产物数量偷偷改成 4", path=REC,
         old=u'"result": {\n    "id": "potato_s_t:starfall_pendant",\n    "count": 1\n  }',
         new=u'"result": {\n    "id": "potato_s_t:starfall_pendant",\n    "count": 4\n  }',
         expect=u"A9 result"),
    dict(id="K153", why=u"四角的岩浆块换成岩浆膏", path=REC,
         old=u'"item": "minecraft:magma_block"', new=u'"item": "minecraft:magma_cream"',
         expect=u"A6 M = 岩浆块"),
    dict(id="K154", why=u"配方文件被删掉", path=REC, mode="delete",
         expect=u"A1 starfall_pendant.json 在"),
    dict(id="K155", why=u"生成器表被改却没重跑（表与盘脱钩）", path=GEN,
         old=u'              "N": ("item", "minecraft:nether_star")}),',
         new=u'              "N": ("item", "minecraft:nether_brick")}),',
         expect=u"A13 表重跑 == 盘上 JSON"),
    dict(id="K156", why=u"英文公告退回「no recipe yet」", path=ANN,
         old=u"the meteor pendant (4 Magma Blocks + 4 Star Steel Ingots + a Nether Star)",
         new=u"the meteor pendant (no recipe yet)",
         expect=u"D5 英文公告不再说星轨坠"),
]

fails, notes = [], []


def run():
    try:
        r = subprocess.run([sys.executable, VERIFY], stdout=subprocess.PIPE,
                           stderr=subprocess.STDOUT, timeout=300)
        return r.returncode, r.stdout.decode("utf-8", "replace")
    except subprocess.TimeoutExpired:
        return 99, u"**超时**"


def summary(out):
    line = [l for l in out.split(u"\n") if u"通过" in l and u"失败" in l]
    return line[-1].strip() if line else u"?"


def main():
    rc, out = run()
    print(u"基线：%s（退出码 %d）" % (summary(out), rc))
    if rc != 0:
        print(u"  [STOP] 基线不绿，先修")
        for l in out.split(u"\n"):
            if l.strip().startswith(u"!!"):
                print(u"    " + l.strip())
        return 1
    n_ok = 0
    for k in KNIVES:
        path = k["path"]
        orig = open(path, "rb").read() if os.path.exists(path) else None
        before = hashlib.sha1(orig).hexdigest() if orig is not None else u"(不存在)"
        try:
            if k.get("mode") == "delete":
                os.remove(path)
            else:
                text = orig.decode("utf-8")
                if text.count(k["old"]) != 1:
                    fails.append(u"%s：锚点命中 %d 次" % (k["id"], text.count(k["old"])))
                    continue
                open(path, "wb").write(text.replace(k["old"], k["new"], 1).encode("utf-8"))
            rc, out = run()
        finally:
            if orig is None:
                if os.path.exists(path):
                    os.remove(path)
            else:
                open(path, "wb").write(orig)
        after = hashlib.sha1(open(path, "rb").read()).hexdigest() if os.path.exists(path) else u"(不存在)"
        if after != before:
            fails.append(u"%s：还原失败" % k["id"])
            break
        if rc != 0 and k["expect"] in out:
            n_ok += 1
            print(u"  [OK]   %s %s ⇒ 咬住「%s」" % (k["id"], k["why"], k["expect"]))
        else:
            print(u"  [BAD]  %s %s（退出码 %d）" % (k["id"], k["why"], rc))
            fails.append(u"%s %s ⇒ %s" % (k["id"], k["why"],
                                          u"门还是绿的" if rc == 0 else u"咬错了检查"))
    rc, out = run()
    print(u"收尾：%s（退出码 %d）" % (summary(out), rc))
    if rc != 0:
        fails.append(u"收尾不是全绿")
    print(u"刀 = %d，咬住 = %d，失败项 = %d" % (len(KNIVES), n_ok, len(fails)))
    for f in fails:
        print(u"  !! " + f)
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())
