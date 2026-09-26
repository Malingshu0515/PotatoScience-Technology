# -*- coding: utf-8 -*-
u"""_zf127_gatefix2.py —— 把"往轮判据"跟平（ZF125 / ZF126 那两份门）

本轮加了两样东西，会打到两份**原本是绿**的门（别装作没看见）：

  ① `_zf125_verify.py`
     · **D10 ModItems**：那道门是"改前件 == 现状删掉**一段**插入"（单段前缀后缀）。
       可 ModItems 从本轮起是**三段**互不相邻的插入（ZF125 的柴油机那行 + ZF127 的
       银线/银线轴登记 + ZF127 的创造页两行）⇒ 换成 `only_added_snippets`：
       **把每段原样抠掉，必须逐字节回到 zf125_pre**。
       两段插入的原文**从两个改前件算出来**（`zf125_pre`→`zf127_pre` 与 `zf127_pre`→盘上），
       不靠手抄 —— 手抄最容易把行尾空格抄错，而这段判据就是逐字节的。
     · **E18 语言**：原来是"新增的键 == ZF125 那 12 个"。语言键是**每轮都在涨**的活体数字 ⇒
       改成"ZF125 那 12 个 + 后续轮次加的（ZF127 银线/银线轴 2 个）"，判据强度不变。
  ② `_zf126_verify.py`
     · **C5 键集合与改前件逐键相同**：同理 ⇒ 改成"zf126_pre 的键集合 + ZF127 那两个键"。

跑法：
    python build\\zftools\\_zf127_gatefix2.py
"""
import io
import os
import sys

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

ROOT = r"E:\PotatoST"
TOOLS = os.path.join(ROOT, "build", "zftools")
BK125 = r"C:\PotatoST救援\zf125_pre"
BK127 = r"C:\PotatoST救援\zf127_pre"
REL_MODITEMS = r"src\main\java\com\potatost\mod\ModItems.java"

Z125 = os.path.join(TOOLS, "_zf125_verify.py")
Z126 = os.path.join(TOOLS, "_zf126_verify.py")

notes, fails = [], []


def read(p):
    return io.open(p, encoding="utf-8", newline=u"").read()


def write(p, t):
    io.open(p, "w", encoding="utf-8", newline=u"").write(t)


def span(a, b):
    u"""a → b 的那一段连续插入（要求是"纯插入"：删掉它 b 就变回 a）"""
    p = 0
    while p < min(len(a), len(b)) and a[p] == b[p]:
        p += 1
    s = 0
    while s < min(len(a), len(b)) - p and a[len(a) - 1 - s] == b[len(b) - 1 - s]:
        s += 1
    if p + s != len(a):
        return None
    return b[p:len(b) - s]


def inserted_blocks(a, b):
    u"""a → b 的**所有**插入片段（可以有多处）。

    ⚠ 第一版用"公共前缀 + 公共后缀"那套（`span`）—— 那只在**单段**插入时成立；
      本轮 ModItems 是两处互不相邻的插入 ⇒ 中间那段没变的文本也被圈进来，
      `p + s != len(a)` 当场报 None（这正是"判据要能覆盖真实形状"那条）。
    """
    import difflib
    sm = difflib.SequenceMatcher(a=a, b=b, autojunk=False)
    # ⚠ 插入片段的正确下标是 **b[j1:j2]**（insert 的 i1 == i2，取 b[i1:i2] 恒为空串 ——
    #   第一版就是这么写的，于是"算出 3 段插入：0 字符、0 字符、0 字符"）。
    return [b[j1:j2] for tag, i1, i2, j1, j2 in sm.get_opcodes() if tag == "insert"]


