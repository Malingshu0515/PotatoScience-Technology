# -*- coding: utf-8 -*-
u"""_zf176_docs.py —— ZF176 文档落笔（§4.176 + §5 行 + §9 段 + 交接第 40 条 + 英文公告）+ 哈希跟平。

背景：用户实测「还是不可以 要不然试试样本只能通过泵输入呢」⇒ 本轮把对外句柄**按接入面分工**：
上/下面 = 样板（输出罐），侧面 = 原料（输入罐），抽的一律是产物。

跑法：python build\\zftools\\_zf176_docs.py [--write]
"""
import hashlib
import io
import json
import os
import re
import sys
import zipfile

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding=u"utf-8", errors="replace")

ROOT = r"E:\PotatoST"
DOC = os.path.join(ROOT, "docs", u"开发档案.md")
HAND = os.path.join(ROOT, "docs", u"多会话协作交接.md")
ANN = os.path.join(ROOT, "docs", "UpdateAnnouncement_EN.md")
V149 = os.path.join(ROOT, "build", "zftools", u"_zf149_verify.py")
JAR = os.path.join(ROOT, "release", u"PotatoST-0.13.jar")

S4 = u"""### 4.176 【可用性雷】两个罐共用一个"聪明路由"的能力句柄 ⇒ 玩家**没法用泵先把样板给上**（0.13 ZF176）

用户实测第二轮反馈：「**还是不可以 要不然试试样本只能通过泵输入呢**」。

ZF166 那版把对外流体句柄做成"聪明路由"：同种优先 → 输入罐空就进输入罐 → 否则进空的那个罐。
逻辑本身没错，但对玩家是**不可预期**的：两个罐都空时，你从管子灌进去的第一笔**一定落到输入罐**
（那是"喂料"），于是"想用泵先给样板"这件事**做不到** —— 必须先想办法把输入罐喂上，第二笔才会进输出罐。

**正解（按接入面分工）**：`FluidConverterBlockEntity.handlerFor(side)`
- **上 / 下面** ⇒ 只碰**输出罐（样板）**（`getTanks() == 1`）；
- **四个侧面（含 null）** ⇒ `fill` 进**输入罐（原料）**，`drain` 从**输出罐**抽（产物要能从管子走）；
- `PotatoST.java` 的能力登记改成 `(machine, side) -> machine.handlerFor(side)`。

**教训**：机器"内部聪明"不等于"玩家能预期"。凡是**同一台机器上有两个语义不同的罐/槽**，
能力句柄就该**按面（或按罐序）明确分工**，而不是让玩家猜这一笔会落到哪 —— 猜错一次就是"这机器坏了"。
按面分工还能被 tooltip 一句话说清：「管道：上/下面 = 样板，侧面 = 原料，抽出来的永远是产物」。

"""

ROW = u"""| ZF176 | **无新备份根**（只改 `FluidConverterBlockEntity` / `PotatoST` / 五份 lang + 门/探针/文档；改前件用 `git show HEAD:`，与 ZF164/ZF168/ZF174 同例。⚠ 轮号：`_zf170_/171_/172_/174_` 都已被占，本轮 **ZF176**（§4.147）） | **0.13：让样板可以只用泵/管道就给上**（用户原话「还是不可以 要不然试试样本只能通过泵输入呢」）。① **病根**（§4.176）：所有面共用"聪明路由" ⇒ 两个罐都空时，管道灌进来的第一笔**必落输入罐**，玩家"想先用泵定样板"做不到。② **正解**：`handlerFor(side)` —— **上/下面 = 输出罐（样板，1 个罐）**、**四个侧面 = 输入罐（原料）+ 抽的一律是产物**；能力登记改走 `handlerFor(side)`（**只此一处**，其余机器仍是 `getFluidHandler`）。③ **按面探针 `Zf176Check` 10/0**：两罐全空时 `Direction.UP` 灌水 1000 mB ⇒ **直接进输出罐（样板定上了）**、输入罐没被碰；侧面灌我们的柴油 ⇒ 进输入罐、样板不动；从任一面抽 ⇒ 抽到的都是**输出罐里的产物**（账对得上）；负对照：样板已定时从上面灌别的流体 ⇒ 0 mB、样板不被顶掉。④ tooltip 五语改成按面说明（**只改值，键数 621/623 不变**）。⑤ 门加 G 段 ⇒ **28/0**。 | 见 §9 ｜ 见 §4.176 |
"""

