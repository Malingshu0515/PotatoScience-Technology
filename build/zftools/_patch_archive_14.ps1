# ============================================================
#  _patch_archive_14.ps1 —— 0.10 ZF14 档案补丁（B 批：配方原料改用标签）
#   ① §4.16 新雷区：PowerShell -replace 后不能跟表达式拼接
#   ② §6.6.1 规则收紧（默认范围 = 粗矿/矿石/锭）+ 硅标为例外
#   ③ §6.6.1 后追加 §6.6.2（入口方向）
#   ④ §11.1 表格 RecipeCheck 一行  ⑤ §5 加 ZF14 行  ⑥ §9 加验收项
#
#  用法：$sb = [scriptblock]::Create([IO.File]::ReadAllText('<本文件>', [Text.Encoding]::UTF8)); & $sb
#  纪律同前：锚点必须恰好 1 次，否则整份放弃；写回 UTF8 无 BOM；不调用 exit。
# ============================================================
$path = 'E:\PotatoST\docs\开发档案.md'
$raw = [IO.File]::ReadAllText($path, [Text.Encoding]::UTF8)
$before = $raw.Length

# ---- ① §4.16 ----
$p1old = '## 5. 版本与 [ZF] 流水线记录'
$p1new = @'
### 4.16 PowerShell 的 `-replace` 后面**不能直接跟表达式拼接**

