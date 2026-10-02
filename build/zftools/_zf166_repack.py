# -*- coding: utf-8 -*-
u"""_zf166_repack.py —— ZF166 的"干净重打"：等另一条线摘掉探针之后跑这一条命令，恢复
「成品 == 构建产物（逐字节）」并把三处哈希联动跟平。

它做的事：
  1. 先查 `src\\main\\java\\com\\potatost\\mod\\Zf*Check.java` 有没有临时探针 —— **有就拒绝**（不重打）；
  2. `gradlew build`（离线）→ 取 `build\\libs\\potato_s_t-0.13.jar`；
  3. 逐字节拷到 `release\\PotatoST-0.13.jar` + 写 `.sha1`（**不再过滤**：树上干净了就该 1:1）；
  4. 自检：无探针 class、含转化器 class、配方 94 份、键 605×4 + 607；
  5. `_zf166_docs.py --write` 把档案 §5/§9、交接 §1、公告、`_zf149_verify.py` 的 WANT_SHA/WANT_SIZE
     与 class 数一起跟到新成品。

跑法：python build\\zftools\\_zf166_repack.py [--write]
"""
import hashlib
import io
import json
import os
import subprocess
import sys
import zipfile

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding=u"utf-8", errors="replace")

ROOT = r"E:\PotatoST"
ZT = os.path.join(ROOT, "build", "zftools")
JAVA = os.path.join(ROOT, r"src\main\java\com\potatost\mod")
BUILT = os.path.join(ROOT, "build", "libs", u"potato_s_t-0.13.jar")
DST = os.path.join(ROOT, "release", u"PotatoST-0.13.jar")


def main(argv):
    write = u"--write" in argv
    probes = [f for f in os.listdir(JAVA)
              if f.startswith(u"Zf") and f.endswith(u"Check.java")]
    if probes:
        print(u"!! 树上还有临时探针：%s" % probes)
        print(u"   ⇒ **拒绝重打**（打出来会带上别人的探针 class，那种 jar 不能发布）。")
        print(u"   等他们把探针摘掉再跑本脚本；期间发布件保持 `_zf166_filter_release.py` 那份（已剔过探针）。")
        return 2
    print(u"树上没有探针 ✓ —— 开始重打")
    if write:
        r = subprocess.run([os.path.join(ROOT, u"gradlew.bat"), u"build", u"--offline",
                            u"--console=plain"], cwd=ROOT, stdout=subprocess.PIPE,
                           stderr=subprocess.STDOUT)
        tail = r.stdout.decode("utf-8", "replace").strip().split(u"\n")[-3:]
        print(u"gradlew build：%s" % u" / ".join(t.strip() for t in tail))
        if r.returncode != 0:
            print(u"!! 构建失败，放弃")
            return 1
        if not os.path.isfile(BUILT):
            print(u"!! 找不到构建产物 %s" % BUILT)
            return 1
        with open(BUILT, "rb") as fi, open(DST, "wb") as fo:
            fo.write(fi.read())
        h = hashlib.sha1(open(DST, "rb").read()).hexdigest()
        io.open(DST + u".sha1", "w", encoding="ascii", newline=u"\n").write(h + u"\n")
        z = zipfile.ZipFile(DST)
        names = z.namelist()
        probes_in = [n for n in names if u"Check" in os.path.basename(n) and n.endswith(u".class")]
        recipes = [n for n in names if n.startswith(u"data/potato_s_t/recipe/") and n.endswith(u".json")]
        counts = {lg: len(json.loads(z.read(u"assets/potato_s_t/lang/%s.json" % lg).decode("utf-8")))
                  for lg in (u"zh_cn", u"lzh")}
        cls = len([n for n in names if n.endswith(u".class")])
        print(u"发布件 = 构建产物（逐字节）：%d B / sha1 %s / class %d" % (os.path.getsize(DST), h, cls))
        print(u"自检：探针 %s ｜ 转化器 %s ｜ 配方 %d ｜ 键 %s"
              % (probes_in or u"无",
                 any(u"FluidConverterBlockEntity.class" in n for n in names), len(recipes), counts))
        fails = []
        if probes_in:
            fails.append(u"产物里有探针 class")
        if not any(u"FluidConverterBlockEntity.class" in n for n in names):
            fails.append(u"转化器 class 不在")
        if len(recipes) != 94:
            fails.append(u"配方 %d ≠ 94" % len(recipes))
        if counts.get(u"zh_cn") != 605 or counts.get(u"lzh") != 607:
            fails.append(u"键数 %s ≠ 605/607" % counts)
        if fails:
            print(u"失败 = %d" % len(fails))
            for f in fails:
                print(u"  !! " + f)
            return 1
        r2 = subprocess.run([sys.executable, os.path.join(ZT, u"_zf166_docs.py"), u"--write"],
                            stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        print(u"_zf166_docs.py --write：\n" + r2.stdout.decode("utf-8", "replace").strip())
        return r2.returncode
    print(u"干跑：树上干净，正式跑要加 --write")
    return 0


if __name__ == u"__main__":
    sys.exit(main(sys.argv[1:]))
