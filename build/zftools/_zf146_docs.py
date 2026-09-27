# -*- coding: utf-8 -*-
u"""_zf146_docs.py —— ZF146 的三处台账（§5 行 / §9 小节 / §4.150~§4.153 四条雷）+ 交接文档

⚠ 规矩（§4.36）：每个锚点都必须**恰好命中 1 次**，多一次少一次都停手 ——
  模糊匹配会顺手改到别处，这个工程为此流过好几次血。

跑法：
    python build\\zftools\\_zf146_docs.py            # 只体检（打印将要插入的内容摘要）
    python build\\zftools\\_zf146_docs.py --write    # 真写
"""
import io
import os
import re
import sys

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

ROOT = r"E:\PotatoST"
DOC = os.path.join(ROOT, r"docs\开发档案.md")
HAND = os.path.join(ROOT, r"docs\多会话协作交接.md")

ROW = r'''| ZF146 | **新建 `zf146_pre`**（**133 份**改前件：`StarfallRitualManager.java`（**本轮唯一的源码改动**）+ `PotatoST.java`（探针挂载点）+ 星轨坠另外两件 + `_zf114_verify.py` / `_zf114_falsify.py` + 九道门 + 全部常驻校验脚本 + 2 份文档 + 旧成品与 `.sha1`；逐份核哈希 + 回读证明 133/133，失败 0。⚠ 开工前查过轮号：`build\zftools` 下没有别的 `_zf146_*`、救援目录下没有 `zf146_pre`（§4.147）） | 0.11：**修星轨坠「中途退出游戏就不会落下 / 再次进入就不能使用了」**（别人反馈，用户转述）。① **根因**：仪式状态原本放在 `private static final Map<UUID, Ritual> ACTIVE` 里，而 `Ritual` 还攥着一个 `ServerLevel` 引用 —— 单机「退回标题界面再进同一个世界」时**类加载器与静态字段跟着 JVM 活着、世界却换了一茬**：`tick()` 拿的是**上一个服务器那个停摆的时钟**（`remain = endTick - ritual.level.getGameTime()`）⇒ `remain` 冻住、永远走不到 0 ⇒ **陨石永远不生成**；而 `use()` 看的是**新世界**的时钟，过了取消窗口就恒判「已锁定」，那条死记录又永远删不掉 ⇒ **星轨坠从此永久失效**（用户报的两条症状正好是这同一根因的两半）；② **修法**：状态搬进**存档** —— `RitualData extends SavedData`，落在 `<存档>/data/potato_s_t_starfall.dat`（与 `raids.dat` 同一个地方），记录里只存**维度的 key**（`ResourceKey<Level>`）而不是 level，每 tick `server.getLevel(ritual.dimension)` 现查、`server.overworld().getDataStorage().computeIfAbsent(...)` 现取 ⇒ **类里从此没有任何能活过一次世界切换的世界引用**（探针接口也一并改成「要 server」）；通报进度（`Next` / `Warned`）一起存，不然读盘会用「刚过 20 秒」的口径补发两条过时通报；③ **证据（两次开服对照，同一份探针改前/改后都编得过、都跑得起来）**：`_zf146_probe.py` 起真服务端 → 右键起手 → **第 300 tick 正常停服**（走完整存档流程）→ 再开一次。**改前**：第二趟三条红（存档里没有仪式数据 / 进世界右键「被拒」失败、耐久 0→1 说明上一场凭空消失 / **等到预期落地后 251 tick 也没等到陨石**）；**改后**：世界时间 1151 退出、预期落地 1451，**陨石正好在 1451 生成**（差 **0** tick、威力 14、y=200），落地把平台炸掉 **121** 格，落地后再右键**又能用了**（耐久 0→1）、进世界那次右键**被拒**（0→0）、且一条过时通报都没补发；④ 存档文件 **191 B**，gzip 解开后能按 NBT 字节序**找到维度名 `minecraft:overworld` 与 `endTick=1451` 的大端 int64**（"存在文件"和"写对了内容"是两件事，两条都量）；⑤ `_zf146_verify.py` **31 项 0 失败**、反证 **K01~K08 八把刀全咬住**（⚠ 第一轮 K01 漏了：「Ritual 里没有世界对象」那条正则只认 `;` 不认 `=`，`private final ServerLevel level = null;` 溜过去了 ⇒ 当场把判据收紧，这就是反证该干的事）；⑥ `_zf114_verify.py` **188 项 0 失败**（本轮一次都没改它，也没把它的 C5~C15 锚点弄丢 —— 重构前先读了它钉着哪些字面量）；⑦ ⚠ 九道门：③④⑤⑥⑦ 全绿，① ② 各 1 条失败、⑧ 红，**三条都不是本轮**（① ② 是翻译线在途的 `lzh` 比基准多 2 键，**HEAD 里就是 510 vs 508**；⑧ 是另一条线**正在改**的 `_zf78_verify.py` 语法错 —— 同一次运行里报错行从 285 漂到 315、文件从 31193 B 长到 33050 B）| 见 §9 ｜ 见 §4.150~§4.153 |
'''


