# ============================================================
#  RecipeCheck.ps1 —— PotatoS&T 合成配方结构校验器 (1.21.1)
#
#  用法（本机执行策略是 Restricted，不能直接双击/& 运行 .ps1）：
#     $sb = [scriptblock]::Create([IO.File]::ReadAllText($路径, [Text.Encoding]::UTF8))
#     & $sb -All
#  或：  powershell.exe -NoProfile -ExecutionPolicy Bypass -File RecipeCheck.ps1 -All
#
#  只校验 minecraft:crafting_shaped；其它类型（smelting/blasting/...）标 [SKIP] 跳过，不计失败。
#
#  校验的不变量（手工写配方最容易翻车的地方）：
#    1. type 必须是 minecraft:crafting_shaped
#    2. pattern 行数 1..3，各行列数一致且 1..3
#    3. pattern 中每个「非空格」字符都要在 key 里有定义（空格 = 空槽）
#    4. key 里不应有未被使用的字符
#    5. key 每个条目必须有 item 或 tag 之一（1.21 起两种都合法）；result.id、result.count 要有效
#    6. 【0.10 ZF14 新增】tag 引用必须真的能解析到 —— 打错一个字母，配方会**静默变成做不出来**，
#       编译不报错、加载不报错、只有玩家摆上去才发现。可解析来源有三处：
#         ① 我们自己的  src/main/resources/data/<ns>/tags/**（含 GenCommonTags.py 生成的 data/c/tags）
#         ② 原版        client.jar        的 data/minecraft/tags/**
#         ③ NeoForge    neoforge-*-universal.jar 的 data/c/tags/**
#       命名空间是 c / minecraft / potato_s_t 却查不到 ⇒ [FAIL]；别的命名空间（别人的 mod）⇒ [WARN] 人工确认。
#
#  注意：本脚本只做结构与标签校验。物品 id 是否真实存在需另行交叉核对
#        （模组物品 -> register("...")；原版物品 -> client.jar 的
#          data/minecraft/recipe/*.json 里 grep，被引用过即正确）
#
#  刻意不调用 exit：用 scriptblock 方式在宿主进程内运行时，exit 会掐断宿主。
# ============================================================
param(
    [Parameter(Position = 0, ValueFromRemainingArguments = $true)]
    [string[]]$Files,
    [switch]$All
)

$ErrorActionPreference = 'Continue'
$recipeDir = 'E:\PotatoST\src\main\resources\data\potato_s_t\recipe'
$resRoot   = 'E:\PotatoST\src\main\resources'
$vanillaJar  = 'E:\gradle-home\caches\minecraft\versions\1.21.1\client.jar'
$neoJarGlob  = 'E:\gradle-home\caches\modules-2\files-2.1\net.neoforged\neoforge\21.1.235'

if ($All) { $Files = @(Get-ChildItem $recipeDir -Filter '*.json' | ForEach-Object { $_.FullName }) }
if (-not $Files -or $Files.Count -eq 0) { Write-Output '用法: RecipeCheck.ps1 <配方.json...> | -All'; return }

# ---------- 已知标签集合（第一次遇到 tag 时才构建，避免白解 jar） ----------
$script:knownTags = $null
$script:tagNote = ''

