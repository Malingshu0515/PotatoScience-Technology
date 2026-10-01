# -*- coding: utf-8 -*-
u"""_zf156_docs.py —— ZF156 文档落地（幂等，默认 dry-run）。

  ① 档案 **§4.164**：三条根因（区块卸载 / 玩家克隆 / 板子跨 mod 口径）+ 两条判据修正；
  ② 档案 **§5** 加 ZF156 行（接在 ZF155 行之后）；
  ③ 档案 **§9** 加 ZF156 小节（**待用户实测**）；
  ④ 交接 **§6** 加第 32 条；
  ⑤ 英文公告末尾加一条（§4.150 日志纪律）。
  ⚠ 版本线本身（0.13）在 `gradle.properties` 里；§1 的语言键数 / 配方份数**本轮没变**（594×4 + lzh 596 / 91）。

跑法：python build\\zftools\\_zf156_docs.py [--write]
"""
import io
import os
import re
import sys

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding=u"utf-8", errors=u"replace")

ROOT = r"E:\PotatoST"
DOC = os.path.join(ROOT, "docs", "开发档案.md")
HAND = os.path.join(ROOT, "docs", "多会话协作交接.md")
ANN = os.path.join(ROOT, "docs", "UpdateAnnouncement_EN.md")

notes, fails, plan = [], [], []


def want(text, old, new, label):
    if new in text:
        notes.append(u"  [跳过] %s（已经在，幂等）" % label)
        return text
    if text.count(old) != 1:
        fails.append(u"%s：锚点命中 %d 次（应为 1）" % (label, text.count(old)))
        return text
    notes.append(u"  [改] %s" % label)
    return text.replace(old, new, 1)