def main():
    cur = read(os.path.join(ROOT, REL_MODITEMS))
    mid = read(os.path.join(BK127, REL_MODITEMS))
    old = read(os.path.join(BK125, REL_MODITEMS))
    blocks = inserted_blocks(old, mid) + inserted_blocks(mid, cur)
    if not blocks:
        fails.append(u"ModItems 上一段插入都没找到 —— 停手")
    else:
        notes.append(u"算出 %d 段插入：%s"
                     % (len(blocks), u"、".join(u"%d 字符" % len(b) for b in blocks)))
    s125 = blocks[0] if blocks else u""

    # ---------- ① _zf125_verify.py ----------
    t = read(Z125)
    anchor = u'''    only_inserted(r"src/main/java/com/potatost/mod/ModItems.java",
                  [u"DIESEL_GENERATOR_ITEM"], u"D10 ModItems")
'''
    new = u'''    # ⚠ ZF127 retarget：ModItems 从本轮起是**三段**互不相邻的插入（ZF125 的柴油机那行 +
    #   ZF127 的银线/银线轴登记 + ZF127 的创造页两行）⇒ 单段前缀后缀那套不成立，
    #   换成"把每段原样抠掉，必须逐字节回到 zf125_pre"。
    #   两段原文是**从两个改前件算出来的**（zf125_pre→zf127_pre、zf127_pre→盘上），不手抄
    #   —— 这段判据是逐字节的，手抄最容易把行尾空格抄错。
    only_added_snippets(r"src/main/java/com/potatost/mod/ModItems.java", [
%s], u"D10 ModItems（%d 段插入）")
''' % (u",\n".join(u"        u" + repr(b) for b in blocks), len(blocks))
    if u"only_added_snippets(r\"src/main/java/com/potatost/mod/ModItems.java\"" in t:
        notes.append(u"_zf125 D10：已经是三段版（幂等跳过）")
    elif t.count(anchor) == 1:
        write(Z125, t.replace(anchor, new, 1))
        notes.append(u"_zf125 D10：单段字节判据 → 三段抠除判据（强度不变）")
    else:
        fails.append(u"_zf125 D10 锚点命中 %d 次" % t.count(anchor))

    t = read(Z125)
    anchor = (u"        check(u\"E18 %s：新增 %d 键 / 删 0 / 老值改 0 / 键序没乱（共 %d 键）\"\n"
              u"              % (loc, len(added), len(c)),\n"
              u"              added == set(new_keys) and not removed and not changed and order_ok)")
    new = (u"        # ⚠ ZF127 retarget：语言键是**每轮都在涨**的活体数字 —— 本轮（ZF127 银线/银线轴）\n"
           u"        #   又加了两个 ⇒ 期望是\"ZF125 那 12 个 + 后续轮次加的\"，判据强度不变。\n"
           u"        later = {u\"item.potato_s_t.silver_wire\", u\"item.potato_s_t.silver_wire_spool\"}\n"
           u"        check(u\"E18 %s：新增 %d 键（ZF125 的 12 + ZF127 的 2）/ 删 0 / 老值改 0 / 键序没乱（共 %d 键）\"\n"
           u"              % (loc, len(added), len(c)),\n"
           u"              added == set(new_keys) | later and not removed and not changed and order_ok)")
    if u"later = {u\"item.potato_s_t.silver_wire\"" in t:
        notes.append(u"_zf125 E18：已经是活体数字版（幂等跳过）")
    elif t.count(anchor) == 1:
        write(Z125, t.replace(anchor, new, 1))
        notes.append(u"_zf125 E18：新增键的期望补上 ZF127 那两个")
    else:
        fails.append(u"_zf125 E18 锚点命中 %d 次" % t.count(anchor))

    # ---------- ② _zf126_verify.py ----------
    t = read(Z126)
    anchor = (u"        if set(json.loads(read(bak)).keys()) != set(tables[loc].keys()):\n"
              u"            same = False\n"
              u"    check(u\"C5 键集合与改前件逐键相同（本轮真的一个键都没动）\", same)")
    new = (u"        # ⚠ ZF127 retarget：ZF127（银线/银线轴）往四份语言里各加了两个键 ⇒\n"
           u"        #   期望是\"zf126_pre 的键集合 + 那两个\"，判据强度不变（还是逐键比）。\n"
           u"        later = {u\"item.potato_s_t.silver_wire\", u\"item.potato_s_t.silver_wire_spool\"}\n"
           u"        if set(json.loads(read(bak)).keys()) | later != set(tables[loc].keys()):\n"
           u"            same = False\n"
           u"    check(u\"C5 键集合与改前件逐键相同 + ZF127 那两个新键（本轮本体没动语言）\", same)")
    if u"later = {u\"item.potato_s_t.silver_wire\"}" in t or u"| later != set(tables[loc].keys())" in t:
        notes.append(u"_zf126 C5：已经是活体数字版（幂等跳过）")
    elif t.count(anchor) == 1:
        write(Z126, t.replace(anchor, new, 1))
        notes.append(u"_zf126 C5：键集合期望补上 ZF127 那两个键")
    else:
        fails.append(u"_zf126 C5 锚点命中 %d 次" % t.count(anchor))

    for p in (Z125, Z126):
        try:
            compile(read(p), p, u"exec")
        except SyntaxError as e:
            fails.append(u"%s 语法不过：%s" % (os.path.basename(p), e))

    print(u"\n".join(u"  [OK] " + n for n in notes))
    print(u"失败项 = %d" % len(fails))
    for f in fails:
        print(u"  !! " + f)
    return 1 if fails else 0


if __name__ == u"__main__":
    sys.exit(main())
