# -*- coding: utf-8 -*-
u"""_zf128_artfix.py —— 素材线在**本轮期间**把银线那两张贴图画了 ⇒ 把"待画数"这条链改成**自洽**

**发生了什么（不是我干的，如实记）**：13:02:18 素材线交出 `silver_wire.png` / `silver_wire_spool.png`
并把两个模型指到自己的贴图上，还重跑了 `TextureCheck.py --plan` ⇒ 待画 **15 → 13**。
这一下把我 ZF127 那轮刚立的三处判据顶红了（`_zf127_verify.py` 的 D2/H1/F5、`_zf128_verify.py` 的 D6、
以及共享的 n_draw 链 `_zf71_verify.py` / `_zf90_verify.py` / 英文公告）。

**这道题的正确解法不是"再手改一次数字"**（素材线每画一张就动一次，历史上已经手改过 6 次：7→6→5→13→12→9→13→15）：
改成**从 `TextureCheck.py` 现数**，两边对齐 —— 以后谁画完图，只要重跑一次 `--plan` 就自动一致。

改什么：
  ① `_zf71_verify.py`：`n_draw == 15 && 公告写 15` → **公告里的数 == 现数**；
  ② `_zf90_verify.py`：四处手写死 15 → 全部改成现数（含"贴图清单表头"那条）；
  ③ `_zf127_verify.py`：D2/H1（"没有自己的贴图 png"）→ 素材线已经画了 ⇒ 改成
     "两个模型指向**我们自己的**贴图、文件在盘上且是合法 PNG"；F5 的 15 → 现数；
  ④ `_zf128_verify.py`：D6 的 15 → 现数；
  ⑤ 英文公告：那句 `15 models still do this` → 现数，并把这条链子补上"素材线画了这两张"。

跑法：
    python build\\zftools\\_zf128_artfix.py
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
DOCS = os.path.join(ROOT, "docs")
ANN = os.path.join(DOCS, u"UpdateAnnouncement_EN.md")
LISTING = os.path.join(DOCS, u"贴图清单.md")

notes, fails = [], []


def read(p):
    return io.open(p, encoding="utf-8", newline=u"").read()


def write(p, t):
    io.open(p, "w", encoding="utf-8", newline=u"").write(t)


def patch(name, path, old, new, times=1):
    t = read(path)
    if t.count(old) == 0 and new in t:
        notes.append(u"%s：已经是新文本（幂等跳过）" % name)
        return
    if t.count(old) != times:
        fails.append(u"%s：锚点命中 %d 次（要 %d 次）—— 停手" % (name, t.count(old), times))
        return
    write(path, t.replace(old, new, times))
    notes.append(u"%s" % name)


def texturecheck_count():
    r = subprocess.run([sys.executable, os.path.join(TOOLS, "TextureCheck.py")],
                       stdout=subprocess.PIPE, stderr=subprocess.STDOUT, cwd=TOOLS)
    out = r.stdout.decode("utf-8", "replace")
    m = re.search(r"待画\s*=\s*(\d+)", out)
    return (int(m.group(1)) if m else -1), out


def main():
    n, out = texturecheck_count()
    if n < 0:
        fails.append(u"TextureCheck 跑不出待画数")
        n = -1
    else:
        notes.append(u"TextureCheck 现数：待画 = %d" % n)

    # ---------- ① _zf71_verify.py ----------
    z71 = os.path.join(TOOLS, u"_zf71_verify.py")
    patch(u"_zf71_verify.py：n_draw 判据改成「公告里的数 == 现数」", z71,
          u'''    check(n_draw == 15 and u"15 models still do this" in doc,
          u"还在借原版贴图的模型 = %d 个（公告写 15）" % n_draw)''',
          u'''    # ⚠ ZF128：这个数**每来一张美术素材就动一次**（素材线在本轮期间把银线那两张画了 ⇒ 15 → 13）
    #   ⇒ 判据改成"公告里的数 == TextureCheck 现数的数"，从此不用每轮手改两处。
    check(n_draw > 0 and (u"%d models still do this" % n_draw) in doc,
          u"还在借原版贴图的模型 = %d 个（公告也必须写 %d）" % (n_draw, n_draw))''')

    # ---------- ② _zf90_verify.py ----------
    z90 = os.path.join(TOOLS, u"_zf90_verify.py")
    t = read(z90)
    if u"n_borrowed" in t:
        notes.append(u"_zf90_verify.py：已经是自洽版（幂等跳过）")
    else:
        old = u'''    check(u"英文公告已改成 15 models still do this", u"15 models still do this" in ann)
    check(u"英文公告里不再写 5/6/7/9/12 models", not any(u"%d models still do this" % n in ann
                                                     for n in (5, 6, 7, 9, 12, 13)))
    z71 = read(os.path.join(TOOLS, u"_zf71_verify.py")) or u""
    check(u"`_zf71_verify.py` 的期望值同步成 15", u"n_draw == 15" in z71)
    listing = read(os.path.join(DOCS, u"贴图清单.md")) or u""
    # ZF110/ZF116/ZF120 重跑过 `TextureCheck.py --plan` ⇒ 表头跟着活体数字走（现在 13 个）
    check(u"贴图清单的待画表头已变 15 个", u"## 待画（15 个" in listing)'''
        new = u'''    # ⚠ ZF128：**改成问 TextureCheck 现数**（素材线每画一张，这个数就动一次；
    #   历史上手改过 6 次：7→6→5→13→12→9→13→15→13）。从此两边自动对齐。
    n_borrowed = -1
    try:
        _r = subprocess.run([sys.executable, os.path.join(TOOLS, u"TextureCheck.py")],
                            stdout=subprocess.PIPE, stderr=subprocess.STDOUT, cwd=TOOLS)
        _m = re.search(r"待画\\s*=\\s*(\\d+)", _r.stdout.decode(u"utf-8", u"replace"))
        n_borrowed = int(_m.group(1)) if _m else -1
    except Exception:
        n_borrowed = -1
    check(u"英文公告那句 `N models still do this` 的 N == TextureCheck 现数（%d）" % n_borrowed,
          n_borrowed > 0 and (u"%d models still do this" % n_borrowed) in ann)
    check(u"英文公告里不再写别的数", not any(
        (u"%d models still do this" % x) in ann for x in (5, 6, 7, 9, 12, 13, 15) if x != n_borrowed))
    z71 = read(os.path.join(TOOLS, u"_zf71_verify.py")) or u""
    check(u"`_zf71_verify.py` 也改成自洽判据（不再钉死一个数字）",
          u'"%d models still do this" % n_draw' in z71)
    listing = read(os.path.join(DOCS, u"贴图清单.md")) or u""
    check(u"贴图清单的待画表头 == TextureCheck 现数（%d 个）" % n_borrowed,
          n_borrowed > 0 and (u"## 待画（%d 个" % n_borrowed) in listing)'''
        if t.count(old) != 1:
            fails.append(u"_zf90_verify.py：锚点命中 %d 次 —— 停手" % t.count(old))
        else:
            t = t.replace(old, new, 1)
            if u"import subprocess" not in t:
                t = t.replace(u"import sys\n", u"import subprocess\nimport sys\n", 1)
            write(z90, t)
            notes.append(u"_zf90_verify.py：四处手写死的 15 → 全部改成 TextureCheck 现数")

    # ---------- ③ _zf127_verify.py ----------
    z127 = os.path.join(TOOLS, u"_zf127_verify.py")
    patch(u"_zf127_verify.py：D2 改成「模型指向我们自己的贴图」", z127,
          u'''    check(u"D2 **没有自己的贴图 png**（用户点名「材质先不画」）",
          not os.path.exists(os.path.join(TEXI, u"silver_wire.png"))
          and not os.path.exists(os.path.join(TEXI, u"silver_wire_spool.png")))''',
          u'''    # ⚠ ZF128：素材线在本轮期间把这两张画了（用户当初说"材质先不画"，图到了就换成正向判据）
    check(u"D2 两个模型指向**我们自己的**贴图（素材线 ZF128 期间画的）",
          mw["textures"]["layer0"] == u"potato_s_t:item/silver_wire"
          and ms["textures"]["layer0"] == u"potato_s_t:item/silver_wire_spool")
    ok_png = True
    for name in (u"silver_wire.png", u"silver_wire_spool.png"):
        p = os.path.join(TEXI, name)
        if not os.path.exists(p) or open(p, "rb").read(8) != b"\\x89PNG\\r\\n\\x1a\\n":
            ok_png = False
    check(u"D2b 那两张 png 在盘上且是真 PNG（读文件头）", ok_png)''')
    patch(u"_zf127_verify.py：H1 改成「有贴图且合法」", z127,
          u'''    check(u"H1 盘上没有银线自己的贴图文件（材质先不画；⚠ 别用 silver* 通配 —— 银锭/银板就叫 silver_*）",
          not os.path.exists(os.path.join(TEXI, u"silver_wire.png"))
          and not os.path.exists(os.path.join(TEXI, u"silver_wire_spool.png")))''',
          u'''    check(u"H1 银线那两张贴图**在盘上**（素材线已经画了；ZF127 时它们是借原版贴图的占位）",
          os.path.exists(os.path.join(TEXI, u"silver_wire.png"))
          and os.path.exists(os.path.join(TEXI, u"silver_wire_spool.png")))''')
    patch(u"_zf127_verify.py：F5 的待画 15 → 现数", z127,
          u'''    check(u"F5 贴图清单表头 = 待画（15 个，且两条新行都在",
          u"## 待画（15 个" in listing
          and u"| `textures/item/` | `silver_wire.png` | 银线 |" in listing
          and u"| `textures/item/` | `silver_wire_spool.png` | 银线轴 |" in listing)''',
          u'''    # ⚠ ZF128：表头那个数改成**问 TextureCheck 现数**（素材线画完就是 13），不再手写死。
    import subprocess as _sp
    _r = _sp.run([sys.executable, os.path.join(TOOLS, u"TextureCheck.py")],
                 stdout=_sp.PIPE, stderr=_sp.STDOUT, cwd=TOOLS)
    _m = re.search(r"待画\\s*=\\s*(\\d+)", _r.stdout.decode(u"utf-8", u"replace"))
    _n = int(_m.group(1)) if _m else -1
    check(u"F5 贴图清单表头 == TextureCheck 现数（%d 个）" % _n,
          _n > 0 and (u"## 待画（%d 个" % _n) in listing)
    check(u"F5b 银线那两张已经搬进「已经有自己贴图的」表",
          u"| `textures/item/` | `silver_wire.png` | 银线 |" in listing
          and u"| `textures/item/` | `silver_wire_spool.png` | 银线轴 |" in listing)''')

    # ---------- ④ _zf128_verify.py ----------
    z128 = os.path.join(TOOLS, u"_zf128_verify.py")
    patch(u"_zf128_verify.py：D6 的待画 15 → 现数", z128,
          u'''    check(u"D6 **待画贴图清单一个数都没变**（毒马铃薯是原版物品，不是我们的模型）",
          u"## 待画（15 个" in listing)''',
          u'''    # ⚠ 数改成**问 TextureCheck 现数**：素材线每画一张它就动一次（本轮期间银线那两张刚到）
    import subprocess as _sp
    _r = _sp.run([sys.executable, os.path.join(TOOLS, u"TextureCheck.py")],
                 stdout=_sp.PIPE, stderr=_sp.STDOUT, cwd=TOOLS)
    _m = re.search(r"待画\\s*=\\s*(\\d+)", _r.stdout.decode(u"utf-8", u"replace"))
    _n = int(_m.group(1)) if _m else -1
    check(u"D6 待画贴图清单的表头 == TextureCheck 现数（%d 个）—— 本轮的改动不碰贴图" % _n,
          _n > 0 and (u"## 待画（%d 个" % _n) in listing)
    check(u"D6b 本轮**没有**动任何贴图/模型（毒马铃薯是原版物品）",
          not os.path.exists(os.path.join(ROOT, r"src\main\resources\assets\potato_s_t\textures\item\poisonous_potato.png")))''')

    # ---------- ⑤ 英文公告 ----------
    patch(u"公告：那句 N models still do this → 现数", ANN,
          u"borrowed from vanilla (15 models still do this",
          u"borrowed from vanilla (%d models still do this" % n)
    patch(u"公告：链子补上「素材线把这两张画了」", ANN,
          u'''  pieces, which deliberately borrow the vanilla iron set for now) -> 15 (the **Silver Wire** and
  **Silver Wire Spool**, new in 0.11 ZF127 — textures deliberately not drawn yet, as requested));''',
          u'''  pieces, which deliberately borrow the vanilla iron set for now) -> 15 (the **Silver Wire** and
  **Silver Wire Spool**, new in 0.11 ZF127, whose textures were deliberately not drawn yet at the
  time) -> 13 (the art line drew those two sprites right after, so the count came back down));''')

    for p in (z71, z90, z127, z128):
        try:
            compile(read(p), os.path.basename(p), u"exec")
        except SyntaxError as e:
            fails.append(u"%s 语法不过：%s" % (os.path.basename(p), e))

    print(u"\n".join(u"  [OK] " + x for x in notes))
    print(u"失败项 = %d" % len(fails))
    for f in fails:
        print(u"  !! " + f)
    return 1 if fails else 0


if __name__ == u"__main__":
    sys.exit(main())
