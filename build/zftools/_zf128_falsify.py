# -*- coding: utf-8 -*-
u"""_zf128_falsify.py —— ZF128 的反证刀（K223~K226，4 把）

口径同前：基线绿 → 改一处语义 ⇒ 门必须 FAIL 且**咬住指定的那一条** ⇒ 逐字节还原 ⇒ 收尾回到全绿。
本轮同时跑**两份**常驻校验（`_zf127_verify.py` + `_zf128_verify.py`），因为其中一把刀要咬的是前者的自洽判据。

刀面：
  K223 图标改回微型粉碎机（"成就栏换成毒马铃薯"没了）
  K224 判据**也**换成毒马铃薯（"成就还是粉碎机"没了）
  K225 生成器那两个常量又并回一个（重跑会把图标写回去）
  K226 `_zf90_verify.py` 的待画数改回手写 15（自洽性没了 ⇒ ZF127 的 F4 应当咬住）
"""
import hashlib
import os
import subprocess
import sys

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

ROOT = r"E:\PotatoST"
ZT = os.path.join(ROOT, r"build\zftools")
ADV = os.path.join(ROOT, r"src\main\resources\data\potato_s_t\advancement\new_beginning.json")
ADVGEN = os.path.join(ZT, u"_zf107_adv.py")
Z90 = os.path.join(ZT, u"_zf90_verify.py")
VERIFIES = [os.path.join(ZT, u"_zf127_verify.py"), os.path.join(ZT, u"_zf128_verify.py")]

KNIVES = [
    dict(id="K223", why=u"图标改回微型粉碎机（用户要的毒马铃薯没了）", path=ADV,
         old=u'"id": "minecraft:poisonous_potato"', new=u'"id": "potato_s_t:micro_crusher"',
         expect=u"A1 display.icon.id = minecraft:poisonous_potato"),
    dict(id="K224", why=u"判据**也**换成毒马铃薯（「成就还是粉碎机」没了）", path=ADV,
         old=u'"items": "potato_s_t:micro_crusher"', new=u'"items": "minecraft:poisonous_potato"',
         expect=u"A3 **判据仍是** potato_s_t:micro_crusher"),
    dict(id="K225", why=u"生成器那两个常量又并回一个（重跑会把图标写回粉碎机）", path=ADVGEN,
         old=u'ROOT_ICON_DISPLAY = "minecraft:poisonous_potato"',
         new=u'ROOT_ICON_DISPLAY = "potato_s_t:micro_crusher"',
         expect=u"B4 `_zf107_adv.py`：判据与图标拆成两个常量"),
    dict(id="K226", why=u"`_zf90_verify.py` 的待画数改回手写 15（自洽性没了）", path=Z90,
         old=u'check(u"英文公告已改成 13 models still do this", u"13 models still do this" in ann)',
         new=u'check(u"英文公告已改成 15 models still do this", u"15 models still do this" in ann)',
         expect=u"F4 `_zf90_verify.py`"),
]

fails = []


def run():
    outs, rc_all = [], 0
    for v in VERIFIES:
        try:
            r = subprocess.run([sys.executable, v], stdout=subprocess.PIPE,
                               stderr=subprocess.STDOUT, timeout=300,
                               env=dict(os.environ, PYTHONIOENCODING=u"utf-8"))
            outs.append(r.stdout.decode("utf-8", "replace"))
            rc_all = rc_all or r.returncode
        except subprocess.TimeoutExpired:
            outs.append(u"**超时**")
            rc_all = 99
    return rc_all, u"\n".join(outs)


def summary(out):
    lines = [l for l in out.split(u"\n") if u"通过" in l and u"失败" in l]
    return u" / ".join(l.strip() for l in lines) or u"?"


def bitten(out, expect):
    return any(l.strip().startswith(u"!!") and expect in l for l in out.split(u"\n"))


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
        orig = open(path, "rb").read()
        before = hashlib.sha1(orig).hexdigest()
        try:
            text = orig.decode("utf-8")
            nl = u"\r\n" if u"\r\n" in text else u"\n"
            old = k["old"].replace(u"\n", nl)
            new = k["new"].replace(u"\n", nl)
            if text.count(old) != 1:
                fails.append(u"%s：锚点命中 %d 次" % (k["id"], text.count(old)))
                print(u"  [BAD]  %s 锚点命中 %d 次" % (k["id"], text.count(old)))
                continue
            open(path, "wb").write(text.replace(old, new, 1).encode("utf-8"))
            rc, out = run()
        finally:
            open(path, "wb").write(orig)
        after = hashlib.sha1(open(path, "rb").read()).hexdigest()
        if after != before:
            fails.append(u"%s：还原失败" % k["id"])
            break
        if rc != 0 and bitten(out, k["expect"]):
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


if __name__ == u"__main__":
    sys.exit(main())
