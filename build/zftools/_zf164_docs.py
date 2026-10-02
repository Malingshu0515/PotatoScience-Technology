# -*- coding: utf-8 -*-
u"""_zf164_docs.py —— ZF164 的文档落笔（§4.171 + §5 行 + §9 小节 + 交接第 36 条 + 英文公告），
并顺手把 §4.159 三处联动的哈希/体积/class 数跟到刚打出来的那份 jar 上。

跑法：python build\\zftools\\_zf164_docs.py [--write]
"""
import hashlib
import io
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

S4 = u"""### 4.171 【兼容雷】Mek 10.7 的气体并进了「化学品」API；而 `DefaultedRegistry.get()` 查不到会**回默认值**（0.13 ZF164）

用户原话：「**mek喷气背包还是不可以灌本mod的氢 你看看能不能做一下兼容 或者搞一个流体转化装置
可以把本mod的流体转成同标签的别的mod流体**」。这一轮两次被"看起来对"的 API 骗到：

**① Mek 里没有 `IGasHandler` / `GasStack` 了 —— 气体并进了化学品。**
`javap` 在 `Mekanism-1.21.1-10.7.19.85.jar` 上找 `mekanism.api.gas.IGasHandler` 直接报"找不到类"；
真正的东西是 `mekanism.api.chemical.{IChemicalHandler, ChemicalStack, Chemical}`，
而物品侧的能力名是 **`mekanism:chemical_handler`**（`javap -c mekanism.common.capabilities.Capabilities`
里那句 `ldc "chemical_handler"`），**不是** `gas_handler`。猜名字的代价就是整轮白写。

**② `MekanismAPI.CHEMICAL_REGISTRY` 是 `DefaultedRegistry`，`get(不存在的 id)` 会回默认值
（`mekanism:empty`），不会给 `null`。** 于是"这个流体在 Mek 那边有没有同名化学品"这件事，
直接 `get(...) != null` 判会**一律判成"有"** —— 探针 A5（负对照）第一跑就是这么红的。
正解：拿 `getKey(candidate)` 反查一遍，只有"注册表里真挂在这个 id 上"才算数
（`MekChemicalBridge.chemicalFor` 里那一行，判据由 `_zf164_verify.py` A5 钉住）。

**这一轮定下来的做法（可复用）**

| 事 | 口径 |
|---|---|
| 映射 | 我们的流体身上的 `c:<名字>` 标签 ⇒ Mek 注册表里**同路径**的化学品（我们的氢 `c:hydrogen` ⇒ `mekanism:hydrogen`）。**一个气体名都不硬写**：找得到就灌、找不到就当灌不了。与 Mek 自己的旋转冷凝器配方同口径（ZF159 已实测 `1 mekanism:oxygen` ⇒ **1:1**） |
| 软依赖 | 全工程**只有** `MekChemicalBridge.java` 一个文件 `import mekanism.*`，而它的**公开方法签名里只有原版/NeoForge 类型** ⇒ 灌装机只在 `present()` 为真时才调它，没装 Mek 的实例根本不会加载这个类；`build.gradle` 用 `compileOnly`（libs 里那份 jar 是 MIT，**不进产物**） |
| 安全性 | 沿用 ZF162 那两道闸：先 `SIMULATE` 算得出能进多少，再 `EXECUTE`；**灌装机只按"真的进去了多少"扣罐扣电**，绝不凭空吞流体 |
| 探针怎么真验 | 把 Mek 拷进 `run\\server\\mods` 跑真服务端（`run/server` 平时只有帕秋莉 + 机械动力），跑完删掉；探针 19 项全绿，其中 B2 是"**喷气背包里真的多出 100 mB 的 `mekanism:hydrogen`**"，B5 是质量守恒（罐 −100 / 物品 +100） |

"""

