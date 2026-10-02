# -*- coding: utf-8 -*-
u"""_zf168_docs.py —— ZF168 的文档落笔（§4.173 + §5 行 + §9 小节 + 交接第 38 条 + 英文公告），
并把哈希/体积/class 数/配方数/键数跟到刚打出来的那份 jar 上（口径同 `_zf166_docs.py`）。

跑法：python build\\zftools\\_zf168_docs.py [--write]
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

S4 = u"""### 4.173 【语义雷 + API 雷】`FluidTank` 对异种流体一律拒收；NeoForge 的桶包装器**按整桶结算**（0.13 ZF168）

用户实测一句话：「**转换器的输出储罐好像改不了**」。拆开是两件事，两件都在 API 的语义里：

**① `FluidTank` 不是"能装任何流体的罐"，而是"认准了第一种流体之后只收这一种"。**
`FluidTank#isFluidValid` 内部是 `isFluidEqual` —— 罐里已经有流体时，**异种流体一律拒收**（返回 0）。
而 ZF166 那版只给了"容器 → 机器"一条路（`pourFrom`），于是**样板一旦定下就再也换不掉**：
手倒换不了（异种拒收）、管道也换不了（能力那条路只在罐空时才收别的流体）、界面更没法清空。
正解不是"放宽拒收"（那会把罐里的东西凭空扔掉），而是**补反方向那条路**：
`fillContainerFrom`（手拿**空**容器右键 = 从罐装进容器）⇒ 玩家「空桶把旧样板装走 → 罐空了 →
再倒新样板」，全程一滴不丢。外加一句明确提示（`pour.occupied` 键）：拿有流体的容器右键、
而目标罐里是另一种流体时，机器会直接告诉玩家"先拿空容器把它装走"。

**② NeoForge 的 `FluidBucketWrapper` 只认整桶：`drain(小于 1000 的量)` 返回 `FluidStack.EMPTY`。**
这一条是"修好之后探针里唯一一条红的"——`heldFluid()` 当时用 `drain(1, SIMULATE)` 探"手里桶里有什么"，
永远拿不到东西 ⇒ 那句提示**永远不出现**（玩家看到的还是"什么都没发生"）。
同理，倒的方向也不能"按罐的余量取"：罐里只剩 600 mB 余量时，`drain(600)` 对桶返回空 ⇒
一整桶水**倒不进去**。正解：**整桶模拟、整桶取**，罐里塞不下的部分再 `fill` 回容器
（`pourFrom` 里那三行；`heldFluid` 用 `drain(Integer.MAX_VALUE, SIMULATE)`）。

**教训**：机器"看着没反应"时，先分清是**罐的语义**（异种拒收）还是**能力的语义**（只认整桶），
两者都会让代码"正确但不работа"——`_zf168_verify.py` 的 D 段与探针的 B2 就是钉这两条的。
"""

ROW = u"""| ZF168 | **新建 `zf168_pre`**（**1478 份**：`FluidConverter*` 四份 java / 五份 lang / 三份文档 / 常驻门与打包脚本 / 成品 0.13 + `.sha1` + `build\\libs` 那份；逐份核 sha1 + 回读，失败 0。⚠ 开工前查过轮号：`_zf168_*` 没人占（§4.147）） | **0.13：修「转换器的输出储罐改不了」**（用户原话见 §9）。① **病根**（§4.173①）：`FluidTank` 对**异种流体一律拒收**，而 ZF166 只给了"容器 → 机器"一条路 ⇒ 样板定下就换不掉（手倒拒收、管道只在罐空时收、界面也没法清空）。② **正解**：补反方向 `fillContainerFrom`（**手拿空容器右键 = 从输出罐装走**；潜行 = 从输入罐装走），换样板流程变成「空桶装走旧的 → 罐空 → 倒新的」，**一滴流体都不凭空消失**（先装容器、再按实际量抽罐，多了退回去）。③ **加一句明确提示**：拿有流体的容器右键、而目标罐里是另一种流体 ⇒ 机器直说「先拿空容器把它装走」（新键 `gui.potato_s_t.fluid_converter.pour.occupied`）。④ **顺手挖出一条 API 雷**（§4.173②）：NeoForge 的桶包装器**只认整桶**（`drain(<1000)` 返回空）⇒ `heldFluid()` 改用 `drain(Integer.MAX_VALUE, SIMULATE)`，倒的方向改成"整桶取、塞不下的还回容器"（否则罐里余量不足一桶时整桶水倒不进去）。⑤ **真开服探针 `Zf168Check` 12/0**（水/岩浆两种**原版有桶**的流体，避开"这个 mod 没给桶"的坑）：设样板 → 直接换被拒并给提示 → 空桶装走 1000 mB（手里变满桶）→ 罐空后换样板成功，外加 4 条负对照与守恒。⑥ 语言 **620 → 621**（lzh 622 → 623，只加那一个键）。⑦ **重打成品**：`release\\PotatoST-0.13.jar` = **{size} 字节 / sha1 `{sha}`**（class {cls}；§4.159 三处联动）。 | 见 §9 ｜ 见 §4.173 |
"""

S9 = u"""### ZF168（0.13）修「转换器的输出储罐改不了」—— **现在换得了了**