LESSONS = r'''
### 4.150 【判据雷】自动跑不出「单机退回标题」那种"JVM 活着、世界换了一茬"的场景（0.11 ZF146）

用户报的星轨坠 bug 有两半：**「不会落下」**（服务端重启后倒计时丢了）与**「再次进入就不能使用了」**
（静态表活着、里面的时钟停摆 ⇒ 永久锁死）。我的探针是**真服务端**（`runServer`）那一路，
它能做的是「**停服 → 再开**」，也就是**第一半**：

- 那一半我拿到了漂亮的对照：同一份探针，改前第二趟红三条、改后全绿（陨石差 0 tick 落在预期时刻）；
- 而「退回标题界面再进世界」根本**起不了进程**（本工程的客户端自动化一直跑不起来），
  它活在**同一个 JVM** 里：虚拟机没重启、类加载器没重启、`static` 字段原封不动。

⇒ 规矩：**探针证不到的那一半，必须在报告里点名写清，并且换成"结构性判据 + 推理"去钉**，
不许把「服务端重启验过了」含糊成「端到端都验过了」。本轮钉法两条：
① 「类里不许有 static 的仪式表」「仪式记录里不许出现 `ServerLevel` / `Level` 字段」——
   这两条一旦有人改回去，常驻校验当场红；② 用户那句话本身就是**运行时证据**：
   「再次进入就不能使用了」只有在"仪式记录活过了世界切换"时才可能发生（否则 `ACTIVE` 是空的、
   右键会照常起手）—— 两条症状互为对方的旁证，这一层推理也照实写进 §9。
'''

LESSONS2 = r'''
### 4.151 【判据雷】切片函数找不到收尾锚点就"一路取到文件尾" ⇒ 负向断言当场假红、换一处又假绿（0.11 ZF146）

`_zf146_verify.py` 里写了个 `cut(text, start, end)` 取源码片段，用于「这段里不许出现 X」这类断言。
第一版收尾锚点我多写了两个星号（`仪式状态的**持久化容器**`，真源码里没有那对星号）：

- `find()` 返回 -1，函数**默默**返回 `text[i:]` —— 片段从 1.2 KB 变成 **16.5 KB**，
  把 `tick()` 里的局部变量 `ServerLevel level = ...` 也圈了进来 ⇒ 「记录里没有世界对象」**假红**；
- 同一个函数的另一种用法（"这段里必须有 Y"）则会因为片段里**多**了无关内容而**假绿**。

⇒ 两条规矩：
① **切片函数取不到收尾锚点必须返回空串**（宁可红，不许悄悄放大范围）；
② 再加一条**守卫断言**专门量切片大小（本轮 A0：「Ritual 1181 字符 / RitualData 3808 字符」），
   因为负向断言拿到**空**切片时会**假绿** —— 空片段里当然"没有"任何不该有的东西。
   这就是「锚点必须 assert 守住」在**取切片**上的版本。
'''

