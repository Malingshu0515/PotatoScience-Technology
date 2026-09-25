# ZF39 备份：动手前建。清单在顶部，跑完逐条交叉核对（§10）。
$ErrorActionPreference = 'Stop'
$proj = 'E:\PotatoST'
$bk   = 'C:\Users\Administrator\Desktop\PotatoST救援_20260917_183054\zf39_pre'

$files = @(
    'src\main\java\com\potatost\mod\PotatoST.java',
    'src\main\java\com\potatost\mod\PotatoSTClient.java',
    'src\main\java\com\potatost\mod\ModBlocks.java',
    'src\main\java\com\potatost\mod\ModItems.java',
    'src\main\java\com\potatost\mod\ModMenus.java',
    'src\main\java\com\potatost\mod\ModEvents.java',
    'src\main\resources\assets\potato_s_t\lang\zh_cn.json',
    'src\main\resources\assets\potato_s_t\lang\en_us.json',
    'src\main\resources\assets\potato_s_t\lang\ja_jp.json',
    'src\main\resources\assets\potato_s_t\lang\ru_ru.json',
    'src\main\resources\data\minecraft\tags\block\mineable\pickaxe.json',
    'src\main\resources\data\minecraft\tags\block\needs_stone_tool.json',
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
Copy-Item -LiteralPath (Join-Path $proj 'release\PotatoST-0.10.jar.sha1') -Destination (Join-Path $bk '_改前_PotatoST-0.10.jar.sha1') -Force
Copy-Item -LiteralPath 'C:\Users\Administrator\.dsh\attachments\v1\files\4c\4cfdb0359b91bfe97943d66fcb198fd4c80ef0d8e5f3a7a68dc7ff1789fe990a\model.obj' -Destination (Join-Path $bk '新增文件\用户原始_model.obj') -Force

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
$lines.Add('ZF39 备份时刻：' + (Get-Date -Format 'yyyy-MM-dd HH:mm:ss'))
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
