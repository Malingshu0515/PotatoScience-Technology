# ZF41 备份：动手前建，清单交叉核对（§10）。
$ErrorActionPreference = 'Stop'
$proj = 'E:\PotatoST'
$bk   = 'C:\Users\Administrator\Desktop\PotatoST救援_20260917_183054\zf41_pre'

$files = @(
    'src\main\java\com\potatost\mod\PotatoST.java',
    'src\main\java\com\potatost\mod\ModBlocks.java',
    'src\main\java\com\potatost\mod\ModItems.java',
    'src\main\java\com\potatost\mod\ElectricBlastFurnaceBlock.java',
    'src\main\java\com\potatost\mod\ElectricBlastFurnacePartBlock.java',
    'src\main\java\com\potatost\mod\ElectricBlastFurnaceBlockEntity.java',
    'src\main\resources\assets\potato_s_t\lang\zh_cn.json',
    'src\main\resources\assets\potato_s_t\lang\en_us.json',
    'src\main\resources\assets\potato_s_t\lang\ja_JP.json'
)
# ja_jp 的真实文件名是 ja_jp.json，上面写错要拦住
$files[8] = 'src\main\resources\assets\potato_s_t\lang\ja_jp.json'
$files += 'src\main\resources\assets\potato_s_t\lang\ru_ru.json'
$files += 'docs\开发档案.md'

if (Test-Path -LiteralPath $bk) { Write-Host "!! $bk 已存在" -ForegroundColor Red; exit 1 }
New-Item -ItemType Directory -Force -Path $bk | Out-Null
New-Item -ItemType Directory -Force -Path (Join-Path $bk '新增文件') | Out-Null

foreach ($f in $files) {
    $src = Join-Path $proj $f
    if (-not (Test-Path -LiteralPath $src)) { throw "缺文件: $src" }
    Copy-Item -LiteralPath $src -Destination $bk -Force
}
Copy-Item -LiteralPath (Join-Path $proj 'release\PotatoST-0.10.jar') -Destination (Join-Path $bk '_改前_PotatoST-0.10.jar') -Force
Copy-Item -LiteralPath (Join-Path $proj 'release\PotatoST-0.10.jar.sha1') -Destination (Join-Path $bk '_改前_PotatoST-0.10.jar.sha1') -Force

$copied = @(Get-ChildItem -LiteralPath $bk -File -Force | Where-Object { $_.Name -notlike '_改前_*' })
Write-Host ("清单条数 = {0}   备份根目录里的改前副本 = {1}" -f $files.Count, $copied.Count)
if ($copied.Count -ne $files.Count) { Write-Host "!! 数量对不上" -ForegroundColor Red; exit 1 }
$bad = 0
foreach ($f in $files) {
    $leaf = Split-Path $f -Leaf
    $a = (Get-FileHash -LiteralPath (Join-Path $proj $f) -Algorithm SHA256).Hash
    $b = (Get-FileHash -LiteralPath (Join-Path $bk $leaf) -Algorithm SHA256).Hash
    if ($a -ne $b) { Write-Host ("!! 副本不一致: $leaf") -ForegroundColor Red; $bad++ }
}
if ($bad -gt 0) { exit 1 }
Write-Host "备份完成并通过清单核对 -> $bk"
