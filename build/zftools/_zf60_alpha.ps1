# _zf60_alpha.ps1 —— 试各种解码姿势，看能不能拿到 webp 的 alpha
#
# 背景：这 7 个文件都是 **webp 带 ALPH 块**（透明通道在里面），但
#       BitmapDecoder.Create($uri,'None','OnLoad') 拿到的是 Bgr32（alpha 全 255），
#       底下的 RGB 是花屏/棋盘格 ⇒ 直接落盘会把花屏一起装进游戏。
# 这里逐个试 BitmapCreateOptions（尤其 PreservePixelFormat），把帧格式与 alpha 统计打出来。
$ErrorActionPreference = 'Stop'
Add-Type -AssemblyName PresentationCore

$att = 'C:\Users\Administrator\.dsh\attachments\v1\objects'
$src = [IO.Path]::Combine($att, '17', '176e4245fc68d07c397878471134ad91649fec5746a814c486378d0ee0565277')  # 钛锭（带 ALPH）
$uri = New-Object System.Uri($src)

function Probe([string]$label, $frame) {
    if ($null -eq $frame) { Write-Host ("  {0,-28} -> 拿不到帧" -f $label); return }
    $w = $frame.PixelWidth; $h = $frame.PixelHeight
    $conv = New-Object System.Windows.Media.Imaging.FormatConvertedBitmap(
        $frame, [System.Windows.Media.PixelFormats]::Bgra32, $null, 0)
    $stride = $w * 4
    $buf = New-Object byte[] ($stride * $h)
    $conv.CopyPixels($buf, $stride, 0)
    $zero = 0; $full = 0
    for ($i = 3; $i -lt $buf.Length; $i += 4) {
        if ($buf[$i] -eq 0) { $zero++ } elseif ($buf[$i] -eq 255) { $full++ }
    }
    Write-Host ("  {0,-28} 帧格式={1,-8} 全透明={2,5} 全不透明={3,5} 左上角BGRA={4},{5},{6},{7}" -f `
        $label, $frame.Format.ToString(), $zero, $full, $buf[0], $buf[1], $buf[2], $buf[3])
}

Write-Host "== 钛锭 =="
Probe 'Create(None)' ([System.Windows.Media.Imaging.BitmapDecoder]::Create($uri, 'None', 'OnLoad').Frames[0])
Probe 'Create(PreservePixelFormat)' ([System.Windows.Media.Imaging.BitmapDecoder]::Create($uri, 'PreservePixelFormat', 'OnLoad').Frames[0])
Probe 'Create(PreservePixelFormat,OnDemand)' ([System.Windows.Media.Imaging.BitmapDecoder]::Create($uri, 'PreservePixelFormat', 'OnDemand').Frames[0])
$bi = New-Object System.Windows.Media.Imaging.BitmapImage
$bi.BeginInit(); $bi.UriSource = $uri; $bi.CreateOptions = 'PreservePixelFormat'; $bi.CacheOption = 'OnLoad'; $bi.EndInit()
Probe 'BitmapImage(PreservePixelFormat)' $bi
Probe 'BitmapFrame.Create(PreservePixelFormat)' ([System.Windows.Media.Imaging.BitmapFrame]::Create($uri, 'PreservePixelFormat', 'OnLoad'))

Write-Host ""
Write-Host "== WIC 解码器能给出的所有像素格式 =="
$dec = [System.Windows.Media.Imaging.BitmapDecoder]::Create($uri, 'PreservePixelFormat', 'OnLoad')
Write-Host ("  decoder = {0}" -f $dec.GetType().FullName)
Write-Host ("  frame0.Format = {0}" -f $dec.Frames[0].Format.ToString())
Write-Host ("  frame0.Palette = {0} 色" -f $dec.Frames[0].Palette.Colors.Count)
Write-Host ("  帧数 = {0}" -f $dec.Frames.Count)
