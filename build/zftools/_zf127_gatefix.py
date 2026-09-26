# -*- coding: utf-8 -*-
u"""_zf127_gatefix.py —— 把"待画贴图数"这条链子跟平：**13 → 15**（ZF127 借了两张原版贴图）

用户原话：「**材质先不画**」⇒ 银线 / 银线轴两个模型借原版贴图（铁粒 / 铁锭）占位，
`TextureCheck.py` 的"还在借原版贴图"就从 **13 → 15**。这个数是**三处一起动**的活体数字
（ZF110/ZF116/ZF120 都走过同一套）：

  ① `_zf71_verify.py` 的 `n_draw == N` 与公告里那句 `N models still do this`；
  ② `_zf90_verify.py` 的三条断言（公告那句、不许再写旧数、`_zf71` 的期望值）；
  ③ `docs/贴图清单.md` 的待画表头（重跑 `TextureCheck.py --plan` 生成）。

⚠ **顺带修一个 §4.81 的老雷**：`_zf71_verify.py` 的 stdout **没有钉成 UTF-8** ⇒
  在 UTF-8 控制台里看得见、被 gatesnap 用管道调起来时按 GBK 崩掉（`UnicodeEncodeError: '⇒'`）
  = **假绿**。它现在在快照里红着就是这个原因（不是内容错）。本脚本按 §4.81 补上那三行。

跑法：
    python build\\zftools\\_zf127_gatefix.py
"""
import io
import os
import re
import subprocess
import sys

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

ROOT = r"E:\PotatoST"
TOOLS = os.path.join(ROOT, "build", "zftools")
DOC = os.path.join(ROOT, r"docs\UpdateAnnouncement_EN.md")
LISTING = os.path.join(ROOT, r"docs\贴图清单.md")
BK = r"C:\PotatoST救援\zf127_pre\docs\贴图清单.md"

OLD_N, NEW_N = 13, 15
notes, fails = [], []


def read(p):
    return io.open(p, encoding="utf-8", newline=u"").read()


def write(p, text):
    io.open(p, "w", encoding="utf-8", newline=u"").write(text)


def patch(name, path, old, new, times=1):
    text = read(path)
    n = text.count(old)
    if n == 0 and new in text:
        notes.append(u"%s：已经是新文本（幂等跳过）" % name)
        return
    if n != times:
        fails.append(u"%s：锚点命中 %d 次（要 %d 次）—— 停手" % (name, n, times))
        return
    write(path, text.replace(old, new, times))
    notes.append(u"%s" % name)


