# ============================================================
#  Audit.ps1 —— PotatoS&T 代码标准审计器（0.09 起作为标准执行）
#
#  用法（本机 ExecutionPolicy 是 Restricted，用 scriptblock 绕开）：
#     $sb = [scriptblock]::Create([IO.File]::ReadAllText('E:\PotatoST\build\zftools\Audit.ps1', [Text.Encoding]::UTF8))
#     & $sb
#
#  这是「以后都按这个标准走」的**可执行版本**。散文标准会腐烂，脚本不会。
#  每次交付前跑一遍，失败项一并修掉再打包。
#
#  检查项：
#    A. 未使用的 import
#    B. 【血泪】有物品栏的方块实体，其方块必须有 onRemove 掉落（0.08 吞物品那次）
#    C. 跨语言键集一致性（委托 LangCheck 的规则）
#    D. 匿名 IEnergyStorage 重复（0.09 提取后应保持为 5 —— 那 5 个语义确实不同）
#    E. 硬编码中文（排除注释）
#    F. TODO / FIXME / XXX / HACK
#    G. 文件规模 Top 榜（超过 400 行提示拆分）
#    H. 版本号 <-> release 产物名 / .sha1 副档一致性（0.10 正式版冻结线）
#    I. 覆写 isItemValid 又自己调 insertItem（insertItem 内部查 isItemValid，会静默失败 → 吞物品）
#    J. 矿物/合金/矿物锭 的 c: 通用标签（用户指令：以后默认兼容别的 mod，由 GenCommonTags.py 生成）
#
#  刻意不调用 exit：scriptblock 在宿主进程内跑时 exit 会掐断宿主。
# ============================================================
param(
    [string]$SrcRoot = 'E:\PotatoST\src\main\java',
    [string]$LangDir = 'E:\PotatoST\src\main\resources\assets\potato_s_t\lang'
)

$ErrorActionPreference = 'Continue'
$fail = 0
$warn = 0

$files = @(Get-ChildItem $SrcRoot -Recurse -Filter '*.java')
Write-Output ("=== PotatoS&T 代码标准审计   （{0} 个 java 文件）" -f $files.Count)
Write-Output ''

# ---------- A. 未使用的 import ----------
Write-Output '--- A. 未使用的 import'
$a = 0
foreach ($f in $files) {
    $lines = [IO.File]::ReadAllLines($f.FullName, [Text.Encoding]::UTF8)
    $body = ($lines | Where-Object { $_ -notmatch '^\s*import\s' }) -join "`n"
    foreach ($l in $lines) {
        if ($l -match '^\s*import\s+(static\s+)?([\w.]+);') {
            $simple = ($matches[2] -split '\.')[-1]
            if ($body -notmatch ('\b' + [regex]::Escape($simple) + '\b')) {
                Write-Output ("  [FAIL] {0}: {1}" -f $f.Name, $l.Trim()); $a++; $fail++
            }
        }
    }
}
if ($a -eq 0) { Write-Output '  [OK]   无' }

# ---------- B. 物品栏掉落守卫（0.08 的雷） ----------
Write-Output ''
Write-Output '--- B. 有物品栏的方块实体 <-> 方块 onRemove 掉落'
$b = 0
$bFound = 0
foreach ($be in ($files | Where-Object { $_.Name -like '*BlockEntity.java' })) {
    $txt = [IO.File]::ReadAllText($be.FullName, [Text.Encoding]::UTF8)
    if ($txt -notmatch 'new ItemStackHandler\(') { continue }
    $bFound++
    $blockName = $be.Name -replace 'BlockEntity\.java$', 'Block.java'
    $block = $files | Where-Object { $_.Name -eq $blockName } | Select-Object -First 1
    if (-not $block) {
        Write-Output ("  [FAIL] {0} 有物品栏，但找不到对应方块 {1}" -f $be.Name, $blockName); $b++; $fail++; continue
    }
    $bt = [IO.File]::ReadAllText($block.FullName, [Text.Encoding]::UTF8)
    $hasOnRemove = $bt -match 'void onRemove\('
    $drops = $bt -match 'MachineDrops\.dropInventory'
    if ($hasOnRemove -and $drops) {
        Write-Output ("  [OK]   {0} -> {1} 有 onRemove + MachineDrops" -f $be.Name, $blockName)
    } else {
        Write-Output ("  [FAIL] {0} -> {1}  有物品栏但【未】掉落（onRemove={2}, dropInventory={3}）—— 破坏即吞物品！" -f $be.Name, $blockName, $hasOnRemove, $drops)
        $b++; $fail++
    }
}
if ($bFound -eq 0) { Write-Output '  （没有带物品栏的方块实体）' }

