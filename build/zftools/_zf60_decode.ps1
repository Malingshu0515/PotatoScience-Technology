# _zf60_decode.ps1 —— 把用户给的 7 张贴图解成干净的 PNG（先落到 build 里的暂存目录）
#
# 为什么用 WPF 而不是 Python：本机没有 Pillow（§6.8 / ZF50 那条路），
# 而 Windows 自带的 WPF 解码器能读 webp（前面几张素材都是这么解的）。
# ⚠ §4.23 的教训：**别拿扩展名当格式证据** —— 这几张文件名都叫 .png，实际是 webp。
#
# ⚠⚠ ZF60 新踩的坑（**webp 的 alpha**）：`BitmapDecoder.Create($uri,'None','OnLoad')`
#     拿到的是 **Bgr32（alpha 全 255）**，透明区域底下是**花屏/棋盘格** —— 直接落盘就把花屏
#     装进游戏了。逐个姿势试出来的正解：
#         **`BitmapImage` + `CreateOptions='PreservePixelFormat'` + `CacheOption='OnLoad'`**
#     再 `FormatConvertedBitmap(..., Bgra32, ...)` ⇒ alpha 就出来了（钛锭实测 484 个全透明像素）。
#     `BitmapDecoder` / `BitmapFrame.Create` 走同一条路都拿不到（都是 Bgr32）。
#
# 用法： $sb=[scriptblock]::Create([IO.File]::ReadAllText(...,[Text.Encoding]::UTF8)); & $sb
$ErrorActionPreference = 'Stop'
Add-Type -AssemblyName PresentationCore

$att = 'C:\Users\Administrator\.dsh\attachments\v1\objects'
$stage = 'E:\PotatoST\build\zftools\_zf60_png'
if (-not (Test-Path $stage)) { New-Item -ItemType Directory -Path $stage | Out-Null }

# 用户原话的顺序：磁铁 铁粉 钛矿石 深层钛矿石 粗钛 钛粉 钛锭
# （他说文件名可能打错 —— 第 5 张的文件名写的是"粗振金"，按**他给的顺序**当"粗钛"处理）
# ⚠ 路径一律用 [IO.Path]::Combine，**不做字符串插值** —— 第一版写 "$att\3f\..." 时收尾引号
#   打成了单引号，PowerShell 从那一行起连环报"哈希字面量不完整"（诊断办法见 _zf60_qcheck.py）。
$jobs = @(
    @{ name = 'magnet';                 src = [IO.Path]::Combine($att, '3f', '3f7fe295da5e9757507e6f69e6c38617ba343234c45c5b18a7dea0af87359e79'); want = 'textures/item/magnet.png' },
    @{ name = 'iron_powder';            src = [IO.Path]::Combine($att, '27', '27afa5a54b5df6078c2b7c39d138b56ed08ba4898bbd6a9ab57baf8ce1234b91'); want = 'textures/item/iron_powder.png' },
    @{ name = 'titanium_ore';           src = [IO.Path]::Combine($att, '86', '86ceaa24e6b9d928abcd29d8f57cdb410946370bb57a7435df7e43bc86a32c76'); want = 'textures/block/titanium_ore.png' },
    @{ name = 'deepslate_titanium_ore'; src = [IO.Path]::Combine($att, 'af', 'af1117c7ced2ec397e6f6f5296551528683741dad91a014df46400cec989a58b'); want = 'textures/block/deepslate_titanium_ore.png' },
    @{ name = 'raw_titanium';           src = [IO.Path]::Combine($att, 'e7', 'e75cbc409b6faae5eaf988d67d315737317291217184e651972b9bf140cda24e'); want = 'textures/item/raw_titanium.png' },
    @{ name = 'titanium_powder';        src = [IO.Path]::Combine($att, '34', '341497c934cd39ad2bb5010428d76756e2e77f7696a4e91085e6ca0f1635067c'); want = 'textures/item/titanium_powder.png' },
    @{ name = 'titanium_ingot';         src = [IO.Path]::Combine($att, '17', '176e4245fc68d07c397878471134ad91649fec5746a814c486378d0ee0565277'); want = 'textures/item/titanium_ingot.png' }
)

$fail = 0
foreach ($job in $jobs) {
    if (-not (Test-Path -LiteralPath $job.src)) {
        Write-Host ("  [FAIL] {0}: 源文件不在 {1}" -f $job.name, $job.src); $fail++; continue
    }
    $head = [IO.File]::ReadAllBytes($job.src)[0..11]
    $magic = ($head | ForEach-Object { '{0:X2}' -f $_ }) -join ''
    # ★ 关键：BitmapImage + PreservePixelFormat 才保得住 webp 的 alpha
    $bi = New-Object System.Windows.Media.Imaging.BitmapImage
    $bi.BeginInit()
    $bi.UriSource = (New-Object System.Uri($job.src))
    $bi.CreateOptions = [System.Windows.Media.Imaging.BitmapCreateOptions]::PreservePixelFormat
    $bi.CacheOption = [System.Windows.Media.Imaging.BitmapCacheOption]::OnLoad
    $bi.EndInit()
    $conv = New-Object System.Windows.Media.Imaging.FormatConvertedBitmap(
        $bi, [System.Windows.Media.PixelFormats]::Bgra32, $null, 0)
    $w = $conv.PixelWidth; $h = $conv.PixelHeight; $stride = $w * 4
    $buf = New-Object byte[] ($stride * $h)
    $conv.CopyPixels($buf, $stride, 0)
    $transparent = 0
    for ($i = 3; $i -lt $buf.Length; $i += 4) { if ($buf[$i] -eq 0) { $transparent++ } }
    $out = Join-Path $stage ($job.name + '.png')
    $enc = New-Object System.Windows.Media.Imaging.PngBitmapEncoder
    $enc.Frames.Add([System.Windows.Media.Imaging.BitmapFrame]::Create($conv))
    $fs = [IO.File]::Create($out)
    $enc.Save($fs)
    $fs.Close()
    Write-Host ("  [OK] {0,-24} {1,3}x{2,-3} 全透明像素={3,5}  头12字节={4}  ->  {5} 字节" -f `
        $job.name, $w, $h, $transparent, $magic, (Get-Item $out).Length)
}

Write-Host ""
Write-Host ("解码完成：{0} 张成功 / {1} 张失败，暂存目录 = {2}" -f ($jobs.Count - $fail), $fail, $stage)
