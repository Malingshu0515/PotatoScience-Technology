# -*- coding: utf-8 -*-
u"""_zf74_falsify.py —— ZF74 反证：四刀（两刀砍资源、一刀砍源码、一刀砍文档），每刀必须被抓住"""
import hashlib
import io
import os
import subprocess
import sys

PROJ = r"E:\PotatoST"
VERIFY = os.path.join(PROJ, u"build", u"zftools", u"_zf74_verify.py")
GAS = os.path.join(PROJ, u"src", u"main", u"resources", u"data", u"c", u"tags", u"fluid",
                   u"gaseous.json")
OIL = os.path.join(PROJ, u"src", u"main", u"resources", u"data", u"c", u"tags", u"fluid",
                   u"crude_oil.json")
FLUIDS = os.path.join(PROJ, u"src", u"main", u"java", u"com", u"potatost", u"mod", u"ModFluids.java")
ARCH = os.path.join(PROJ, u"docs", u"开发档案.md")

CASES = [
    (u"1 资源 · gaseous 少挂一个氧", GAS,
     u'    "potato_s_t:oxygen",\n', u"", u"A gaseous.json"),
    (u"2 资源 · crude_oil 改成 replace:true（会覆盖别人）", OIL,
     u'"replace": false', u'"replace": true', u"A crude_oil.json"),
    (u"3 源码 · isGas 不再认 #c:gaseous", FLUIDS,
     u"return fluid.defaultFluidState().is(Tags.Fluids.GASEOUS);", u"return false;", u"B2"),
    (u"4 文档 · 档案里删掉作废声明", ARCH,
     u"2a35a9eeda99", u"XXXXXXXXXXXXXXXX", u"C7"),
]


def sha1b(data):
    return hashlib.sha1(data).hexdigest()


def run():
    env = dict(os.environ)
    env["PYTHONIOENCODING"] = "utf-8"
    p = subprocess.run([sys.executable, u"-X", u"utf8", VERIFY],
                       stdout=subprocess.PIPE, stderr=subprocess.STDOUT, env=env)
    return p.returncode, p.stdout.decode("utf-8", "replace")


def main():
    bad = []
    print(u"反证开始：%d 刀\n" % len(CASES))
    for label, path, old, new, expect in CASES:
        with io.open(path, "rb") as fh:
            original = fh.read()
        before = sha1b(original)
        text = original.decode("utf-8")
        n = text.count(old)
        if n < 1:
            bad.append(u"%s：锚点 0 次" % label)
            print(u"  [SKIP] %s（锚点 0 次）" % label)
            continue
        try:
            io.open(path, "wb").write(text.replace(old, new, n if expect == u"C7" else 1).encode("utf-8"))
            rc, out = run()
            caught = (rc != 0) and any((u"[FAIL]" in ln and expect in ln) for ln in out.split(u"\n"))
            first = u""
            for ln in out.split(u"\n"):
                if u"[FAIL]" in ln:
                    first = ln.strip()
                    break
            if caught:
                print(u"  [OK]   %s ⇒ %s" % (label, first))
            else:
                bad.append(u"%s：没抓到（rc=%d）" % (label, rc))
                print(u"  [FAIL] %s ⇒ 没抓到（rc=%d，首条 %s）" % (label, rc, first))
        finally:
            io.open(path, "wb").write(original)
            same = sha1b(io.open(path, "rb").read()) == before
            print(u"         还原: %s  %s" % (u"逐字节相同" if same else u"!! 不一致", before[:12]))
            if not same:
                bad.append(u"%s：还原后哈希不一致" % label)
    print(u"\n--- 还原后复跑 ---")
    rc, out = run()
    print(u"  " + ([ln.strip() for ln in out.split(u"\n") if u"检查项 =" in ln] or [u"(无汇总)"])[0])
    if rc != 0:
        bad.append(u"还原后仍不绿")
    print(u"\n反证刀数 = %d   异常 = %d" % (len(CASES), len(bad)))
    for b in bad:
        print(u"  !! " + b)
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