ROW = u"""| ZF164 | **新建 `zf164_pre`**（**1175 份**：`build.gradle` / `libs/Mekanism-*.jar` / 5 个 java（含新桥）/ 五份 lang / 三份文档 / 常驻门与打包脚本 / 成品 0.13 + `.sha1` + `build\\libs` 那份；逐份核 sha1 + 回读，失败 0。⚠ 开工前查过轮号：`_zf164_*` 没人占（§4.147）） | **0.13：灌装机 × Mekanism —— 用户的喷气背包现在能灌我们的氢了**（用户原话见 §9）。① **先把 API 查清楚**（两次翻车见 §4.171）：Mek 10.7 的气体已并进**化学品** API，物品能力名是 `mekanism:chemical_handler`，类型是 `IChemicalHandler`/`ChemicalStack`（`IGasHandler`/`GasStack` 已不存在）；`MekanismAPI.CHEMICAL_REGISTRY` 是 `DefaultedRegistry`，`get()` 查不到会**回默认值** ⇒ 必须 `getKey()` 反查。② **软依赖**：`libs/Mekanism-1.21.1-10.7.19.85.jar`（MIT，12 MB，照 JEI/帕秋莉那条"离线构建用本地 jar"的先例）+ `compileOnly`；**全工程只有 `MekChemicalBridge` 一个文件 import `mekanism.*`**，且它的公开签名里没有 Mek 类型 ⇒ 没装 Mek 的实例不会加载它，`_zf164_verify.py` A6/A7 + D1/D2 四处钉住。③ **映射**：我们流体的 `c:<名字>` 标签 ⇒ Mek 注册表同路径化学品（氢/氧/氯/硫酸都对得上；原油/柴油/石脑油/液化气/汽油在 Mek 那边**没有**同名化学品 ⇒ 照旧灌不了），1:1，与 Mek 旋转冷凝器同口径；**映射查一次缓存一次**。④ **灌装机第三条路**：`tryFillSlot` 末尾接 `tryFillMekChemical`，顺序 = 自家气罐/油桶 → 别人的**液体**容器（ZF162）→ **Mek 化学品容器**；`spaceFor`/`acceptsFluid`/`stateOf` 三处都先问 `present()`；安全闸门与 ZF162 一致（SIMULATE → EXECUTE，**只按真进去的量扣罐扣电**）。⑤ **真开服探针 `Zf164Check` 19 项 ALL OK**（Mek 拷进 `run/server/mods` 跑、跑完删掉）：**喷气背包里真的多出 100 mB 的 `mekanism:hydrogen`**、罐 5000→4900、电 −1200 FE、质量守恒、诊断不再说"灌不了"，外加 6 条负对照（绿宝石 / Mek 没有同名化学品的流体 / 原油 / 自家气罐两条老规矩 / 锁定数字）。⑥ 常驻 `_zf164_verify.py`（A 软依赖 8 / B 第三条路 4 / C 探针文档键数 5 / D 产物软依赖 2）。⑦ **语言键数不变**（593×4 + 595，诊断复用现有的 `UNSUPPORTED`）⇒ 键数门一份都不用动。⑧ **重打成品**：`release\\PotatoST-0.13.jar` = **{size} 字节 / sha1 `{sha}`**（class {cls}；§4.159 三处联动）。 | 见 §9 ｜ 见 §4.171 |
"""

S9 = u"""### ZF164（0.13）灌装机 × Mekanism：**喷气背包现在真的能灌我们的氢了** —— **待你实测**

用户原话：「**mek喷气背包还是不可以灌本mod的氢 你看看能不能做一下兼容 或者搞一个流体转化装置
可以把本mod的流体转成同标签的别的mod流体**」

**① 结论先说**：做了**兼容**，没做"流体转化装置" —— 因为后者解决不了这个问题：
Mek 的喷气背包吃的是 Mek 自己的**化学品（气体）**，而 Mek 那边根本没有"氢气液体"可转
（旋转冷凝器就是把 `#c:hydrogen` 流体 ↔ `mekanism:hydrogen` 气体那一步）。
所以正解是让**灌装机认识 Mek 的化学品容器**，把罐里的我们的氢按 Mek 的口径变成
`mekanism:hydrogen` 灌进去。

**② 实测证据（真开服 + 真 Mek 10.7.19）**：罐里放我们的氢 5000 mB、槽里放一个**全新喷气背包**，
跑 20 tick ⇒ **喷气背包里多出 100 mB 的 `mekanism:hydrogen`**、罐剩 4900 mB、电扣 1200 FE、
罐减少量 == 物品增加量（质量守恒）。喷气背包自己的罐是 **24000 mB**。

**③ 谁对得上、谁对不上**（"同标签"这条口径的实现方式）：

| 我们的流体 | 标签 | Mek 同名化学品 | 能不能灌进 Mek 气体物品 |
|---|---|---|---|
| 氢 / 氧 / 氯 / 硫酸 | `c:hydrogen` / `c:oxygen` / `c:chlorine` / `c:sulfuric_acid` | `mekanism:hydrogen` / `:oxygen` / `:chlorine` / `:sulfuric_acid` | ✅ |
| 原油 / 柴油 / 石脑油 / 液化气 / 汽油 | 有 `c:` 标签 | **Mek 没有同名的** | ❌（照旧灌不了，诊断说"灌不了"） |
| 任意流体 | — | — | 我自己**一个气体名都没硬写**：找得到同名化学品才灌 |

**④ 软依赖说清楚**：这一版把 Mekanism 作为**编译期依赖**（`libs/` 里 12 MB 的 jar，MIT，照 JEI/帕秋莉的先例），
但它是 `compileOnly` —— **没装 Mek 的玩家一切照旧**（那个桥的类根本不会被加载；产物 jar 里也没有 Mek 的任何 class）。
喷气背包只收氢：罐里放原油时它照样拒收（负对照实测）。

**⑤ 要你实测的三条**
1. 装 Mek 的整合包里：往灌装机罐里灌我们的**氢**（管道或手倒都行），槽里放**喷气背包**，
   等它灌 —— 背包里的氢气会涨（Mek 自己的 GUI/tooltip 能看到）。
2. 罐里放我们的**氧/氯**配 Mek 的气体罐（`mekanism:gas_tank` 之类），同样应该能灌。
3. **没装 Mek** 的整合包里，灌装机一切照旧（放气罐/油桶/别的 mod 的液体容器都能灌，喷气背包那类会显示"灌不了"）。

"""

