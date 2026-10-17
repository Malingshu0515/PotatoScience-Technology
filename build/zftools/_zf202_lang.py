# -*- coding: utf-8 -*-
u"""_zf202_lang.py —— 跟平"语言键数"（ZF201 那条线加了钢制工具 ⇒ 691/693 → 698/700）。

为什么要单开一个脚本：抬版本（ZF202）和"键数变了"是**两件事**，混在一个替换表里以后不好读。
只动**断言键数的那几行**（含 zh_cn / lzh / keys_jar / 五语种 / 语言键 的行），别的数字一碰不碰。
跑法：python build\\zftools\\_zf202_lang.py [--write]
"""
import io
import json
import os
import re
import sys
import zipfile

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding=u"utf-8", errors="replace")

NEW = r"E:\PotatoST\PotatoSTneoforge1.21.1"
ZT = os.path.join(NEW, "build", "zftools")
LIB = os.path.join(NEW, "build", "libs", u"potato_s_t-0.16.jar")
FILES = [u"_zf186_verify.py", u"_zf188_verify.py", u"_zf190_verify.py", u"_zf192_verify.py",
         u"_zf194_verify.py", u"_zf196_verify.py", u"_zf198_verify.py",
         u"_zf202_repack.py", u"_zf202_bump.py"]
OLD_CN, OLD_LZH = 691, 693          # ZF201 之前的键数（改动前）
NEW_CN, NEW_LZH = 698, 700          # ZF201 之后的键数（钢制工具那一批 +7 键）


def counts():
    z = zipfile.ZipFile(LIB)
    c = {f: len(json.loads(z.read(u"assets/potato_s_t/lang/%s.json" % f).decode("utf-8")))
         for f in (u"zh_cn", u"en_us", u"lzh", u"ja_jp", u"ru_ru")}
    z.close()
    return c


def main(argv):
    write = u"--write" in argv
    c = counts()
    print(u"jar 内键数：%s" % c)
    key = {u"zh_cn": c[u"zh_cn"], u"en_us": c[u"en_us"], u"ja_jp": c[u"ja_jp"],
           u"ru_ru": c[u"ru_ru"], u"lzh": c[u"lzh"]}
    hits = {}
    for fn in FILES:
        p = os.path.join(ZT, fn)
        if not os.path.isfile(p):
            print(u"  跳过（不在）：%s" % fn)
            continue
        text = io.open(p, encoding="utf-8", newline=u"").read()
        out, n = [], 0
        for line in text.split(u"\n"):
            touched = False
            if any(t in line for t in (u"zh_cn", u"en_us", u"lzh", u"ja_jp", u"ru_ru",
                                       u"keys_jar", u"五语种", u"语言键", u"键 %d", u"键数")):
                # 只替换 691/693 这种"键数"数字（带单词边界，不碰更长数字/哈希）
                def rep(m):
                    v = int(m.group(0))
                    return u"%d" % NEW_CN if v == OLD_CN else (u"%d" % NEW_LZH if v == OLD_LZH else m.group(0))
                new_line, k = re.subn(u"(?<![0-9a-zA-Z])(691|693)(?![0-9a-zA-Z])", rep, line)
                if k and new_line != line:
                    line = new_line
                    n += k
                    touched = True
            out.append(line)
        if n:
            hits[fn] = n
            print(u"  %-22s 改 %d 处" % (fn, n))
            if write:
                io.open(p, "w", encoding="utf-8", newline=u"").write(u"\n".join(out))
    print(u"共动 %d 份 / %d 处；写入=%s" % (len(hits), sum(hits.values()), write))
    # 复查：常驻门里不许再出现旧键数
    bad = []
    for fn in FILES:
        p = os.path.join(ZT, fn)
        if os.path.isfile(p):
            t = io.open(p, encoding="utf-8").read()
            if re.search(u"(?<![0-9a-zA-Z])691(?![0-9a-zA-Z])", t):
                bad.append(fn)
    print(u"复查：还写着 691 的文件 %s" % (bad or u"无"))
    return 1 if bad else 0


if __name__ == u"__main__":
    sys.exit(main(sys.argv[1:]))