**现象**（0.10 ZF14）：`RecipeCheck.ps1` 里这么写
```powershell
$key = ($tag -replace '^([^:]+):', "`$1/$reg" + ':')
```
运行时抛 `The -ireplace operator allows only two elements to follow it, not 3`，
`$key` 变成空串 ⇒ **7 个标签全被判成「解析不到」**。当时第一反应是"标签名写错了"，
其实**是解析代码自己坏了**——差点去改根本没问题的数据。

**原因**：PowerShell 把 `-replace A, B + C` 解析成**三个参数**（逗号分隔的参数列表），
而不是 `-replace A, (B + C)`。这里不按"先算加法"的直觉走。

**规则**：`-replace` 的替换串只要是拼出来的，**一律加括号**：
```powershell
$key = ($tag -replace '^([^:]+):', ("`$1/" + $reg + ':'))
```
`-join` / `-split` / `-f` 后面跟拼接表达式时同样建议加括号。

> 同一批还踩了个索引错：jar 里 `data/<ns>/tags/<注册表>/<路径>.json` 的 `[1]` 恒为 `"tags"`，
> **注册表名在 `[2]`**。两个 bug 叠在一起时症状一样（全是"查不到"），所以**先量再改**，别猜。

---

## 5. 版本与 [ZF] 流水线记录
'@

# ---- ② §6.6.1 规则收紧 ----
$p2old = '**规则（用户指令，长期有效）：以后的矿物、合金、矿物锭 ——默认就要挂 `c:` 标签兼容别的 mod；
其他物品等用户点名再做。** 由 `Audit.ps1` 的 **J 项**机械强制，别指望记性。'
$p2new = @'
**规则（用户指令，长期有效，两个方向都管）：默认只对「粗矿 / 矿石 / 锭」做跨 mod 兼容；
宝石、红石、硅等一切其他物品都要用户点名才做。** 由 `Audit.ps1` 的 **J 项**机械强制，别指望记性。

- 「矿物」的范围就三条：**粗矿（`raw_*`）· 矿石（`*_ore`）· 锭（`*_ingot`，合金按锭算）**。
- 已经存在的例外（用户单独批过或已当场披露，不算默认范围）：C 批的 `c:gems/amethyst` / `c:gems/quartz`
  两条粉碎规则（做 C 时用户看过清单并拍板），以及 `c:silicon`（已披露，用户否决就删 `item/silicon.json`）。
'@

# ---- ③ §6.6.1 末尾追加 §6.6.2 ----
$p3old = @'
**没做的**：`c:ore_rates/*`（矿石稀有度）——语义没吃透，宁可先不写，免得给别的 mod 的机器喂错信息。
'@
$p3new = @'
**没做的**：`c:ore_rates/*`（矿石稀有度）——语义没吃透，宁可先不写，免得给别的 mod 的机器喂错信息。

### 6.6.2 入口方向：配方原料改用标签（0.10 ZF14）

`data/potato_s_t/recipe/` 里改了 6 个配方、共 9 处原料（**全部落在「粗矿/矿石/锭」范围内**）：

| 配方 | 原来 | 现在 |
|---|---|---|
| 铝锭 熔炼 / 高炉 ×2 | `potato_s_t:raw_aluminum` | `#c:raw_materials/aluminum` |
| 银锭 熔炼 / 高炉 ×2 | `potato_s_t:raw_silver` | `#c:raw_materials/silver` |
| 动力能源捕获器 | `raw_cobalt` · `raw_nickel` · `minecraft:raw_iron` | `#c:raw_materials/cobalt` · `nickel` · `iron` |
| 接线端子 | `minecraft:iron_ingot` · `potato_s_t:aluminum_ingot` | `#c:ingots/iron` · `#c:ingots/aluminum` |

**按范围铁律没动的**：紫水晶碎片、下界石英（宝石），红石与红石块、金块、铁块（方块）。

**⚠ 换标签之前必须先确认标签里真的有原版物品**，否则配方会静默变成做不出来。
`c:ingots/iron` / `c:raw_materials/iron` 都解包核对过，分别含 `minecraft:iron_ingot` / `minecraft:raw_iron` ✓。

**⚠ 已知副作用（跨 mod 兼容的固有代价，不是 bug）**：我们的「粗铝 → 铝锭」现在匹配整个
`c:raw_materials/aluminum`。别的 mod 若也有「它的粗铝 → 它的铝锭」，同一个输入就对应两条不同产物的配方，
原版只会取其中一条（JEI 两条都显示）。要吃标签兼容就绕不开。

**校验器同步升级**（`RecipeCheck.ps1`）：
1. 认 `"tag"` 形式的原料（以前只认 `"item"`，改完配方反而会报失败）；
2. **新增第 6 条不变量：标签引用必须能解析**——来源是本项目 `data/**/tags` + 原版 `client.jar`
   + NeoForge `universal.jar`（实测共 1039 个已知标签）。命名空间是 `c` / `minecraft` / `potato_s_t`
   却查不到 ⇒ `[FAIL]`；别人的命名空间 ⇒ `[WARN]` 人工确认。
3. 顺手修了个老毛病：`$ok` 原来读全局 `$fail`，第一次失败后后面的配方都不再计数。
'@

# ---- ④ §11.1 表格 ----
$p4old = '| `RecipeCheck.ps1` | 配方结构不变量（含空格空槽） | 失败项 = 0 |'
$p4new = '| `RecipeCheck.ps1` | 配方结构不变量（含空格空槽）+ **标签引用能否解析** | 失败项 = 0 |'

# ---- ⑤ §5 加 ZF14 ----
$p5old = '| ZF13 | `zf13_pre` | 0.10：**出口方向——36 个 `c:` 通用标签**（锭/合金/粗矿/矿石/硅）+ `GenCommonTags.py` 生成器 + Audit **J 项**。用户指令：**PCL 实例不再同步 jar** | 见 §6.6.1 |'
$p5new = $p5old + @'

| ZF14 | `zf14_pre` | 0.10：**入口方向——6 个配方共 9 处原料改用 `c:` 标签**；`RecipeCheck.ps1` 支持 tag 并新增「标签必须能解析」校验（含负向测试） | 见 §6.6.2 / §4.16 |
'@

# ---- ⑥ §9 验收项 ----
$p6old = '      所以原木只能逐种精确匹配。石英建材同理（没有"石英建材"这种通用标签）'
$p6new = $p6old + @'

- [ ] **配方改用标签后未在游戏内验证**（0.10 ZF14，**这条优先级最高**——改错了就是"东西做不出来"）：
      [ ] 粗铝 / 粗银 仍能烧成铝锭 / 银锭（熔炼与高炉各试一次）
      [ ] 动力能源捕获器：用我们自己的粗钴 / 粗镍 / 原版粗铁 都能摆出来
      [ ] 接线端子：原版铁锭 + 我们的铝锭 仍能摆出来
      [ ] 顺带确认标签没被别的数据包改空（`Loaded N recipes` 应仍为 1298）
'@

$pairs = @(
    @{ old = $p1old; new = $p1new },
    @{ old = $p2old; new = $p2new },
    @{ old = $p3old; new = $p3new },
    @{ old = $p4old; new = $p4new },
    @{ old = $p5old; new = $p5new },
    @{ old = $p6old; new = $p6new }
)

$bad = 0
foreach ($p in $pairs) {
    $count = ([regex]::Matches($raw, [regex]::Escape($p.old))).Count
    if ($count -ne 1) {
        Write-Output ("  [FAIL] 锚点出现 {0} 次（应为 1 次）：{1}..." -f $count, $p.old.Substring(0, [Math]::Min(44, $p.old.Length)))
        $bad++
    }
}

if ($bad -gt 0) {
    Write-Output '锚点校验未通过，档案未改动。'
} else {
    foreach ($p in $pairs) { $raw = $raw.Replace($p.old, $p.new) }
    [IO.File]::WriteAllText($path, $raw, (New-Object Text.UTF8Encoding($false)))
    Write-Output ("  [OK]   6 处替换完成：{0} 字符 -> {1} 字符" -f $before, $raw.Length)
}
