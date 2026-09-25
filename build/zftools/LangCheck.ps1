# ============================================================
#  LangCheck.ps1 —— PotatoS&T 多语言文件一致性校验器
#
#  用法（本机执行策略 Restricted，用 scriptblock 绕开）：
#     $sb = [scriptblock]::Create([IO.File]::ReadAllText($路径, [Text.Encoding]::UTF8))
#     & $sb                 # 默认校验 assets\potato_s_t\lang 下全部 .json
#     & $sb -Dir <目录>
#
#  校验 5 项（多语言最容易翻车的地方）：
#    1. JSON 能否解析（且必须是 UTF-8，不能带 BOM）
#    2. 各语言**键集合必须完全一致**（缺键 = 游戏里直接显示原始 key）
#    3. 各语言的**格式占位符签名必须一致**（%s 个数与 %% 位置；漏了会崩或显示错）
#    4. 相邻语言之间**是否有值完全相同的条目**（多为漏翻，也可能是专有名词，故只 WARN）
#    5. 换行风格与 BOM 报告
#
#  刻意不调用 exit：用 scriptblock 在宿主进程内跑时，exit 会把宿主一起掐断。
# ============================================================
param(
    [string]$Dir = 'E:\PotatoST\src\main\resources\assets\potato_s_t\lang'
)

$ErrorActionPreference = 'Continue'
$files = @(Get-ChildItem $Dir -Filter '*.json' | Sort-Object Name)
if ($files.Count -eq 0) { Write-Output "目录里没有 .json: $Dir"; return }

$fail = 0
$warn = 0
$data = @{}      # 语言 -> 有序字典(key -> value)
$order = @{}     # 语言 -> 键顺序

Write-Output "== 载入 =="
foreach ($f in $files) {
    $lang = [IO.Path]::GetFileNameWithoutExtension($f.Name)
    $bytes = [IO.File]::ReadAllBytes($f.FullName)
    $bom = ($bytes.Length -ge 3 -and $bytes[0] -eq 0xEF -and $bytes[1] -eq 0xBB -and $bytes[2] -eq 0xBF)
    $txt = [Text.Encoding]::UTF8.GetString($bytes)
    $crlf = ([regex]::Matches($txt, "`r`n")).Count
    $lf   = ([regex]::Matches($txt, "(?<!`r)`n")).Count
    $obj = $null
    try { $obj = $txt | ConvertFrom-Json }
    catch { Write-Output ("  [FAIL] {0,-10} JSON 解析失败: {1}" -f $lang, $_.Exception.Message); $fail++; continue }
    $h = [ordered]@{}
    foreach ($p in $obj.PSObject.Properties) { $h[$p.Name] = $p.Value }
    $data[$lang] = $h
    $order[$lang] = @($h.Keys)
    $bomTag = if ($bom) { 'BOM!' } else { 'no-BOM' }
    $styleTag = if ($lf -eq 0) { 'CRLF' } elseif ($crlf -eq 0) { 'LF' } else { 'MIXED' }
    Write-Output ("  {0,-10} {1,4} 键   {2,-8} {3}" -f $lang, $h.Count, $styleTag, $bomTag)
    if ($bom) { $fail++ }
}

$langs = @($data.Keys | Sort-Object)
if ($langs.Count -lt 2) { Write-Output "只有一种语言，无需比对"; return }

Write-Output "`n== ① 键集合一致性（基准: $($langs[0])） =="
$base = $langs[0]
$baseKeys = $order[$base]
foreach ($l in $langs) {
    if ($l -eq $base) { continue }
    $lk = $order[$l]
    $miss = @($baseKeys | Where-Object { $lk -notcontains $_ })
    $extra = @($lk | Where-Object { $baseKeys -notcontains $_ })
    if ($miss.Count -eq 0 -and $extra.Count -eq 0) {
        Write-Output ("  [OK]   {0,-10} 与基准完全一致（{1} 键）" -f $l, $lk.Count)
    } else {
        $fail++
        Write-Output ("  [FAIL] {0,-10} 缺失 {1} 键, 多出 {2} 键" -f $l, $miss.Count, $extra.Count)
        $miss  | Select-Object -First 20 | ForEach-Object { Write-Output ("           - 缺失: " + $_) }
        $extra | Select-Object -First 20 | ForEach-Object { Write-Output ("           + 多出: " + $_) }
    }
}

Write-Output "`n== ② 格式占位符签名一致性 =="
function Get-Sig([string]$s) {
    # 把所有 % 及其后一个字符抽出来当签名（%s / %% / %d 都覆盖），忽略裸 % 后跟空格的排版用法
    $m = [regex]::Matches($s, '%(?<c>.)')
    $out = @()
    foreach ($x in $m) { $c = $x.Groups['c'].Value; if ($c -match '[sdif%]') { $out += ('%' + $c) } }
    return ($out -join '|')
}
$bad = 0
foreach ($k in $baseKeys) {
    $sigs = @{}
    foreach ($l in $langs) {
        $v = $data[$l][$k]
        if ($null -eq $v) { continue }
        $sigs[$l] = Get-Sig ([string]$v)
    }
    $uniq = @($sigs.Values | Sort-Object -Unique)
    if ($uniq.Count -gt 1) {
        $bad++; $fail++
        Write-Output ("  [FAIL] $k")
        foreach ($l in $langs) { Write-Output ("           {0,-10} 签名= '{1}'" -f $l, $sigs[$l]) }
    }
}
if ($bad -eq 0) { Write-Output "  [OK]   所有 $($baseKeys.Count) 个键的占位符签名完全一致" }

Write-Output "`n== ③ 未翻译嫌疑（与基准语言值完全相同，专有名词属正常） =="
$same = 0
foreach ($k in $baseKeys) {
    foreach ($l in $langs) {
        if ($l -eq $base) { continue }
        $bv = [string]$data[$base][$k]; $lv = [string]$data[$l][$k]
        if ($null -ne $lv -and $bv -eq $lv -and $bv -notmatch '^\s*$') {
            $same++
            if ($same -le 12) { Write-Output ("  [WARN] $k  ->  $l = '$lv'") }
        }
    }
}
if ($same -eq 0) { Write-Output "  [OK]   没有完全相同值的条目" } else { Write-Output ("  合计 $same 条（多为专有名词/代号，人工确认即可）"); $warn += $same }

Write-Output "`n------------------------------"
Write-Output ("语言数 = {0}   基准键数 = {1}   失败项 = {2}   未翻译嫌疑 = {3}" -f $langs.Count, $baseKeys.Count, $fail, $same)
if ($fail -gt 0) { Write-Output "结论: 有失败项" } else { Write-Output "结论: 全部通过" }