function Get-KnownTags {
    if ($null -ne $script:knownTags) { return $script:knownTags }
    $set = New-Object System.Collections.Generic.HashSet[string]
    # ① 我们自己的 data/<ns>/tags/<registry>/**：路径 -> <ns>:<path>
    $tagDirs = Get-ChildItem (Join-Path $resRoot 'data') -Recurse -Directory -Filter 'tags' -ErrorAction SilentlyContinue
    foreach ($d in $tagDirs) {
        $ns = $d.Parent.Name
        foreach ($reg in (Get-ChildItem $d.FullName -Directory -ErrorAction SilentlyContinue)) {
            foreach ($f in (Get-ChildItem $reg.FullName -Recurse -Filter '*.json' -ErrorAction SilentlyContinue)) {
                $rel = $f.FullName.Substring($reg.FullName.Length + 1) -replace '\\', '/' -replace '\.json$', ''
                [void]$set.Add("$ns/$($reg.Name):$rel")
            }
        }
    }
    # ② ③ 两个 jar 里的 item 标签
    Add-Type -AssemblyName System.IO.Compression.FileSystem -ErrorAction SilentlyContinue
    $jars = @()
    if (Test-Path $vanillaJar) { $jars += $vanillaJar }
    $neo = Get-ChildItem $neoJarGlob -Recurse -Filter '*universal.jar' -ErrorAction SilentlyContinue | Select-Object -First 1
    if ($neo) { $jars += $neo.FullName }
    foreach ($j in $jars) {
        try { $z = [IO.Compression.ZipFile]::OpenRead($j) } catch { continue }
        foreach ($e in @($z.Entries | Where-Object { $_.FullName -match '^data/[^/]+/tags/[^/]+/.+\.json$' })) {
            # FullName = data/<ns>/tags/<registry>/<path>.json
            $parts = ($e.FullName -replace '^data/', '' -replace '\.json$', '') -split '/'
            $ns = $parts[0]
            $reg = $parts[2]      # ★ parts[1] 恒为 "tags"，注册表名在 [2]（这里写错过一次）
            $path = ($parts[3..($parts.Count - 1)]) -join '/'
            [void]$set.Add("$ns/$reg`:$path")
        }
        $z.Dispose()
    }
    $script:tagNote = ("已知标签 {0} 个（来源：本项目 {1} + jar {2} 个）" -f $set.Count, $tagDirs.Count, $jars.Count)
    $script:knownTags = $set
    return $set
}

function Test-TagKnown([string]$raw) {
    $tag = $raw.Trim().TrimStart('#')
    $known = Get-KnownTags
    foreach ($reg in @('item', 'block', 'fluid')) {
        # ⚠ 括号必须加：PowerShell 会把 `-replace A, B + C` 当成**三个参数**，
    #   而不是把 B+C 拼成一个替换串（0.10 ZF14 就是这里让 7 个标签全查不到）
    $key = ($tag -replace '^([^:]+):', ("`$1/$reg" + ':'))
        if ($known.Contains($key)) { return $true }
    }
    return $false
}

$fail = 0
$skip = 0
$ok   = 0
$ids  = New-Object System.Collections.Generic.List[string]
$tagRefs = New-Object System.Collections.Generic.List[string]

