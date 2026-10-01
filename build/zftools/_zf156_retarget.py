# -*- coding: utf-8 -*-
u"""_zf156_retarget.py —— ZF156 把**版本线抬到 0.13** 之后，把断言版本号/成品名的门跟平。

只动这三类（判据**不放宽**，仍是逐字比那一个常量 / 那一个文件名）：
  ① `_zf73_verify.py`  C1：`mod_version=0.12` → `0.13`
  ② `_zf79_verify.py`  ：`mod_version=0.12` → `0.13`
  ③ `_zf78_verify.py`  ：⚠ 这条本来就**自相矛盾**（标签写 0.12、断言写 `mod_version=0.11`，ZF150 只改了标签）
                        ⇒ 一并跟到 0.13，并在注释里写明这次是**修矛盾**而不是放宽判据。
  ④ `_zf149_verify.py` ：成品名 `PotatoST-0.12.jar` → `0.13`（哈希/字节数在打包脚本里跟，见 `_zf156_pkg.py`）。

⚠ 历史脚本/档案里的 "0.12" 字样**不许批量改**（§4.132：只碰自己点名的清单）——
   那 40 多份写死 `release\\PotatoST-0.11.jar` 的老门同理：它们指的那份 jar 还在盘上、还是它们的参照物。

跑法：python build\\zftools\\_zf156_retarget.py [--write]
"""
import io
import os
import sys

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding=u"utf-8", errors="replace")

ROOT = r"E:\PotatoST"
ZT = os.path.join(ROOT, "build", "zftools")

JOBS = [
    (u"_zf73_verify.py", 1,
     u'check(u"C1 mod_version = 0.12", re.search(r"mod_version=0\\.12", props) is not None)',
     u'check(u"C1 mod_version = 0.13", re.search(r"mod_version=0\\.13", props) is not None)'),
    (u"_zf79_verify.py", 1,
     u'check(u"mod_version 现在是 0.12（ZF147 抬的版本线）",\n'
     u'          props is not None and u"mod_version=0.12" in props)',
     u'check(u"mod_version 现在是 0.13（ZF156 抬的版本线）",\n'
     u'          props is not None and u"mod_version=0.13" in props)'),
    (u"_zf78_verify.py", 1,
     u'check(u"mod_version 现在是 0.12（ZF147 抬的版本线）",\n'
     u'          props is not None and u"mod_version=0.11" in props)',
     u'# ⚠ ZF156：这条原来标签写 0.12、断言写 `mod_version=0.11`（ZF150 只改了标签）——\n'
     u'    #   本轮把两边一起跟到 0.13：是**修自相矛盾**，不是放宽判据（仍是逐字比那个常量）。\n'
     u'    check(u"mod_version 现在是 0.13（ZF156 抬的版本线）",\n'
     u'          props is not None and u"mod_version=0.13" in props)'),
    (u"_zf149_verify.py", 1,
     u'u"""_zf149_verify.py —— ZF149 **常驻校验**：成品 `release\\\\PotatoST-0.12.jar` 里真的有手册。',
     u'u"""_zf149_verify.py —— ZF149 **常驻校验**：成品 `release\\\\PotatoST-0.13.jar` 里真的有手册。'),
    (u"_zf149_verify.py", 1,
     u'JAR = os.path.join(ROOT, "release", u"PotatoST-0.12.jar")',
     u'JAR = os.path.join(ROOT, "release", u"PotatoST-0.13.jar")'),
    (u"_zf149_verify.py", 1,
     u'check(os.path.isfile(JAR), u"A1 release\\\\PotatoST-0.12.jar 在")',
     u'check(os.path.isfile(JAR), u"A1 release\\\\PotatoST-0.13.jar 在")'),
]


def main(argv):
    write = u"--write" in argv
    fails = []
    # ⚠ 同一份文件有多个 job 时**不能**各自基于"读到的原文"排队再一起写：
    #   那样最后一次写会把前面几次的改动**盖掉**（第一版就是这么把 `_zf149_verify.py`
    #   的 docstring / JAR 两处改动弄丢的 —— 只有排在最后的 A1 标签活了下来）。
    #   正确做法：一份文件只读一次、在同一份 text 上依次替换、最后写一次。
    texts = {}
    order = []
    for name, expect, old, new in JOBS:
        p = os.path.join(ZT, name)
        if p not in texts:
            texts[p] = io.open(p, encoding=u"utf-8", newline=u"").read()
            order.append(p)
        text = texts[p]
        if new in text and old not in text:
            print(u"  [跳过] %s（已经改过，幂等）" % name)
            continue
        n = text.count(old)
        if n != expect:
            fails.append(u"%s：锚点命中 %d 次（应为 %d）\n      %r" % (name, n, expect, old[:70]))
            continue
        texts[p] = text.replace(old, new)
        print(u"  [改] %-20s %s" % (name, old.split(u"\n")[0][:66]))
    plan = [(p, texts[p]) for p in order if texts[p] != io.open(p, encoding=u"utf-8", newline=u"").read()]
    print(u"计划写盘 %d 份（%d 处改动）" % (len(plan), sum(1 for _ in JOBS)))
    for f in fails:
        print(u"  !! " + f)
    if fails or not write:
        if not write:
            print(u"（没加 --write，只算不写）")
        return 1 if fails else 0
    for p, new in plan:
        io.open(p, u"w", encoding=u"utf-8", newline=u"").write(new)
        print(u"  已写 %s" % os.path.relpath(p, ROOT))
    return 0


if __name__ == u"__main__":
    sys.exit(main(sys.argv[1:]))
