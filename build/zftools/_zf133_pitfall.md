### 4.113 【陷阱】假玩家探针：**一出生就是死的**，而且必须进 `PlayerList`

ZF133 的冲击波探针头几轮全军覆没，两个原因叠在一起，而症状都指向**错误的方向**：

| 现象 | 真因 | 判据 |
|---|---|---|
| 波「起了」（`activeCount=1`、耐久扣了 120）却**一格都不拆**，下一 tick 就消失 | 假玩家 `placeNewPlayer` 之后**血量是 0**（`alive=false`），而 `ShockwaveManager.tick()` 第一句就是「发射者还在不在」 | 探针打印 `[HP] t=20 hp=0.0 alive=false`；救法 `setHealth(max)` + `deathTime=0` + `revive()`，**并且在开场就断言「满血存活」**（前提也要有判据） |
| 同上，且「按 UUID 找回玩家」的服务端逻辑一律判成「人已经走了」 | 假玩家**没进 `PlayerList`**，`getPlayer(uuid)` 恒 null | `server.getPlayerList().placeNewPlayer(conn, p, cookie)`；⚠ 1.21.1 的 `PlayerList` **没有** `add(ServerPlayer)` |
| 平台上的假玩家被苦力怕炸死、测试方块被炸飞 | 悬空石台**厚度只有 1 格**、台面下方无光 ⇒ 刷怪；爆炸波及台面 | 开场 `setDifficulty(PEACEFUL, true)` + `discard()` 掉范围内的 `Mob`；每个场景开局 `keepAlive()` |
| `setGameMode` 抛 NPE（`connection.latency()`） | 顺序反了：**必须先接上 `connection` 再 `setGameMode`** | 见 `Zf133Check.makePlayer()` 的注释 |

### 4.114 【陷阱】PowerShell 5.1 + 中文代码页读**无 BOM 的 UTF-8 ps1** ⇒ 报的错指向错误方向

`Audit.ps1` / `LangCheck.ps1` / `RecipeCheck.ps1` 都是**无 BOM 的 UTF-8**，
而本机是 **Windows PowerShell 5.1 + GBK 代码页**：`powershell -File xxx.ps1` 会按 ANSI 解码源码，
中文连同后面的 `}` 一起被吃坏，报出来的是 **「缺少右花括号 / Unexpected token」** ——
看着像「门脚本坏了」，其实是**调用方式不对**（我第一版就这么误判了三道门）。

正确调法（三个 .ps1 自己头部就写着）：

```powershell
$sb = [scriptblock]::Create([IO.File]::ReadAllText('<路径>', [Text.Encoding]::UTF8)); & $sb
```

⇒ 一句话规矩：**门报语法错，先怀疑调用方式**。`_zf133_gates.py` 已按正确方式固化。

### 4.115 【陷阱】框架事件**不是**判据：末地龙重写 `hurt()` 不调 `super.hurt()`

「末地那一刀打出了 12 点伤害」这件事，我一开始用 NeoForge 的 `LivingIncomingDamageEvent` 去抓，
**监听器一次都没被调用**，于是连报三轮「命中 0 次」。而同一时刻的 `hurt(...)` 明明**返回 true**、
末地龙血量 208 → 196。

根因：**末地龙重写了 `LivingEntity#hurt`，不走 `super.hurt`** ⇒ NeoForge 在 `super.hurt` 里发的事件压根不发。
⇒ 规矩：**「调了 `hurt` 就一定有事件」是错的**；事件的覆盖范围取决于**被观测对象怎么实现**。
判据要么改成「当场量血量变化」（本轮最终做法：反射造一道波 → 直接调 `damageAt` → 当场读 `getHealth()`，
实测 `40.0 -> 28.0`），要么换成别的可观测事实。

同一条还有第二个坑：**末地龙每 tick 回 1 血** ⇒ 「过 40 tick 再比血量」同样是**测不出来**的
（实测掉血实体 0 个）。**「伤害没发生」和「伤害被再生盖掉了」在快照法里长得一模一样。**

### 4.116 【陷阱】探针的时间线常量**不许撞车**（同值 = 后面整段被静默跳过）

`Zf133Check` 用 `if (t == T_A) ... else if (t == T_B) ...` 派发场景。
我把 `T_B_CHECK` 从 60 改成 120 时没注意 `T_D` **本来就是 120** ⇒ 后者永远轮不到
⇒ `buildD()` 没跑、`wallLog` 是 null ⇒ tick 里 NPE ⇒ **整场在 t=150 崩掉，后面九个场景一个没跑**。
而报告上看着像「一堆互不相关的失败」。

防复发：探针开场加了一条**自检** —— 把所有 `T_*` 常量两两比一遍，撞车就当场 FAIL 并打印是哪两个。

### 4.117 【陷阱】「改注释」**绝不能**和「功能行」放在同一次替换里（本轮代价最大的坑）

我用一个脚本把某段代码**连同注释**一起替换，意图只是「把语义写清楚」，
结果把夹在其中的一句 `if (state.isAir()) { continue; }` **吞掉了**。
后果：空气被当成「斧子挖不动的方块」（`isCorrectToolForDrops(空气) = false`）⇒
**每一格空气都把波挡死** ⇒ 波在第 1 tick 就散。

而这个 bug 的**探针表现是「宽度内 6 根原木只掉 5 根」** —— 看着像「判据顺序错了」，
于是我朝着那个方向改了四轮（改判据、挪检查点、量血量…），越改越远。
最后是「把挡住波的那一格打出来」（`[WB]` 126 条记录**全是 Air**）一句话定案。

⇒ 规矩两条：

1. **纯注释改动就只改注释**（整段注释块单独替换，功能行一个字别动）；
2. 遇到「少拆一格」这类**部分失败**，第一步是**把参与判定的那一格/那一步打出来**，
   而不是先改判据 —— 症状的位置（少一格）与原因的位置（空气被判成墙）可能毫无关系。