D4_TITLE = u"### 4.164 【判据雷】区块卸载也会走 setRemoved；玩家持久化数据在克隆里会丢；板子的跨 mod 口径（0.13 ZF156）"
D4 = D4_TITLE + u"""

用户这一轮点了三件事：「**有些时候端子上已经连接的线会消失（不知道是不是刷新没的问题）**」
「**potatoST手册每回进游戏都会给一本 过于冗杂 改成只有玩家第一次进入游戏才会给**」
「**本mod配方里的金属板可以兼容别的mod金属板（板子确实通用 但是咱们的合成配方只认本mod板）**」。
三条都不是"文件写错了"，是**运行期语义**踩了坑，所以三条都拿真服务端探针（`Zf156Check`，20 项）当主证。

**① 端子连线：区块卸载也会叫 `setRemoved()`，而我们在那儿断了对端。**
`ServerLevel.unload(LevelChunk)`（`ServerLevel.java:965-967`）就是干这个的：
`chunk.clearAllBlockEntities()`；而 `LevelChunk.clearAllBlockEntities()`（`LevelChunk.java:616-618`）
对**每一个**方块实体先 `onChunkUnloaded()`、**再** `setRemoved()`。
原来的 `TerminalBlockEntity.setRemoved()` 不分青红皂白地"通知所有对端把连接删掉"⇒
**玩家一走远、区块一卸载，双方就开始互相划账**：被卸载的那一份自己那份连接表没动
（卸载前 `ChunkMap.processUnloads` 先存盘 `ChunkMap.java:544`、再卸载 `:546`），
可**还活着的那一份**被划掉了，而且当场 `sync()` 到客户端 ⇒ 线当场看不见。
谁画线？`TerminalRenderer.renderFeWires` 里 `if (selfPos.compareTo(otherPos) > 0) continue;`
—— **每根线只由坐标小的那一端画**，所以只要消失的是"坐标小的那一端"，线就**永久**没了
（要重新接一次才回来）。两个端子谁大谁小纯看坐标 ⇒ 这就是用户说的「**有些时候**」。
修法：用原版给的判据把两条路分开 —— `onChunkUnloaded()` 先被叫过就是"区块卸载"（不拆线），
没被叫过就是"方块真没了"（照旧通知对端，三条路：挖掉 / 被替换 / NeoForge 的
`removeErroringBlockEntities`）。⚠ 早退必须放在 `isClientSide` 判断**之前**：
客户端重收区块包（`LevelChunk.replaceWithPacketData`）也走 `clearAllBlockEntities()`，标记要当场消费掉。

**② 手册每回都发：玩家持久化数据在"克隆"里会被丢掉。**
1.21.1 里换维度与死亡重生走的是同一套：`ServerGamePacketListenerImpl:1669`
（`CHANGED_DIMENSION`）与 `:1676`（`KILLED`）都调 `PlayerList.respawn(...)`，
而它第 468 行 `serverplayer.restoreFrom(player, keepInventory)` —— `ServerPlayer.restoreFrom`
（`ServerPlayer.java:1437`）只搬**一个**键：
`if (old.contains(PERSISTED_NBT_TAG)) getPersistentData().put(PERSISTED_NBT_TAG, ...)`。
别的键（包括 0.12 写在持久化数据里的 `potato_s_t_guide_given`）**一律不搬** ⇒
**每换一次维度、每死一次，标记就没了**，下次进游戏又发一本。
真实存档也对得上：同一个玩家在 `科技mod乱炖\\saves\\新的世界`（没死过）里带标记、
在 `新的世界 (1)`（有 `LastDeathLocation` + `SpawnDimension`）里标记就没了。
修法：标记搬进 **NeoForge 附件**（`ModAttachments.GUIDE_GIVEN`，`serialize(Codec.BOOL)` +
**`copyOnDeath()`**）—— `restoreFrom` 的倒数第四行 `EventHooks.onPlayerClone(...)`
会触发 NeoForge 自己的 `AttachmentInternals.onPlayerClone` → `copyAttachmentsFrom(original, isWasDeath)`，
死过一次的那种只拷声明了 `copyOnDeath` 的（`AttachmentInternals.java:53`）。
0.12 的老标记**只读留着**（老存档里已经拿过书的不补发第二本），登录时顺手把它迁移到附件上。

**③ 金属板：配方原料写的是"物品"，而板子的跨 mod 口径是"标签"。**
`{"tag": ...}` 是原版 `Ingredient` 就支持的写法（`Ingredient.Value.MAP_CODEC` 的 fallback，
原版配方自己就在用 `minecraft:planks`）；而 `c:plates/<金属>` 这三条证据都在盘上：
① 沉浸工程 12.4.2 自带 14 张 `c:plates/*`（`immersiveengineering:plate_iron` 等）；
② 机械动力 6.0.10 自带 5 张（`create:iron_sheet` 等，父标签 `c:plates` 也写了）；
③ **我们自己的 7 张 `c:plates/<金属>` 是另一条线 ZF152 挂的**（那轮做的是反方向：
"让我们的板进别人的配方"）。
所以本轮**不需要**往标签里硬写别人的物品 id —— 把 29 处原料从
`{"item": "potato_s_t:<金属>_plate"}` 换成 `{"tag": "c:plates/<金属>"}`，
谁挂标签谁就能顶上（Create 的铁片、IE 的铁板都能直接当原料）。
⚠ **副产品账**：那 15 份数据文件（7 张子标签 + 父标签 + 7 条 `create:pressing`）
在 ZF152 那条线**只落在盘上、还没进 git**；本轮的配方现在**引用**它们，
所以这一轮把它们一并带上车（否则 HEAD 里我的配方指向一个空标签 = 死配方）。

**④ 判据修正一：探针数"板原料"要按「配方 + 标签」去重，不能按合成格数。**
第一版按"合成格"数，报出 **70 处**（一条配方里同一个板占好几个格子会重复计），
而盘上是 **29 处** JSON 引用。判据当场改成 `Set<配方id + 标签id>` 去重 = 29，
并把"格子展开数"降级成报告里的一行观察记录（观察记录里 70 这个数是对的，只是口径不同）。

**⑤ 判据修正二：格式门（无 BOM / 纯 LF）只对本轮动过的文件判。**
盘上**本来**就有两份别人留下的 CRLF 配方（`copper_wire_spool.json` / `power_cable_spool.json`，
HEAD 里就是 CRLF）—— 第一版把整个配方目录都判进去，等于把别人的账算到自己头上。
改成"只判本轮改过的 21 份配方 + `gradle.properties`"，别人那两份只列成 `[INFO]` 情报。
"""
D4_ANCHOR = u"| ZF147 | \u26a0 **没有备份根也要有账**"

