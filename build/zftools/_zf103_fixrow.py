# -*- coding: utf-8 -*-
u"""_zf103_fixrow.py —— 把合金炉中文介绍图「第 2 层 第 5 行」改回 `SRRC`（用户确认过）

来历：用户润色中文时那一行从 `SRRC` 变成了 `CRRS` —— 但**那不是句子、是图纸的图例**
（每个字母代表一种方块类型）。结构代码 `AlloySmelterStructure` 那边一直是 `SRRC`，
而这张介绍图是 ZF57 那轮**从代码机械生成**的 ⇒ 代码是唯一真相，图得跟它一致，
否则玩家照图搭会搭错。用户在对话里确认「改回 SRRC」。

做法：先按 `_zf52_verify.py` 的同一套解析把那一行找出来，**只改这一行**，
其余键与其余行一字不动；改完再复跑 `_zf52_verify.py` 自证。
"""
import io
import json
import os
import subprocess
import sys

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

ROOT = r"E:\PotatoST"
TOOLS = os.path.join(ROOT, "build", "zftools")
P = os.path.join(ROOT, r"src\main\resources\assets\potato_s_t\lang\zh_cn.json")
KEY = u"tooltip.potato_s_t.alloy_smelter"
# ⚠ 第一版我以为图纸里写的是字母 `SRRC`/`CRRS` —— 那是 `_zf52_verify.py` **归一化之后**的叫法；
#    中文图里用的是**图例数字**（1 耐热 / 2 一般 / 3 加热 / 4 高炉 / 5 接线 / 6 散热 / 7 主控 / 0 空）。
#    实际差的是第 2 层最后一行：中文 `2222|7116` vs 代码/英文 `2222|6117`。
NEEDLE = u"2222|7116"
WANT = u"2222|6117"
fails = []


def main():
    raw = io.open(P, encoding="utf-8").read()
    data = json.loads(raw)
    text = data.get(KEY)
    if text is None:
        print(u"  [FAIL] 找不到 %s" % KEY)
        return 1
    n = text.count(NEEDLE)
    if n != 1:
        fails.append(u"`%s` 在介绍里出现 %d 次（必须 1 次）" % (NEEDLE, n))
    if fails:
        print(u"  [FAIL] %s ⇒ 一个字节都不写" % fails)
        return 1
    fixed = text.replace(NEEDLE, WANT, 1)
    # 用**行级**替换写回原文，保住用户的排版/缩进（不重新 dump 整个文件）
    old_line = None
    lines = raw.split(u"\n")
    for i, l in enumerate(lines):
        if l.strip().startswith(u'"%s"' % KEY):
            old_line = i
            break
    if old_line is None:
        print(u"  [FAIL] 找不到 %s 那一行" % KEY)
        return 1
    j = json.dumps(fixed, ensure_ascii=False)
    indent = u"    "
    lines[old_line] = u'%s"%s":  %s%s' % (
        indent, KEY, j, u"," if lines[old_line].rstrip().endswith(u",") else u"")
    out = u"\n".join(lines)
    back = json.loads(out)
    if back.get(KEY) != fixed or len(back) != len(data):
        # 逐键比对：除这一条，别的必须完全一样
        diff = [k for k in data if back.get(k) != data[k]]
        print(u"  [FAIL] 回读不一致（%s）⇒ 不写" % diff)
        return 1
    io.open(P, "w", encoding="utf-8", newline=u"").write(out)
    print(u"  [OK]   %s：`%s` → `%s`（只改这一行，其余 %d 键一字未动）"
          % (KEY, NEEDLE, WANT, len(back) - 1))

    env = dict(os.environ)
    env["PYTHONIOENCODING"] = "utf-8"
    r = subprocess.run([sys.executable, os.path.join(TOOLS, "_zf52_verify.py")],
                       capture_output=True, text=True, encoding="utf-8", errors="replace",
                       env=env, cwd=ROOT)
    tail = [l for l in (r.stdout or u"").splitlines() if u"失败项" in l or u"结论" in l]
    print(u"  ↳ 复跑 _zf52_verify.py：%s" % u" / ".join(t.strip() for t in tail[-2:]))
    if r.returncode != 0:
        fails.append(u"_zf52_verify.py 仍不过（exit=%d）" % r.returncode)
    print(u"\n失败项 = %d" % len(fails))
    for f in fails:
        print(u"  !! " + f)
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())
