# -*- coding: utf-8 -*-
u"""_zf156_fix2.py —— 打包后补三笔：

  ① `_zf149_verify.py`：把被 `_zf156_retarget.py` 那个"多 job 排队写"bug **盖掉**的两处
     （docstring 与 `JAR` 路径）补回来（0.12 → 0.13）。
  ② `_zf149_jar.py`：`mods.toml` 渲染后的版本断言 0.12 → 0.13（第 8 行 docstring 一起）。
  ③ **修交接 §1 那一行被吃掉的字符** —— 它在 HEAD（ZF155 的 `57423ee`）里就是坏的：
     反引号被换成了 `\\`、开头 `` `r `` 整个没了（`release` 变成 `elease`）。
     这行是 §4.159"三处联动"的锚点之一，必须是一行**正常**的 markdown。
     顺手把成品换成 0.13。

跑法：python build\\zftools\\_zf156_fix2.py [--write]
"""
import hashlib
import io
import os
import sys

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding=u"utf-8", errors=u"replace")

ROOT = r"E:\PotatoST"
ZT = os.path.join(ROOT, "build", "zftools")
Z149V = os.path.join(ZT, u"_zf149_verify.py")
Z149J = os.path.join(ZT, u"_zf149_jar.py")
HAND = os.path.join(ROOT, "docs", u"多会话协作交接.md")
JAR = os.path.join(ROOT, "release", u"PotatoST-0.13.jar")

fails, notes = [], []


def sub(path, pairs, label):
    text = io.open(path, encoding="utf-8", newline=u"").read()
    for old, new in pairs:
        if new in text and old not in text:
            notes.append(u"  [跳过] %s：%s（已经是新的）" % (label, old[:44]))
            continue
        if text.count(old) != 1:
            fails.append(u"%s：锚点命中 %d 次 → %s" % (label, text.count(old), old[:60]))
            continue
        text = text.replace(old, new, 1)
        notes.append(u"  [改] %s：%s" % (label, old[:52].replace(u"\n", u" ")))
    io.open(path, u"w", encoding="utf-8", newline=u"").write(text)


def main(argv):
    write = u"--write" in argv
    sha = hashlib.sha1(open(JAR, "rb").read()).hexdigest()
    size = os.path.getsize(JAR)
    size_str = u"{:,}".format(size)
    print(u"成品：%s（%d B / %s）" % (os.path.basename(JAR), size, sha))

    # ① _zf149_verify.py 补两处
    sub(Z149V, [
        (u'u"""_zf149_verify.py —— ZF149 **常驻校验**：成品 `release\\\\PotatoST-0.12.jar` 里真的有手册。',
         u'u"""_zf149_verify.py —— ZF149 **常驻校验**：成品 `release\\\\PotatoST-0.13.jar` 里真的有手册。'),
        (u'JAR = os.path.join(ROOT, "release", u"PotatoST-0.12.jar")',
         u'JAR = os.path.join(ROOT, "release", u"PotatoST-0.13.jar")'),
    ], u"_zf149_verify.py 补回 JAR 路径")

    # ② _zf149_jar.py 的 mods.toml 版本断言
    sub(Z149J, [
        (u'  ④ `neoforge.mods.toml` 渲染后：版本 0.12、`patchouli` 是 required；',
         u'  ④ `neoforge.mods.toml` 渲染后：版本 0.13、`patchouli` 是 required；'),
        (u'check(u\'version="0.12"\' in toml, u"④ mods.toml 里版本是 0.12")',
         u'check(u\'version="0.13"\' in toml, u"④ mods.toml 里版本是 0.13")'),
    ], u"_zf149_jar.py mods.toml 版本")

    # ③ 交接 §1 成品行：整行重写（原行在 HEAD 里就是坏字符）
    hand = io.open(HAND, encoding="utf-8", newline=u"").read()
    lines = hand.split(u"\n")
    hit = [i for i, l in enumerate(lines) if u"已发布成品" in l]
    if len(hit) != 1:
        fails.append(u"交接 §1 成品行命中 %d 行" % len(hit))
    else:
        i = hit[0]
        old = lines[i]
        new = (u"| **已发布成品** | `release\\PotatoST-0.13.jar` = `%s`（%s B，**最新一次重打**："
               u"含 ZF148 手册 / ZF149 打包 / **ZF151 挖掘口径修复** / ZF150 金属粒 / ZF153 振金剑 / "
               u"ZF155 通用升级模板 / **ZF156 端子连线 / 手册只发一次 / 金属板跨 mod**）"
               u"⚠ 哈希**随重打走**：`_zf149_verify.py` 的 W2/W3 与公告一起对账（§4.159 三处联动） |"
               % (sha, size_str))
        if old == new:
            notes.append(u"  [跳过] 交接 §1 成品行（已经是新的）")
        else:
            lines[i] = new
            hand = u"\n".join(lines)
            io.open(HAND, u"w", encoding="utf-8", newline=u"").write(hand)
            broken = (u"\\" in old and u"`" not in old)
            notes.append(u"  [改] 交接 §1 成品行 → %s…（%s B）；旧行是坏字符行：%s"
                         % (sha[:12], size_str, u"是（反引号被吃）" if broken else u"否"))

    print(u"\n".join(notes))
    print(u"失败项 = %d" % len(fails))
    for f in fails:
        print(u"  !! " + f)
    if not write:
        print(u"⚠ 本脚本 ①②③ 三笔都是「补回 / 修坏」性质，**直接写盘**（不带 --write 也一样）")
    return 1 if fails else 0


if __name__ == u"__main__":
    sys.exit(main(sys.argv[1:]))
