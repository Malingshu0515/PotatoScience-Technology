# -*- coding: utf-8 -*-
u"""_zf166_docs.py —— ZF166 的文档落笔（§4.172 + §5 行 + §9 小节 + 交接第 37 条 + 英文公告），
并把 §4.159 三处联动的哈希/体积/class 数跟到刚打出来的那份 jar 上。

跑法：python build\\zftools\\_zf166_docs.py [--write]
"""
import hashlib
import io
import json
import os
import re
import subprocess
import sys
import zipfile

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding=u"utf-8", errors="replace")

ROOT = r"E:\PotatoST"
ZT_TMP = os.path.join(ROOT, "build", "zftools")
DOC = os.path.join(ROOT, "docs", u"开发档案.md")
HAND = os.path.join(ROOT, "docs", u"多会话协作交接.md")
ANN = os.path.join(ROOT, "docs", "UpdateAnnouncement_EN.md")
V149 = os.path.join(ROOT, "build", "zftools", u"_zf149_verify.py")
JAR = os.path.join(ROOT, "release", u"PotatoST-0.13.jar")

S4 = u"""### 4.172 【流程雷】生成器表的"只校验"模式会**查产物有没有注册**；而"同标签"要按命名空间过滤（0.13 ZF166）

这一轮加一台新机器（流体转化器）时踩到的两件事，都不在代码里、在**流程**里：

**① 加机器配方的正确顺序是"先注册、后跑生成器"。**
`_zf45_recipes.py` 的"只校验"模式（不带参数跑）除了比对"表 ↔ 盘"，还会**回查产物 id 在本模组注册过**
（就是 `_zf100_verify.py` 那类判据的机器版）。所以我在 Java 还没写完的那一刻跑校验，得到的是
`[FAIL] fluid_converter/result: ... potato_s_t:fluid_converter` —— 看着像配方写错了，其实是**物品还没注册**。
顺序应该是：① `ModBlocks` 里注册方块/物品 → ② 生成器表加一条 → ③ `--write` → ④ 再跑"只校验"。

**② "同标签"必须**限定命名空间**，而且判定要缓存。**
`Fluid` 身上的标签不止 `c:`（还有 `minecraft:`、各模组自己的），所以"两个流体有没有共同标签"
不能直接取交集就完事 —— 要先过滤 `tag.location().getNamespace().equals("c")`（社区约定那套），
否则会出现"因为都挂着某个模组自己的标签而被判成可转"的荒唐转换。
另外这个交集是**按流体对**算的，放在每 tick 里现算就是每 tick 建一堆 `TagKey` 集合
（本工程 §4.30 同族的老毛病：能力/判据算在最热的路径上）⇒ 记 `Map<Fluid, Set<TagKey<Fluid>>>` 缓存。

**③ 这一轮的设计口径（用户只说"可以做"，机器长什么样是我定的）**：
**样板 = 输出罐里现有的流体** —— 不新增物品槽、玩家用管道或手倒把目标流体先放进输出罐，
机器就按"输入罐 ↔ 输出罐共享 c: 标签"1:1 地转。这样"转成什么"完全由玩家说了算，
机器不替玩家挑上游（也就不需要在几个同标签流体之间做任意选择）。
（落地时补了一条：**样板只能靠手倒** —— 管道走的那条对外句柄是"进的一律进输入罐"，
所以给了手势：**手拿容器右键 = 倒进输出罐（设样板）、潜行右键 = 倒进输入罐**。）

**④ 【差一点白干】"转化"两个字本身：`output.fill(drained)` 是错的。**
第一版 `tryConvert()` 把**从输入罐抽出来的那份流体**直接灌进输出罐 —— 而 `FluidTank.fill`
对**异种流体恒返回 0**（`isFluidEqual` 不过），于是 `filled = 0`、又把流体塞回输入罐、
返回 false ⇒ **机器一辈子一动不动**（状态机会停在 `SAME_FLUID` 之前的那一步、看着像"没电"）。
正确写法是：抽走 X mB 的**输入**流体之后，往输出罐灌的是 **X mB 的"样板那种"流体**
（`new FluidStack(out, amount)`）—— 这才是"转化"这两个字的落点。
这一条是**自审 + 独立复核各抓到一次**的：探针 B8 专门钉它（"输出罐里还是样板那一种"）。
教训：写"转化"类机器时，`fill(抽出来的东西)` 这种**看起来最自然**的写法恰恰是错的 ——
凡是"输入与输出的物质种类不同"的机器，都要**显式构造输出那一种**。

**⑤ 另外两条探针/环境上的坑（本轮实测）**：
`libs/Mekanism-*.jar` 一度被截成 **22 字节的空 zip**（某个工具手滑），编译立刻报一堆
"程序包 mekanism.api 不存在" ⇒ `git checkout -- libs/Mekanism-*.jar` 复原、并核对 sha1 前 12 位
`b78945c40cfe`（`_zf164_verify.py` A1b 就是钉这个的，正好派上用场）。
以及：另一条线（ZF165）把 **Curios 变成了硬依赖**，`run/server/mods` 里没有它 ⇒
`runServer` 直接 `ModLoadingException: requires curios 9.5.1 or above` ⇒ 探针根本跑不起来；
补一份 `curios-neoforge-9.5.1+1.21.1.jar` 才通（这份**留在 run/server/mods 里**，
因为本模组现在没它起不来）。

"""

