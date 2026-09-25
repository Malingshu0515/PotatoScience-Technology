# ============================================================
#  _patch_archive_10c.ps1 —— 0.10 档案补丁（同步载体字段漏进 saveAdditional）
#
#  用法：
#     $sb = [scriptblock]::Create([IO.File]::ReadAllText('E:\PotatoST\build\zftools\_patch_archive_10c.ps1', [Text.Encoding]::UTF8))
#     & $sb
#
#  纪律同前两个补丁：锚点必须恰好 1 次，否则整份放弃、一个字节都不写；
#  写回 UTF8 无 BOM（保留 CRLF）；刻意不调用 exit。
# ============================================================
$path = 'E:\PotatoST\docs\开发档案.md'
$raw = [IO.File]::ReadAllText($path, [Text.Encoding]::UTF8)
$before = $raw.Length

$pair1old = '   发包只在**状态翻转时**做，别每 tick 发。'
$pair1new = @'
   发包只在**状态翻转时**做，别每 tick 发。
   ⚠ **状态字段必须写进 `saveAdditional()`**——`getUpdateTag()` 返回的就是 `saveWithoutMetadata()`。
   只把状态放在 `ContainerData` 里（或忘了写进 save），客户端永远收不到，声音一次都不会响（见 §4.15）。
'@

$pair2old = '## 5. 版本与 [ZF] 流水线记录'
$pair2new = @'
### 4.15 【致命】"同步载体"字段漏进 `saveAdditional()`，客户端永远收不到

**现象（0.10 自查时抓到，没出包）**：微型粉碎机的循环音设计成"运行状态翻转就 `sync()`"，
但 `status` 当初被定义成"仅供 GUI、**不存盘**"，`saveAdditional()` 里根本没写它——
而 `getUpdateTag()` 返回的正是 `saveWithoutMetadata()`。**包里没有 status ⇒ 客户端 `isRunning()` 恒为 false
⇒ 声音一次都不会响**。编译查不出、Audit 查不出、进游戏"看"也看不出，**只有"听"才发现**，是典型的静默失效。

**规则：**
1. 凡是"要同步给客户端的字段"，**必须走 `saveAdditional()` / `loadAdditional()`**（或单独塞进 update tag）。
   别以为放进 `ContainerData` 就够了——`ContainerData` **只在界面打开时**才同步。
2. 加完同步要**自己把链路走一遍**：状态在哪儿翻转 → 谁调 `sync()` → `getUpdateTag()` 里到底有没有这个字段
   → 客户端哪个方法读它。0.10 就是靠这条自查在打包前抓住的。

---

## 5. 版本与 [ZF] 流水线记录
'@

$pairs = @(
    @{ old = $pair1old; new = $pair1new },
    @{ old = $pair2old; new = $pair2new }
)

$bad = 0
foreach ($p in $pairs) {
    $count = ([regex]::Matches($raw, [regex]::Escape($p.old))).Count
    if ($count -ne 1) {
        Write-Output ("  [FAIL] 锚点出现 {0} 次（应为 1 次）：{1}..." -f $count, $p.old.Substring(0, [Math]::Min(50, $p.old.Length)))
        $bad++
    }
}

if ($bad -gt 0) {
    Write-Output '锚点校验未通过，档案未改动。'
} else {
    foreach ($p in $pairs) { $raw = $raw.Replace($p.old, $p.new) }
    [IO.File]::WriteAllText($path, $raw, (New-Object Text.UTF8Encoding($false)))
    Write-Output ("  [OK]   2 处替换完成：{0} 字符 -> {1} 字符" -f $before, $raw.Length)
}
