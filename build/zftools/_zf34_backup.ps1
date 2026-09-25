# -*- coding: utf-8 -*-
# ZF34 备份：**动手之前**建（§10 反复栽过的那条规矩）
# 用法：pwsh -File 本脚本

$ErrorActionPreference = 'Stop'
$proj = 'E:\PotatoST'
$bk   = 'C:\Users\Administrator\Desktop\PotatoST救援_20260917_183054\zf34_pre'

if (Test-Path -LiteralPath $bk) {
    Write-Host "!! $bk 已存在——先确认它不是本次的，再决定是否删" -ForegroundColor Red
    exit 1
}
New-Item -ItemType Directory -Force -Path $bk | Out-Null
New-Item -ItemType Directory -Force -Path (Join-Path $bk '_素材') | Out-Null
New-Item -ItemType Directory -Force -Path (Join-Path $bk '新增文件') | Out-Null

# 本次会被改的既有文件（拍平到 $bk 根，映射写进 _说明.txt）
$files = @(
    'src\main\java\com\potatost\mod\ModBlocks.java',
    'src\main\java\com\potatost\mod\ModItems.java',
    'src\main\resources\assets\potato_s_t\lang\zh_cn.json',
    'src\main\resources\assets\potato_s_t\lang\en_us.json',
    'src\main\resources\assets\potato_s_t\lang\ja_jp.json',
    'src\main\resources\assets\potato_s_t\lang\ru_ru.json',
    'src\main\resources\data\minecraft\tags\block\mineable\pickaxe.json',
    'docs\开发档案.md'
)
foreach ($f in $files) {
    $src = Join-Path $proj $f
    if (-not (Test-Path -LiteralPath $src)) { throw "缺文件: $src" }
    Copy-Item -LiteralPath $src -Destination $bk -Force
}

# 要被**改名**的 6 张中文贴图（改名前的原样留档）+ 用户原始素材
$textures = @('一般金属块.png', '高级金属块.png', '稳定金属块.png', '耐热金属块.png', '加热装置.png', '散热装置.png')
foreach ($t in $textures) {
    $src = Join-Path $proj ('src\main\resources\assets\potato_s_t\textures\block\' + $t)
    if (-not (Test-Path -LiteralPath $src)) { throw "缺贴图: $src" }
    Copy-Item -LiteralPath $src -Destination (Join-Path $bk '_素材') -Force
}
foreach ($t in @('一般金属块.webp', '高级金属块.webp', '稳定金属块.webp', '耐热金属块.webp', '加热装置.webp', '散热装置.webp')) {
    $src = Join-Path $proj ('build\zftools\_block_imgs\' + $t)
    if (Test-Path -LiteralPath $src) { Copy-Item -LiteralPath $src -Destination (Join-Path $bk '_素材') -Force }
}

# 改前的成品 jar（SHA1 作废凭据）
Copy-Item -LiteralPath (Join-Path $proj 'release\PotatoST-0.10.jar') -Destination (Join-Path $bk '_改前_PotatoST-0.10.jar') -Force

# 逐份算哈希 —— 注意算的是**备份副本自己**的，不是源文件的（§10：曾被"pre==post"骗过）
$hashFile = Join-Path $bk '_sha256.txt'
$lines = New-Object System.Collections.Generic.List[string]
$lines.Add('ZF34 备份时刻：' + (Get-Date -Format 'yyyy-MM-dd HH:mm:ss'))
$lines.Add('下面每一行都是**备份副本自己**重算出来的 SHA256（不是源文件的）')
$lines.Add('')
foreach ($item in (Get-ChildItem -LiteralPath $bk -Recurse -File -Force | Where-Object { $_.Name -ne '_sha256.txt' } | Sort-Object FullName)) {
    $h = (Get-FileHash -LiteralPath $item.FullName -Algorithm SHA256).Hash.ToLower()
    $rel = $item.FullName.Substring($bk.Length + 1)
    $lines.Add(('{0}  {1,10}  {2}' -f $h, $item.Length, $rel))
}
Set-Content -LiteralPath $hashFile -Value $lines -Encoding UTF8

Write-Host "备份完成 -> $bk"
Get-ChildItem -LiteralPath $bk -Recurse -File -Force | Sort-Object FullName | ForEach-Object {
    Write-Host ('  ' + $_.FullName.Substring($bk.Length + 1) + '   ' + $_.Length + ' B')
}
