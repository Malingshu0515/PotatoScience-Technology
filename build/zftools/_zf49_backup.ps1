# ZF49 备份：动手前建，清单交叉核对（§10）。
# ZF49 = 合金冶炼炉多方块（控制器方块 + 接线口方块 + 方块实体 + 菜单界面 + 结构校验）。
$ErrorActionPreference = 'Stop'
$proj = 'E:\PotatoST'
$bk   = 'C:\Users\Administrator\Desktop\PotatoST救援_20260917_183054\zf49_pre'

$files = @(
    'src\main\java\com\potatost\mod\ModBlocks.java',
    'src\main\java\com\potatost\mod\ModMenus.java',
    'src\main\java\com\potatost\mod\PotatoST.java',
    'src\main\java\com\potatost\mod\PotatoSTClient.java',
    'src\main\resources\data\minecraft\tags\block\mineable\pickaxe.json',
    'src\main\resources\data\minecraft\tags\block\needs_stone_tool.json',
    'src\main\resources\assets\potato_s_t\lang\zh_cn.json',
    'src\main\resources\assets\potato_s_t\lang\en_us.json',
    'src\main\resources\assets\potato_s_t\lang\ja_jp.json',
    'src\main\resources\assets\potato_s_t\lang\ru_ru.json',
    'docs\开发档案.md'
)
if (Test-Path -LiteralPath $bk) { Write-Host "!! $bk 已存在" -ForegroundColor Red; exit 1 }
New-Item -ItemType Directory -Force -Path $bk | Out-Null
New-Item -ItemType Directory -Force -Path (Join-Path $bk '新增文件') | Out-Null
foreach ($f in $files) {
    $src = Join-Path $proj $f
    if (-not (Test-Path -LiteralPath $src)) { throw "缺文件: $src" }
    Copy-Item -LiteralPath $src -Destination $bk -Force
}
Copy-Item -LiteralPath (Join-Path $proj 'release\PotatoST-0.10.jar') -Destination (Join-Path $bk '_改前_PotatoST-0.10.jar') -Force
$copied = @(Get-ChildItem -LiteralPath $bk -File -Force | Where-Object { $_.Name -notlike '_改前_*' })
Write-Host ("清单条数 = {0}   改前副本 = {1}" -f $files.Count, $copied.Count)
if ($copied.Count -ne $files.Count) { exit 1 }
$bad = 0
foreach ($f in $files) {
    $leaf = Split-Path $f -Leaf
    $a = (Get-FileHash -LiteralPath (Join-Path $proj $f) -Algorithm SHA256).Hash
    $b = (Get-FileHash -LiteralPath (Join-Path $bk $leaf) -Algorithm SHA256).Hash
    if ($a -ne $b) { Write-Host ("!! 副本不一致: $leaf") -ForegroundColor Red; $bad++ }
}
if ($bad -gt 0) { exit 1 }
Write-Host "改前 jar SHA1 = " -NoNewline
(Get-FileHash -LiteralPath (Join-Path $bk '_改前_PotatoST-0.10.jar') -Algorithm SHA1).Hash.ToLower()
Write-Host "备份完成并通过清单核对 -> $bk"