D5_ROW = (u"| ZF156 | **新建 `zf156_pre`**（**140 份**：`TerminalBlockEntity.java` / `GuideBook.java` / "
          u"`PotatoST.java`（⚠ 探针挂载点，动手前就在清单里）/ `ModItems.java`（只改注释）/ "
          u"28 份含金属板的配方 / `c:plates*` 标签 / `gradle.properties` / 三份文档 / 全部常驻门 / "
          u"成品 0.12 + `.sha1` + `build\\libs` 那份；逐份核 sha1 + 回读，失败 0。"
          u"⚠ 开工前查过轮号：`_zf156_*` 没人占、救援目录里没有 `zf156_pre`（§4.147））"
          u" | **0.13：三个小修**（用户原话「0.13 先简单修一下bug和一些小建议 1.有些时候端子上已经连接的线会消失"
          u"（不知道是不是刷新没的问题）2.potatoST手册每回进游戏都会给一本 过于冗杂 改成只有玩家第一次进入游戏才会给 "
          u"3.本mod配方里的金属板可以兼容别的mod金属板（板子确实通用 但是咱们的合成配方只认本mod板）」）。"
          u"① **端子连线消失**：根因是 `LevelChunk.clearAllBlockEntities()`（区块卸载那条路，"
          u"`ServerLevel.unload` → `:616-618`）会先 `onChunkUnloaded()` 再 `setRemoved()`，"
          u"而旧 `setRemoved` 一律通知对端删连接 ⇒ 走远一次就互相划账；又因为每根线只由坐标小的那端画，"
          u"所以「有时候」永久消失。修法：`onChunkUnloaded` 打标记、`setRemoved` 见标记就只消费不拆线"
          u"（真挖掉/被替换/崩掉移除三条路照旧通知对端）。"
          u"② **手册每回都发**：根因是换维度（`ServerGamePacketListenerImpl:1669`）与死亡（`:1676`）"
          u"都走 `PlayerList.respawn` → `ServerPlayer.restoreFrom`，而 `restoreFrom` "
          u"只搬 `PERSISTED_NBT_TAG` 一个键 ⇒ 0.12 写在持久化数据里的标记每换一次维度/每死一次就丢。"
          u"修法：标记搬进 **NeoForge 附件**（`ModAttachments.GUIDE_GIVEN`，`serialize(Codec.BOOL)` + "
          u"`copyOnDeath()`），老标记只读迁移（已拿过书的不补发）。"
          u"③ **金属板跨 mod**：29 处原料从 `{\"item\": \"potato_s_t:<金属>_plate\"}` 换成 "
          u"`{\"tag\": \"c:plates/<金属>\"}`（21 份配方；液压机那 7 份产物一字未动）—— 靠的是社区约定 + "
          u"IE/Create 自己挂好的标签，不硬写别人的 id；另把 ZF152 那条线**只在盘上、没进 git** 的 15 份 "
          u"`c:plates*` / `pressing` 数据一并带上车（我的配方现在引用它们）。"
          u"④ 探针 `Zf156Check`（真开服）**20 项 ALL OK**：区块卸载后对端仍在（FE + 动力）、"
          u"卸载那份自己的表没被清空、真挖掉仍会清（负对照）；附件默认 false → 标记 true → "
          u"`copyAttachmentsFrom(isDeath=true/false)` 两条路都带过去、老机制**不**带（负对照）、"
          u"老标记仍算已给过；表里 29 处 `#c:plates/*` 原料 / 铁铜板原料同时认 Create 的铁片铜片 / "
          u"标签两边都收着 / 金片不混进来（负对照）/ 配方总数仍 91。"
          u"⑤ 常驻 `_zf156_verify.py` + 反证 11 把刀 + 版本线 0.12 → **0.13**（三份断言版本号的老门跟平）"
          u"| 见 §9 ｜ 见 §4.164 |\n")