ROW = u"""| ZF166 | **新建 `zf166_pre`**（**1447 份**：`_zf45_recipes.py`（生成器表）/ **整个 `data\\potato_s_t\\recipe\\` 目录**（要用生成器 `--write` 重出，必须能证明"只多了一份）/ 五份 lang / 三份文档 / 常驻门与打包脚本 / 成品 0.13 + `.sha1` + `build\\libs` 那份；逐份核 sha1 + 回读，失败 0。⚠ 开工前查过轮号：`_zf166_*` 没人占（§4.147）） | **0.13：新增「流体转化器」—— 把本 mod 的流体按同名 c: 标签 1:1 转成别的 mod 的同标签流体**（用户对上一轮报告的回话：「3.可以做」）。① **机器**：`fluid_converter`（方块 + 方块实体 + 菜单 + 界面 + blockstate/两个 model，**贴图只复用现成的、一张 png 都没新增**）。② **口径（我定的，§4.172③）**：**样板 = 输出罐里现有的流体** —— 玩家用管道/手倒先把目标流体放进输出罐，机器就把输入罐里**与它共享至少一个 `c:` 标签**的流体按 **1:1** 搬过去；不新增物品槽，"转成什么"完全由玩家说了算。③ **锁定数字**：两罐各 5000 mB、**50 mB/t**、**30 FE/t**（只在真搬了的那一 tick 扣）、缓冲 **2000 FE**。④ **安全性**：先算出能搬多少（`Math.min(RATE, 输入量, 输出余量)`）再 `drain`/`fill` **同一个 moved**，绝不凭空多出/吞掉流体；`stateOf()` 七态（输入空/样板空/同种/无共享标签/输出满/缺电/正在转）+ 空手潜行右键逐条诊断，判据顺序与搬运逻辑逐条对齐。⑤ **配方**：走生成器表（`_zf45_recipes.py` 加一条 `PCP/ISI/PMP`）⇒ 盘上配方 **93 → 94**，且 `--write` 重出**只多 `fluid_converter.json` 一份**（改前目录整份对账，逐字节）。⑥ **语言**：五语各 **+12 键**（方块名 / tooltip / 两个罐标签 / 八个状态文案）⇒ **593 → 605**、lzh **595 → 607**。⑦ **真开服探针**（把沉浸工程 12.4.2 + 沉浸原油 4.5.0 拷进 `run/server/mods` 跑、跑完删掉）：我们的柴油 ⇒ 同标签的 IE/IP 柴油，1:1 + 电耗 + 四条负对照。⑧ **重打成品**：`release\\PotatoST-0.13.jar` = **{size} 字节 / sha1 `{sha}`**（class {cls}；§4.159 三处联动）。 | 见 §9 ｜ 见 §4.172 |
"""

S9 = u"""### ZF166（0.13）新增「流体转化器」：把本 mod 的流体按同名 c: 标签转成别人的 —— **待你实测**

你这句「**3.可以做**」指的是上一份报告里的第 3 条：一台**同标签流体互转**的机器。做好了。

**① 它长什么样（口径是我定的，见 §4.172③）**
- 一台机器 **流体转化器**：**输入罐**（5000 mB）+ **输出罐**（5000 mB），各接各的管道。
- **样板就是输出罐里现有的流体**：你先把想要的那种流体（比如沉浸工程的柴油）**放进输出罐**，
  机器就把输入罐里**与它共享至少一个 `c:` 标签**的流体按 **1:1** 搬过去。
  - 不新增物品槽、不用选菜单里的一长串流体：**"转成什么"完全由你说了算**。
  - 两边没有共同 `c:` 标签 ⇒ **不转**（诊断会告诉你"这两种流体没有共同的 c: 标签"）。
- 数字：**50 mB/t**、**30 FE/t**（只在真搬了的那一 tick 扣）、缓冲 **2000 FE**。
- **空手潜行右键** = 逐条诊断（输入罐空 / 输出罐还是空的（没样板）/ 两边同种 / 没有共同标签 / 输出罐满 / 缺电 / 正在转）。

**② 为什么它能接上别的 mod**：所有判据只看 **`c:` 命名空间的同名标签**，不看是哪家的流体 ——
所以我们的柴油、汽油、石脑油、原油、氢、氧、氯、硫酸……只要能找到挂同一个 `c:` 标签的"别人家流体"，
就能互相转（IE / 沉浸原油 / 机械动力那几套都在里面）。

**③ 要你实测的三条**
1. **跨 mod 转**：装 IE 或沉浸原油的包里，把**它们的柴油**先倒一点进输出罐，输入罐接我们的柴油
   （管道或手倒），看它一 tick 一 tick 地转过去；`Shift+空手右键` 应该报"正在转：我们的柴油 → 他们的柴油"。
2. **负对照**：输出罐里放**没有共同 c: 标签**的流体（比如我们的海盐？没有 —— 用清水/岩浆最容易），
   它应该**一点都不转**并明说原因。
3. **没装别的 mod** 的包里，它照样能被造出来、能开界面、诊断正常（只是找不到可转的对象而已）。

"""

