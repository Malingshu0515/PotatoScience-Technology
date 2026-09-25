# _zf60_chunks.ps1 —— 看这 7 个 webp 里到底有没有 alpha（并强制按 Bgra32 再解一遍）
#
# 背景：WPF 的 BitmapDecoder 自己挑了个 Bgr32（无 alpha）的帧格式 —— 但预览图看着是白底，
#      两边矛盾，所以这里直接读 RIFF/WEBP 的块结构（ALPH / VP8X 的 alpha 标志位），
#      再强制转 Bgra32 看 alpha 通道是不是全 255。
$ErrorActionPreference = 'Stop'
Add-Type -AssemblyName PresentationCore

$att = 'C:\Users\Administrator\.dsh\attachments\v1\objects'
$files = @(
    @{ name = 'magnet';                 p = [IO.Path]::Combine($att, '3f', '3f7fe295da5e9757507e6f69e6c38617ba343234c45c5b18a7dea0af87359e79') },
    @{ name = 'iron_powder';            p = [IO.Path]::Combine($att, '27', '27afa5a54b5df6078c2b7c39d138b56ed08ba4898bbd6a9ab57baf8ce1234b91') },
    @{ name = 'titanium_ore';           p = [IO.Path]::Combine($att, '86', '86ceaa24e6b9d928abcd29d8f57cdb410946370bb57a7435df7e43bc86a32c76') },
    @{ name = 'deepslate_titanium_ore'; p = [IO.Path]::Combine($att, 'af', 'af1117c7ced2ec397e6f6f5296551528683741dad91a014df46400cec989a58b') },
    @{ name = 'raw_titanium';           p = [IO.Path]::Combine($att, 'e7', 'e75cbc409b6faae5eaf988d67d315737317291217184e651972b9bf140cda24e') },
    @{ name = 'titanium_powder';        p = [IO.Path]::Combine($att, '34', '341497c934cd39ad2bb5010428d76756e2e77f7696a4e91085e6ca0f1635067c') },
    @{ name = 'titanium_ingot';         p = [IO.Path]::Combine($att, '17', '176e4245fc68d07c397878471134ad91649fec5746a814c486378d0ee0565277') }
)

foreach ($f in $files) {
    $bytes = [IO.File]::ReadAllBytes($f.p)
    $chunks = @()
    $pos = 12
    while ($pos + 8 -le $bytes.Length) {
        $fourcc = [Text.Encoding]::ASCII.GetString($bytes, $pos, 4)
        $size = [BitConverter]::ToUInt32($bytes, $pos + 4)
        $chunks += ("{0}({1})" -f $fourcc, $size)
        $pos += 8 + $size + ($size % 2)
    }
    # 强制 Bgra32
    $uri = New-Object System.Uri($f.p)
    $dec = [System.Windows.Media.Imaging.BitmapDecoder]::Create($uri, 'None', 'OnLoad')
    $frame = $dec.Frames[0]
    $conv = New-Object System.Windows.Media.Imaging.FormatConvertedBitmap(
        $frame, [System.Windows.Media.PixelFormats]::Bgra32, $null, 0)
    $w = $conv.PixelWidth; $h = $conv.PixelHeight; $stride = $w * 4
    $buf = New-Object byte[] ($stride * $h)
    $conv.CopyPixels($buf, $stride, 0)
    $aMin = 255; $aMax = 0; $aZero = 0
    for ($i = 3; $i -lt $buf.Length; $i += 4) {
        $a = $buf[$i]
        if ($a -lt $aMin) { $aMin = $a }
        if ($a -gt $aMax) { $aMax = $a }
        if ($a -eq 0) { $aZero++ }
    }
    Write-Host ("{0,-24} 帧格式={1,-8} alpha: min={2,3} max={3,3} 全透明像素={4,5}  块: {5}" -f `
        $f.name, $frame.Format.ToString(), $aMin, $aMax, $aZero, ($chunks -join ' '))
    # 左上角像素（BGRA 顺序打印）
    Write-Host ("{0,-24} 左上角 BGRA = {1},{2},{3},{4}" -f '', $buf[0], $buf[1], $buf[2], $buf[3])
}
