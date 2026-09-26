# _zf140_jpeg_dump.ps1 -- decode a JPEG to raw 32bpp pixels with .NET System.Drawing.
#
# WHY .NET and not a hand-written decoder: this project has decoded every JPEG it ever
# received this way since _zf83 ("exactly what Explorer shows you"), see _zf110_jpeg_dump.ps1.
# The one difference here is LockBits + Marshal.Copy instead of GetPixel-per-pixel:
# the black-hole source is 690x1227 = 846630 pixels, and GetPixel would crawl.
#
# ⚠ THIS FILE IS DELIBERATELY PURE ASCII: powershell.exe 5.1 reads a no-BOM .ps1 as the
#   ANSI codepage (GBK here) and would corrupt any Chinese literal. Callers pass paths in.
#
# Read-only on the source image; writes <Out> = raw BGRA, top-down, Stride*Height bytes,
# and prints "W H STRIDE" on stdout so the Python side can reshape without guessing.
param(
  [Parameter(Mandatory = $true)][string]$Src,
  [Parameter(Mandatory = $true)][string]$Out
)
$ErrorActionPreference = 'Stop'
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8
Add-Type -AssemblyName System.Drawing

if (-not (Test-Path -LiteralPath $Src)) { throw ("NOT FOUND: " + $Src) }

$bytes = [System.IO.File]::ReadAllBytes($Src)
$ms = New-Object System.IO.MemoryStream(, $bytes)
$img = [System.Drawing.Image]::FromStream($ms)

# Re-draw onto a known-format bitmap: Image.FromStream hands back whatever the codec felt
# like (24bppRgb for a plain JPEG); Format32bppArgb makes the byte layout unambiguous.
$bmp = New-Object System.Drawing.Bitmap($img.Width, $img.Height, [System.Drawing.Imaging.PixelFormat]::Format32bppArgb)
$g = [System.Drawing.Graphics]::FromImage($bmp)
$g.DrawImage($img, 0, 0, $img.Width, $img.Height)
$g.Dispose()

$w = $bmp.Width
$h = $bmp.Height
$rect = New-Object System.Drawing.Rectangle(0, 0, $w, $h)
$data = $bmp.LockBits($rect, [System.Drawing.Imaging.ImageLockMode]::ReadOnly, [System.Drawing.Imaging.PixelFormat]::Format32bppArgb)
$stride = $data.Stride
$buf = New-Object byte[] ($stride * $h)
[System.Runtime.InteropServices.Marshal]::Copy($data.Scan0, $buf, 0, $buf.Length)
$bmp.UnlockBits($data)
$bmp.Dispose(); $img.Dispose(); $ms.Dispose()

[System.IO.File]::WriteAllBytes($Out, $buf)
Write-Host ("W H STRIDE = {0} {1} {2}   bytes = {3}" -f $w, $h, $stride, $buf.Length)
Write-Host ("raw = " + $Out)
