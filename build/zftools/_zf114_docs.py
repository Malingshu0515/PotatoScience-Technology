# -*- coding: utf-8 -*-
u"""_zf114_docs.py —— ZF114 建档：§5 一行 + §9 一节 + §4 四条新雷区

规矩：**只加行**（§4.7 汇合点文件）。每处插入都用唯一锚点 + 命中次数断言，
写完再复核一遍"插进去的东西在文件里恰好出现一次"。

跑法：
    python build\\zftools\\_zf114_docs.py            # 体检
    python build\\zftools\\_zf114_docs.py --write     # 写入
"""
import io
import sys

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

DOC = r"E:\PotatoST\docs\开发档案.md"

ROW = (u"| ZF114 | **新建 `zf114_pre`**（725 份改前件：`ModItems`/`PotatoST`/`PotatoSTClient` + 四份 lang + "
       u"`data/c/tags/**` + **全部 `_zf*.py` / `_zf*.ps1` 与九道门** + 3 份文档 + 旧成品 jar 与 `.sha1`；"
       u"逐份核哈希、失败 0。⚠ **另有 1 份补账**（动手之后才发现要碰）：`LithiumBatteryPlantBlock.java` —— "
       u"Audit 的 B 项报出 ZF112 那台机器「有物品栏但未掉落」，按 §4.13 补 `onRemove`，见 `zf114_pre\\_补说明.txt`） | "
       u"0.11：**星轨坠 + 粗振金**。① **本工程三个「第一次」**：自定义实体（陨石）、自定义数据包（S2C 倒计时）、"
       u"HUD 图层（快捷栏上方的红色倒计时）—— 三样都是先 javap 查出真签名再写的，编译一次过；"
       u"② 数值逐条照用户原话：耐久 **4**（右键一次扣 1、不可附魔）、**600 tick** 倒计时、**前 200 tick 可取消**、"
       u"剩余 **20/15/10/5/3/2 秒**各通报一条、最后 1 秒播「使用者 + 坐标」、陨石从 **y=200** 以恒定 1.8 格/tick 落下"
       u"（约 3.8 秒）、落地 roll **7~20** 威力（**一个数两用**：既是原版爆炸 power，也是掉落档位）、"
       u"**7~12 只出粗铁/粗铜**、**13 以上**从 `#c:raw_materials` 抽、**15 以上**固定 +3 个粗振金、爆炸**破坏地形 + 带火**；"
       u"③ 落点**定在右键那一刻**（用户拍板）—— 探针专门验了「跑开 30 格之后原地毫发无伤」；"
       u"④ **不要太卡**：尾迹每 tick 8 火焰 + 3 浓烟（熔岩/末地烛按 `%3`/`%5` 抽稀）、爆炸走原版 `Level#explode`、"
       u"喷射 6~12 件；倒计时同步**只发 4 个包**（发截止时刻，客户端自己算剩余秒数）；"
       u"⑤ 战果：`_zf114_verify.py` **182 项 0 失败**、反证 **13 把刀全咬住**、真服务端探针 **29 项 ALL OK**、"
       u"**八道门全绿**；四语言 **417 → 432 键**（20 份往轮校验 + 英文公告 + ZF115 的基线一次改全） | 见 §9 |\n")

