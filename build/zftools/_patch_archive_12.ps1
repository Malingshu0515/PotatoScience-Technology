# ============================================================
#  _patch_archive_12.ps1 —— 0.10 ZF12 档案补丁（跨 mod 标签兼容）
#
#  用法：
#     $sb = [scriptblock]::Create([IO.File]::ReadAllText('E:\PotatoST\build\zftools\_patch_archive_12.ps1', [Text.Encoding]::UTF8))
#     & $sb
#
#  纪律同前几个补丁：每处锚点必须恰好 1 次，否则整份放弃、一个字节都不写；
#  写回 UTF8 无 BOM（保留 CRLF）；刻意不调用 exit。
# ============================================================
$path = 'E:\PotatoST\docs\开发档案.md'
$raw = [IO.File]::ReadAllText($path, [Text.Encoding]::UTF8)
$before = $raw.Length

# ---- A. §5 流水线表加 ZF12 行 ----
$aOld = '| ZF11 | （未单独备份） | 0.10 冻结线内：**微型粉碎机**（1 输入 + 3 输出 / 2500 FE / 红石信号=关机 / 三色状态灯）+ **硅**物品 + **灌装机完成音效** + **微型粉碎机循环音**。首轮产出 BUG（`insertItem` 静默失败吞产物，见 §4.14）→ 同日修复重发 | 见 §6.2 / §6.5 |'
$aNew = $aOld + @'

| ZF12 | `zf12_pre` + `zf12_project` | 0.10：**粉碎机配方表支持 `c:` 标签**（别的 mod 的绿宝石/钻石矿石、紫水晶、石英自动认）；扫 475 个 jar 实证标签命名 | 见 §6.6 |
'@

# ---- B. 新增 §6.6 ----
$bOld = '## 7. 权威情报来源（怎么查原版行为，别靠记忆）'
$bNew = @'
### 6.6 跟**别的 mod 兼容**：靠标签，不靠改代码（0.10 ZF12 实例）

**核心事实：名字相同 ≠ 同一个物品。** `potato_s_t:silicon` 和别的 mod 的 `xxx:silicon` 是两个独立注册项，
永远不会自动合并。让它们互通的唯一可扩展机制，是**把双方都挂进同一个标签**。

**⚠ NeoForge 的 `c:` 标签是"桥接"，不是独立清单**（0.10 解包核实）：
```
c:ores/emerald = #minecraft:emerald_ores + #forge:ores/emerald(可选)
c:gems/quartz  = minecraft:quartz        + #forge:gems/quartz(可选)
```
所以别的 mod 无论按新约定挂 `c:`、还是沿用 `#minecraft:*_ores`、还是老式的 `forge:`，我们都能认。
**NeoForge 只预置原版材料的标签**（532 个 c: 标签里 item 占 277，金属只有 copper/gold/iron/netherite）——
铝银镍钴铀钢硅这些名字**全靠社区约定**，自己建就对了，不必等谁提供。

**标签文件放哪**：`data/c/tags/item/<路径>.json`——**命名空间是 `c`，不是 `potato_s_t`**（放错等于没写）。
```json
{ "values": ["potato_s_t:aluminum_ingot"] }
```
标签文件跨 mod **合并**（`replace` 默认 false），NeoForge 的、别人的、我们的会叠在一起。

**实证过的名字**（0.10 扫了 4 个整合包共 475 个 jar 抽出来的，不是背的）：

| 我们的物品 | 标签 | 谁在用 |
|---|---|---|
| 高碳钢 | `c:ingots/steel` | IE / TConstruct / ad_astra / createnuclear / createbigcannons / mapperbase（6 个都用） |
| 铀锭 | `c:ingots/uranium` | IE / ExtremeReactors2 / DCTweaks |
| 铝 · 银 · 镍锭 | `c:ingots/aluminum` · `silver` · `nickel` | IE |
| 钴锭 | `c:ingots/cobalt` | TConstruct |
| 硅 | `c:silicon` | Refined Storage |
| 6 种原矿 | `c:raw_materials/<金属>` | IE / TConstruct |