LESSONS3 = r'''
### 4.152 【流程雷】判据吃到了自己的散文：把"改前的坏代码"写进类注释，于是"不许再有那张 static 表"被自己的说明文字判红（0.11 ZF146）

本轮为了让后人看懂病根，我在 `StarfallRitualManager` 的类注释里**原样引用**了改前那行：

```java
 * private static final Map<UUID, Ritual> ACTIVE   // ← 注释里的"反面教材"
```

结果常驻校验里「**类里没有 static 的仪式表**」这条——正则先扫到注释里那行、再看到 `ACTIVE` 这个词——
**红给我看**。判据没写错，是我让**散文**混进了**代码**的判据里。

⇒ 规矩：**结构性判据先剃注释（`/* */` 与 `//`）再判**，判代码不判文字；
写"反面教材"式注释是对的（§4.150 那种边界就该写清楚），所以**要改的是判据、不是注释**。
'''

LESSONS4 = r'''
### 4.153 【工具雷】`gradlew runServer --args="..."` 会把 run 配置里的 `--nogui` 顶掉 ⇒ `ImmediateWindowHandler` 当场 NPE（0.11 ZF140 在 runClient 上踩、ZF146 在 runServer 上又踩一次）

本轮要换存档名，手一滑就用了 `--args="--nogui --world zf146restart"`（`build.gradle` 的 `server` 段本来
就带了 `argument '--nogui'`，`--args` 是**替换**不是追加）。服务端的报错跟 ZF140 那次一模一样：

```
Exception in thread "main" java.lang.NullPointerException
    at java.util.ImmutableCollections$ListN.indexOf(...)
    at ...fml_loader...ImmediateWindowHandler.load(ImmediateWindowHandler.java:49)
```

⇒ 规矩：**这个工程的 run 配置不许用 `--args`**。要换存档名，就改 `run\server\server.properties`
的 `level-name`（ZF77 就是这么干的），跑完记得还原 —— 本轮把它写进 `_zf146_probe.py` 的
`set-world` / `restore-world` 两个子命令里，还原时逐字节核对。
'''


def insert_before(text, anchor, block):
    n = text.count(anchor)
    if n != 1:
        raise RuntimeError(u"锚点命中 %d 次（应为 1）：%r" % (n, anchor[:40]))
    i = text.index(anchor)
    return text[:i] + block + text[i:]


def main(argv):
    write = u"--write" in argv
    doc = io.open(DOC, encoding=u"utf-8", newline=u"").read()
    hand = io.open(HAND, encoding=u"utf-8", newline=u"").read()

    # ① §5 台账：插在 ZF145 那一行**之后**（用行首正则定位，必须恰好一行）
    hits = list(re.finditer(r"(?m)^\| ZF145 \|.*$", doc))
    if len(hits) != 1:
        print(u"!! §5 里 ZF145 行命中 %d 次" % len(hits))
        return 1
    if re.search(r"(?m)^\| ZF146 \|", doc):
        print(u"  [跳过] §5 里已经有 ZF146 行")
    else:
        j = hits[0].end()
        doc = doc[:j] + u"\n" + ROW.rstrip(u"\n") + doc[j:]

    # ② §9 小节：插在 §10 之前（也就是 §9 的末尾）
    if u"### ZF146（0.11）" in doc:
        print(u"  [跳过] §9 里已经有 ZF146 小节")
    else:
        doc = insert_before(doc, u"## 10. 备份策略", SECTION9)

    # ③ 四条雷：插在 §6 之前（也就是 §4 的末尾）
    for name, block in ((u"4.150", LESSONS), (u"4.151", LESSONS2),
                        (u"4.152", LESSONS3), (u"4.153", LESSONS4)):
        if u"### " + name in doc:
            print(u"  [跳过] 已经有 §%s" % name)
            continue
        doc = insert_before(doc, u"## 6. 内容速查：加一样东西要动哪些文件", block)

    # ④ 交接文档：追加一节
    if u"## 7. ZF146 这一轮的交接" in hand:
        print(u"  [跳过] 交接文档已有 ZF146 一节")
    else:
        hand = hand.rstrip(u"\n") + u"\n" + HANDOFF

    # ⑤ 发布对账（幂等）：把本轮成品 SHA1 与"上一版作废"写进 §9
    sha1_now = u"a26d33633b7e791da7888477404a78c8cbbb61c4"
    sha1_old = u"84239f4a9fd35b6d285f7542a195d940cdb56132"
    if u"a26d33633b7e791da7888477404a78c8cbbb61c4" in doc:
        print(u"  [跳过] §9 里已经写了本轮的 SHA1")
    else:
        doc = insert_before(doc, u"**另**：`StarfallMeteorEntity` 的 `Power` / `Owner`",
                            RELEASE_NOTE % (sha1_now, sha1_old))

    print(u"§5 ZF146 行：%s" % (u"在" if u"| ZF146 |" in doc else u"**不在**"))
    print(u"§9 ZF146 小节：%s" % (u"在" if u"### ZF146（0.11）" in doc else u"**不在**"))
    for name in (u"4.150", u"4.151", u"4.152", u"4.153"):
        print(u"§%s：%s" % (name, u"在" if (u"### " + name) in doc else u"**不在**"))
    print(u"交接 §7：%s" % (u"在" if u"## 7. ZF146 这一轮的交接" in hand else u"**不在**"))
    if not write:
        print(u"（体检模式，没写盘）")
        return 0
    io.open(DOC, u"w", encoding=u"utf-8", newline=u"\n").write(doc)
    io.open(HAND, u"w", encoding=u"utf-8", newline=u"\n").write(hand)
    assert io.open(DOC, encoding=u"utf-8", newline=u"").read() == doc
    assert io.open(HAND, encoding=u"utf-8", newline=u"").read() == hand
    print(u"已写入：%s / %s" % (DOC, HAND))
    return 0


