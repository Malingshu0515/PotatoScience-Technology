# -*- coding: utf-8 -*-
u"""_zf127_docs2.py —— 给 `_zf127_docs.py` 收尾：回填常驻校验的项数 + 把"自己写错的判据"补全

`_zf127_docs.py` 写文档时校验器还没跑（项数未知，先写了占位 `0 项`）⇒ 本脚本：
  ① 把三处占位换成真数（`_zf127_verify.py` 实跑出来的项数）；
  ② 把校验器**自己**写错的三条判据补进 §4.106 那张表（D5 拿 pattern 字面值比、
     F1 自指（标签里就写着旧数字）、H1 用 `silver*` 通配把银锭银板也算进去了）；
  ③ §9 证据表里那条"我自己写错的判据"补上这三条。

跑法：
    python build\\zftools\\_zf127_docs2.py
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
DOCS = os.path.join(ROOT, "docs")
ARC = os.path.join(DOCS, u"开发档案.md")
HAND = os.path.join(DOCS, u"多会话协作交接.md")
VERIFY = os.path.join(ROOT, r"build\zftools\_zf127_verify.py")

notes, fails = [], []


def read(p):
    return io.open(p, encoding="utf-8", newline=u"").read()


def write(p, t):
    io.open(p, "w", encoding="utf-8", newline=u"").write(t)


def main():
    r = subprocess.run([sys.executable, VERIFY], stdout=subprocess.PIPE,
                       stderr=subprocess.STDOUT, timeout=300)
    out = r.stdout.decode("utf-8", "replace")
    m = re.search(r"通过 = (\d+)\s+失败 = (\d+)", out)
    if not m or int(m.group(2)) != 0:
        fails.append(u"校验器不是全绿（%s）⇒ 不回填" % (m.group(0) if m else u"没有汇总行"))
        n = 0
    else:
        n = int(m.group(1))
        notes.append(u"校验器实测：通过 = %d（全绿）" % n)

    if n:
        arc = read(ARC)
        c = arc.count(u"**0 项**")
        if c:
            write(ARC, arc.replace(u"**0 项**", u"**%d 项**" % n))
            notes.append(u"档案：%d 处占位 0 项 → %d 项" % (c, n))
        else:
            notes.append(u"档案：没有占位（已经填过）")
        hand = read(HAND)
        c = hand.count(u"**0 项**")
        if c:
            write(HAND, hand.replace(u"**0 项**", u"**%d 项**" % n))
            notes.append(u"交接：%d 处占位 0 项 → %d 项" % (c, n))
        else:
            notes.append(u"交接：没有占位（已经填过）")

    # ② §4.106 那张表补三行（校验器自己的三处期望写错）
    arc = read(ARC)
    anchor = (u"| 断言\"铜线那根一 tick 传 1024\" ⇒ 得 0 | 那头的端子是新建的、"
              u"**我忘了给它灌电**；而且它在 `NONE` 模式，`receiveEnergy` 恒 0 |")
    add = (u"\n| 常驻校验 D5：拿 `pattern` 的**字面值**比银线/铜线"
           u"（`[\"SS\"]` vs `[\"CC\"]`）⇒ 假 FAIL | 字母只是 key 的索引，**形状一样、字母当然不同** "
           u"⇒ 要比的是行列数与材料表 |"
           u"\n| 常驻校验 F1：**自指** —— 这条判据的标签里就写着那个旧数字，"
           u"于是它把自己扫出来了 | 自查类判据要**跳过自己**（同类：§4.96/§4.99 的"
           u"\"空文件也全绿\"） |"
           u"\n| 常驻校验 H1：用 `silver*` 通配找\"银线的贴图\" | 银锭/银板本来就叫 `silver_ingot.png` / "
           u"`silver_plate.png` ⇒ 通配太宽，**要点名那两个文件** |")
    if u"常驻校验 D5：拿" in arc:
        notes.append(u"§4.106：三条校验器判据已经补过（幂等跳过）")
    elif arc.count(anchor) == 1:
        write(ARC, arc.replace(anchor, anchor + add, 1))
        notes.append(u"§4.106：补上校验器自己的三处期望写错（D5 / F1 / H1）")
    else:
        fails.append(u"§4.106 的锚点命中 %d 次" % arc.count(anchor))

    # ③ §9 证据表那一行补上"校验器自己也写错了三条"
    arc = read(ARC)
    old = (u"| 我自己写错的判据（如实记） | ① 反例\"8 根铜线围空线轴不匹配任何配方\"（其实能出铜线轴）；"
           u"② \"线轴用完手里是空的\"（空线轴会被塞回刚空出的那一格）；③ \"铜线那根一 tick 1024\""
           u"（忘了给那头的端子灌电）—— 三条都是**期望写错**，机器没错（§4.106） |")
    new = (u"| 我自己写错的判据（如实记） | **探针三条**：① 反例\"8 根铜线围空线轴不匹配任何配方\""
           u"（其实能出铜线轴）；② \"线轴用完手里是空的\"（空线轴会被塞回刚空出的那一格）；"
           u"③ \"铜线那根一 tick 1024\"（忘了给那头的端子灌电）；**常驻校验三条**："
           u"④ 拿 `pattern` 字面值比银/铜（字母不同是正常的）；⑤ F1 **自指**（标签里就写着旧数字）；"
           u"⑥ H1 用 `silver*` 通配（把银锭/银板也算进来了）—— **六条全是期望写错，机器没错**（§4.106） |")
    if u"**常驻校验三条**" in arc:
        notes.append(u"§9：六条判据失误已经记过（幂等跳过）")
    elif arc.count(old) == 1:
        write(ARC, arc.replace(old, new, 1))
        notes.append(u"§9：把校验器自己那三条也记进\"我写错的判据\"")
    else:
        fails.append(u"§9 那条的锚点命中 %d 次" % arc.count(old))

    print(u"\n".join(u"  [OK] " + x for x in notes))
    print(u"失败项 = %d" % len(fails))
    for f in fails:
        print(u"  !! " + f)
    return 1 if fails else 0


if __name__ == u"__main__":
    sys.exit(main())