你报的原话：「**转换器的输出储罐好像改不了**」。查清了，是**两条 API 语义**叠出来的，不是界面问题：

**① 为什么改不了**：那个罐不是"什么都能装的罐" —— 它认准了第一种流体之后**只收这一种**
（Minecraft 的 `FluidTank` 就是这规矩：异种流体一律拒收）。而上一版只给了"**把容器里的倒进罐**"
一条路 ⇒ 样板一旦定下，手倒换不了、管道也换不了（管道只在罐空时才收别的流体）、界面里更没有"清空"。
**你看到的就是"右键半天，一点反应都没有"。**

**② 现在怎么换**（新加的路，和倒进去对称）：
- **手拿空桶（或空的气罐/油桶/别的 mod 的空容器）右键机器 = 从输出罐把样板装走**；潜行右键 = 从输入罐装走。
- 于是换样板 = **空桶右键装走旧的 → 罐空了 → 再倒新的进去**。全程**一滴流体都不凭空消失**
  （装走的量 == 桶里真正拿到的量，罐里塞不下的部分还回容器）。
- 你要是**忘了这一步**、直接拿"装着另一种流体的桶"右键：机器现在会**明说**
  「输出罐里已经是别的流体（X）—— 手拿空容器右键机器就能把样板装走，然后再倒新的」。

**③ 顺手挖出一条真雷（顺便修掉）**：NeoForge 的**桶包装器只认整桶** ——
`drain(少于 1000 mB)` 会返回空。所以"罐里只剩不到一桶的余量时，一整桶水会倒不进去"，
而"探手里桶里装的是什么"也会永远探不到（那句提示就永远不出现）。现在改成**整桶模拟、整桶取、
塞不下的还回容器**。

**④ 实测证据（真服务端）**：水桶设样板 → 直接倒岩浆**被拒**（罐一滴不动）且给出提示 →
空桶右键装走 1000 mB（手里变满桶）→ 罐空后倒岩浆**成功**（样板换成岩浆）；
外加 4 条负对照（空罐装不出、钻石装不出、空罐不产生假桶、往输入罐倒水也进不去）与守恒 —— **12/0 全绿**。

