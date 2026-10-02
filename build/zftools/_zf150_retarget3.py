# -*- coding: utf-8 -*-
"""_zf150_retarget3.py —— 把**所有真判据**里的 579/581 跟到 583/585

盘上活体数字（ZF150 之后）：
  四语言 **583** 键（579 + 四种粒各 1 键）
  `lzh`  **585** 键（581 + 4；= 583 + language.name/region 两个元数据键）

## 谁改、谁不改（这是本脚本的全部价值）

改：`_zf*_verify.py` 里**非注释行**上的 579/581 —— 那是判据。
不改：
  · `_zf149_verify.py` —— 它查的是**已发布 jar**（`release\\PotatoST-0.12.jar`，
    里面确实是 579/581）。本轮**没打包**，那个数就是事实，改它反而错。
  · 各种 `*_probe_utf8.txt` / `*_reds.txt` / `*_src*.txt` —— 历史证据落档。
  · `*_docs.py` / `*_gatefix.py` / `*_falsify.py` 里的 `OLD, NEW = "508", "579"`
    这类 —— 是**上一轮**的账，改了就是篡改历史。
  · `*.md` 的档案条目（§9 的历史记录）。

⚠ 逐行看过再改，改完打印每条 diff 摘要，人工可核。跑完立刻 `ast.parse` 自检。
"""
import ast
import io
import os
import re
import sys

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

TOOLS = r"E:\PotatoST\build\zftools"
OLD4, NEW4 = 579, 583      # 四语言
OLD5, NEW5 = 581, 585      # lzh
SKIP = {"_zf149_verify.py"}  # 查已发布 jar 的，不动

fails, changed = [], []


def classify(ln):
    """返回 'judge'（要改）/ 'skip'（别动）"""
    s = ln.strip()
    if s.startswith(u"#") or s.startswith(u"//"):
        return "skip"
    # 查 jar / 成品的
    if any(h in ln for h in (u"RELEASE", u"release", u"PotatoST-0.1", u"成品")):
        return "skip"
    return "judge"


def main():
    for fn in sorted(os.listdir(TOOLS)):
        if not re.match(r"^_zf\d+_verify\.py$", fn) or fn in SKIP:
            continue
        p = os.path.join(TOOLS, fn)
        src = io.open(p, encoding="utf-8").read()
        lines = src.split(u"\n")
        n_ch = 0
        for i, ln in enumerate(lines):
            if not re.search(r"\b(579|581)\b", ln):
                continue
            if classify(ln) != "judge":
                continue
            new = re.sub(r"\b579\b", str(NEW4), ln)
            new = re.sub(r"\b581\b", str(NEW5), new)
            if new != ln:
                lines[i] = new
                n_ch += 1
        if n_ch:
            out = u"\n".join(lines)
            try:
                ast.parse(out)
            except SyntaxError as e:
                fails.append(u"%s 改后语法错误：%s" % (fn, e))
                print(u"  !! %s 语法错误，**没写盘**：%s" % (fn, e))
                continue
            io.open(p, "w", encoding="utf-8", newline="\n").write(out)
            changed.append((fn, n_ch))
            print(u"  [OK] %-24s 改了 %d 行" % (fn, n_ch))

    print(u"\n共改 %d 份" % len(changed))
    if not changed:
        print(u"  （没有需要改的）")

    print(u"\n== 复查：跳过名单与残留 ==")
    for fn in sorted(os.listdir(TOOLS)):
        if not re.match(r"^_zf\d+_verify\.py$", fn):
            continue
        src = io.open(os.path.join(TOOLS, fn), encoding="utf-8").read()
        left = [ln.strip()[:80] for ln in src.split(u"\n")
                if re.search(r"\b579\b", ln) and classify(ln) == "judge"]
        if left:
            print(u"  %-24s 仍有 %d 行判据写着 579" % (fn, len(left)))
            for x in left[:3]:
                print(u"      %s" % x)

    print(u"\n失败项 = %d" % len(fails))
    for f in fails:
        print(u"  !! " + f)
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())
