# -*- coding: utf-8 -*-
u"""_zf107_probe_archive.py —— 核对"事后重建的探针源码"与"当时的探针报告"是否一致

背景（如实记）：ZF107 的临时探针 `Zf107Check.java` 我**先从 src 删了、没先抄进
`build/zftools/check/`**（违反本工程老规矩，是我的 slip），而它也没赶上第一个 git 提交。
现在 `build/zftools/check/Zf107Check.java` 是**按会话原文重建**的。

这份脚本就是重建件的"可信度证据"：**把重建件里所有中文/长字符串字面量逐条拿到
当时的运行报告 `_zf107_probe_utf8.txt` 里去找** ——
  · 报告里出现的（= 当时真跑过这句）算命中；
  · 报告里找不到的逐条列出来（那说明重建件里多了东西，或者那句话当时没走到）。

口径：**只做核对、不改任何文件**。
"""
import io
import os
import re
import sys

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

ZT = r"E:\PotatoST\build\zftools"
SRC = os.path.join(ZT, r"check\Zf107Check.java")
REPORT = os.path.join(ZT, u"_zf107_probe_utf8.txt")

fails = []


def main():
    src = io.open(SRC, encoding="utf-8").read()
    rep = io.open(REPORT, encoding="utf-8").read()
    n_pass = 0
    # ① 报告本身在、且判词是全绿
    print(u"报告：%s（%d 字节）" % (REPORT, len(rep.encode("utf-8"))))
    if u"判词：全绿" in rep:
        n_pass += 1
        print(u"  [OK]   报告判词 = 全绿")
    else:
        fails.append(u"报告判词不是全绿")
    n_ok = rep.count(u"[OK]")
    n_fail = rep.count(u"[FAIL]")
    print(u"  [--]   报告里 [OK] = %d，[FAIL] = %d" % (n_ok, n_fail))
    if n_fail:
        fails.append(u"报告里有 %d 条 FAIL" % n_fail)

    # ② 只核对"整句字面量"的断言文案：
    #    · `check(u"……", …)` —— 整句就是断言名（不是 p + "…" 那种拼接碎片）
    #    · `say(TAG + "……")`   —— 整句就是进度行
    #    ⚠ 第一版把**所有含中文的字面量**（连 javadoc 注释和拼接碎片都算）拿去比，
    #      于是 46 条里 8 条"找不到"，命中率 82.6% 判成"不可信" —— 那是**尺子错**，不是重建件错
    #      （§4.30 同族：尺子不对时先修尺子）。现在按"整句"这个可判定的口径来。
    whole = []
    for pat in (r'check\(\s*u?"((?:[^"\\]|\\.)*)"\s*[,)]',
                r'say\(TAG \+ "((?:[^"\\]|\\.)*)"'):
        for m in re.finditer(pat, src):
            s = m.group(1).replace(u"\\n", u"")
            if len(s) >= 4 and s not in whole:
                whole.append(s)
    # 这几条只在"出事了"或"某个分支"时才输出；当时没发生 ⇒ 报告里当然没有。
    # 单列出来并写明理由 —— 这样"报告里找不到"这件事只有这两种**已知**解释，不留含糊。
    NOT_TAKEN = [u"石油那条进度在（没法查油桶判据）",
                 u"report write failed: ",
                 u"register failed: ",
                 u"exception: "]
    hit = [l for l in whole if l in rep]
    miss = [l for l in whole if l not in rep and l not in NOT_TAKEN]
    print(u"整句断言文案 = %d 条；在报告里找到 %d 条" % (len(whole), len(hit)))
    n_pass += len(hit)
    for l in NOT_TAKEN:
        if l in whole and l not in rep:
            print(u"  [OK]   未走到的分支/错误分支（当时没发生 ⇒ 没输出）：%s" % l)
            n_pass += 1
        else:
            fails.append(u"未走到的分支那条对不上：%s" % l)
    if miss:
        print(u"  [--]   还对不上的 %d 条：" % len(miss))
        for l in miss[:25]:
            print(u"        · %s" % l[:110])
        fails.append(u"有 %d 条整句断言在报告里找不到" % len(miss))

    # ③ 关键结构：四个段标题 + 27 条路径表 + 325/0 的收尾
    for key in (u"① inventory", u"② tree", u"③ display", u"④ real triggers",
                u"收尾：27 条全部点亮", u"空油桶"):
        if key in rep:
            n_pass += 1
        else:
            fails.append(u"报告里缺关键段：%s" % key)
    print(u"")
    print(u"通过 = %d   失败 = %d" % (n_pass, len(fails)))
    for f in fails:
        print(u"  !! " + f)
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())
