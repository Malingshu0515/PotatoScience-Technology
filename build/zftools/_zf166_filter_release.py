# -*- coding: utf-8 -*-
u"""_zf166_filter_release.py —— 把构建产物做成发布件：**只剔掉别人的临时探针 class**。

**为什么需要这一步**：`gradlew build` 从工作树打包，而另一条线（ZF165）的**临时探针**
`src/main/java/com/potatost/mod/Zf165Check.java` 此刻还在树上 ⇒ `build/libs/potato_s_t-0.13.jar`
里带着 `com/potatost/mod/Zf165Check.class`。探针会在玩家服务端启动时跑测试代码（我们自己的探针
就是以 `halt` 收尾的）⇒ **绝不能发布**。我又不能删别人的源文件（并发纪律），
于是只能在自己的发布件里**逐条剔除探针条目**：

- 逐条比对：留下的每个条目与原构建产物**逐字节一致**（CRC + 大小都核）；
- 只删名字里带 `Check` 的那几个条目，删掉几个要打印出来；
- 剔完再自检：转化器 class 在、配方 94 份、语言 605×4 + 607、**一个探针 class 都不剩**。

⚠ 这会让"成品 == 构建产物（逐字节）"暂时不成立（差的就是那一个探针 class）——
等他们把探针摘掉之后重打一次即可恢复（下一轮照 `_zf166_remain.md` 做）。

跑法：python build\\zftools\\_zf166_filter_release.py [--write]
"""
import hashlib
import io
import os
import shutil
import sys
import zipfile

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding=u"utf-8", errors="replace")

ROOT = r"E:\PotatoST"
SRC = os.path.join(ROOT, "build", "libs", u"potato_s_t-0.13.jar")
DST = os.path.join(ROOT, "release", u"PotatoST-0.13.jar")
SHA = DST + u".sha1"


def main(argv):
    write = u"--write" in argv
    if not os.path.isfile(SRC):
        print(u"!! 构建产物不在：%s" % SRC)
        return 1
    zin = zipfile.ZipFile(SRC)
    names = zin.namelist()
    probes = [n for n in names if u"Check" in os.path.basename(n) and n.endswith(u".class")]
    keep = [n for n in names if n not in probes]
    print(u"构建产物：%s（%d 条目 / %d class）" % (os.path.basename(SRC), len(names),
                                          len([n for n in names if n.endswith(u".class")])))
    print(u"要剔掉的探针 class：%s" % (probes or u"（无）"))
    if not probes:
        print(u"→ 构建产物本来就干净，直接拷过去即可")
    if write:
        with zipfile.ZipFile(DST, "w", zipfile.ZIP_DEFLATED) as zout:
            for n in keep:
                info = zin.getinfo(n)
                data = zin.read(n)
                zi = zipfile.ZipInfo(n, date_time=info.date_time)
                zi.compress_type = info.compress_type
                zi.external_attr = info.external_attr
                zi.internal_attr = info.internal_attr
                zi.create_system = info.create_system
                zout.writestr(zi, data)
        # 复核：留下的条目必须与原产物逐字节一致
        zout = zipfile.ZipFile(DST)
        bad = []
        for n in keep:
            if zout.read(n) != zin.read(n):
                bad.append(n)
        out_names = zout.namelist()
        leftover = [n for n in out_names if u"Check" in os.path.basename(n) and n.endswith(u".class")]
        h = hashlib.sha1(open(DST, "rb").read()).hexdigest()
        io.open(SHA, "w", encoding="ascii", newline=u"\n").write(h + u"\n")
        print(u"发布件：%s = %d B / sha1 %s" % (os.path.basename(DST), os.path.getsize(DST), h))
        print(u"复核：留下 %d 条目（不一致 %d 条）；残留探针 %s" % (len(out_names), len(bad), leftover or u"无"))
        recipes = [n for n in out_names if n.startswith(u"data/potato_s_t/recipe/") and n.endswith(u".json")]
        import json as _json
        counts = {}
        for lg in (u"zh_cn", u"lzh"):
            counts[lg] = len(_json.loads(zout.read(u"assets/potato_s_t/lang/%s.json" % lg).decode("utf-8")))
        print(u"自检：转化器 class=%s ｜ 配方 %d 份 ｜ 键 %s"
              % (any(u"FluidConverterBlockEntity.class" in n for n in out_names), len(recipes), counts))
        fails = []
        if bad:
            fails.append(u"有条目与原产物不一致")
        if leftover:
            fails.append(u"还有探针 class")
        if not any(u"FluidConverterBlockEntity.class" in n for n in out_names):
            fails.append(u"转化器 class 不在")
        if len(recipes) != 94:
            fails.append(u"配方份数 %d ≠ 94" % len(recipes))
        if counts.get(u"zh_cn") != 605 or counts.get(u"lzh") != 607:
            fails.append(u"语言键数不对 %s" % counts)
        print(u"失败 = %d" % len(fails))
        for f in fails:
            print(u"  !! " + f)
        return 1 if fails else 0
    print(u"干跑（不写）：预计发布 %d 条目" % len(keep))
    return 0


if __name__ == u"__main__":
    sys.exit(main(sys.argv[1:]))