def main():
    # ---------- ① _zf71_verify.py：UTF-8 钉子 + n_draw 15 ----------
    z71 = os.path.join(TOOLS, "_zf71_verify.py")
    pin_old = u"""import subprocess
import sys

ROOT = r"E:\\PotatoST"
"""
    pin_new = u"""import subprocess
import sys

# ⚠ §4.81：常驻校验必须自己把 stdout 钉成 UTF-8，否则被 gatesnap 用**管道**调起来时
#   会按 GBK 编码崩在 `⇒` 这种字符上（本文件 2026-09-26 前一直如此 ⇒ 快照里"假绿"）。
try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

ROOT = r"E:\\PotatoST"
"""
    patch(u"_zf71_verify.py：补 §4.81 的 UTF-8 stdout 钉子", z71, pin_old, pin_new)

    patch(u"_zf71_verify.py：n_draw %d -> %d（三处数字一起）" % (OLD_N, NEW_N), z71,
          u'''    check(n_draw == 9 and u"9 models still do this" in doc,
          u"还在借原版贴图的模型 = %d 个（公告写 9）" % n_draw)''',
          u'''    check(n_draw == 15 and u"15 models still do this" in doc,
          u"还在借原版贴图的模型 = %d 个（公告写 15）" % n_draw)''')

    patch(u"_zf71_verify.py：注释里补上 ZF110/ZF116/ZF120/ZF127 这条链", z71,
          u'''    #   **ZF110** 用户给了星璨钢头盔的背包图标 ⇒ **13 → 12**
    #   （公告同一句、`_zf90_verify.py` 的两条断言一起改，别只改一边）''',
          u'''    #   **ZF110** 用户给了星璨钢头盔的背包图标 ⇒ **13 → 12**
    #   （公告同一句、`_zf90_verify.py` 的两条断言一起改，别只改一边）；
    #   **ZF116** 胸甲/护腿/靴子三件也拿到图 ⇒ **12 → 9**；**ZF120**（振金套那条线）
    #   四件背包图标又借回原版铁套 ⇒ **9 → 13**；
    #   **ZF127** 银线 / 银线轴（用户点名「材质先不画」）借铁粒 / 铁锭 ⇒ **13 → 15**
    #   （这一次把 `_zf71_verify.py` 也一起跟到 15 —— ZF120 那次漏了它，它就一直红着）''')

    # ---------- ② _zf90_verify.py：三处 15 ----------
    z90 = os.path.join(TOOLS, "_zf90_verify.py")
    patch(u"_zf90_verify.py：公告那句 13 -> 15", z90,
          u'''check(u"英文公告已改成 13 models still do this", u"13 models still do this" in ann)''',
          u'''check(u"英文公告已改成 15 models still do this", u"15 models still do this" in ann)''')
    patch(u"_zf90_verify.py：旧数名单里补 13", z90,
          u'''not any(u"%d models still do this" % n in ann
                                                     for n in (5, 6, 7, 9, 12)))''',
          u'''not any(u"%d models still do this" % n in ann
                                                     for n in (5, 6, 7, 9, 12, 13)))''')
    patch(u"_zf90_verify.py：_zf71 的期望值 13 -> 15", z90,
          u'''check(u"`_zf71_verify.py` 的期望值同步成 13", u"n_draw == 13" in z71)''',
          u'''check(u"`_zf71_verify.py` 的期望值同步成 15", u"n_draw == 15" in z71)''')
    patch(u"_zf90_verify.py：贴图清单表头 13 -> 15", z90,
          u'''check(u"贴图清单的待画表头已变 13 个", u"## 待画（13 个" in listing)''',
          u'''check(u"贴图清单的待画表头已变 15 个", u"## 待画（15 个" in listing)''')
    patch(u"_zf90_verify.py：注释补 ZF127 一条", z90,
          u'''    #   **ZF120**（振金套，另一条线）四件背包图标又借回原版铁套 ⇒ **9 → 13**（同样三处一起改）''',
          u'''    #   **ZF120**（振金套，另一条线）四件背包图标又借回原版铁套 ⇒ **9 → 13**（同样三处一起改）
    #   **ZF127** 银线 / 银线轴（用户点名「材质先不画」）⇒ **13 → 15**（四处一起改：
    #   公告那句、本脚本两条、`_zf71_verify.py` 的 `n_draw`、`docs/贴图清单.md` 的表头）''')

    # ---------- ③ 英文公告 ----------
    patch(u"公告：键数 476 -> 478", DOC,
          u"(476 keys each)", u"(478 keys each)")
    patch(u"公告：13 models still do this -> 15", DOC,
          u"**Some textures are placeholders** borrowed from vanilla (13 models still do this",
          u"**Some textures are placeholders** borrowed from vanilla (15 models still do this")
    patch(u"公告：那条链子补上 15", DOC,
          u'''helmet) -> 9 (Star Steel chestplate, leggings and boots) -> 13 again (the four Vibranium
  pieces, which deliberately borrow the vanilla iron set for now));''',
          u'''helmet) -> 9 (Star Steel chestplate, leggings and boots) -> 13 again (the four Vibranium
  pieces, which deliberately borrow the vanilla iron set for now) -> 15 (the **Silver Wire** and
  **Silver Wire Spool**, new in 0.11 ZF127 — textures deliberately not drawn yet, as requested));''')

    # ---------- ④ 贴图清单：重跑生成器 ----------
    before = read(LISTING) if os.path.exists(LISTING) else u""
    r = subprocess.run([sys.executable, os.path.join(TOOLS, "TextureCheck.py"), u"--plan"],
                       stdout=subprocess.PIPE, stderr=subprocess.STDOUT, cwd=TOOLS)
    out = r.stdout.decode("utf-8", "replace")
    for l in out.split(u"\n"):
        if u"待画" in l and u"个" in l:
            notes.append(u"[TextureCheck] " + l.strip())
    if r.returncode != 0:
        fails.append(u"TextureCheck --plan 退出码 %d" % r.returncode)
    after = read(LISTING)
    if u"## 待画（15 个" not in after:
        fails.append(u"贴图清单表头没变成 15")
    else:
        notes.append(u"贴图清单表头 = 待画（15 个")
    for name in (u"silver_wire", u"silver_wire_spool"):
        row = [l for l in after.split(u"\n") if l.startswith(u"| `textures/item/` | `%s.png`" % name)]
        if row:
            notes.append(u"待画表里有 %s：%s" % (name, row[0].strip()))
        else:
            fails.append(u"待画表里没有 %s 那一行" % name)

    # 手写的那半必须原样接回（`---` 之后的内容一字不动）
    if before:
        mark = u"\n---\n\n## ZF"
        i, j = before.find(mark), after.find(mark)
        if i < 0 or j < 0:
            fails.append(u"手写部分的分隔标记不见了（改前 %d / 改后 %d）" % (i, j))
        elif before[i:] != after[j:]:
            fails.append(u"手写部分被改动了（%d 字符 vs %d 字符）" % (len(before[i:]), len(after[j:])))
        else:
            notes.append(u"手写部分原样接回（%d 字符一字未动）" % len(before[i:]))

    print(u"\n".join(u"  [OK] " + n for n in notes))
    print(u"失败项 = %d" % len(fails))
    for f in fails:
        print(u"  !! " + f)
    return 1 if fails else 0


if __name__ == u"__main__":
    sys.exit(main())
