# ============================================================
#  _patch_archive_10.ps1 —— 0.10 档案补丁（音效那次）
#
#  用法（ExecutionPolicy 是 Restricted，用 scriptblock 绕开）：
#     $sb = [scriptblock]::Create([IO.File]::ReadAllText('E:\PotatoST\build\zftools\_patch_archive_10.ps1', [Text.Encoding]::UTF8))
#     & $sb
#
#  纪律（写进 §4.6 / §4.7）：
#    - 每处替换都先验锚点**恰好出现 1 次**，不是 1 次就整份放弃、一个字节都不写
#    - 写回用 UTF8 **无 BOM**，且原样保留 CRLF
#    - 刻意不调用 exit（scriptblock 在宿主进程内跑时 exit 会掐断宿主）
# ============================================================
$path = 'E:\PotatoST\docs\开发档案.md'
$raw = [IO.File]::ReadAllText($path, [Text.Encoding]::UTF8)
$before = $raw.Length

$pairs = @(
    @{
        old = '| ZF11 | （未单独备份） | 0.10 冻结线内：**微型粉碎机**（1 输入 + 3 输出 / 2500 FE / 红石信号=关机 / 三色状态灯）+ **硅**物品。首轮产出 BUG（`insertItem` 静默失败吞产物，见 §4.14）→ 同日修复重发 | 见 §6.2 |'
        new = '| ZF11 | （未单独备份） | 0.10 冻结线内：**微型粉碎机**（1 输入 + 3 输出 / 2500 FE / 红石信号=关机 / 三色状态灯）+ **硅**物品 + **灌装机完成音效**。首轮产出 BUG（`insertItem` 静默失败吞产物，见 §4.14）→ 同日修复重发 | 见 §6.2 / §6.5 |'
    },
    @{
        old = '输出形如：`语言数 = 4   基准键数 = 103   失败项 = 0`。'
        new = '输出形如：`语言数 = 4   基准键数 = 112   失败项 = 0`（0.10 时是 112 键）。'
    }
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
    Write-Output ("  [OK]   2 处替换完成：{0} 字节 -> {1} 字节" -f $before, $raw.Length)
}
