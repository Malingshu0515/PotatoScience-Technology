# ============================================================
#  _zf55_gates.ps1 —— ZF55 交付前六项门（§11.1）
#  用法： pwsh -NoProfile -ExecutionPolicy Bypass -File build\zftools\_zf55_gates.ps1
#  （.ps1 直接跑会被执行策略挡，所以带 -ExecutionPolicy Bypass）
# ============================================================
$ErrorActionPreference = 'Continue'
$z = 'E:\PotatoST\build\zftools'
$env:PYTHONIOENCODING = 'utf-8'

function Run-Ps1([string]$name, [string]$file, [string[]]$extra) {
    Write-Output ""
    Write-Output "==================== $name ===================="
    $sb = [scriptblock]::Create([IO.File]::ReadAllText("$z\$file", [Text.Encoding]::UTF8))
    if ($extra) { & $sb @extra } else { & $sb }
}

function Run-Py([string]$name, [string]$file, [string[]]$extra) {
    Write-Output ""
    Write-Output "==================== $name ===================="
    if ($extra) { & python "$z\$file" @extra } else { & python "$z\$file" }
}

Run-Ps1 'Audit.ps1'        'Audit.ps1'        $null
Run-Ps1 'LangCheck.ps1'    'LangCheck.ps1'    $null
Run-Ps1 'RecipeCheck.ps1'  'RecipeCheck.ps1'  @('-All')
Run-Py  'ModelCheck.py'    'ModelCheck.py'    $null
# ⚠ JsonCheck.py **必须带目录**：不带参数它会"检查 0 个文件"然后退出 0（§4.32 记了这个坑）
Run-Py  'JsonCheck.py'     'JsonCheck.py'     @('E:\PotatoST\src\main\resources')
Run-Py  'SoundCheck.py'    'SoundCheck.py'    $null
Run-Py  'ZF55 verify'      '_zf55_verify.py'  $null

Write-Output ""
Write-Output "==================== 门结束 ===================="