S9 = u"""### ZF176（0.13）样板现在**可以只用泵给**了 —— **待你实测**

你第二轮的原话：「**还是不可以 要不然试试样本只能通过泵输入呢**」。按你这个思路做了，而且做成了**确定的规则**：

| 接到哪一面 | 灌进去的是 | 抽出来的是 |
|---|---|---|
| **上 / 下面** | **样板**（输出罐）—— 两罐全空时也能直接定上 | 产物（输出罐） |
| **四个侧面** | **原料**（输入罐） | 产物（输出罐） |

手倒那套照旧：**普通右键 = 原料**、**潜行右键 = 样板**、**空容器右键 = 把罐里的装走**。
tooltip 里也把这条写清了（五语），不用再猜。

**实测证据（真服务端，按面查能力）**：两个罐全空时从**上面**泵 1000 mB 水 ⇒ **直接落进输出罐 = 样板定上了**，
输入罐一个字节没动；从**侧面**泵我们的柴油 ⇒ 进输入罐、样板不动；从任一面抽 ⇒ 抽到的都是输出罐里的产物
（300 + 200 抽走后剩 500，账对得上）；负对照：样板已定时从上面灌**别的**流体 ⇒ 0 mB，样板不被顶掉 —— **10/0 全绿**。

**要你实测**：把泵/管道**接到机器的上面或下面**，把你要当样板的那种流体泵进去（罐全空也行）；
原料从**侧面**进；产物从管子抽走。
"""

HAND40 = u"""40. **ZF176 的账（0.13：让样板可以只用泵给）**：① 用户第二轮反馈「还是不可以 要不然试试样本只能通过泵输入呢」；
    病根是**所有面共用一个"聪明路由"**（§4.176）：两罐全空时管道的第一笔必落输入罐 ⇒ 先用泵定样板做不到。
    ② 正解：`FluidConverterBlockEntity.handlerFor(side)` —— **上/下面 = 输出罐（样板，1 罐）**、
    **侧面 = 输入罐 + 抽的一律是产物**；`PotatoST.java` 登记改 `handlerFor(side)`（⚠ 只改转化器那一处，
    `getFluidHandler()` 这个串在文件里有 4 处，我第一遍一次全替换、误伤了灌装机/饮料罐装机/柴油发电机，
    已用 `_zf176_fixreg.py` 按"归属检查"改回 —— 教训：**批量替换前先数命中次数**）。
    ③ 按面探针 `Zf176Check` **10/0**；门加 G 段（**28/0**）。④ tooltip 五语改成按面说明（只改值）。
"""


def sha(p):
    h = hashlib.sha1()
    with open(p, "rb") as fh:
        for c in iter(lambda: fh.read(1 << 16), b""):
            h.update(c)
    return h.hexdigest()


def read(p):
    return io.open(p, encoding="utf-8", newline=u"").read()


