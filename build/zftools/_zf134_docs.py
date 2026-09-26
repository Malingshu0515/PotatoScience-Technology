# -*- coding: utf-8 -*-
"""_zf134_docs.py —— 档案落笔：§9 补一段（任意角度）+ §4.125/§4.126 两条坑

锚点（都先数出现次数）：
  · §4：插在 "### 4.118 【陷阱】假玩家探针" 之前 —— 接在 4.124 之后 ⇒ 4.125 / 4.126
  · §9：插在 ZF133 段里"#### 四·补"那一节的**结尾**（即 "#### 五、本轮踩的坑" 之前，
    若没有该标题则插在 ZF133 段末）

跑法：python build\\zftools\\_zf134_docs.py [--write]
"""
import io
import os
import sys

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
DOC = r"E:\PotatoST\docs\开发档案.md"
T = r"E:\PotatoST\build\zftools"
WRITE = "--write" in sys.argv

PIT = io.open(os.path.join(T, "_zf134_pitfall.md"), encoding="utf-8").read()

SECTION = """#### 四·补二（2026-09-26 用户追加需求）：冲击波改成**任意水平角度**

用户原话：「冲击目前只会朝正方向（正东西南北）改成可以有角度的（比如东南 21° 这种）」。

**原来的结构为什么只有四个方向**：`Wave` 里存的是「主轴 + 正负号」两个字段
（`alongX` 与 `sign`），采样点直接在主轴坐标上加减整数 ⇒ 只能落在 8 个方格方向上。

**新结构：方向向量 + 法线方向的固定网格**（改成任意角度的关键，也是"正方向行为不变"的关键）：

```java
double dirX, dirZ;                   // 归一化的水平朝向（|dir| = 1）
double perpX = -dirZ, perpZ = dirX;  // 左手法线 = 阵面横铺的方向
double frontX = originX + dirX * travelled;
double frontZ = originZ + dirZ * travelled;
double lat = lateral - HALF_WIDTH;   // -3 .. +2（横向偏移仍走**固定单位网格**）
int bx = (int) Math.floor(frontX + perpX * lat);
int bz = (int) Math.floor(frontZ + perpZ * lat);
```

**为什么正方向仍然逐字等价**：朝向是 +X 时 `perp = (0, +1)` ⇒ `bx = frontX`、`bz = frontZ + lat`
—— 与旧代码完全一致（朝向 +Z 时 `perp = (-1, 0)`，整体对称，同构）。
⇒ **旧探针的九场一个字都不用改就该继续过**，这就是"正方向没坏"的判据。

| 落点 | 变化 |
|---|---|
| `ShockwaveManager.fire()` | 视线取**水平投影再归一化**；视线垂直（水平投影退化）时用 `yaw` 算方向兜底 |
| `ShockwaveManager.tick()` | 采样 = 前缘 + 法线 × 横向偏移（前缘是**双精度**，斜着走才有意义） |
| `ShockwaveNetworking` | 包里 `alongX + sign` → `dirX + dirZ`（两个 `double`） |
| `client/ShockwaveClientState` | Wave 记录改成 dirX/dirZ |
| `client/ShockwaveRenderer` | 光墙不再"沿 x 或沿 z 的一面平板"，改成按法线算两个端点 ⇒ **斜着也正对朝向** |
| 粒子 | 与 `tick()` 用同一套公式（前缘 + 法线 × 偏移）⇒ 斜着放时粒子也跟着斜 |

**证据**：

| 项 | 值 |
|---|---|
| 探针（新增第 ⑩ 场） | **ALL OK**。斜角场：yaw=-69°（水平朝向 21°）、正前方 6 格沿斜线摆 3 根原木 ⇒ **全拆**；正东那一列的 2 个对照点 ⇒ **一根没被碰** |
| 旧九场 | 一字未改、全部继续通过 ⇒ **正方向的行为没变**（这是"改成任意角度"最该守住的回归） |
| 常驻校验 | **96 项 0 失败**（新增 B2 改写 / B24 / B24b / B25 / B26 / C14 / C15 / G7） |
| 反证 | `_zf134_falsify_angle.py` **3/3 咬住**：把法线抹掉（退回轴向）/ 去掉归一化 / 去掉垂直兜底，各当场红 |
| 期间修掉的探针账 | (g2) 把斧子扣爆成了空气 ⇒ 后面场景没得用（改成**新建一把**）；冷却按 **Item** 记且假玩家不在 tick 循环里 ⇒ 不会自己走（重建之后再清一次）|

"""


def main():
    s = io.open(DOC, encoding="utf-8").read()
    R4 = "### 4.118 【陷阱】假玩家探针"
    n4 = s.count(R4)
    print("§4 锚点 %d 次" % n4)
    assert n4 == 1, "§4 锚点不唯一"

    # §9：找 ZF133 段里的 "#### 四·补" 那一节结尾（下一个 "#### " 或下一个 "### " 之前）
    i9 = s.find("#### 四·补（2026-09-26 21:37")
    print("§9 的「四·补」锚点 %s" % ("找到" if i9 > 0 else "**没找到**"))
    if i9 > 0:
        nxt = s.find("\n#### ", i9 + 10)
        if nxt < 0:
            nxt = s.find("\n### ", i9 + 10)
        print("  该节结束于偏移 %d" % nxt)
    else:
        nxt = -1

    if not WRITE:
        print("（只看；要落笔加 --write）")
        return

    # §4.125/4.126
    i = s.index(R4)
    s = s[:i] + PIT.strip("\n") + "\n\n" + s[i:]

    # §9 补二
    if nxt > 0:
        s = s[:nxt] + "\n" + SECTION + s[nxt:]

    io.open(DOC, "w", encoding="utf-8", newline="\n").write(s)
    print("已落笔")
    body = io.open(DOC, encoding="utf-8").read()
    for k in ("4.125", "4.126", "四·补二", "任意水平角度", "21°"):
        print("  复核 %-14s 出现 %d 次" % (k, body.count(k)))


main()
