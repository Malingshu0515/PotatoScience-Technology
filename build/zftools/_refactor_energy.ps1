# 0.09 重构：把 灌装机 / 晒盐机 / 电解器 三份逐字相同的匿名 IEnergyStorage 换成 MachineEnergyStorage
# 用法：$sb = [scriptblock]::Create([IO.File]::ReadAllText($路径, [Text.Encoding]::UTF8)); & $sb
$ErrorActionPreference = 'Stop'
$root = 'E:\PotatoST\src\main\java\com\potatost\mod'

$targets = @('FillingMachineBlockEntity', 'SaltDryerBlockEntity', 'ElectrolyzerBlockEntity')
$nl = "`r`n"   # 这三个文件都是 CRLF
$fail = 0
$totalRemoved = 0

foreach ($name in $targets) {
    $p = Join-Path $root "$name.java"
    $t = [IO.File]::ReadAllText($p, [Text.Encoding]::UTF8)
    $before = ($t -split "`r?`n").Count

    $rx = [regex]'(?s)private final IEnergyStorage energyStorage = new IEnergyStorage\(\) \{.*?\r?\n    \};'
    $ms = $rx.Matches($t)
    if ($ms.Count -ne 1) { Write-Output ("  [FAIL] {0}: 匹配到 {1} 处（须为 1）" -f $name, $ms.Count); $fail++; continue }

    $body = $ms[0].Value
    # 语义护栏：确认待替换的确实是"只收不放"的形状
    $guard = ($body -match 'canReceive\(\)\s*\{\s*return true;') -and `
             ($body -match 'canExtract\(\)\s*\{\s*return false;') -and `
             ($body -match 'extractEnergy\([^)]*\)\s*\{\s*return 0;')
    if (-not $guard) { Write-Output ("  [FAIL] {0}: 形状不符（不是纯只收不放），已跳过" -f $name); $fail++; continue }

    $oldLines = ($body -split "`r?`n").Count
    $new = @(
        '    /**',
        '     * 只收不放的能量缓冲。0.09 起三台机器共用 {@link MachineEnergyStorage}，',
        '     * 不再各自维护一份逐字相同的匿名实现（原先 8 个方块实体共约 500 行重复）。',
        '     */',
        '    private final IEnergyStorage energyStorage = MachineEnergyStorage.receiveOnly(',
        '            () -> MAX_ENERGY,',
        '            () -> this.energy,',
        '            value -> {',
        '                this.energy = value;',
        '                this.setChanged();',
        '            });'
    ) -join $nl

    $t2 = $t.Remove($ms[0].Index, $ms[0].Length).Insert($ms[0].Index, $new)
    [IO.File]::WriteAllText($p, $t2, (New-Object System.Text.UTF8Encoding($false)))

    $after = ($t2 -split "`r?`n").Count
    $totalRemoved += ($before - $after)
    Write-Output ("  [OK]   {0,-30} {1} 行 -> {2} 行  (省 {3} 行；原匿名体 {4} 行)" -f $name, $before, $after, ($before - $after), $oldLines)
}

Write-Output ("`n失败项 = " + $fail + "   合计减少 = " + $totalRemoved + " 行")
if ($fail -gt 0) { Write-Output "有失败项"; return }

Write-Output "`n== 替换后三个文件的新能量段 =="
foreach ($name in $targets) {
    $p = Join-Path $root "$name.java"
    $lines = [IO.File]::ReadAllLines($p, [Text.Encoding]::UTF8)
    $i = -1
    for ($k = 0; $k -lt $lines.Count; $k++) { if ($lines[$k] -match 'MachineEnergyStorage\.receiveOnly') { $i = $k; break } }
    Write-Output ("=== " + $name)
    if ($i -ge 0) { for ($j = [Math]::Max(0, $i - 4); $j -lt [Math]::Min($i + 10, $lines.Count); $j++) { Write-Output ("    " + $lines[$j]) } }
    else { Write-Output "    (未找到新块!)" }
}