**⑤ 要你实测**：拿一桶**别的流体**（比如水）对着转化器右键设成样板，然后**空桶右键**把它装回来，
再倒你要的那种 —— 三下之内应该能换掉；直接拿别的流体倒，机器会告诉你先装走。
"""

HAND38 = u"""38. **ZF168 的账（0.13：修「转换器的输出储罐改不了」）**：① 用户原话见档案 §9；两条 API 语义见 **§4.173**
    （`FluidTank` 异种流体一律拒收 ⇒ 样板换不掉；NeoForge **桶包装器只认整桶** ⇒ `drain(<1000)` 返回空、
    探不出桶里有什么、余量不足一桶时整桶水倒不进）。② 加的是**反方向那条路** `fillContainerFrom`
    （手拿空容器右键 = 从罐装走；潜行 = 从输入罐），换样板 = 空桶装走旧的 → 罐空 → 倒新的；
    **一滴不凭空消失**（先装容器再按实际量抽罐，多了退回去）。③ 加一句明确提示（新键
    `gui.potato_s_t.fluid_converter.pour.occupied`，语言 620 → 621 / lzh 622 → 623）。
    ④ 探针 `Zf168Check` **12/0**（水与岩浆两种原版有桶的流体，避开"这个 mod 没给桶"的坑）。
    ⑤ ⚠ 教训：机器"看着没反应"时先分清是**罐的语义**还是**能力的语义** —— 两者都会让代码
    "正确但不动"；`_zf168_verify.py` 的 D 段与探针 B2 就是钉这两条的。
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
        print(u"!! 成品不在：%s（先打包）" % JAR)
        return 1
    size, h = os.path.getsize(JAR), sha(JAR)
    z = zipfile.ZipFile(JAR)
    names = z.namelist()
    cls = len([n for n in names if n.endswith(u".class")])
    recipes = len([n for n in names if n.startswith(u"data/potato_s_t/recipe/") and n.endswith(u".json")])
    keys_zh = len(json.loads(z.read(u"assets/potato_s_t/lang/zh_cn.json").decode("utf-8")))
    keys_lzh = len(json.loads(z.read(u"assets/potato_s_t/lang/lzh.json").decode("utf-8")))
    print(u"成品：%d 字节 / sha1 %s / class %d / 配方 %d / 键 %d+%d"
          % (size, h, cls, recipes, keys_zh, keys_lzh))
    v149 = read(V149)
    m = re.search(u'WANT_SHA = u"([0-9a-f]{40})"', v149)
    old_sha = m.group(1) if m else u""
    m = re.search(u"WANT_SIZE = (\\d+)", v149)
    old_size = u"{:,}".format(int(m.group(1))) if m else u""
    m = re.search(u"\\*\\*(\\d+) classes, 43 advancements", read(ANN))
    old_cls = m.group(1) if m else u""
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
    if u"### 4.173 " not in doc:
        a = u"| ZF147 |"
        if doc.count(a) != 1:
            fails.append(u"档案：§5 表头锚点 %d 次" % doc.count(a))
        else:
            doc = doc.replace(a, S4 + a, 1)
    if u"| ZF168 |" not in doc:
        a2 = u"| 见 §9 ｜ 见 §4.172 |\n"
        if doc.count(a2) != 1:
            fails.append(u"档案：ZF166 行尾锚点 %d 次" % doc.count(a2))
        else:
            doc = doc.replace(a2, a2 + ROW.format(size=u"{:,}".format(size), sha=h, cls=cls) + u"\n", 1)
    if u"### ZF168（0.13）" not in doc:
        a3 = u"## 10. 备份策略"
        if doc.count(a3) != 1:
            fails.append(u"档案：§10 锚点 %d 次" % doc.count(a3))
        else:
            doc = doc.replace(a3, u"\n" + S9 + u"---\n\n## 10. 备份策略", 1)
    doc = refresh(doc)
    if write and not fails:
        io.open(DOC, "w", encoding="utf-8", newline=u"").write(doc)

    hand = read(HAND)
    if u"38. **ZF168 的账" not in hand:
        a4 = u"## 7. ZF146 这一轮的交接（星轨坠的仪式状态搬进存档）"
        if hand.count(a4) != 1:
            fails.append(u"交接：§7 锚点 %d 次" % hand.count(a4))
        else:
            hand = hand.replace(a4, u"\n" + HAND38 + u"\n---\n\n## 7. ZF146 这一轮的交接", 1)
    hand = refresh(hand)
    if write and not fails:
        io.open(HAND, "w", encoding="utf-8", newline=u"").write(hand)

    vn = read(V149)
    vn = re.sub(u'WANT_SHA = u"[0-9a-f]{40}"', u'WANT_SHA = u"%s"' % h, vn, count=1)
    vn = re.sub(u"WANT_SIZE = \\d+", u"WANT_SIZE = %d" % size, vn, count=1)
    vn = re.sub(u"\\*\\*\\d+ classes, 43 advancements, \\d+ recipes\\*\\*",
                u"**%d classes, 43 advancements, %d recipes**" % (cls, recipes), vn)
    vn = re.sub(u"跟到 \\d+ / \\d+（43 不变", u"跟到 %d / %d（43 不变" % (cls, recipes), vn)
    if vn == read(V149):
        fails.append(u"_zf149_verify.py：一个靶子都没换到")
    elif write and not fails:
        io.open(V149, "w", encoding="utf-8", newline=u"").write(vn)

    ann = read(ANN)
    if u"## New in 0.13 ZF168" not in ann:
        a5 = u"## New in 0.13 ZF166 - The Fluid Converter: same-tag fluids, across mods"
        if ann.count(a5) != 1:
            fails.append(u"公告：ZF166 段锚点 %d 次" % ann.count(a5))
        else:
            block = (u"## New in 0.13 ZF168 - The Fluid Converter's output tank can now be changed\n\n"
                     u"- **You can now change the sample (target) fluid in the Fluid Converter.**\n"
                     u"  A Minecraft fluid tank only ever accepts the fluid it already holds, and the\n"
                     u"  machine only had a \"container -> machine\" path, so once a sample was set it\n"
                     u"  could not be replaced at all - which is what \"the output tank cannot be\n"
                     u"  changed\" was about.\n"
                     u"- **New: right-click the machine with an *empty* container to take fluid out of\n"
                     u"  the output tank** (sneak-right-click for the input tank). To switch samples:\n"
                     u"  empty the output tank with an empty bucket, then pour the new fluid in. Not a\n"
                     u"  single mB is created or destroyed.\n"
                     u"- If you right-click with a container that holds a *different* fluid, the\n"
                     u"  machine now tells you to take the old sample out first.\n"
                     u"- Verified on a real server: sample set -> direct swap refused (with the hint) ->\n"
                     u"  empty bucket takes 1000 mB out (bucket comes back full) -> the new sample pours\n"
                     u"  in fine, plus four negative controls (12/0).\n"
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