D9_ANCHOR = u"## 10. 备份策略"
D9 = u"""### ZF156（0.13）三个小修：**端子连线不再凭空消失** / **手册只发一次** / **金属板跨 mod** —— **待你实测**

用户原话：「**0.13 先简单修一下bug和一些小建议 1.有些时候端子上已经连接的线会消失（不知道是不是刷新没的问题）
2.potatoST手册每回进游戏都会给一本 过于冗杂 改成只有玩家第一次进入游戏才会给
3.本mod配方里的金属板可以兼容别的mod金属板（板子确实通用 但是咱们的合成配方只认本mod板）**」。

**你手上要试的三件事**

| # | 怎么试 | 应该看到 |
|---|---|---|
| 1 | 两个端子用线轴连上（铜线/银线/紫线都行），然后**走远到区块卸载**（十几格以外、或者干脆退出重进这个世界），再回来看 | 线**还在**。以前会「有时候」永久消失，得重新接一次 —— 根因见 §4.164① |
| 2 | 新玩家第一次进游戏 | 给一本手册（照旧） |
| 3 | 同一个玩家：**去一趟下界/末地/暮色**、或者**死一次重生**、再退出重进 | **不再**补发手册（以前每换一次维度或每死一次，下次进游戏就再来一本） |
| 4 | 装着沉浸工程：拿**沉浸工程的铁板**代替我们的铁板去合成（比如电容器、灌装机、太阳能板这些用铁板的机器） | 能合成。铜板/铝板/钢板/银板/镍板同理（IE 的板都挂在这些标签上） |
| 5 | 装着机械动力：拿 **Create 的铁片/铜片**（`create:iron_sheet` / `create:copper_sheet`）当原料 | 能合成（Create 自己就挂在 `c:plates/iron` / `c:plates/copper` 上） |
| 6 | 没装那些 mod 时：拿**我们自己的板**照常合成 | 一切照旧 —— 本轮只是"多认别人家的板"，自家人家的板都还认 |
| 7 | 液压机压板（铁锭→铁板那种） | 产物还是**我们自己的板**（没动）；只认我们自己的锭（这条不在本轮范围） |

**已知边界（说清楚，别以为是漏了）**
- 板的跨 mod 兼容**只走 `c:plates/<金属>` 这个社区约定**：别人挂了标签就能用，没挂就不行
  （IE 12.4.2 与 Create 6.0.10 都挂了；机械动力的"片"和沉浸工程的"板"都能当我们的原料）。
  **钴板**只有我们自己有（别人没这个金属），所以 `c:plates/cobalt` 里只有我们那一件。
- 手册的"发过了"标记现在是**附件**：老存档里已经拿过书、标记还在的玩家**不会**补发；
  标记已经丢了的（0.12 期间死过/换过维度）会**补发一本**，之后再也不会多发。
- 端子那条修的是"区块卸载"这条路；**真把端子挖掉**该断还是断（探针 A5 专门验了这条负对照）。

---

"""

H6_ANCHOR = (u"    ③ 谁要拿 ZF139 的探针源码复核那轮结论，**以报告 `_zf139_probe_utf8.txt` 为准**（52 项全绿那份）。")
H6_NEW = H6_ANCHOR + u"""
    ④ 谁要拿 ZF155 的探针源码复核那轮结论，**以报告 `_zf155_probe_utf8.txt` 为准**（28 项全绿那份）。

32. **ZF156 的账（0.13 三个小修）**：① 三条根因与修法见档案 §4.164，探针 `Zf156Check`
    （真开服 20 项，报告 `_zf156_probe_utf8.txt`）。② **我定的、用户没说的**：端子那条**只**修
    "区块卸载"这一路（真挖掉照旧断，负对照 A5）；手册标记**搬进附件**而不是打补丁
    （`getPersistentData()` 这条路的失效面是整个"玩家克隆"，不止死亡）；金属板**只**改原料不改产物、
    **只**走 `c:plates/*` 不硬写别人的物品 id。③ ⚠ **我把 ZF152 那条线没进 git 的 15 份数据带上车了**
    （7 张 `c:plates/*` 子标签 + 父标签 + 7 条 `create:pressing`）：本轮 29 处配方原料现在引用它们，
    不带上车 HEAD 里就是"配方指向空标签 = 死配方"。那 15 份是 ZF152 的产物，**不是我写的**。
    ④ 版本线 0.12 → **0.13**：`gradle.properties` 一处 + 三份断言 `mod_version` 的老门跟平
    （`_zf73` / `_zf78` / `_zf79_verify.py`；其中 `_zf78` 那条本来就自相矛盾 —— 标签写 0.12、断言写 0.11，
    本轮一并跟到 0.13）。⑤ 已知小债：`copper_wire_spool.json` / `power_cable_spool.json`
    这两份配方**是 CRLF**（HEAD 里就是，不是本轮弄的，`.gitattributes` 是 `* -text` 所以 git 不会自动转）；
    本轮只把它记成情报，没顺手改（别人的文件）。"""

