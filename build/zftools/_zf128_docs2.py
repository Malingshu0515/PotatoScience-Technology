# -*- coding: utf-8 -*-
u"""_zf128_docs2.py —— 收尾：回填项数 + 记两件"本轮期间真实发生的事"

① 三处占位 `**0 项**` 回填成 `_zf128_verify.py` 实跑的项数；
② §4.111：两条新雷（**生成器里的反斜杠路径被真转义**、**子进程 stdout 编码要钉**）；
③ §9 补一段：**素材线在本轮期间把银线那两张贴图画了**（待画 15 → 13）⇒ 我把"待画数"这条链
   改成**从 `TextureCheck.py` 现数**（不再手写死），并顺手把两处判据跟平；
④ 交接 §6 第 20 条补上同一件事。

跑法：
    python build\\zftools\\_zf128_docs2.py
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
VERIFY = os.path.join(ROOT, r"build\zftools\_zf128_verify.py")

notes, fails = [], []


def read(p):
    return io.open(p, encoding="utf-8", newline=u"").read()


def write(p, t):
    io.open(p, "w", encoding="utf-8", newline=u"").write(t)


LESSON = u'''### 4.111 【生成器与子进程】反斜杠路径被"真转义" / 子进程 stdout 的编码要钉（0.11 ZF128）

两件都在同一轮撞上，都是"我写的脚本 / 我起的子进程"那边出的问题：

**① 生成器里的反斜杠路径被真转义了**（§4.24 家族的又一面）。
`_zf128_artfix.py` 用 `u\'\'\'...\'\'\'` 装"要写进目标文件的那段文本"，里面写了
`r"src\\main\\resources\\..."` —— 那个 `r` 前缀只是**被写进文件**的内容；在**生成它的那个字符串**里
`\\r` / `\\a` / `\\t` 是**真转义** ⇒ 盘上那行源码被拆成了两行（`src\\main` + 回车 + `esources` + 响铃 + …），
`_zf128_verify.py` 当场 `SyntaxError: unterminated string literal`。

**规矩**：凡是要往文件里写**反斜杠**的生成器，装文本的那个字符串自己也得是 raw
（`u\'\'\'...\'\'\'` → `ur\'\'\'...\'\'\'` 不行就 `u"..."` 里把 `\\` 写成 `\\\\`），
或者干脆**别拼路径**（`os.path.join` / 正斜杠）。
**验法**：改完立刻 `compile()` 目标文件（本轮就是这么当场发现的），并顺便搜一遍
`\\r`/`\\x07`/制表符这类控制字符。

**② 子进程的 stdout 编码必须钉住**（§4.81 的镜像面）。
父脚本用 `subprocess` 调 `TextureCheck.py` 时，**子进程**的 stdout 被管道接走 ⇒ 它按**本地编码（GBK）**
输出，而父进程按 UTF-8 解码 ⇒「待画」两字变成乱码，正则 `待画\\s*=\\s*(\\d+)` 一条都匹配不上，
`n_draw` 静默变成 `-1`（这就是 ZF127 那轮 `_zf71_verify.py` 里 `n_draw` 判据"看着有、其实没生效"的原因）。
**规矩**：起子进程就带上 `env=dict(os.environ, PYTHONIOENCODING="utf-8")` ——
一句话，两边都省心；`_zf127_verify.py` / `_zf128_verify.py` / `_zf90_verify.py` 都已改成这样。

**③ 顺带一条口径**：像"待画贴图数"这种**每来一张美术素材就会动**的活体数字，
判据应该**去问那个唯一的来源**（`TextureCheck.py --plan` 现跑现数），而不是每轮手改 3~4 处
（历史上手改过 7→6→5→13→12→9→13→15→13 八次，每次都有人漏一处）。

'''

ADDENDUM = u'''
#### 五、⚠ 本轮期间**素材线把银线那两张贴图画了**（不是我干的，如实记）

写这一轮的文档时（13:02），素材线在同一棵树上交付了 `silver_wire.png` / `silver_wire_spool.png`
并把两个模型指到自己的贴图上，还重跑了 `TextureCheck.py --plan` ⇒ **待画 15 → 13**，
ZF127 那轮立的"材质先不画（不许有自己的 png）"那几条判据当场被顶红（这正是它们该有的行为）。

我怎么收的（判据强度一处都没放宽）：

| 落点 | 原来 | 现在 |
|---|---|---|
| `_zf127_verify.py` D1/D2/D2b/H1 | 模型借原版贴图、**不许**有自己的 png | 模型指向**我们自己的**贴图、两张 png 在盘上且是真 PNG（读文件头） |
| `_zf127_verify.py` F2/F3/F4/F5、`_zf128_verify.py` D6 | 手写死"15" | **现问 `TextureCheck.py`**（`PYTHONIOENCODING=utf-8`），两边自动对齐 |
| `_zf107_verify.py` C1/C2/C5 | 泛化判据（图标带本模组命名空间 / 图标是模组注册物品 / 图标 ∈ 判据物品） | 给 `new_beginning` 三条**专属**判据（点名毒马铃薯 + **图标必须 ≠ 判据物品**），其余 34 条一个字不动 |
| `_zf125_verify.py` E3 | 控制器方块模型 `textures.all` == 那张占位图 | 素材线给控制器加了顶面贴图（`cube_bottom_top`）⇒ 改成"**每一处贴图都是控制器自己的图且在盘上**"，以后再加面不用改门 |
| 文档 | —— | §4.111 记两条雷；交接 §6 第 20 条补记这一段 |

⚠ 换行、控制字符那类事故也是本轮真发生的：见 §4.111 ①（生成器里的 `\\r`/`\\t` 被真转义）。

'''


def main():
    r = subprocess.run([sys.executable, VERIFY], stdout=subprocess.PIPE,
                       stderr=subprocess.STDOUT, timeout=300,
                       env=dict(os.environ, PYTHONIOENCODING=u"utf-8"))
    out = r.stdout.decode("utf-8", "replace")
    m = re.search(r"通过 = (\d+)\s+失败 = (\d+)", out)
    if not m or int(m.group(2)) != 0:
        fails.append(u"校验器不是全绿 ⇒ 不回填（%s）" % (m.group(0) if m else u"没有汇总行"))
        n = 0
    else:
        n = int(m.group(1))
        notes.append(u"`_zf128_verify.py` 实测：通过 = %d（全绿）" % n)

    if n:
        for path, label in ((ARC, u"档案"), (HAND, u"交接")):
            t = read(path)
            c = t.count(u"**0 项**")
            if c:
                write(path, t.replace(u"**0 项**", u"**%d 项**" % n))
                notes.append(u"%s：%d 处占位 0 项 → %d 项" % (label, c, n))
            else:
                notes.append(u"%s：没有占位（已填过）" % label)

    # ② §4.111
    t = read(ARC)
    anchor = u"## 7. 权威情报来源（怎么查原版行为，别靠记忆）"
    if u"### 4.111" in t:
        notes.append(u"§4.111 已经写过（幂等跳过）")
    elif t.count(anchor) == 1:
        write(ARC, t.replace(anchor, LESSON + anchor, 1))
        notes.append(u"档案 §4 新增 4.111（生成器转义 / 子进程编码）")
    else:
        fails.append(u"§4 锚点命中 %d 次" % t.count(anchor))

    # ③ §9 补一段（接在"要你实测"之前）
    t = read(ARC)
    anchor = u"#### 四、要你实测\n\n**重启客户端**（或 `F3+T` 重载数据包）后打开成就界面"
    if u"#### 五、⚠ 本轮期间**素材线把银线那两张贴图画了**" in t:
        notes.append(u"§9 那一段已经写过（幂等跳过）")
    elif t.count(anchor) == 1:
        write(ARC, t.replace(anchor, ADDENDUM.strip() + u"\n\n" + anchor, 1))
        notes.append(u"档案 §9：补上「素材线在本轮期间画了银线贴图」那一段")
    else:
        fails.append(u"§9 锚点命中 %d 次" % t.count(anchor))

    # ④ 交接第 20 条补记
    t = read(HAND)
    old = u"⑤ 证据：探针 **21 项全绿**\n    （含\"交毒马铃薯不亮 / 交微型粉碎机点亮\"）+ `_zf128_verify.py` **%d 项** + 反证 **K223~K226 四把**。\n"
    old2 = u"⑤ 证据：探针 **21 项全绿**（含「交毒马铃薯不亮 / 交微型粉碎机点亮」）+ `_zf128_verify.py` **35 项** + 反证 **K223~K226 四把**。"
    add = (u"\n    ⑥ ⚠ **本轮期间素材线把银线那两张贴图画了**（13:02）⇒ 待画 **15 → 13**，"
           u"ZF127 立的\"不许有自己的 png\"那几条判据当场被顶红 ⇒ 已按\"图到了就换成正向判据\"跟平，"
           u"并把**待画数这条链改成现问 `TextureCheck.py`**（顺手钉了子进程编码 `PYTHONIOENCODING=utf-8`）；"
           u"另有两处「素材线改了、我这边跟平判据」：`_zf107_verify.py` 的 C1/C2/C5（根节点图标专属判据）、"
           u"`_zf125_verify.py` 的 E3（控制器模型加了顶面贴图）。见 §4.111 与 §9 第五节。\n")
    if u"⑥ ⚠ **本轮期间素材线" in t:
        notes.append(u"交接第 20 条：已经补记（幂等跳过）")
    elif t.count(old2) == 1:
        write(HAND, t.replace(old2, old2 + add, 1))
        notes.append(u"交接 §6 第 20 条：补记素材线那一段")
    else:
        fails.append(u"交接第 20 条锚点命中 %d 次" % t.count(old2))

    print(u"\n".join(u"  [OK] " + x for x in notes))
    print(u"失败项 = %d" % len(fails))
    for f in fails:
        print(u"  !! " + f)
    return 1 if fails else 0


if __name__ == u"__main__":
    sys.exit(main())
