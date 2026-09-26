# -*- coding: utf-8 -*-
u"""_zf137_rename.py —— 把"星璨钢头盔夜视"这一轮从 **ZF135 改号到 ZF137**（防撞号）

## 为什么要改

多条线在**同一分钟里**各自开工，号是抢的：

| 号 | 谁用过 |
|---|---|
| ZF134 | 我（星璨钢斧的配方，21:39 起）+ 冲击波那条线（`_zf134_manager*.py`，21:50 起） |
| ZF135 | 贴图/动画那条线（`_zf135_anim.py` 等，**22:00:48** 起）+ 我（夜视，22:03:17 起） |
| ZF136 | 振金加强那条线（`ModArmorMaterials` 里已经写着「⚠ ZF136：护甲值各 +1」） |

⇒ 这一轮改用 **ZF137**（134/135/136 都被占了），只改**我自己的**文件与引用它的三处：
`_zf104_gates.ps1` 的两段段名、`_zf104_gatecount.py` 的注释、档案里那一节的标题。

⚠ **不许**碰别人的 `_zf135_*.py`（贴图/动画线那一批）—— 它们的号与我无关。

跑法：
    python build/zftools/_zf137_rename.py            # 只体检
    python build/zftools/_zf137_rename.py --write
"""
import io
import os
import sys

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

PROJ = r"E:\PotatoST"
ZT = os.path.join(PROJ, "build", "zftools")
ARCH = os.path.join(PROJ, "docs", "开发档案.md")

OLD, NEW = u"zf135", u"zf137"
# 只动这一轮自己的文件（贴图/动画线那批 `_zf135_anim/dedupe/look/fluidcheck/preview/docs/section/pitfall/row` 一律不碰）
MY_FILES = [u"_zf135_verify.py", u"_zf135_falsify.py", u"_zf135_lang.py",
            u"_zf135_falsify.txt", u"_zf135_compile.log", u"_zf135_falsify_compile.log"]
# 引用它们的两个共用件（整份里的 zf135 只出现在我这两段/这行注释里）
REFS = [
    (os.path.join(ZT, u"_zf104_gates.ps1"),
     [(u"ZF135 verify", u"ZF137 verify"), (u"ZF135 falsify", u"ZF137 falsify"),
      (u"# ZF135 本轮：星璨钢头盔给夜视 I / 4 s", u"# ZF137 本轮：星璨钢头盔给夜视 I / 4 s")]),
    (os.path.join(ZT, u"_zf104_gatecount.py"),
     [(u"**ZF135 再加两段**（`ZF135 verify` + `ZF135 falsify`）",
       u"**ZF137 再加两段**（`ZF137 verify` + `ZF137 falsify`）")]),
]

fails = []


def main(argv):
    write = u"--write" in argv
    for name in MY_FILES:
        src = os.path.join(ZT, name)
        dst = os.path.join(ZT, name.replace(OLD, NEW))
        if not os.path.isfile(src):
            fails.append(u"找不到 %s" % name)
            continue
        if os.path.exists(dst):
            fails.append(u"目标已存在（别人占了？）：%s" % os.path.basename(dst))
            continue
        print(u"  [%s] %s → %s" % (u"改" if write else u"将改", name, os.path.basename(dst)))
        if not write:
            continue
        if name.endswith(u".py"):
            text = io.open(src, encoding="utf-8").read()
            n = text.count(OLD)
            text = text.replace(OLD, NEW)
            try:
                compile(text, dst, "exec")
            except SyntaxError as e:
                fails.append(u"%s 改完语法坏：%s" % (name, e))
                continue
            io.open(dst, "w", encoding="utf-8", newline=u"").write(text)
            print(u"        ↳ 内部 %s → %s 共 %d 处" % (OLD, NEW, n))
        else:
            io.open(dst, "wb").write(io.open(src, "rb").read())
        os.remove(src)

    for path, pairs in REFS:
        name = os.path.basename(path)
        text = io.open(path, encoding="utf-8").read()
        hits = 0
        for a, b in pairs:
            if a in text:
                print(u"  [%s] %s：%s" % (u"改" if write else u"将改", name, a[:44]))
                text = text.replace(a, b)
                hits += 1
        if u"ZF135" in text.replace(u"ZF1350", u""):
            fails.append(u"%s 里还残留 ZF135（可能有别人的段也被改到，停手）" % name)
            continue
        if write and hits:
            io.open(path, "w", encoding="utf-8", newline=u"").write(text)

    # 档案那一节：标题与正文里的 ZF135 → ZF137（只在那一节里，别动别处）
    text = io.open(ARCH, encoding="utf-8").read()
    i = text.find(u"### ZF135（0.11）星璨钢头盔给夜视")
    j = text.find(u"### ZF13", i + 10)
    if i < 0:
        fails.append(u"档案里找不到那一节的标题")
    else:
        end = j if j > 0 else len(text)
        sec = text[i:end]
        n = sec.count(u"ZF135")
        print(u"  [%s] 开发档案.md：那一节里 %s → %s 共 %d 处" % (u"改" if write else u"将改", OLD, NEW, n))
        if write:
            text = text[:i] + sec.replace(u"ZF135", u"ZF137") + text[end:]
            io.open(ARCH, "w", encoding="utf-8", newline=u"").write(text)

    print(u"\n失败项 = %d" % len(fails))
    for f in fails:
        print(u"  !! " + f)
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
