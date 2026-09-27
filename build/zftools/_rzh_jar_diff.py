# -*- coding: utf-8 -*-
r"""_rzh_jar_diff.py —— 比两个 jar 的**条目清单**差集。

起因：重建后的 jar 比旧的小了 700 KB（5.76 MB → 5.04 MB）。体积变化本身不一定是错
（构建方式、压缩率、并行线同时改了资源都可能），但**必须弄清楚少了什么**，
不能"看起来没报错就算了"。

用法：`python build/zftools/_rzh_jar_diff.py <旧 jar> <新 jar>`
输出 `_rzh_jar_diff.txt`。
"""
from __future__ import print_function
import io
import os
import sys
import zipfile

OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), u"_rzh_jar_diff.txt")


def entries(path):
    z = zipfile.ZipFile(path)
    d = {}
    for i in z.infolist():
        if i.is_dir():
            continue
        d[i.filename] = i.file_size
    z.close()
    return d


def main():
    if len(sys.argv) < 3:
        print(u"用法: python _rzh_jar_diff.py <旧 jar> <新 jar>")
        return 1
    a, b = entries(sys.argv[1]), entries(sys.argv[2])
    only_a = sorted(set(a) - set(b))
    only_b = sorted(set(b) - set(a))
    both = sorted(set(a) & set(b))
    changed = [(k, a[k], b[k]) for k in both if a[k] != b[k]]

    L = [u"旧：%s（%d 条目，%.1f MB）" % (sys.argv[1], len(a), os.path.getsize(sys.argv[1]) / 1048576.0),
         u"新：%s（%d 条目，%.1f MB）" % (sys.argv[2], len(b), os.path.getsize(sys.argv[2]) / 1048576.0),
         u""]

    def by_prefix(names):
        import collections
        c = collections.Counter()
        for n in names:
            c[n.split(u"/")[0] + u"/" + (n.split(u"/")[1] if n.count(u"/") > 0 else u"")] += 1
        return c

    L.append(u"== 只在旧 jar 里（%d 个）==" % len(only_a))
    for k, v in by_prefix(only_a).most_common(20):
        L.append(u"   %-46s %d" % (k, v))
    for n in only_a[:25]:
        L.append(u"      %s" % n)
    L.append(u"")
    L.append(u"== 只在新 jar 里（%d 个）==" % len(only_b))
    for k, v in by_prefix(only_b).most_common(20):
        L.append(u"   %-46s %d" % (k, v))
    for n in only_b[:25]:
        L.append(u"      %s" % n)
    L.append(u"")
    L.append(u"== 同名但大小变了（%d 个）==" % len(changed))
    delta = 0
    for k, x, y in changed:
        delta += y - x
        L.append(u"   %-64s %8d -> %8d  (%+d)" % (k, x, y, y - x))
    L.append(u"")
    L.append(u"同名条目净变化：%+d 字节；两 jar 条目数差 %+d"
             % (delta, len(b) - len(a)))

    io.open(OUT, u"w", encoding=u"utf-8", newline=u"\n").write(u"\n".join(L) + u"\n")
    print(u"wrote %s  (只在旧 %d / 只在新 %d / 变了 %d)"
          % (OUT, len(only_a), len(only_b), len(changed)))
    return 0


if __name__ == u"__main__":
    sys.exit(main())