S4 = u"""
### 4.86 【探针雷】无头服务端里的假玩家：光 `new Connection` 不够，还要给它一个 `EmbeddedChannel`（0.11 ZF114）

写星轨坠探针时，假玩家一"起手"就抛：

```
java.lang.NullPointerException: Cannot invoke "io.netty.channel.Channel.attr(AttributeKey)"
  because the return value of "net.minecraft.network.Connection.channel()" is null
```

§4.43 那条只说了"挂一个没连上的 `Connection`，`send()` 就只入队" —— 那对**发进度奖励**够用，
但**系统聊天包**（`displayClientMessage` 走的那个）会解引用 `connection.channel()`，channel 为 null 就炸。
（`attr(...)` 的调用点既不在 `Connection` 也不在 `ServerGamePacketListenerImpl` 的字节码里，多半在 NeoForge 的补丁里 ——
追不到就不要追，直接把夹具修对。）

**修法**（一行反射）：`Connection.channel` 是 `private io.netty.channel.Channel channel`，
塞一个 netty 的 `EmbeddedChannel`（本地通道，**不进网络**、写进去只是入队）：

```java
Field f = Connection.class.getDeclaredField("channel");
f.setAccessible(true);
f.set(conn, new io.netty.channel.embedded.EmbeddedChannel());
```

> 同轮还有一条**产品侧**的教训（同一个报错的下半场）：NeoForge 的 `NetworkRegistry.checkPacket`
> 会拒绝把自定义 payload 发给"**没登记过这条通道**"的客户端 ——
> `UnsupportedOperationException: Payload potato_s_t:starfall may not be sent to the client!`。
> 无头假玩家必然没登记，但**原版客户端 / 版本对不上的客户端**同样会踩 ⇒ 产品代码里
> `StarfallNetworking.sendTo` 现在用 try/catch 兜住、只报一次英文日志：
> **倒计时归服务端管，HUD 只是装饰，不该因为发不出包就让整个右键崩掉。**

### 4.87 【方法论】探针的三种"假 FAIL"：参照物拿错、记账范围不对、夹具前提没验（0.11 ZF114）

星轨坠探针连跑 5 次才全绿，**每一次的 FAIL 都是判据自己的错**（产品代码一行没错）：

| 现象 | 根因 | 规矩 |
|---|---|---|
| 「玩家跑开后原地毫发无伤」报「被破坏 25 格」 | 我拿**木板**去比玩家跑开后的新位置 —— 那儿本来就不是木板（平台只铺在落点），`!is(OAK_PLANKS)` **恒真** | 判据要能失败，但不能**恒**失败；比"有没有变"要**先拍快照**，别比"是不是某个方块" |
| 「喷射件数 8，实际 16 / 17」 | 记账把**爆炸炸出来的东西**算成了"喷出来的矿"：先是地下的天然矿石、后来是木板掉落、再后来是**上一次跑剩下的旧掉落物** | 记账的**判据**要和被测对象对齐（只收矿物）；试验场要**清场**（同存档重复跑必须可复现）；场地要**悬空**（离地 50 格，爆炸够不到任何天然方块） |
| 「爆坑 0 / 火 0 / 矿物 0」 | `getHeightmapPos` 在**区块没加载**时返回世界底部（实测 y=-63）⇒ 平台被埋进深层石头、陨石在半空就炸了 | 夹具的**前提**也要断言（"地表高度 > 0"，否则直接收工）—— 前提不成立时后面几十条断言全是噪声 |

**共同点**：三条都不是"代码坏了"，而是"**探针看到的世界与真实世界不一样**"（§4.31 同源）。
所以探针里凡是"手工摆一个场景"，都要问一句：真玩家（真存档、真区块、真掉落物）看到的会是这个吗？

### 4.88 【数据事实】`#c:raw_materials` 不是"你那 9 种粗矿"—— NeoForge 的通用标签自带原版三项（0.11 ZF114）

给星轨坠写"13 以上从全部粗矿里抽"时，探针打出来的清单里出现了 **Raw Gold**：
NeoForge 的 `universal.jar` 往 `c:raw_materials` 里塞了原版的 **粗铁 / 粗铜 / 粗金**，
本工程的 `data/c/tags/item/raw_materials.json` 只是**合并**上去的那 9 条。

⇒ 两条推论：① 用户原话「12 以上所有粗矿标签都有」**字面上就包含原版粗金**，照做即可（本轮就是这么做的）；
② 反过来说，**"我的粗矿集合"永远不等于那张标签** —— 要精确控制集合就得自己列白名单，
想让整合包/别的 mod 一起玩就用标签，两者不能混着猜。这跟 §4.39「`c:` 兼容标签 ≠ 原版功能标签」是同一族：
**标签是数据，不是你的代码**。

### 4.89 【实现雷】爆炸会清掉物品实体 ⇒ "喷出来的东西"必须在 `explode` **之后**生成（0.11 ZF114）

星轨坠落地要同时做两件事：爆炸 + 喷射粗矿。第一版把"生成掉落物"写在 `explode` **之前**，
结果物品实体被自己的爆炸清掉（原版爆炸对物品实体走 `Entity#hurt`/`discard`）。

**正确次序：先炸、后撒。** 而且这是**可文本断言**的：`_zf114_verify.py` 的 D1 直接比
`impact()` 里 `level.explode(` 与 `new ItemEntity(` 的**行号先后**，反证刀 J01 把两段对调 ⇒ 当场挂。
凡是"一次事件里既破坏又产出"的地方（陨石、粉碎、拆解掉落），都要问一句**谁先谁后**。
"""