RELEASE_NOTE = r'''**发布**：成品 `release\PotatoST-0.11.jar` = **`%s`** —— ⚠ **上一版 `%s` 作废**
（同版本原地重打包，§3 发布六步）。发布脚本 `_zf146_publish.py` 带四道闸：
陈旧闸（jar 必须比源码新）、常驻校验全绿、探针闸（源码树里不许挂着 `Zf*Check.register()`）、
**两次开服对照闸**（改前那份必须红、改后那份必须绿）—— 少一道就"一个字节都不拷"。

'''

SECTION9 = r'''
### ZF146（0.11）星轨坠的仪式状态搬进存档 —— 修「中途退出就不会落下 / 再次进入不能用了」—— **待你实测**

**别人反馈的原话**（你转述）：「星轨坠 中途退出游戏就不会落下 再次进入就不能使用了」。

**病根**：仪式的倒计时原本存在**类的静态字段**里（`private static final Map<UUID, Ritual> ACTIVE`），
而那条记录还攥着一个 `ServerLevel` 引用。单机「退回标题界面 → 再进同一个世界」时，
**JVM 没重启、类加载器没重启、静态字段原封不动，世界却换了一茬**：

- `tick()` 算的是 `remain = endTick - ritual.level.getGameTime()`，而 `ritual.level` 是**上一个服务器**
  的 `ServerLevel` —— 它的时钟在退出那一刻就停摆了 ⇒ `remain` 冻住、永远走不到 0 ⇒
  **陨石永远不生成**（症状一）；
- `use()` 看的是**新世界**的时钟，过了 10 秒取消窗口就恒判「已锁定」；
  而那条死记录**永远删不掉**（删除只有"取消"和"`remain <= 0`"两条路，两条都走不到）⇒
  **星轨坠从此永久失效**（症状二）。

两条症状是同一根因的两半，而且**互为旁证**：「再次进入就不能使用了」只有在
"仪式记录活过了世界切换"时才可能发生 —— 否则表是空的，右键会照常起手。

**改法**：状态搬进**存档**（`RitualData extends SavedData` ⇒ `<存档>/data/potato_s_t_starfall.dat`），
记录里只留**维度的 key**，每 tick 现查维度、现取存档数据。倒计时因此能跨
「退回标题」「关掉游戏」「专用服务端重启」接着走 —— 玩家仍然赖不掉那颗已经叫来的陨石（ZF114 定下的语义）。

| 场景 | 改前 | 改后 |
|---|---|---|
| 倒计时走到一半退出（第 15 秒） | 存档里什么都没有 | 191 B 的 `.dat`，含维度名与 `endTick` |
| 再进来 | 陨石永不落下（上一场凭空消失） | **陨石正好在预期时刻生成**（差 0 tick） |
| 再进来时右键 | 会当成新起手（耐久 0→1） | 被拒（耐久 0→0），因为上一场还锁着 |
| 落地之后 | —— | **又能用了**（耐久 0→1） |

**⚠ 我能证到哪、证不到哪**：探针走的是**真服务端**那一路，证的是「**停服 → 再开**」。
而「退回标题界面」那种"JVM 活着、世界换了一茬"的场景本工程自动化跑不起来 ——
它由两条结构性判据钉住（类里不许有 static 的仪式表、记录里不许有 `ServerLevel` 字段），
详见 §4.150。**要你实测的是**：单机拿星轨坠右键 → 在 30 秒内退回标题 → 再进世界，
应当看到倒计时接着走、陨石照落，落地后道具能继续用（一共 4 点耐久）。

**另**：`StarfallMeteorEntity` 的 `Power` / `Owner` 本来就写进了实体存档，
所以「陨石已经在下落时退出」这种情况一直是好的（本轮没有再跑一趟验它）。
'''