ANN_ADD = u"""
## New in 0.13 ZF156 - Three small fixes

- **Terminal wires no longer vanish.** Wires used to disappear "sometimes" after you walked away and
  came back. Cause: when a chunk unloads, Minecraft calls `setRemoved()` on every block entity
  (right after `onChunkUnloaded()`), and our terminal used to unlink its partner there - so the two
  ends forgot about each other and the wire was gone for good. Terminals now tell the two cases
  apart: a chunk unload keeps the wire, actually breaking a terminal still removes it.
- **The guide book is given only once, ever.** It used to be handed out again after every dimension
  change or death: 1.21 recreates your player at those moments, and the old "already given" flag
  lived in player data that is dropped by that clone. The flag now lives in a NeoForge attachment
  with `copyOnDeath`, so it survives respawns, dimension changes and relogs. Existing saves that
  still carry the old flag are not given a second book.
- **Metal plates are now cross-mod.** All 29 plate ingredients in our recipes now use the common
  `c:plates/<metal>` tags instead of our own plate items, so another mod's plate works just as well:
  Immersive Engineering's `plate_iron` / `plate_copper` / ... and Create's `iron_sheet` /
  `copper_sheet` can be used in our machines' recipes. Our own plates keep working exactly as before,
  and the hydraulic press still produces our plates.
"""


def main(argv):
    write = u"--write" in argv

    doc = io.open(DOC, encoding=u"utf-8", newline=u"").read()
    nums = [int(m.group(1)) for m in re.finditer(u"(?m)^#{3,4} 4\\.([0-9]+)", doc)]
    mx = max(nums)
    already = D4_TITLE in doc
    print(u"档案 §4 最大编号 = %d（目标 §4.164；已写入 = %s）" % (mx, already))
    if not already and mx != 163:
        fails.append(u"§4 编号不是 164（实测 max=%d）—— 停手先看清" % mx)

    doc2 = want(doc, D9_ANCHOR, D9 + D9_ANCHOR, u"档案 §9 加 ZF156 小节")
    if D4_TITLE not in doc2:
        doc2 = want(doc2, D4_ANCHOR, D4 + u"\n\n" + D4_ANCHOR, u"档案 §4.164")
    if u"| ZF156 |" in doc2:
        notes.append(u"  [跳过] 档案 §5 的 ZF156 行（已经在，幂等）")
    else:
        anchor = u"| 见 §9 ｜ 见 §4.163 |\n"
        if doc2.count(anchor) != 1:
            fails.append(u"档案 §5：找不到 ZF155 行尾（命中 %d 次）" % doc2.count(anchor))
        else:
            doc2 = doc2.replace(anchor, anchor + D5_ROW, 1)
            notes.append(u"  [改] 档案 §5 加 ZF156 行（接在 ZF155 之后）")
    if doc2 != doc:
        plan.append((DOC, doc, doc2))

    hand = io.open(HAND, encoding=u"utf-8", newline=u"").read()
    h2 = want(hand, H6_ANCHOR, H6_NEW, u"交接 §6 加第 32 条")
    if h2 != hand:
        plan.append((HAND, hand, h2))

    ann = io.open(ANN, encoding=u"utf-8", newline=u"").read()
    if u"## New in 0.13 ZF156" in ann:
        notes.append(u"  [跳过] 公告 ZF156 那一条（已经在，幂等）")
    else:
        plan.append((ANN, ann, ann.rstrip(u"\n") + u"\n" + ANN_ADD))
        notes.append(u"  [改] 公告末尾加 ZF156 那一条")

    print(u"\n".join(notes))
    print(u"")
    print(u"计划写盘 %d 份" % len(plan))
    print(u"失败项 = %d" % len(fails))
    for f in fails:
        print(u"  !! " + f)
    if fails or not write:
        if not write:
            print(u"（没加 --write，只算不写）")
        return 1 if fails else 0
    for path, _old, new in plan:
        io.open(path, u"w", encoding=u"utf-8", newline=u"").write(new)
        print(u"  已写 %s" % os.path.relpath(path, ROOT))
    return 0


if __name__ == u"__main__":
    sys.exit(main(sys.argv[1:]))
