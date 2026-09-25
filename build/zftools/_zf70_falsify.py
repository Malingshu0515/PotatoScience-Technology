# -*- coding: utf-8 -*-
"""_zf70_falsify.py —— 反证：把「和」退回成「或」的写法，看校验抓不抓得住

把 stronger_power.json 的 requirements 从
    [["generator"], ["power_capturer"]]      （外层 AND：两个都要）
改回
    [["generator", "power_capturer"]]        （内层 OR：任选其一 —— 本轮探针真踩过的坑）

跑完必须**原样还原**（用改前字节写回，并核 SHA1）。
"""
import hashlib
import io
import os
import subprocess
import sys

P = r"E:\PotatoST\src\main\resources\data\potato_s_t\advancement\stronger_power.json"
VERIFY = r"E:\PotatoST\build\zftools\_zf70_verify.py"

GOOD = u'  "requirements": [\n    [\n      "generator"\n    ],\n    [\n      "power_capturer"\n    ]\n  ],'
BAD = u'  "requirements": [\n    [\n      "generator",\n      "power_capturer"\n    ]\n  ],'


def sha1(b):
    return hashlib.sha1(b).hexdigest()


def main():
    orig = io.open(P, "rb").read()
    text = orig.decode("utf-8")
    if text.count(GOOD) != 1:
        print(u"锚点没命中（找到 %d 次），反证未执行" % text.count(GOOD))
        return 1
    io.open(P, "w", encoding="utf-8", newline="\n").write(text.replace(GOOD, BAD, 1))
    print(u"已把 requirements 改成 [['generator', 'power_capturer']]（= 或）")
    try:
        env = dict(os.environ)
        env["PYTHONIOENCODING"] = "utf-8"
        r = subprocess.run([sys.executable, VERIFY], capture_output=True, env=env)
        out = r.stdout.decode("utf-8", "replace")
        bad_lines = [l for l in out.split("\n") if "[FAIL]" in l or u"检查项" in l or u"失败项 =" in l]
        print(u"\n".join(bad_lines))
        print(u"退出码 = %d" % r.returncode)
    finally:
        io.open(P, "wb").write(orig)
        back = io.open(P, "rb").read()
        print(u"\n已还原：%s（%s）" % (sha1(back)[:12], u"与改前一致" if back == orig else u"**不一致！**"))
    return 0


if __name__ == "__main__":
    sys.exit(main())