HANDOFF = r'''
---

## 7. ZF146 这一轮的交接（星轨坠的仪式状态搬进存档）

1. **我改了哪一处**：`src\main\java\com\potatost\mod\StarfallRitualManager.java`（**唯一源码改动**）
   + `docs\开发档案.md` + 本文件 + 新增 `build\zftools\_zf146_{pre,probe,runserver 并入 probe,verify,falsify,gates,publish,docs}.py`
   与探针存档 `build\zftools\check\Zf146Check.java`。
   **没有碰**任何 lang / 贴图 / 配方 / 模型 / 别人的 `_zf*` 脚本。
2. **两条「不是我」的红**（都按 `git status` + HEAD 逐条查过）：
   - **门 ① ②**：`lzh.json` **510 键** vs 其余四语 **508 键** —— **HEAD 里就是这样**
     （`git status` 对 `lzh.json` 是干净的），是文言文那条线的在途账；我这轮**一条语言键都没加**。
   - **门 ⑧**：`build\zftools\_zf78_verify.py` 语法错（中文字符串里写了 ASCII 双引号），
     **另一条线正在改它**：12:09 时错在第 **285** 行、12:10 再跑就漂到第 **315** 行
     （文件 31193 B → 33050 B）。**我没动它**（它在 `git status` 里是 `M`，不是我改的）。
     顺带一提：把引号修好之后它还会 `UnboundLocalError: tower`，是**半成品**，
     所以「顺手帮它修好」这条路走不通 —— 留给那条线。
3. **我留下的东西**：探针存档 `run\server\zf146restart\`（里面只有一个悬空木平台与一个炸坑，
   谁都可以删）；`run\server\server.properties` 的 `level-name` **已还原**成 `zf77_newtest`（逐字节核过）。
   探针源码按惯例存档在 `build\zftools\check\Zf146Check.java`（报告 `check\zf146_*.log`）。
4. **给后面的线提个醒（§4.153）**：`gradlew runServer --args="..."` 会**顶掉** run 配置里的 `--nogui`，
   1.21.1 的 `ImmediateWindowHandler` 当场 NPE（ZF140 在 runClient 上踩过同一个坑）。
   要换存档名就改 `run\server\server.properties` 的 `level-name`。
5. **轮号**：本轮用 **ZF146**（开工前查过：`build\zftools` 下没有 `_zf146_*`、救援目录下没有 `zf146_pre`）；
   动手后发现**新增脚本会把这轮的轮号变成 ToolLint 的"当前轮次"**（`LATEST` 取最大号），
   所以 `_zf146_*` 里的 `publish` / `docs` / `backup` 类脚本必须当场满足门 ⑧ 的三条硬规矩。
'''


if __name__ == u"__main__":
    sys.exit(main(sys.argv[1:]))