# ---------- C. 跨语言键集一致性 ----------
Write-Output ''
Write-Output '--- C. 跨语言键集一致性'
$langFiles = @(Get-ChildItem $LangDir -Filter '*.json' -ErrorAction SilentlyContinue)
if ($langFiles.Count -lt 2) { Write-Output '  [SKIP] 语言文件少于 2 个' }
else {
    $keys = @{}
    $bom = 0
    foreach ($lf in $langFiles) {
        $bytes = [IO.File]::ReadAllBytes($lf.FullName)
        if ($bytes.Length -ge 3 -and $bytes[0] -eq 0xEF) { Write-Output ("  [FAIL] {0} 带 BOM" -f $lf.Name); $bom++; $fail++ }
        $o = [IO.File]::ReadAllText($lf.FullName, [Text.Encoding]::UTF8) | ConvertFrom-Json
        $keys[[IO.Path]::GetFileNameWithoutExtension($lf.Name)] = @($o.PSObject.Properties.Name)
    }
    $langs = @($keys.Keys | Sort-Object)
    $base = $langs[0]; $baseK = $keys[$base]
    $c = 0
    foreach ($l in $langs) {
        if ($l -eq $base) { continue }
        $miss = @($baseK | Where-Object { $keys[$l] -notcontains $_ })
        $extra = @($keys[$l] | Where-Object { $baseK -notcontains $_ })
        if ($miss.Count -gt 0 -or $extra.Count -gt 0) {
            Write-Output ("  [FAIL] {0}: 缺 {1} 键, 多 {2} 键" -f $l, $miss.Count, $extra.Count); $c++; $fail++
        }
    }
    if ($c -eq 0 -and $bom -eq 0) { Write-Output ("  [OK]   {0} 种语言键集完全一致（各 {1} 键），无 BOM" -f $langs.Count, $baseK.Count) }
}

# ---------- D. 匿名 IEnergyStorage 重复 ----------
Write-Output ''
Write-Output '--- D. 匿名 IEnergyStorage（0.09 提取后基准 = 5，语义确实不同的那 5 个）'
$d = @()
foreach ($f in $files) {
    if ([IO.File]::ReadAllText($f.FullName, [Text.Encoding]::UTF8) -match 'new IEnergyStorage\(\)\s*\{') { $d += $f.Name }
}
Write-Output ("  数量 = {0}  -> {1}" -f $d.Count, ($d -join ', '))
if ($d.Count -gt 5) { Write-Output '  [WARN] 超过基准 5：可能有新的复制粘贴，考虑复用 MachineEnergyStorage'; $warn++ }

# ---------- E. 硬编码中文（排除注释） ----------
Write-Output ''
Write-Output '--- E. 硬编码中文（排除注释行与行尾注释）'
$e = 0
foreach ($f in $files) {
    $n = 0
    foreach ($l in [IO.File]::ReadAllLines($f.FullName, [Text.Encoding]::UTF8)) {
        $n++
        $code = $l -replace '//.*$', ''
        if ($code -match '"[^"]*[\u4e00-\u9fff][^"]*"' -and $l -notmatch '^\s*(\*|/\*|//)') {
            Write-Output ("  [FAIL] {0}:{1}  {2}" -f $f.Name, $n, $l.Trim()); $e++; $fail++
        }
    }
}
if ($e -eq 0) { Write-Output '  [OK]   无（用户可见文本都走了 lang 文件）' }

# ---------- F. TODO ----------
Write-Output ''
Write-Output '--- F. TODO / FIXME / XXX / HACK'
$fcount = 0
foreach ($f in $files) {
    foreach ($m in (Select-String -Path $f.FullName -Pattern 'TODO|FIXME|XXX|HACK')) {
        Write-Output ("  [WARN] {0}:{1}  {2}" -f $f.Name, $m.LineNumber, $m.Line.Trim()); $fcount++; $warn++
    }
}
if ($fcount -eq 0) { Write-Output '  [OK]   无' }

