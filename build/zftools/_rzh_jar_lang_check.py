# -*- coding: utf-8 -*-
r"""_rzh_jar_lang_check.py —— 校验**构建产物**里到底带了哪些语言文件。

为什么要有这一道（这个门是踩了坑之后才立的）：
    玩家反馈「切到文言后本模组显示英文」。查到根因是
    `release/PotatoST-0.11.jar` 里只有 en_us / ja_jp / ru_ru / zh_cn —— **没有 lzh.json**。
    jar 是加文言文之前构建的。

    而我上一轮的校验（`_rzh_lzh_verify.py`）只证明了"源文件写对了"：
    键集齐、字形对、无 BOM。**源文件对 ≠ 资源进包**。缺的那一环没有门守着，
    所以它一路绿着走到玩家手里。

判据：
  A `assets/potato_s_t/lang/` 下每一份语言文件都在 jar 里（与源目录逐个对齐）
  B 每一份在 jar 里的**字节数与源文件一致**（防止打进旧版本）
  C 加载校验：把 jar 里的 lang 当资源读出来，键集与源文件一致
  D 语言总数（顺带看一眼有没有多出/漏掉）

用法：
    python build/zftools/_rzh_jar_lang_check.py [jar 路径]
默认取 `build/libs/` 下最新的 jar。
"""
from __future__ import print_function
import io
import json
import os
import sys
import zipfile

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
SRC = os.path.join(ROOT, u"src", u"main", u"resources", u"assets", u"potato_s_t", u"lang")
LIBS = os.path.join(ROOT, u"build", u"libs")
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), u"_rzh_jar_lang_check.txt")


def newest_jar():
    if not os.path.isdir(LIBS):
        return None
    cands = [os.path.join(LIBS, n) for n in os.listdir(LIBS)
             if n.endswith(u".jar") and not n.endswith(u"-sources.jar")]
    if not cands:
        return None
    return max(cands, key=os.path.getmtime)


def main():
    jar = sys.argv[1] if len(sys.argv) > 1 else newest_jar()
    L = []
    if not jar or not os.path.exists(jar):
        L.append(u"找不到 jar（build/libs 下没有产物）")
        io.open(OUT, u"w", encoding=u"utf-8", newline=u"\n").write(u"\n".join(L) + u"\n")
        print(u"wrote %s" % OUT)
        return 1

    L.append(u"jar: %s" % jar)
    L.append(u"     %d 字节，改于 %s"
             % (os.path.getsize(jar),
                __import__(u"time").strftime(u"%Y-%m-%d %H:%M:%S",
                                             __import__(u"time").localtime(os.path.getmtime(jar)))))
    bad = 0

    z = zipfile.ZipFile(jar)
    in_jar = dict((n[len(u"assets/potato_s_t/lang/"):], n) for n in z.namelist()
                  if n.startswith(u"assets/potato_s_t/lang/") and n.endswith(u".json"))
    src = sorted(n for n in os.listdir(SRC) if n.endswith(u".json"))

    L.append(u"")
    L.append(u"== A/B/C 源目录 %d 份 vs jar 里 %d 份 ==" % (len(src), len(in_jar)))
    for name in src:
        sp = os.path.join(SRC, name)
        raw = io.open(sp, u"rb").read()
        if name not in in_jar:
            bad += 1
            L.append(u"  [缺] %-14s 源文件在，**jar 里没有** —— 游戏查不到这个语言" % name)
            continue
        jraw = z.read(in_jar[name])
        same = (jraw == raw)
        if not same:
            bad += 1
        # 加载校验
        try:
            a = json.loads(raw.decode(u"utf-8"))
            b = json.loads(jraw.decode(u"utf-8"))
            keys_same = set(a) == set(b)
        except Exception as e:                       # noqa: BLE001
            keys_same = False
            L.append(u"  [错] %s 解析失败：%s" % (name, e))
        if not keys_same:
            bad += 1
        L.append(u"  %-14s 源 %6d B / 包内 %6d B  %s  键集%s  %d 键"
                 % (name, len(raw), len(jraw), u"逐字节一致" if same else u"**不一致**",
                    u"一致" if keys_same else u"**不一致**", len(b) if keys_same else -1))

    extra = sorted(set(in_jar) - set(src))
    if extra:
        L.append(u"  [注意] jar 里有源目录没有的：%s" % u", ".join(extra))

    L.append(u"")
    L.append(u"== D 结论 ==")
    L.append(u"  语言文件 %d 份：%s" % (len(in_jar), u", ".join(sorted(in_jar))))
    L.append(u"  lzh 在不在包里：%s" % (u"在" if u"lzh.json" in in_jar else u"**不在**"))
    L.append(u"")
    L.append(u"失败项 = %d" % bad)
    z.close()

    io.open(OUT, u"w", encoding=u"utf-8", newline=u"\n").write(u"\n".join(L) + u"\n")
    print(u"wrote %s  (失败 %d)" % (OUT, bad))
    return 1 if bad else 0


if __name__ == u"__main__":
    sys.exit(main())