foreach ($f in $Files) {
    $name = Split-Path $f -Leaf
    Write-Output "=== $name"
    $failBefore = $fail

    $o = $null
    try { $o = Get-Content -LiteralPath $f -Raw | ConvertFrom-Json }
    catch { Write-Output "    [FAIL] JSON 解析失败: $($_.Exception.Message)"; $fail++; Write-Output ''; continue }

    # 非定形配方：跳过（合法，只是不在本校验器范围）
    if ($o.type -ne 'minecraft:crafting_shaped') {
        Write-Output "    [SKIP] type = $($o.type)（只校验 crafting_shaped）"
        if ($o.result.id) { $ids.Add($o.result.id) }
        if ($o.ingredient.item) { $ids.Add($o.ingredient.item) }
        if ($o.ingredient.tag) { $tagRefs.Add($o.ingredient.tag) }
        $skip++
        Write-Output ''
        continue
    }

    Write-Output "    category = $($o.category)   result = $($o.result.id) x$($o.result.count)"

    # 2 尺寸
    $rows = @($o.pattern)
    $rowLens = @($rows | ForEach-Object { "$_".Length })
    $uniq = @($rowLens | Select-Object -Unique)
    if ($rows.Count -lt 1 -or $rows.Count -gt 3) {
        Write-Output "    [FAIL] 行数 $($rows.Count) 不在 1..3"; $fail++
    } elseif ($uniq.Count -ne 1) {
        Write-Output "    [FAIL] 各行列数不一致: $($rowLens -join ',')"; $fail++
    } elseif ($uniq[0] -lt 1 -or $uniq[0] -gt 3) {
        Write-Output "    [FAIL] 列数 $($uniq[0]) 不在 1..3"; $fail++
    } else {
        Write-Output "    [OK]   尺寸 $($rows.Count)x$($uniq[0])"
        foreach ($r in $rows) { Write-Output ("           |" + $r + "|") }
    }

    # 3 / 4
    $keyed = @()
    if ($o.key) { $keyed = @($o.key.PSObject.Properties.Name) }
    $used = New-Object System.Collections.Generic.HashSet[string]
    foreach ($r in $rows) { foreach ($ch in "$r".ToCharArray()) { if ($ch -ne ' ') { [void]$used.Add([string]$ch) } } }
    $missing = @($used | Where-Object { $keyed -notcontains $_ })
    $unused  = @($keyed | Where-Object { -not $used.Contains($_) })
    if ($missing.Count -gt 0) { Write-Output "    [FAIL] 模式用了但 key 里没有: $($missing -join ',')"; $fail++ }
    else { Write-Output "    [OK]   模式字符全部在 key 中（空格=空槽，已忽略）" }
    if ($unused.Count -gt 0) { Write-Output "    [WARN] key 里未被使用的字符: $($unused -join ',')" }
    else { Write-Output "    [OK]   无冗余 key" }

    # 5 内容：item 与 tag 二选一
    foreach ($k in $keyed) {
        $it = $o.key.$k.item
        $tg = $o.key.$k.tag
        if (-not [string]::IsNullOrWhiteSpace($it)) {
            Write-Output "           '$k' -> $it"; $ids.Add($it)
        } elseif (-not [string]::IsNullOrWhiteSpace($tg)) {
            Write-Output "           '$k' -> #$tg（标签）"; $tagRefs.Add($tg)
        } else {
            Write-Output "    [FAIL] key '$k' 既没有 item 也没有 tag"; $fail++
        }
    }
    if ([string]::IsNullOrWhiteSpace($o.result.id)) { Write-Output '    [FAIL] result.id 为空'; $fail++ }
    else { $ids.Add($o.result.id) }
    if (-not $o.result.count -or $o.result.count -lt 1) { Write-Output "    [FAIL] result.count = $($o.result.count)（须 >=1）"; $fail++ }

    if ($fail -eq $failBefore) { $ok++ }
    Write-Output ''
}

# ---------- 6. 标签引用必须能解析 ----------
Write-Output '--- 标签引用校验（打错一个字母 = 配方静默做不出来）'
$uniqTags = @($tagRefs | Select-Object -Unique | Sort-Object)
if ($uniqTags.Count -eq 0) {
    Write-Output '  （没有配方用标签当原料）'
} else {
    $unknownHard = 0
    foreach ($t in $uniqTags) {
        $ns = ($t -split ':')[0]
        if (Test-TagKnown $t) {
            Write-Output ("  [OK]   #$t")
        } elseif ($ns -eq 'c' -or $ns -eq 'minecraft' -or $ns -eq 'potato_s_t') {
            Write-Output ("  [FAIL] #$t 解析不到（本项目 / 原版 / NeoForge 三处都没有）—— 名字打错了？"); $fail++; $unknownHard++
        } else {
            Write-Output ("  [WARN] #$t 属于别人的命名空间，本机无法核对，交付前人工确认"); 
        }
    }
    Write-Output ("  " + $script:tagNote)
}

Write-Output "------------------------------"
Write-Output "定形配方通过 = $ok    跳过(非定形) = $skip    失败项合计 = $fail"
Write-Output "引用到的物品 id（去重）:"
$ids | Select-Object -Unique | Sort-Object | ForEach-Object { Write-Output "  $_" }
Write-Output "引用到的标签（去重）:"
if ($uniqTags.Count -eq 0) { Write-Output '  （无）' } else { $uniqTags | ForEach-Object { Write-Output "  #$_" } }
if ($fail -gt 0) { Write-Output "结论: 有失败项" } else { Write-Output "结论: 全部通过" }
