# ZF38 备份：**动手之前**建。清单在文件顶部，跑完逐条交叉核对（§10）。
# 本阶段：新增"低级发电机"整台机器（Java ×4 + 资源 ×7）+ 改 8 个既有文件。
$ErrorActionPreference = 'Stop'
$proj = 'E:\PotatoST'
$bk   = 'C:\Users\Administrator\Desktop\PotatoST救援_20260917_183054\zf38_pre'

# ===== 本阶段打算碰的既有文件（清单，逐行核对）=====
$files = @(
    'src\main\java\com\potatost\mod\PotatoST.java',
    'src\main\java\com\potatost\mod\PotatoSTClient.java',
    'src\main\java\com\potatost\mod\ModBlocks.java',
    'src\main\java\com\potatost\mod\ModItems.java',
    'src\main\java\com\potatost\mod\ModMenus.java',
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
New-Item -ItemType Directory -Force -Path (Join-Path $bk '新增文件') | Out-Null

foreach ($f in $files) {
    $src = Join-Path $proj $f
    if (-not (Test-Path -LiteralPath $src)) { throw "缺文件: $src" }
    Copy-Item -LiteralPath $src -Destination $bk -Force
}

# 改前成品 + 它的 .sha1
Copy-Item -LiteralPath (Join-Path $proj 'release\PotatoST-0.10.jar') -Destination (Join-Path $bk '_改前_PotatoST-0.10.jar') -Force
Copy-Item -LiteralPath (Join-Path $proj 'release\PotatoST-0.10.jar.sha1') -Destination (Join-Path $bk '_改前_PotatoST-0.10.jar.sha1') -Force

# 交叉核对：备份根目录里的改前副本必须与清单逐条对得上
$copied = @(Get-ChildItem -LiteralPath $bk -File -Force | Where-Object { $_.Name -notlike '_改前_*' })
Write-Host ("清单条数 = {0}   备份根目录里的改前副本 = {1}" -f $files.Count, $copied.Count)
if ($copied.Count -ne $files.Count) { Write-Host "!! 数量对不上，停下来查" -ForegroundColor Red; exit 1 }
$bad = 0
foreach ($f in $files) {
    $leaf = Split-Path $f -Leaf
    $a = (Get-FileHash -LiteralPath (Join-Path $proj $f) -Algorithm SHA256).Hash
    $b = (Get-FileHash -LiteralPath (Join-Path $bk $leaf) -Algorithm SHA256).Hash
    if ($a -ne $b) { Write-Host ("!! 副本不一致: $leaf") -ForegroundColor Red; $bad++ }
}
if ($bad -gt 0) { exit 1 }

$lines = New-Object System.Collections.Generic.List[string]
$lines.Add('ZF38 备份时刻：' + (Get-Date -Format 'yyyy-MM-dd HH:mm:ss'))
$lines.Add('下面每一行都是**备份副本自己**重算出来的 SHA256')
$lines.Add('本阶段将修改的既有文件清单（共 ' + $files.Count + ' 个）：')
foreach ($f in $files) { $lines.Add('    ' + $f) }
$lines.Add('')
$lines.Add('本阶段将新建的文件（不在本备份的"改前副本"里，因为他们本来不存在）：')
foreach ($n in @(
    'src\main\java\com\potatost\mod\LowGeneratorBlock.java',
    'src\main\java\com\potatost\mod\LowGeneratorBlockEntity.java',
    'src\main\java\com\potatost\mod\LowGeneratorMenu.java',
    'src\main\java\com\potatost\mod\client\LowGeneratorScreen.java',
    'src\main\resources\assets\potato_s_t\blockstates\low_generator.json',
    'src\main\resources\assets\potato_s_t\models\block\low_generator.json',
    'src\main\resources\assets\potato_s_t\models\item\low_generator.json',
    'src\main\resources\assets\potato_s_t\textures\block\low_generator_side.png',
    'src\main\resources\assets\potato_s_t\textures\block\low_generator_top.png',
    'src\main\resources\data\potato_s_t\loot_table\blocks\low_generator.json',
    'src\main\resources\data\potato_s_t\recipe\low_generator.json'
)) { $lines.Add('    ' + $n) }
$lines.Add('')
foreach ($item in (Get-ChildItem -LiteralPath $bk -Recurse -File -Force | Where-Object { $_.Name -ne '_sha256.txt' } | Sort-Object FullName)) {
    $h = (Get-FileHash -LiteralPath $item.FullName -Algorithm SHA256).Hash.ToLower()
    $rel = $item.FullName.Substring($bk.Length + 1)
    $lines.Add(('{0}  {1,10}  {2}' -f $h, $item.Length, $rel))
}
Set-Content -LiteralPath (Join-Path $bk '_sha256.txt') -Value $lines -Encoding UTF8

Write-Host "备份完成并通过清单核对 -> $bk"
Write-Host ("  （{0} 个改前副本已存档）" -f $copied.Count)
