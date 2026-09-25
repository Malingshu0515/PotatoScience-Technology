# ============================================================
#  _patch_archive_13.ps1 —— 0.10 ZF13 档案补丁
#   ① §3 记录「PCL 实例不再同步 jar」  ② §6.6.1 出口方向完成 + 长期规则
#   ③ §11.1 表格 A~J  ④ §11.2 加第 7 条  ⑤ §5 加 ZF13 行
#
#  用法：
#     $sb = [scriptblock]::Create([IO.File]::ReadAllText('E:\PotatoST\build\zftools\_patch_archive_13.ps1', [Text.Encoding]::UTF8))
#     & $sb
#
#  纪律同前：锚点必须恰好 1 次，否则整份放弃、一个字节都不写；写回 UTF8 无 BOM；不调用 exit。
# ============================================================
$path = 'E:\PotatoST\docs\开发档案.md'
$raw = [IO.File]::ReadAllText($path, [Text.Encoding]::UTF8)
$before = $raw.Length

# ---- ① §3 发布六步的第 6 步 ----
$p1old = '6. 拷进启动器实例，**并删掉实例里的旧版本 jar**（同 modId 两份会让游戏起不来）'
$p1new = @'
6. ~~拷进启动器实例~~ → **用户指令（2026-09-18）：PCL 实例暂不需要同步 jar**，出好 `release\` 包即算完成。
   哪天要恢复同步：**先 sha256 比对实例内旧 jar 与 `release\` 的同名副本**，确认等价再删；
   且实例 mods 里同名 mod 的 jar **有且只有 1 个**
'@

# ---- ② §6.6 末尾追加 §6.6.1 ----
$p2old = @'
---

## 7. 权威情报来源（怎么查原版行为，别靠记忆）
'@
$p2new = @'
### 6.6.1 出口方向已完成（0.10 ZF13）+ 一条长期规则

**规则（用户指令，长期有效）：以后的矿物、合金、矿物锭 ——默认就要挂 `c:` 标签兼容别的 mod；
其他物品等用户点名再做。** 由 `Audit.ps1` 的 **J 项**机械强制，别指望记性。

**生成器**：`python build\zftools\GenCommonTags.py`（改完脚本顶部的 `METALS` / `ALLOYS` / `SINGLES` 重跑）。
一次产出 36 个文件，覆盖：

| 方向 | 文件 | 说明 |
|---|---|---|
| 锭 | `c:ingots/<金属>` **和**扁平的 `c:<金属>_ingots` | 两种写法生态里都在用，所以两种都发 |
| 合金 | `c:ingots/steel` | 高碳钢按钢算 |
| 粗矿 | `c:raw_materials/<金属>` | |
| 矿石 | `c:ores/<金属>` 的 **item + block 两份** | 不同 mod 的机器查的注册表不一样，缺一份就等于没挂 |
| 矿石所在岩石 | `c:ores_in_ground/stone` · `deepslate`（block） | 别的 mod 的机器靠它判掉落 |
| 硅 | `c:silicon` | 有确切实证（Refined Storage） |

⚠ **还必须额外挂大类父标签**：NeoForge 的 `c:ingots` / `c:ores` / `c:raw_materials` **只列了原版子标签**
（`c:ingots` 里只有 copper/gold/iron/netherite）。不把自己塞进这一层，"查任意锭"的机器照样看不到我们的铝。
生成器已代劳（对应 `item/ingots.json` 等三个文件）。

**没做的**：`c:ore_rates/*`（矿石稀有度）——语义没吃透，宁可先不写，免得给别的 mod 的机器喂错信息。

---

## 7. 权威情报来源（怎么查原版行为，别靠记忆）
'@

# ---- ③ §11.1 表格 ----
$p3old = '| `Audit.ps1` | 代码标准总检（下面 A~I 九项） | 失败项 = 0 |'
$p3new = '| `Audit.ps1` | 代码标准总检（下面 A~J 十项） | 失败项 = 0 |'

# ---- ④ §11.2 硬性规则 ----
$p4old = '6. **"能不能放下"的预检与"实际写入"必须共用同一套公式**（§4.14 规则 2）——别一份用 `insertItem` 返回值、一份自己算'
$p4new = $p4old + @'

7. **新增矿物 / 合金 / 矿物锭，必须同时挂上 `c:` 通用标签**（J 项）——
   跑 `python build\zftools\GenCommonTags.py`，跑完再交付。见 §6.6.1
'@

# ---- ⑤ §5 流水线表加 ZF13 ----
$p5old = '| ZF12 | `zf12_pre` + `zf12_project` | 0.10：**粉碎机配方表支持 `c:` 标签**（别的 mod 的绿宝石/钻石矿石、紫水晶、石英自动认）；扫 475 个 jar 实证标签命名 | 见 §6.6 |'
$p5new = $p5old + @'

| ZF13 | `zf13_pre` | 0.10：**出口方向——36 个 `c:` 通用标签**（锭/合金/粗矿/矿石/硅）+ `GenCommonTags.py` 生成器 + Audit **J 项**。用户指令：**PCL 实例不再同步 jar** | 见 §6.6.1 |
'@

$pairs = @(
    @{ old = $p1old; new = $p1new },
    @{ old = $p2old; new = $p2new },
    @{ old = $p3old; new = $p3new },
    @{ old = $p4old; new = $p4new },
    @{ old = $p5old; new = $p5new }
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
    Write-Output ("  [OK]   5 处替换完成：{0} 字符 -> {1} 字符" -f $before, $raw.Length)
}
