# ZF35 备份：**动手之前**建。
# §10 新规矩：清单**不凭记忆**——本文件顶部就是那张表，脚本跑完逐行核对"备份目录里的文件"与表，
#             数量对不上就报错退出。ZF34 就是凭记忆列清单漏了 needs_stone_tool.json。
$ErrorActionPreference = 'Stop'
$proj = 'E:\PotatoST'
$bk   = 'C:\Users\Administrator\Desktop\PotatoST救援_20260917_183054\zf35_pre'

# ===== 本阶段打算碰的既有文件（清单，逐行核对）=====
$files = @(
    'src\main\java\com\potatost\mod\ModBlocks.java',
    'src\main\java\com\potatost\mod\ModItems.java',
    'src\main\resources\assets\potato_s_t\lang\zh_cn.json',
    'src\main\resources\assets\potato_s_t\lang\en_us.json',
    'src\main\resources\assets\potato_s_t\lang\ja_jp.json',
    'src\main\resources\assets\potato_s_t\lang\ru_ru.json',
    'src\main\resources\data\minecraft\tags\block\mineable\pickaxe.json',
    'src\main\resources\data\minecraft\tags\block\needs_stone_tool.json',
    'docs\开发档案.md'
)

if (Test-Path -LiteralPath $bk) {
    Write-Host "!! $bk 已存在——先确认它不是本次的" -ForegroundColor Red
    exit 1
}
New-Item -ItemType Directory -Force -Path $bk | Out-Null
New-Item -ItemType Directory -Force -Path (Join-Path $bk '_素材') | Out-Null
New-Item -ItemType Directory -Force -Path (Join-Path $bk '新增文件') | Out-Null

foreach ($f in $files) {
    $src = Join-Path $proj $f
    if (-not (Test-Path -LiteralPath $src)) { throw "缺文件: $src" }
    Copy-Item -LiteralPath $src -Destination $bk -Force
}

# 用户原始素材（新建方块用，不算"既有文件"）
Copy-Item -LiteralPath (Join-Path $proj 'build\zftools\_block_imgs\接线块.webp') -Destination (Join-Path $bk '_素材') -Force
Copy-Item -LiteralPath (Join-Path $proj 'build\zftools\_block_imgs\接线块.rgba') -Destination (Join-Path $bk '_素材') -Force
Copy-Item -LiteralPath (Join-Path $proj 'build\zftools\_zf35_decode.ps1') -Destination (Join-Path $bk '新增文件') -Force

# 改前成品 + 它的 .sha1
Copy-Item -LiteralPath (Join-Path $proj 'release\PotatoST-0.10.jar') -Destination (Join-Path $bk '_改前_PotatoST-0.10.jar') -Force
Copy-Item -LiteralPath (Join-Path $proj 'release\PotatoST-0.10.jar.sha1') -Destination (Join-Path $bk '_改前_PotatoST-0.10.jar.sha1') -Force

# ===== 交叉核对：备份目录里的"改前副本"个数必须等于清单条数 =====
$copied = @(Get-ChildItem -LiteralPath $bk -File -Force | Where-Object { $_.Name -notlike '_改前_*' })
Write-Host ("清单条数 = {0}   备份根目录里的改前副本 = {1}" -f $files.Count, $copied.Count)
if ($copied.Count -ne $files.Count) {
    Write-Host "!! 数量对不上——清单与备份不一致，停下来查" -ForegroundColor Red
    exit 1
}
# 逐个文件核对：备份副本必须与源**逐字节一致**
$bad = 0
foreach ($f in $files) {
    $leaf = Split-Path $f -Leaf
    $a = (Get-FileHash -LiteralPath (Join-Path $proj $f) -Algorithm SHA256).Hash
    $b = (Get-FileHash -LiteralPath (Join-Path $bk $leaf) -Algorithm SHA256).Hash
    if ($a -ne $b) { Write-Host ("!! 副本不一致: $leaf") -ForegroundColor Red; $bad++ }
}
if ($bad -gt 0) { exit 1 }

# 哈希清单（算的是**备份副本自己**的，§10）
$lines = New-Object System.Collections.Generic.List[string]
$lines.Add('ZF35 备份时刻：' + (Get-Date -Format 'yyyy-MM-dd HH:mm:ss'))
$lines.Add('下面每一行都是**备份副本自己**重算出来的 SHA256')
$lines.Add('本阶段将修改的既有文件清单（共 ' + $files.Count + ' 个）：')
foreach ($f in $files) { $lines.Add('    ' + $f) }
$lines.Add('')
foreach ($item in (Get-ChildItem -LiteralPath $bk -Recurse -File -Force | Where-Object { $_.Name -ne '_sha256.txt' } | Sort-Object FullName)) {
    $h = (Get-FileHash -LiteralPath $item.FullName -Algorithm SHA256).Hash.ToLower()
    $rel = $item.FullName.Substring($bk.Length + 1)
    $lines.Add(('{0}  {1,10}  {2}' -f $h, $item.Length, $rel))
}
Set-Content -LiteralPath (Join-Path $bk '_sha256.txt') -Value $lines -Encoding UTF8

Write-Host "备份完成并通过清单核对 -> $bk"
Get-ChildItem -LiteralPath $bk -Recurse -File -Force | Sort-Object FullName | ForEach-Object {
    Write-Host ('  ' + $_.FullName.Substring($bk.Length + 1) + '   ' + $_.Length + ' B')
}