⚠ **扁平式**写法同时存在（`c:steel_ingots`，ad_astra / createbigcannons 是两种都发）。要最大化兼容就两种都挂。

**三个方向**：① **出口** = 我们挂 `c:` 标签（纯数据文件，零代码风险）；
② **入口** = 我们的合成配方把 `"item"` 改成 `"tag"` 当原料；③ **机器配方** = 见 §6.2 的 `TagRule`。

**怎么查某个 mod 到底挂什么标签（别猜，去解包）**：看它 jar 里的 `data/*/tags/item*/`——
**1.20.1 及以前是复数 `tags/items/`，1.20.5 起才是单数 `tags/item/`**。0.10 先按单数扫 98 个 1.20.1 mod
全部落空，换成复数才扫出 152 个标签。**版本不同路径不同，别再踩。**

**整合包作者一行就能给我们加兼容**（比我们发十个文件还快）：
```js
// KubeJS
ServerEvents.tags('item', e => e.add('c:ingots/aluminum', 'potato_s_t:aluminum_ingot'))
```

---

## 7. 权威情报来源（怎么查原版行为，别靠记忆）
'@

# ---- C. §9 已知限制 ----
$cOld = '      [ ] 硅的图标应是**原版火药**（占位），方块是灰底带齿的占位贴图'
$cNew = $cOld + @'

- [ ] **粉碎机的标签兼容未在游戏内验证**（0.10 ZF12）：本机实例里**没有任何科技 mod**，所以只能验"原版物品照旧"：
      [ ] 绿宝石矿石 / 深层绿宝石矿石 / 钻石矿石 / 深层钻石矿石 / 下界石英 / 紫水晶碎片 → 仍能正常粉碎（精确条目与标签两条路都通）
      [ ] 真正验证跨 mod 得往实例塞一个科技 mod（Thermal / IE / Mekanism），再拿它的矿石试
- [ ] 粉碎机**不认别的 mod 的原木**：产物必须跟着输入变（橡木出橡木木板），标签只能给固定产物，
      所以原木只能逐种精确匹配。石英建材同理（没有"石英建材"这种通用标签）
'@

# ---- D. §7 加一行查标签的方法 ----
$dOld = '；**别去 `%USERPROFILE%\.gradle`** |'
$dNew = '；**别去 `%USERPROFILE%\.gradle`** |
| 某个 mod 到底挂了哪些标签 | 解它的 jar 看 `data/<ns>/tags/item*/`。**1.20.1 及以前是复数 `tags/items/`，1.20.5 起才是单数 `tags/item/`**——0.10 先按单数扫 98 个 1.20.1 mod 全落空，换复数才扫出 152 个标签 |'

$pairs = @(
    @{ old = $aOld; new = $aNew },
    @{ old = $bOld; new = $bNew },
    @{ old = $cOld; new = $cNew },
    @{ old = $dOld; new = $dNew }
)

$bad = 0
foreach ($p in $pairs) {
    $count = ([regex]::Matches($raw, [regex]::Escape($p.old))).Count
    if ($count -ne 1) {
        Write-Output ("  [FAIL] 锚点出现 {0} 次（应为 1 次）：{1}..." -f $count, $p.old.Substring(0, [Math]::Min(46, $p.old.Length)))
        $bad++
    }
}

if ($bad -gt 0) {
    Write-Output '锚点校验未通过，档案未改动。'
} else {
    foreach ($p in $pairs) { $raw = $raw.Replace($p.old, $p.new) }
    [IO.File]::WriteAllText($path, $raw, (New-Object Text.UTF8Encoding($false)))
    Write-Output ("  [OK]   4 处替换完成：{0} 字符 -> {1} 字符" -f $before, $raw.Length)
}
