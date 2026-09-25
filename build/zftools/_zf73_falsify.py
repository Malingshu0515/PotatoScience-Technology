# -*- coding: utf-8 -*-
u"""_zf73_falsify.py —— ZF73 反证：把真值改坏，校验**必须**挂（四刀，两刀砍源码）

  1. **源码**：`ModFluids.isGas` 的正向列举里删掉一个气体（氧气的源）⇒ A14 必须 FAIL
  2. **资源**：配方 `"count": 1` → `2`（改成"吃 2 出 2"）⇒ B10 必须 FAIL
  3. **资源**：`crude_oil_still.png` 换成**假 PNG**（证明"真 PNG 头"这条断言不是摆设）⇒ B1 必须 FAIL
  4. **语言**：从 `zh_cn.json` 删掉 `tooltip.potato_s_t.oil_bucket.rule` 一行 ⇒ B12/B11 必须 FAIL

每刀都先读原字节到内存、改坏、跑校验、再**按字节还原**并核 SHA1；只要有一刀"改坏了却不挂"，
脚本自己报 FAIL —— 那说明断言是摆设。
"""
import hashlib
import io
import os
import subprocess
import sys

PROJ = r"E:\PotatoST"
VERIFY = os.path.join(PROJ, u"build", u"zftools", u"_zf73_verify.py")
FLUIDS = os.path.join(PROJ, u"src", u"main", u"java", u"com", u"potatost", u"mod", u"ModFluids.java")
RECIPE = os.path.join(PROJ, u"src", u"main", u"resources", u"data", u"potato_s_t", u"recipe",
                      u"oil_bucket.json")
PNG = os.path.join(PROJ, u"src", u"main", u"resources", u"assets", u"potato_s_t", u"textures",
                   u"block", u"crude_oil_still.png")
ZH = os.path.join(PROJ, u"src", u"main", u"resources", u"assets", u"potato_s_t", u"lang",
                  u"zh_cn.json")

CASES = [
    (u"1 源码 · isGas 正向列举里挖掉氧气", FLUIDS,
     u"return fluid == OXYGEN.get() || fluid == FLOWING_OXYGEN.get()",
     u"return fluid == FLOWING_OXYGEN.get()", u"A14"),
    (u"2 配方 · 产出 1 个改成 2 个", RECIPE,
     u'"count": 1', u'"count": 2', u"B10"),
    (u"3 贴图 · 真 PNG 换成假 PNG", PNG,
     b"\x89PNG\r\n\x1a\n", b"NOTAPNG!", u"B1"),
    (u"4 语言 · 删掉油桶规则键", ZH,
     u'  "tooltip.potato_s_t.oil_bucket.rule":', u'  "tooltip.potato_s_t.oil_bucket.RULE_OFF":',
     u"B12"),
]


def sha1_bytes(data):
    return hashlib.sha1(data).hexdigest()


def run_verify():
    env = dict(os.environ)
    env["PYTHONIOENCODING"] = "utf-8"
    proc = subprocess.run([sys.executable, u"-X", u"utf8", VERIFY],
                          stdout=subprocess.PIPE, stderr=subprocess.STDOUT, env=env)
    return proc.returncode, proc.stdout.decode("utf-8", "replace")


def main():
    bad = []
    print(u"反证开始：%d 刀\n" % len(CASES))
    for label, path, old, new, expect in CASES:
        with io.open(path, "rb") as fh:
            original = fh.read()
        before_sha = sha1_bytes(original)
        if isinstance(old, bytes):
            hits = original.count(old)
            mutated = original.replace(old, new, 1)
        else:
            text = original.decode("utf-8")
            hits = text.count(old)
            mutated = text.replace(old, new, 1).encode("utf-8")
        if hits != 1:
            bad.append(u"%s：锚点命中 %d 次，无法反证" % (label, hits))
            print(u"  [SKIP] %s（锚点 %d 次）" % (label, hits))
            continue
        try:
            with io.open(path, "wb") as fh:
                fh.write(mutated)
            rc, out = run_verify()
            caught = (rc != 0) and any((u"[FAIL]" in ln and expect in ln) for ln in out.split(u"\n"))
            first = u""
            for ln in out.split(u"\n"):
                if u"[FAIL]" in ln:
                    first = ln.strip()
                    break
            if caught:
                print(u"  [OK]   %s ⇒ 校验挂在这条: %s" % (label, first))
            else:
                bad.append(u"%s：改坏了却没挂（rc=%d）" % (label, rc))
                print(u"  [FAIL] %s ⇒ 没抓到（rc=%d, 首条 FAIL=%s）" % (label, rc, first))
        finally:
            with io.open(path, "wb") as fh:
                fh.write(original)
            same = sha1_bytes(open(path, "rb").read()) == before_sha
            print(u"         还原: %s  %s" % (u"逐字节相同" if same else u"!! 不一致", before_sha[:12]))
            if not same:
                bad.append(u"%s：还原后哈希不一致！" % label)

    print(u"\n--- 还原后复跑校验（应当全绿） ---")
    rc, out = run_verify()
    tail = [ln for ln in out.split(u"\n") if u"检查项 =" in ln]
    print(u"  " + (tail[0].strip() if tail else u"(没拿到汇总行)"))
    if rc != 0:
        bad.append(u"还原后校验仍不绿（rc=%d）" % rc)

    print(u"\n反证刀数 = %d   异常 = %d" % (len(CASES), len(bad)))
    for b in bad:
        print(u"  !! " + b)
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