S9 = u"""
### ZF114（0.11）星轨坠 + 粗振金 —— **待你实测**

用户原话：「加一个 星轨坠 道具 右键使用（一共四点耐久右键一次扣1点 不可附魔） 快捷栏上方显示30s红色倒计时
10s之前再次右键可以取消 10s之后聊天栏通报倒计时 不可取消 最后1s聊天栏显示 星轨坠使用者 坐标
作用：召唤出1个陨石 从y=200砸下来 伴随粒子效果 落地后产生7~20power的爆炸 带火
并喷射出一些粗矿 7-12只有铁铜 12以上所有粗矿标签都有 15以上固定产出3个粗振金
尽你所你做炫酷一点 同时不要太卡 谢谢了」

四条拍板（都取默认项）：**粗振金 = 本轮新增物品**（只做物品）／**落点 = 右键那一刻的位置**／
**爆炸 = 破坏地形 + 带火**／**先不给配方**（只能创造模式拿）。

- [ ] **要你实测的（一次看全）**：
      ① 创造页最后有 **星轨坠**（紫名、4 点耐久条）和 **粗振金**；
      ② 右键 ⇒ 快捷栏上方出现**红色倒计时**（带深色底条，最后 5 秒会轻微脉动、颜色转亮红）；
      ③ **前 10 秒**再右键一次 ⇒ 取消（聊天栏提示"召唤已取消"，耐久**不再扣**）；
      ④ 再起手、等过 10 秒再右键 ⇒ 提示"已经锁定，取消不了了"，仪式照走；
      ⑤ 10 秒之后聊天栏会按 **20/15/10/5/3/2 秒**通报，**最后 1 秒**播「谁 + 坐标」；
      ⑥ 到点：天上掉下一颗**旋转的岩浆火球**（带火焰/浓烟/末地烛尾迹与呼啸声），
         从 y=200 砸下来约 4 秒；落地**大爆炸 + 起火**，并**喷出一批粗矿**；
      ⑦ 关键一条：**右键之后跑开** —— 陨石仍然砸**原来那一格**（不是追着你跑）；
      ⑧ 威力是随机的（7~20）：多试几次能看到档位差异 —— 低威力只出**粗铁/粗铜**，
         高威力出**各种粗矿**（含原版**粗金**，因为它在 `#c:raw_materials` 里，见 §4.88），
         **15 以上**额外给 **3 个粗振金**。
- [ ] ⚠ **威力 20 是个大坑**：TNT 的 power 是 4，20 就是它的 5 倍，半径十几格、还会引燃 —— 别在基地里试。
- [ ] ⚠ **还没有配方的名单**（用户明确"先不给配方"）：**星轨坠** 与 **粗振金** 都在里面
      （加上原有的 扳手 / 高级金属块）。
- [ ] ⚠ **粗振金目前"只有来源、没有下游"**：矿石、深层变体、锭、用途、配方都还没有 ——
      与"硫"当初同一条口径（用户没说的不发明）。
- [ ] 本轮**不动**任何活体数字以外的内容：四语言 **417 → 432 键**（+15），
      20 份往轮校验 + 英文公告 + ZF115 的脚本基线已一次改全。
- [ ] 取证与存档：反证 13 把刀（`_zf114_falsify.py`）、真服务端探针 `check/Zf114Check.java`
      与 UTF-8 报告 `check/zf114_星轨坠取证.log`（29 项 ALL OK）、
      贴图生成器 `_zf114_textures.py`（两张 16×16 程序生成占位，落盘前都出图看过）。
- [ ] **顺手替 ZF112 补的一条**：`Audit.ps1` 的 B 项报出「锂电池构造间有物品栏但未掉落」，
      按 §4.13 给它补了 `onRemove` + `MachineDrops.dropInventory`（改的是**方块类**，
      ZF115 正在改的是方块实体类，两个文件不重叠）。**这条不在用户需求里，是门抓出来的。**

**成品**：`release\\PotatoST-0.11.jar` = **`303c5d468b96826ef6836b0a4e54ccb8a539557c`**（4,298,939 B）。
⚠ **上一版 `90510e1890af79242cb41e0cda0a2f6472b12cdf` 作废**（同版本原地重打包）。
注意这一版**同时包含 ZF109~ZF113 那几轮尚未打包的改动**（共享工作树，一次 build 全带上了）。

"""