# ---------- G. 规模 ----------
Write-Output ''
Write-Output '--- G. 文件规模 Top 8（>400 行建议拆分）'
$rows = foreach ($f in $files) { [pscustomobject]@{ L = ([IO.File]::ReadAllLines($f.FullName, [Text.Encoding]::UTF8)).Count; N = $f.Name } }
$rows | Sort-Object L -Descending | Select-Object -First 8 | ForEach-Object {
    $tag = if ($_.L -gt 400) { ' <== 偏大' } else { '' }
    Write-Output ("  {0,5}  {1}{2}" -f $_.L, $_.N, $tag)
    if ($_.L -gt 400) { $warn++ }
}

Write-Output ''
# ---------- H. 版本号 <-> release 产物 / .sha1 副档 ----------
Write-Output '--- H. 版本号 <-> release 产物名 / .sha1 副档'
$gp = 'E:\PotatoST\gradle.properties'
$relDir = 'E:\PotatoST\release'
if (-not (Test-Path $gp)) { Write-Output ("  [SKIP] 找不到 {0}" -f $gp) }
else {
    $ver = $null
    foreach ($l in [IO.File]::ReadAllLines($gp, [Text.Encoding]::UTF8)) {
        if ($l -match '^\s*mod_version\s*=\s*(\S+)') { $ver = $matches[1] }
    }
    $jars = @(Get-ChildItem $relDir -Filter '*.jar' -ErrorAction SilentlyContinue | Sort-Object LastWriteTime -Descending)
    if ($jars.Count -eq 0) { Write-Output '  [SKIP] release 里没有 jar' }
    else {
        $newest = $jars[0]
        $expect = "PotatoST-$ver.jar"
        Write-Output ("  mod_version = {0}    最新产物 = {1}" -f $ver, $newest.Name)
        # 0.10 起为正式版冻结线：除用户另行说明，版本号应恒为 0.10
        if ($ver -ne '0.10' -and $ver -notmatch '^0\.1[1-9]$') {
            Write-Output ("  [WARN] mod_version = {0}，不在 0.10 冻结线上（用户已说明后续均为 v0.10 正式版）" -f $ver); $warn++
        }
        if ($newest.Name -ne $expect) {
            Write-Output ("  [FAIL] 最新产物名与版本号不符（应为 {0}）—— 要么忘了改 mod_version，要么忘了复制新 jar" -f $expect); $fail++
        } else { Write-Output '  [OK]   产物名与版本号一致' }
        $sha = $newest.FullName + '.sha1'
        if (-not (Test-Path $sha)) { Write-Output '  [FAIL] 缺少 .sha1 副档'; $fail++ }
        else {
            $recorded = ([IO.File]::ReadAllText($sha, [Text.Encoding]::UTF8)).Trim().Split(' ')[0]
            $actual = (Get-FileHash $newest.FullName -Algorithm SHA1).Hash.ToLower()
            if ($recorded -ne $actual) {
                Write-Output ("  [FAIL] .sha1 与实际文件不符！记录 = {0}  实际 = {1}" -f $recorded, $actual); $fail++
            } else { Write-Output ("  [OK]   .sha1 校验一致 {0}" -f $actual) }
        }
    }
}

Write-Output ''
# ---------- I. isItemValid 门禁 vs 自己调 insertItem ----------
Write-Output '--- I. 覆写 isItemValid 同时又调 insertItem（0.10 微型粉碎机吞产物那次）'
$icount = 0
foreach ($f in $files) {
    $t = [IO.File]::ReadAllText($f.FullName, [Text.Encoding]::UTF8)
    if ($t -notmatch 'boolean\s+isItemValid\s*\(') { continue }
    if ($t -notmatch '\.insertItem\s*\(') { continue }
    Write-Output ("  [WARN] {0}：同时覆写 isItemValid 又调用 insertItem" -f $f.Name)
    Write-Output '         insertItem 内部会查 isItemValid —— 往被禁的槽位插会【静默失败】（原样返回），'
    Write-Output '         调用方若不查返回值就成了"吞物品"。确认插入目标槽在 isItemValid 里为 true，否则改用 setStackInSlot。'
    $icount++; $warn++
}
if ($icount -eq 0) { Write-Output '  [OK]   无（覆写 isItemValid 的类都没用 insertItem）' }

