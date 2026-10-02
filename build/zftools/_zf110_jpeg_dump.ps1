# _zf110_jpeg_dump.ps1 —— decode the user's newly placed oil-bucket JPEG with .NET System.Drawing
#
# WHY .NET (not a hand-written decoder): the project's established practice from _zf83_plates.py --
#   the pixel dump is produced by .NET System.Drawing, i.e. "exactly what Explorer shows you".
#   _zf83 / _zf86 / _zf87 all use this same pipeline; this script keeps that convention.
#
# ⚠ THIS FILE IS DELIBERATELY PURE ASCII.
#   powershell.exe 5.1 reads a no-BOM .ps1 as the ANSI codepage (GBK on this box), which corrupts
#   any Chinese literal baked into the script. So every Chinese name is built at runtime from
#   UTF-16 code points via [char] -- the file itself stays 7-bit clean and is read identically
#   by both PowerShell 5.1 and pwsh 7.
#
# Read-only on the source image; only writes the pixel-dump JSON. Touches nothing in use.
$ErrorActionPreference = 'Stop'
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8
Add-Type -AssemblyName System.Drawing

# --- build the Chinese path segments from code points ---
# 0x7528 0x6237 0x7D20 0x6750 = U+7528 U+6237 U+7D20 U+6750  ->  "用户素材"
$u = -join ([char]0x7528, [char]0x6237, [char]0x7D20, [char]0x6750)
# 0x6CB9 0x6876 = U+6CB9 U+6876  ->  "油桶"
$oil = -join ([char]0x6CB9, [char]0x6876)

$src = 'E:\PotatoST\build\' + $u + '\' + $oil + '.jpg'
$out = 'E:\PotatoST\build\zftools\_zf110_oil_pixels.json'

Write-Host ("source : " + $src)
if (-not (Test-Path -LiteralPath $src)) { throw ("NOT FOUND: " + $src) }

$bytes = [System.IO.File]::ReadAllBytes($src)
$ms = New-Object System.IO.MemoryStream(,$bytes)
$img = [System.Drawing.Image]::FromStream($ms)
$bmp = New-Object System.Drawing.Bitmap($img)
$w = $bmp.Width; $h = $bmp.Height

$px = New-Object System.Collections.Generic.List[string]
for ($y = 0; $y -lt $h; $y++) {
  for ($x = 0; $x -lt $w; $x++) {
    $c = $bmp.GetPixel($x, $y)
    $px.Add("$($c.R),$($c.G),$($c.B),$($c.A)")
  }
}
$bmp.Dispose(); $img.Dispose(); $ms.Dispose()

$obj = [ordered]@{ 'w' = $w; 'h' = $h; 'src' = ($oil + '.jpg'); 'px' = $px }
$json = $obj | ConvertTo-Json -Depth 3 -Compress
[System.IO.File]::WriteAllText($out, $json, (New-Object System.Text.UTF8Encoding($false)))

Write-Host "size   = ${w}x${h}   pixels = $($px.Count)"
Write-Host "first4 = $($px[0..3] -join ' | ')"
Write-Host "json   = $out  ($((Get-Item $out).Length) B)"

$ramp = ' .:-=+*#%@'
Write-Host ""
for ($y = 0; $y -lt $h; $y++) {
  $line = ''
  for ($x = 0; $x -lt $w; $x++) {
    $p = $px[$y * $w + $x].Split(',')
    $lum = (0.299 * [int]$p[0] + 0.587 * [int]$p[1] + 0.114 * [int]$p[2]) / 255.0
    $line += $ramp[[int][math]::Floor($lum * ($ramp.Length - 1))]
  }
  Write-Host "  |$line|"
}
