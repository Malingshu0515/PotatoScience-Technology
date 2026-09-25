# _zf50_decode.ps1 —— 把用户给的"合金主控_001.png"（**其实是 webp**）解码成裸 BGRA 像素
#
# 为什么用 WPF 而不是 Python：本机没有 Pillow，而 §6.8 已经证实 Windows 自带的
# WPF 解码器能读 webp（ZF33/ZF34/ZF35 那几张素材都是这么解的）。
# ⚠ §4.23 的教训：**别拿扩展名当格式证据** —— 这个文件名字叫 .png，头 16 字节却是
#    "RIFF....WEBP"（52 49 46 46 ... 57 45 42 50），所以按 webp 解。
$ErrorActionPreference = 'Stop'
Add-Type -AssemblyName PresentationCore

$src = 'C:\Users\Administrator\.dsh\attachments\v1\objects\fc\fc58af9a25b801b274cac271fa461bc781def17745bca586ab0a1450e4d7618f'
$out = 'E:\PotatoST\build\zftools\_zf50_raw.bin'

$uri = New-Object System.Uri($src)
$dec = [System.Windows.Media.Imaging.BitmapDecoder]::Create($uri, 'None', 'OnLoad')
$frame = $dec.Frames[0]
Write-Host ("解码器 = {0}" -f $dec.GetType().Name)
Write-Host ("原始尺寸 = {0} x {1}   格式 = {2}" -f $frame.PixelWidth, $frame.PixelHeight, $frame.Format)

$conv = New-Object System.Windows.Media.Imaging.FormatConvertedBitmap(
    $frame, [System.Windows.Media.PixelFormats]::Bgra32, $null, 0)
$w = $conv.PixelWidth
$h = $conv.PixelHeight
$stride = $w * 4
$buf = New-Object byte[] ($stride * $h)
$conv.CopyPixels($buf, $stride, 0)
[IO.File]::WriteAllBytes($out, $buf)
Write-Host ("已写出裸 BGRA：{0}（{1} 字节，{2}x{3}）" -f $out, $buf.Length, $w, $h)

# 直方图：按"不透明像素"统计出现最多的颜色，**按 BGRA 原样打印**
$counts = @{}
for ($i = 0; $i -lt $buf.Length; $i += 4) {
    if ($buf[$i + 3] -eq 0) { continue }
    $k = '{0:X2}{1:X2}{2:X2}' -f $buf[$i], $buf[$i + 1], $buf[$i + 2]
    if ($counts.ContainsKey($k)) { $counts[$k]++ } else { $counts[$k] = 1 }
}
Write-Host '裸字节直方图（顺序 = B,G,R —— 未做任何通道交换）：'
$counts.GetEnumerator() | Sort-Object -Property Value -Descending | Select-Object -First 10 | ForEach-Object {
    Write-Host ("    {0}  x{1}" -f $_.Key, $_.Value)
}