Write-Output ''
# ---------- J. 矿物 / 合金 / 矿物锭 的 c: 通用标签 ----------
Write-Output '--- J. 矿物/合金/锭 的 c: 通用标签（用户指令：以后默认兼容别的 mod）'
$tagRoot = 'E:\PotatoST\src\main\resources\data\c\tags'
$j = 0
if (-not (Test-Path $tagRoot)) {
    Write-Output '  [FAIL] 找不到 data/c/tags —— 一条兼容标签都没有'; $fail++
} else {
    $tagText = (Get-ChildItem $tagRoot -Recurse -Filter '*.json' |
                ForEach-Object { [IO.File]::ReadAllText($_.FullName, [Text.Encoding]::UTF8) }) -join "`n"
    # 已注册 id 的清单取自 lang 键（LangCheck 的 C 项已保证四语键集一致）
    $ids = @()
    foreach ($lf in (Get-ChildItem $LangDir -Filter 'zh_cn.json' -ErrorAction SilentlyContinue)) {
        $o = [IO.File]::ReadAllText($lf.FullName, [Text.Encoding]::UTF8) | ConvertFrom-Json
        foreach ($p in $o.PSObject.Properties.Name) {
            if ($p -match '^(?:item|block)\.potato_s_t\.(.+)$') { $ids += $matches[1] }
        }
    }
    # 【ZF74 补】流体也是 id：从 ModFluids.java 的注册里抄（原来只认 lang 的 item/block 键，
    #            于是所有 potato_s_t:<fluid> 都被误判成"不存在"）
    $fluidIds = @()
    $fluidsFile = 'E:\PotatoST\src\main\java\com\potatost\mod\ModFluids.java'
    if (Test-Path $fluidsFile) {
        $ft = [IO.File]::ReadAllText($fluidsFile, [Text.Encoding]::UTF8)
        foreach ($fm in [regex]::Matches($ft, 'FLUIDS\.register\("([a-z0-9_]+)"')) {
            $fluidIds += $fm.Groups[1].Value
        }
    }
    $fluidIds = @($fluidIds | Sort-Object -Unique)
    $ids = @($ids + $fluidIds | Sort-Object -Unique)
    # ①b 每种流体都必须挂进某个 c: 标签（ZF74 规矩：以后的流体也要和别的 mod 通用，见档案 §6.19）
    foreach ($fid in $fluidIds) {
        if ($tagText -notmatch ('potato_s_t:' + [regex]::Escape($fid) + '\b')) {
            Write-Output ("  [FAIL] 流体 {0} 没挂进任何 c: 标签 —— 见档案 §6.19" -f $fid); $j++; $fail++
        }
    }
    # ① 每个 *_ingot / raw_* / *_ore 都必须挂在某个 c: 标签里
    $need = @($ids | Where-Object { $_ -match '_ingot$' -or $_ -match '^raw_' -or $_ -match '_ore$' })
    foreach ($id in $need) {
        if ($tagText -notmatch ('potato_s_t:' + [regex]::Escape($id) + '\b')) {
            Write-Output ("  [FAIL] {0} 没挂进任何 c: 标签 —— 跑一遍 GenCommonTags.py" -f $id); $j++; $fail++
        }
    }
    # ② 标签里引用的 id 必须真实注册（防打错字）
    foreach ($m in [regex]::Matches($tagText, 'potato_s_t:([a-z0-9_]+)')) {
        if ($ids -notcontains $m.Groups[1].Value) {
            Write-Output ("  [FAIL] c: 标签引用了不存在的 id：potato_s_t:{0}" -f $m.Groups[1].Value); $j++; $fail++
        }
    }
    # ③ 合金：名字上看不出是合金，只能显式点名
    if ($tagText -notmatch 'potato_s_t:high_carbon_steel') {
        Write-Output '  [FAIL] 高碳钢（合金）没挂进 c:ingots/steel 或 c:steel_ingots'; $j++; $fail++
    }
    if ($j -eq 0) {
        Write-Output ("  [OK]   {0} 个矿物/锭/粗矿全部已挂 c: 标签，引用 id 全部真实存在（标签文件 {1} 个）" -f `
            $need.Count, @(Get-ChildItem $tagRoot -Recurse -Filter '*.json').Count)
    }
}

Write-Output ''
Write-Output '=============================='
Write-Output ("失败项 = {0}   提示项 = {1}" -f $fail, $warn)
if ($fail -gt 0) { Write-Output '结论: 有失败项，必须先修再交付' } else { Write-Output '结论: 通过' }
