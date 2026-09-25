# ZF35：把用户给的 webp 素材解成裸像素（WPF BitmapDecoder → Bgra32 → CopyPixels）
# 用法：pwsh -File _zf35_decode.ps1 <输入路径(任意扩展名)> <输出.rgba>
#
# ⚠ §4.23 的教训：**先打印原始字节再谈通道顺序**，别靠文件名/扩展名猜。
#   本脚本只负责"解出来并打印"，怎么解释通道由人看了字节再定。
param(
    [Parameter(Mandatory = $true)][string]$In,
    [Parameter(Mandatory = $true)][string]$Out
)

$ErrorActionPreference = 'Stop'
Add-Type -AssemblyName PresentationCore

$fs = [IO.File]::OpenRead($In)
try {
    $dec = [Windows.Media.Imaging.BitmapDecoder]::Create($fs, 'None', 'OnLoad')
    $frame = $dec.Frames[0]
    $conv = New-Object Windows.Media.Imaging.FormatConvertedBitmap(
        $frame, [Windows.Media.PixelFormats]::Bgra32, $null, 0)
    $w = $conv.PixelWidth
    $h = $conv.PixelHeight
    $stride = $w * 4
    $buf = New-Object byte[] ($stride * $h)
    $conv.CopyPixels($buf, $stride, 0)
    [IO.File]::WriteAllBytes($Out, $buf)
    Write-Output ("尺寸 = {0}x{1}   裸像素 {2} 字节 -> {3}" -f $w, $h, $buf.Length, $Out)

    # ---- 原始字节打印（不做任何解释、不做任何变换）----
    Write-Output "原始字节抽样（每 4 字节一组，按文件顺序原样打印）："
    $samples = @(
        @{ n = '左上角 (0,0)';           i = 0 },
        @{ n = '左中 (0,h/2)';           i = ([int]($h / 2) * $w) * 4 },
        @{ n = '正中 (w/2,h/2)';         i = (([int]($h / 2) * $w) + [int]($w / 2)) * 4 },
        @{ n = '正中偏内 (w/2-2,h/2)';   i = (([int]($h / 2) * $w) + [int]($w / 2) - 2) * 4 },
        @{ n = '正上 (w/2, h/2-12)';     i = (([int]($h / 2) - 12) * $w + [int]($w / 2)) * 4 }
    )
    foreach ($s in $samples) {
        $i = $s.i
        Write-Output ("  {0,-22} = ({1},{2},{3},{4})" -f $s.n, $buf[$i], $buf[$i + 1], $buf[$i + 2], $buf[$i + 3])
    }

    # 找"最饱和的不透明像素"——原样打印它的 4 个字节
    $best = -1; $bestSat = -1
    for ($i = 0; $i -lt $buf.Length; $i += 4) {
        if ($buf[$i + 3] -lt 200) { continue }
        $mx = [Math]::Max($buf[$i], [Math]::Max($buf[$i + 1], $buf[$i + 2]))
        $mn = [Math]::Min($buf[$i], [Math]::Min($buf[$i + 1], $buf[$i + 2]))
        if (($mx - $mn) -gt $bestSat) { $bestSat = $mx - $mn; $best = $i }
    }
    Write-Output ("最饱和不透明像素（字节序原样）= ({0},{1},{2},{3})  饱和度={4}" -f `
        $buf[$best], $buf[$best + 1], $buf[$best + 2], $buf[$best + 3], $bestSat)
    Write-Output "  ⇒ 按 R,G,B,A 读 = ($($buf[$best]),$($buf[$best+1]),$($buf[$best+2]))"
    Write-Output "  ⇒ 按 B,G,R,A 读 = ($($buf[$best+2]),$($buf[$best+1]),$($buf[$best]))"
}
finally {
    $fs.Dispose()
}
