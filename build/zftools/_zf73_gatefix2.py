# -*- coding: utf-8 -*-
r"""_zf73_gatefix2.py —— 把 `_zf69_verify.py` 里写死的 jar 路径改成"跟着版本走"

最后一条红：`jar 里定形配方 = 29 条（实际 28）` —— 原因是那个脚本里写死了
`build\libs\potato_s_t-0.10.jar` 与 `release\PotatoST-0.10.jar` 两个路径；
ZF73 把版本提到 0.11 之后，它读的还是**旧产物**（28 条配方）。
改成按 `gradle.properties` 的 `mod_version` 拼路径，并回退到"release 目录里最新的 PotatoST-*.jar"。
"""
import glob
import io
import os
import sys

PATH = r"E:\PotatoST\build\zftools\_zf69_verify.py"
PROJ = r"E:\PotatoST"

OLD_BUILD = u'BUILD_JAR = os.path.join(ROOT, r"build\\libs\\potato_s_t-0.10.jar")'
NEW_BUILD = u'''def _mod_version():
    """从 gradle.properties 读版本 —— 0.10 之后产物名跟着版本走，别再写死。"""
    try:
        with io.open(os.path.join(ROOT, "gradle.properties"), "r", encoding="utf-8") as fh:
            for line in fh:
                if line.startswith("mod_version="):
                    return line.strip().split("=", 1)[1]
    except Exception:
        pass
    return "0.10"


def _newest(patterns):
    hits = []
    for p in patterns:
        hits.extend(glob.glob(p))
    hits = [h for h in hits if os.path.isfile(h)]
    hits.sort(key=lambda p: os.path.getmtime(p), reverse=True)
    return hits[0] if hits else patterns[0]


MOD_VERSION = _mod_version()
BUILD_JAR = _newest([os.path.join(ROOT, r"build\\libs\\potato_s_t-%s.jar" % MOD_VERSION),
                     os.path.join(ROOT, r"build\\libs\\potato_s_t-*.jar")])'''

OLD_REL = u'release = os.path.join(ROOT, r"release\\PotatoST-0.10.jar")'
NEW_REL = u'''release = _newest([os.path.join(ROOT, r"release\\PotatoST-%s.jar" % MOD_VERSION),
                        os.path.join(ROOT, r"release\\PotatoST-*.jar")])'''

# 需要 glob：脚本里原来没有 import glob
OLD_IMPORT = u"import hashlib"
NEW_IMPORT = u"import glob\nimport hashlib"

fails = []


def main():
    text = io.open(PATH, "r", encoding="utf-8").read()
    for old, new, label, expect in ((OLD_IMPORT, NEW_IMPORT, u"加 import glob", 1),
                                    (OLD_BUILD, NEW_BUILD, u"BUILD_JAR 跟着版本走", 1),
                                    (OLD_REL, NEW_REL, u"release jar 跟着版本走", 1)):
        n = text.count(old)
        if n != expect:
            fails.append(u"%s：命中 %d 次" % (label, n))
            print(u"  !! %s：命中 %d 次（应 %d）" % (label, n, expect))
            return 1
        text = text.replace(old, new, 1)
        print(u"  [OK] %s" % label)
    io.open(PATH, "w", encoding="utf-8", newline=u"\n").write(text)
    print(u"_zf69_verify.py 已改成读 v%s 的产物" % u"（gradle.properties）")
    return 0


if __name__ == "__main__":
    sys.exit(main())
