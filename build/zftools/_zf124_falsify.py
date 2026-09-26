# -*- coding: utf-8 -*-
u"""_zf124_falsify.py —— ZF124 的反证刀（K183~K186，4 把）

口径同前：基线绿 → 改一处语义 ⇒ 门必须 FAIL 且**咬住指定的那一条**（串必须出现在以 `!!`
开头的 FAIL 行里）⇒ 逐字节还原 ⇒ 收尾回到全绿。

刀面：
  · 把中文标题改回「新的开始！」（复现改名之前的样子）；
  · 只把 en_us 改回去（"四语言都改了"这条被打破）；
  · 把创造页图标改回铝锭；
  · 把 `_zf70_verify.py` 的目标值改回去（往轮门又会红）。
"""
import hashlib
import io
import os
import re
import subprocess
import sys

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

ROOT = r"E:\PotatoST"
ZT = os.path.join(ROOT, r"build\zftools")
LANG = os.path.join(ROOT, r"src\main\resources\assets\potato_s_t\lang")
ITEMS = os.path.join(ROOT, r"src\main\java\com\potatost\mod\ModItems.java")
Z70 = os.path.join(ZT, u"_zf70_verify.py")
VERIFY = os.path.join(ZT, u"_zf124_verify.py")

TITLE_RE = u'("advancements\\.potato_s_t\\.new_beginning\\.title"\\s*:\\s*)"PotatoS&T"'

KNIVES = [
    dict(id="K183", why=u"把 zh_cn 的页签名改回「新的开始！」", path=os.path.join(LANG, u"zh_cn.json"),
         mode="resub", old_re=TITLE_RE, new_re=u'\\1"新的开始！"',
         expect=u"zh_cn：标题 = PotatoS&T"),
    dict(id="K184", why=u"只把 en_us 改回 A New Beginning!（「四语言都改了」被打破）",
         path=os.path.join(LANG, u"en_us.json"),
         mode="resub", old_re=TITLE_RE, new_re=u'\\1"A New Beginning!"',
         expect=u"en_us：标题 = PotatoS&T"),
    dict(id="K185", why=u"创造页图标改回铝锭", path=ITEMS,
         old=u".icon(() -> new ItemStack(STARFALL_PENDANT.get()))",
         new=u".icon(() -> new ItemStack(ALUMINUM_INGOT.get()))",
         expect=u".icon(...) 用的是星轨坠"),
    dict(id="K186", why=u"把 _zf70_verify 的目标值改回去（往轮门又会红）", path=Z70,
         old=u'title_zh=u"PotatoS&T",', new=u'title_zh=u"新的开始！",',
         expect=u"_zf70 的根成就 title_zh 已改成 PotatoS&T"),
]

fails = []


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
            if k.get("mode") == "resub":
                new_text, n = re.subn(k["old_re"], k["new_re"], text, count=1)
                if n != 1:
                    fails.append(u"%s：正则命中 %d 次" % (k["id"], n))
                    continue
                open(path, "wb").write(new_text.encode("utf-8"))
            else:
                if text.count(k["old"]) != 1:
                    fails.append(u"%s：锚点命中 %d 次" % (k["id"], text.count(k["old"])))
                    continue
                open(path, "wb").write(text.replace(k["old"], k["new"], 1).encode("utf-8"))
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


if __name__ == "__main__":
    sys.exit(main())