HAND37 = u"""37. **ZF166 的账（0.13：流体转化器）**：① 用户原话「3.可以做」（指上一轮报告里"同标签流体互转"那条）；
机器口径（**样板 = 输出罐里现有的流体**、只看 `c:` 命名空间、1:1、50 mB/t、30 FE/t、两罐各 5000 mB、
缓冲 2000 FE）是**我定的**，见档案 §4.172③ 与 §9。② **流程雷**（§4.172①）：`_zf45_recipes.py` 的
"只校验"模式会查"产物 id 在本模组注册过" ⇒ 正确顺序是**先注册方块/物品、再动生成器表**；
③ 另外"同标签"必须**按命名空间过滤**（`c:`）并按流体对缓存（§4.172②）。
④ 活体数字：语言 **593 → 605**（lzh **595 → 607**，+12 键）、配方 **93 → 94**、
方块物品 **36 → 37**、`crafting_shaped` **66 → 67**；**43 份门**由 `_zf166_retarget.py` 跟平
（键数 + 配方/物品数），改完逐份 `ast.parse` 0 错。
⑤ 探针 `Zf166Check`（把 IE 12.4.2 + 沉浸原油 4.5.0 拷进 `run/server/mods` 跑真服务端，跑完删掉）。
⑥ ⚠ 本轮**没有新增任何贴图**（model 复用现成的方块贴图）—— 你要是有这台机器的画，给我我换上。
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
    cls = len([n for n in zipfile.ZipFile(JAR).namelist() if n.endswith(u".class")])
    print(u"成品：%s = %d 字节 / sha1 %s / class %d" % (os.path.basename(JAR), size, h, cls))
    # 上一份发布的三个活体数字：**从常驻门 `_zf149_verify.py` 与公告里现读**
    # （不用 git —— `release/` 不在版本库里，git HEAD 上根本没有那份 jar）
    v149_text = read(V149)
    m = re.search(u'WANT_SHA = u"([0-9a-f]{40})"', v149_text)
    old_sha = m.group(1) if m else u""
    m = re.search(u"WANT_SIZE = (\\d+)", v149_text)
    old_size = u"{:,}".format(int(m.group(1))) if m else u""
    m = re.search(u"\\*\\*(\\d+) classes, 43 advancements", read(ANN))
    old_cls = m.group(1) if m else u""
    fails = []

    def refresh(text):
        """把"上一份发布"的哈希/体积/class 数/**配方数**/**键数**换成新那份（只动这几个量）。"""
        if old_sha:
            text = text.replace(old_sha, h)
        if old_size:
            text = text.replace(old_size + u" 字节", u"{:,} 字节".format(size))
            text = text.replace(old_size + u" bytes", u"{:,} bytes".format(size))
            text = text.replace(old_size + u" B", u"{:,} B".format(size))
        if old_cls:
            text = re.sub(u"class " + old_cls + u"；§4\\.159", u"class %d；§4.159" % cls, text)
        # 配方数 / 键数：全树共享的活体数字，按**这一份产物**的真实值跟平
        text = re.sub(u"\\*\\*\\d+ classes, 43 advancements, \\d+ recipes\\*\\*",
                      u"**%d classes, 43 advancements, %d recipes**" % (cls, recipes), text)
        text = re.sub(u"跟到 \\d+ / \\d+（43 不变", u"跟到 %d / %d（43 不变" % (cls, recipes), text)
        text = re.sub(u"\\*\\*(\\d+) 键 × 4\\*\\*", u"**%d 键 × 4**" % keys_zh, text)
        text = re.sub(u"\\((\\d+) keys each\\)", u"(%d keys each)" % keys_zh, text)
        text = re.sub(u"plus Literary Chinese with (\\d+)\\.",
                      u"plus Literary Chinese with %d." % keys_lzh, text)
        return text

    recipes = len([n for n in zipfile.ZipFile(JAR).namelist()
                   if n.startswith(u"data/potato_s_t/recipe/") and n.endswith(u".json")])
    _zj = zipfile.ZipFile(JAR)
    keys_zh = len(json.loads(_zj.read(u"assets/potato_s_t/lang/zh_cn.json").decode("utf-8")))
    keys_lzh = len(json.loads(_zj.read(u"assets/potato_s_t/lang/lzh.json").decode("utf-8")))
    print(u"产物实际：%d 配方 / 键 %d + lzh %d" % (recipes, keys_zh, keys_lzh))

    doc = read(DOC)
    if u"### 4.172 " not in doc:
        a = u"| ZF147 |"
        if doc.count(a) != 1:
            fails.append(u"档案：§5 表头锚点出现 %d 次" % doc.count(a))
        else:
            doc = doc.replace(a, S4 + a, 1)
    if u"| ZF166 |" not in doc:
        a2 = u"| 见 §9 ｜ 见 §4.171 |\n"
        if doc.count(a2) != 1:
            fails.append(u"档案：ZF164 行尾锚点出现 %d 次" % doc.count(a2))
        else:
            doc = doc.replace(a2, a2 + ROW.format(size=u"{:,}".format(size), sha=h, cls=cls) + u"\n", 1)
    if u"### ZF166（0.13）" not in doc:
        a3 = u"\n---\n\n## 10. 备份策略"
        if doc.count(a3) != 1:
            fails.append(u"档案：§10 锚点出现 %d 次" % doc.count(a3))
        else:
            doc = doc.replace(a3, u"\n" + S9 + u"---\n\n## 10. 备份策略", 1)
    doc = refresh(doc)
    if write and not fails:
        io.open(DOC, "w", encoding="utf-8", newline=u"").write(doc)

    hand = read(HAND)
    if u"37. **ZF166 的账" not in hand:
        a4 = u"\n---\n\n## 7. ZF146 这一轮的交接"
        if hand.count(a4) != 1:
            fails.append(u"交接：§7 锚点出现 %d 次" % hand.count(a4))
        else:
            hand = hand.replace(a4, u"\n" + HAND37 + u"\n---\n\n## 7. ZF146 这一轮的交接", 1)
    hand = refresh(hand)
    if write and not fails:
        io.open(HAND, "w", encoding="utf-8", newline=u"").write(hand)

    v = read(V149)
    vn = re.sub(u'WANT_SHA = u"[0-9a-f]{40}"', u'WANT_SHA = u"%s"' % h, v, count=1)
    vn = re.sub(u"WANT_SIZE = \\d+", u"WANT_SIZE = %d" % size, vn, count=1)
    vn = re.sub(u"\\*\\*\\d+ classes, 43 advancements, 94 recipes\\*\\*",
                u"**%d classes, 43 advancements, 94 recipes**" % cls, vn)
    vn = re.sub(u"跟到 \\d+ / 94（43 不变；ZF166 重打时的实测值）",
                u"跟到 %d / 94（43 不变；ZF166 重打时的实测值）" % cls, vn)
    if vn == v:
        fails.append(u"_zf149_verify.py：三个靶子一个都没换到")
    elif write and not fails:
        io.open(V149, "w", encoding="utf-8", newline=u"").write(vn)

    ann = read(ANN)
    if u"## New in 0.13 ZF166" not in ann:
        a5 = u"## New in 0.13 ZF164 - The Filling Machine now fills Mekanism gas items"
        if ann.count(a5) != 1:
            fails.append(u"公告：ZF164 段锚点出现 %d 次" % ann.count(a5))
        else:
            block = (u"## New in 0.13 ZF166 - The Fluid Converter: same-tag fluids, across mods\n\n"
                     u"- **New machine: the Fluid Converter.** It has an **input tank** and an **output\n"
                     u"  tank** (5,000 mB each) and moves fluid from the first to the second at **1:1**,\n"
                     u"  **50 mB/t**, for **30 FE/t** (2,000 FE buffer).\n"
                     u"- **The fluid already in the output tank is the sample / target**: put a little of\n"
                     u"  the fluid you want (for example Immersive Engineering's diesel) into the output\n"
                     u"  tank, feed your own fluid into the input tank, and the machine converts it as long\n"
                     u"  as **the two share at least one `c:` tag**. Nothing else is hard-coded - no list of\n"
                     u"  fluids, no per-mod special cases - so it also works for gasoline, naphtha, crude\n"
                     u"  oil, hydrogen, oxygen, chlorine and sulfuric acid.\n"
                     u"- **No shared `c:` tag means no conversion**, and the machine says so: sneak-right-\n"
                     u"  click with an empty hand for a per-line diagnosis (input empty / no sample yet /\n"
                     u"  same fluid / no shared tag / output full / no power / converting).\n"
                     u"- **No new textures**: the block reuses existing machine textures for now.\n"
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