def main(argv):
    write = "--write" in argv
    text = io.open(DOC, encoding="utf-8").read()
    lines = text.split(u"\n")

    # ---------- ① §5：插在 ZF116 那行之后（那是目前表格的最后一行） ----------
    row_idx = None
    for i, l in enumerate(lines):
        if l.startswith(u"| ZF116 |"):
            row_idx = i
    assert row_idx is not None, u"找不到 §5 表格最后一行（| ZF116 |）"

    # ---------- ② §4：插在 4.85 之前（同簇里最新的一条） ----------
    s4_idx = None
    for i, l in enumerate(lines):
        if l.startswith(u"### 4.85 "):
            s4_idx = i
    assert s4_idx is not None, u"找不到 §4.85 的标题行"

    # ---------- ③ §9：插在 ## 10 之前 ----------
    s9_idx = None
    for i, l in enumerate(lines):
        if l.startswith(u"## 10. 备份策略"):
            s9_idx = i
    assert s9_idx is not None, u"找不到 ## 10. 备份策略"

    print(u"锚点：§5 表格末行 @%d，§4.85 @%d，## 10 @%d" % (row_idx + 1, s4_idx + 1, s9_idx + 1))

    if not write:
        print(u"（体检模式：三处锚点都命中恰好一次，未写盘）")
        return 0

    # 从后往前插，避免行号漂移
    lines.insert(s9_idx, S9.rstrip(u"\n"))
    lines.insert(s4_idx, S4.strip(u"\n"))
    lines.insert(row_idx + 1, ROW.rstrip(u"\n"))
    new_text = u"\n".join(lines)
    io.open(DOC, "w", encoding="utf-8", newline=u"").write(new_text)

    # ---------- 复核 ----------
    check = io.open(DOC, encoding="utf-8").read()
    bad = 0
    for label, needle, want in ((u"§5 行", u"| ZF114 | **新建 `zf114_pre`**", 1),
                                (u"§9 节", u"### ZF114（0.11）星轨坠 + 粗振金", 1),
                                (u"§4.86", u"### 4.86 【探针雷】", 1),
                                (u"§4.87", u"### 4.87 【方法论】探针的三种", 1),
                                (u"§4.88", u"### 4.88 【数据事实】", 1),
                                (u"§4.89", u"### 4.89 【实现雷】爆炸会清掉物品实体", 1)):
        n = check.count(needle)
        print(u"   %-8s 出现 %d 次 %s" % (label, n, u"✓" if n == want else u"✗"))
        bad += 0 if n == want else 1
    print(u"写入完成：%d -> %d 行（新增 %d 行），复核失败 = %d"
          % (len(text.split(u"\n")), len(check.split(u"\n")), len(check.split(u"\n")) - len(text.split(u"\n")), bad))
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