HAND36 = u"""36. **ZF164 的账（0.13：灌装机 × Mekanism，喷气背包能灌我们的氢了）**：
    ① 用户原话与逐条落实见档案 §9；两条被 API 骗到的教训见 **§4.171**
    （Mek 10.7 的气体并进了化学品 API、能力名是 `mekanism:chemical_handler`；
    `DefaultedRegistry.get()` 查不到会**回默认值** ⇒ 必须 `getKey()` 反查）。
    ② **软依赖**：`libs/Mekanism-1.21.1-10.7.19.85.jar`（MIT，12 MB）+ `compileOnly`；
    全工程**只有** `MekChemicalBridge.java` 一个文件 `import mekanism.*`，且公开签名里没有 Mek 类型
    ⇒ 没装 Mek 的实例不会加载它（`_zf164_verify.py` A6/A7/D1/D2 钉住）。
    ③ **映射**：我们流体的 `c:<名字>` 标签 ⇒ Mek 注册表同路径的化学品（1:1，与 Mek 旋转冷凝器同口径），
    **一个气体名都没硬写**；氢/氧/氯/硫酸对得上，原油/柴油/石脑油/液化气/汽油在 Mek 那边没有同名的 ⇒ 照旧灌不了。
    ④ **探针 `Zf164Check` 19/0**（把 Mek 拷进 `run/server/mods` 跑真服务端，跑完删掉）：
    喷气背包里真的多出 100 mB `mekanism:hydrogen`（罐 −100 / 电 −1200 / 质量守恒）+ 6 条负对照。
    ⑤ **语言键数不变**（593×4 + 595）⇒ 键数门一份都没动；class 数 364 → 365（多的是那个桥）。
    ⑥ ⚠ 我没做"流体转化装置"：Mek 那边没有"氢气液体"这种东西可转（喷气背包要的是**气体**），
    做那个也解决不了这个问题 —— 这条已在 §9 里写清楚，你要是仍想要一台"同标签流体互转"的机器，
    那是另一件事（对流体与流体之间才成立），说一句我单开一轮。
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
    cls = len([n for n in z.namelist() if n.endswith(u".class")])
    print(u"成品：%s = %d 字节 / sha1 %s / class %d" % (os.path.basename(JAR), size, h, cls))
    fails = []

    doc = read(DOC)
    if u"### 4.171 " not in doc:
        a = u"| ZF147 |"
        if doc.count(a) != 1:
            fails.append(u"档案：§5 表头锚点出现 %d 次" % doc.count(a))
        else:
            doc = doc.replace(a, S4 + a, 1)
    if u"| ZF164 |" not in doc:
        a2 = u"| 见 §9 ｜ 见 §4.169 / §4.170 |\n"
        if doc.count(a2) != 1:
            fails.append(u"档案：ZF162 行尾锚点出现 %d 次" % doc.count(a2))
        else:
            doc = doc.replace(a2, a2 + ROW.format(size=u"{:,}".format(size), sha=h, cls=cls) + u"\n", 1)
    if u"### ZF164（0.13）" not in doc:
        a3 = u"\n---\n\n## 10. 备份策略"
        if doc.count(a3) != 1:
            fails.append(u"档案：§10 锚点出现 %d 次" % doc.count(a3))
        else:
            doc = doc.replace(a3, u"\n" + S9 + u"---\n\n## 10. 备份策略", 1)
    if write and not fails:
        io.open(DOC, "w", encoding="utf-8", newline=u"").write(doc)

    hand = read(HAND)
    if u"36. **ZF164 的账" not in hand:
        a4 = u"\n---\n\n## 7. ZF146 这一轮的交接"
        if hand.count(a4) != 1:
            fails.append(u"交接：§7 锚点出现 %d 次" % hand.count(a4))
        else:
            hand = hand.replace(a4, u"\n" + HAND36 + u"\n---\n\n## 7. ZF146 这一轮的交接", 1)
    hand = hand.replace(u"`94087543011773822c0b369fc1e44c64fe9071a3`（5,882,220 B",
                        u"`%s`（%s B" % (h, u"{:,}".format(size)))
    if write and not fails:
        io.open(HAND, "w", encoding="utf-8", newline=u"").write(hand)

    v = read(V149)
    vn = re.sub(u'WANT_SHA = u"[0-9a-f]{40}"', u'WANT_SHA = u"%s"' % h, v, count=1)
    vn = re.sub(u"WANT_SIZE = \\d+", u"WANT_SIZE = %d" % size, vn, count=1)
    vn = vn.replace(u"u\"**364 classes, 43 advancements, 93 recipes**\" in ann",
                    u"u\"**%d classes, 43 advancements, 93 recipes**\" in ann" % cls)
    vn = vn.replace(u"u\"C7 公告 Download 段那一句的三个数跟到 364 / 93",
                    u"u\"C7 公告 Download 段那一句的三个数跟到 %d / 93" % cls)
    if vn == v:
        fails.append(u"_zf149_verify.py：三处靶子一个都没换到")
    elif write and not fails:
        io.open(V149, "w", encoding="utf-8", newline=u"").write(vn)

    ann = read(ANN)
    if u"## New in 0.13 ZF164" not in ann:
        a5 = u"## New in 0.13 ZF162 - Wrench and blast-furnace item removed"
        if ann.count(a5) != 1:
            fails.append(u"公告：ZF162 段锚点出现 %d 次" % ann.count(a5))
        else:
            block = (u"## New in 0.13 ZF164 - The Filling Machine now fills Mekanism gas items\n\n"
                     u"- **Your Mekanism jetpack can now be filled with our hydrogen.** The machine also\n"
                     u"  understands Mekanism's **chemical** items (Mekanism 10.7 merged gases into the\n"
                     u"  chemical API; the item capability is `mekanism:chemical_handler`), so a jetpack -\n"
                     u"  or any Mek gas item - that sits in a slot gets filled from the matching tank.\n"
                     u"- **The mapping is tag-driven and 1:1**: our fluid's `c:<name>` tag is matched to\n"
                     u"  Mekanism's chemical of the same path (our `c:hydrogen` -> `mekanism:hydrogen`).\n"
                     u"  Hydrogen, oxygen, chlorine and sulfuric acid line up; crude oil, diesel, naphtha,\n"
                     u"  LPG and gasoline have no same-named Mekanism chemical, so they still cannot be\n"
                     u"  filled into gas items. **No gas name is hard-coded.**\n"
                     u"- **Verified on a real server with Mekanism 10.7.19 installed**: 20 ticks put\n"
                     u"  **100 mB of `mekanism:hydrogen`** into a brand-new jetpack while the tank dropped by\n"
                     u"  exactly 100 mB and 1,200 FE was spent (mass balance checked), plus six negative\n"
                     u"  controls (non-containers, fluids without a Mekanism counterpart, the tank/drum\n"
                     u"  rules, the locked numbers).\n"
                     u"- **Soft dependency**: Mekanism is a compile-only dependency (MIT, jar in `libs/`).\n"
                     u"  Instances **without** Mekanism behave exactly as before - the bridge class is never\n"
                     u"  loaded and no Mekanism class ends up in our jar.\n"
                     u"- **Download:** `release/PotatoST-0.13.jar` - **{size} bytes**, sha1 **`{sha}`**.\n\n"
                     ).format(size=u"{:,}".format(size), sha=h)
            ann = ann.replace(a5, block + a5, 1)
    ann = ann.replace(u"5,882,220 bytes, sha1 `94087543011773822c0b369fc1e44c64fe9071a3`",
                      u"%s bytes, sha1 `%s`" % (u"{:,}".format(size), h))
    ann = ann.replace(u"**5,882,220 bytes**, sha1 **`94087543011773822c0b369fc1e44c64fe9071a3`**",
                      u"**%s bytes**, sha1 **`%s`**" % (u"{:,}".format(size), h))
    ann = ann.replace(u"**364 classes, 43 advancements, 93 recipes**",
                      u"**%d classes, 43 advancements, 93 recipes**" % cls)
    if write and not fails:
        io.open(ANN, "w", encoding="utf-8", newline=u"").write(ann)

    print(u"模式：%s" % (u"落盘" if write else u"干跑（不写）"))
    print(u"失败 = %d" % len(fails))
    for f in fails:
        print(u"  !! " + f)
    return 1 if fails else 0


if __name__ == u"__main__":
    sys.exit(main(sys.argv[1:]))