def main(argv):
    write = u"--write" in argv
    if not os.path.isfile(JAR):
        print(u"!! 成品不在")
        return 1
    size, h = os.path.getsize(JAR), sha(JAR)
    z = zipfile.ZipFile(JAR)
    names = z.namelist()
    cls = len([n for n in names if n.endswith(u".class")])
    recipes = len([n for n in names if n.startswith(u"data/potato_s_t/recipe/") and n.endswith(u".json")])
    keys_zh = len(json.loads(z.read(u"assets/potato_s_t/lang/zh_cn.json").decode("utf-8")))
    keys_lzh = len(json.loads(z.read(u"assets/potato_s_t/lang/lzh.json").decode("utf-8")))
    print(u"成品：%d 字节 / sha1 %s / class %d / 配方 %d / 键 %d+%d" % (size, h, cls, recipes, keys_zh, keys_lzh))
    v149 = read(V149)
    m = re.search(u'WANT_SHA = u?"([0-9a-f]{40})"', v149)
    old_sha = m.group(1) if m else u""
    m = re.search(u"WANT_SIZE = (\\d+)", v149)
    old_size = u"{:,}".format(int(m.group(1))) if m else u""
    m = re.search(u"\\*\\*(\\d+) classes, 43 advancements", read(ANN))
    old_cls = m.group(1) if m else u""
    print(u"旧靶子：sha %s… size %s class %s" % (old_sha[:12], old_size or u"?", old_cls or u"?"))
    fails = []

    def refresh(text):
        if old_sha:
            text = text.replace(old_sha, h)
        if old_size:
            for unit in (u" 字节", u" bytes", u" B"):
                text = text.replace(old_size + unit, u"{:,}{}".format(size, unit))
        if old_cls:
            text = re.sub(u"class " + old_cls + u"；§4\\.159", u"class %d；§4.159" % cls, text)
        text = re.sub(u"\\*\\*\\d+ classes, 43 advancements, \\d+ recipes\\*\\*",
                      u"**%d classes, 43 advancements, %d recipes**" % (cls, recipes), text)
        text = re.sub(u"跟到 \\d+ / \\d+（43 不变", u"跟到 %d / %d（43 不变" % (cls, recipes), text)
        text = re.sub(u"\\*\\*(\\d+) 键 × 4\\*\\*", u"**%d 键 × 4**" % keys_zh, text)
        text = re.sub(u"\\((\\d+) keys each\\)", u"(%d keys each)" % keys_zh, text)
        text = re.sub(u"plus Literary Chinese with (\\d+)\\.",
                      u"plus Literary Chinese with %d." % keys_lzh, text)
        return text

    doc = read(DOC)
    if u"### 4.176 " not in doc:
        a = u"| ZF147 |"
        if doc.count(a) != 1:
            fails.append(u"档案 §5 表头锚点 %d 次" % doc.count(a))
        else:
            doc = doc.replace(a, S4 + a, 1)
    if u"| ZF176 |" not in doc:
        a2 = u"| 见 §9 ｜ 见 §4.174 |\n"
        if doc.count(a2) != 1:
            fails.append(u"档案 ZF174 行尾锚点 %d 次" % doc.count(a2))
        else:
            doc = doc.replace(a2, a2 + ROW + u"\n", 1)
    if u"### ZF176（0.13）" not in doc:
        a3 = u"## 10. 备份策略"
        if doc.count(a3) != 1:
            fails.append(u"档案 §10 锚点 %d 次" % doc.count(a3))
        else:
            doc = doc.replace(a3, S9 + u"\n" + a3, 1)
    doc = refresh(doc)
    if write and not fails:
        io.open(DOC, "w", encoding="utf-8", newline=u"").write(doc)

    hand = read(HAND)
    if u"40. **ZF176 的账" not in hand:
        a4 = u"## 7. ZF146 这一轮的交接"
        if hand.count(a4) != 1:
            fails.append(u"交接 §7 锚点 %d 次" % hand.count(a4))
        else:
            hand = hand.replace(a4, HAND40 + u"\n" + a4, 1)
    hand = refresh(hand)
    if write and not fails:
        io.open(HAND, "w", encoding="utf-8", newline=u"").write(hand)

    vn = read(V149)
    vn = re.sub(u'WANT_SHA = u?"[0-9a-f]{40}"', u'WANT_SHA = u"%s"' % h, vn, count=1)
    vn = re.sub(u"WANT_SIZE = \\d+", u"WANT_SIZE = %d" % size, vn, count=1)
    vn = re.sub(u"\\*\\*\\d+ classes, 43 advancements, \\d+ recipes\\*\\*",
                u"**%d classes, 43 advancements, %d recipes**" % (cls, recipes), vn)
    vn = re.sub(u"跟到 \\d+ / \\d+（43 不变", u"跟到 %d / %d（43 不变" % (cls, recipes), vn)
    if vn == read(V149):
        fails.append(u"_zf149_verify.py：一个靶子都没换到")
    elif write and not fails:
        io.open(V149, "w", encoding="utf-8", newline=u"").write(vn)

    ann = read(ANN)
    if u"## New in 0.13 ZF176" not in ann:
        a5 = u"## New in 0.13 ZF174 - No more spilling fluid into the world"
        if ann.count(a5) != 1:
            fails.append(u"公告 ZF174 段锚点 %d 次" % ann.count(a5))
        else:
            block = (u"## New in 0.13 ZF176 - Feed the sample with a pipe\n\n"
                     u"- **The Fluid Converter's fluid handler is now split by face**, so you can set the\n"
                     u"  sample with a pump instead of guessing which tank a pipe will fill:\n"
                     u"  - **top and bottom faces -> the SAMPLE tank** (the output tank; one tank only),\n"
                     u"  - **the four sides -> the INPUT tank** (raw fluid), and draining from any face\n"
                     u"    always yields the product (the output tank).\n"
                     u"- This matters because both tanks start empty: with the old \"smart routing\" the\n"
                     u"  first pipe-full always landed in the input tank, so you could not set the sample\n"
                     u"  with a pump at all.\n"
                     u"- Hand pouring is unchanged: right-click = input, sneak-right-click = sample,\n"
                     u"  right-click with an empty container = take fluid out. The tooltip now spells the\n"
                     u"  pipe rule out in all five languages.\n"
                     u"- Verified on a real server by querying the capability per face: with both tanks\n"
                     u"  empty, 1,000 mB pumped into the top face lands in the output tank (sample set),\n"
                     u"  the sides fill the input tank, draining always takes the product (500 mB left\n"
                     u"  after taking 300 + 200), and a different fluid cannot displace the sample. 10/0.\n"
                     u"- **Download:** `release/PotatoST-0.13.jar` - **{size} bytes**, sha1 **`{sha}`**.\n\n"
                     ).format(size=u"{:,}".format(size), sha=h)
            ann = ann.replace(a5, block + a5, 1)
    ann = refresh(ann)
    if write and not fails:
        io.open(ANN, "w", encoding="utf-8", newline=u"").write(ann)

    print(u"模式：%s" % (u"落盘" if write else u"干跑（不写）"))
    print(u"失败 = %d" % len(fails))
    for f in fails:
        print(u"  !! " + f)
    return 1 if fails else 0


if __name__ == u"__main__":
    sys.exit(main(sys.argv[1:]))
