# ============================================================
#  _zf64_gates.ps1 —— ZF64 交付前七项门 + 各轮盘面复核
#  用法（本机执行策略 Restricted，用 scriptblock 绕开）：
#    $sb=[scriptblock]::Create([IO.File]::ReadAllText('E:\PotatoST\build\zftools\_zf64_gates.ps1',[Text.Encoding]::UTF8)); & $sb *> 日志
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
# ZF61：贴图体检（文件头是不是真 PNG / 尺寸 / 谁还在借原版贴图）
Run-Py  'TextureCheck.py'  'TextureCheck.py'  $null
# ⚠ JsonCheck.py **必须带目录**：不带参数它会"检查 0 个文件"然后退出 0（§4.32 记了这个坑）
Run-Py  'JsonCheck.py'     'JsonCheck.py'     @('E:\PotatoST\src\main\resources')
Run-Py  'SoundCheck.py'    'SoundCheck.py'    $null
Run-Py  'ZF54 verify'      '_zf54_verify.py'  $null
Run-Py  'ZF52 verify'      '_zf52_verify.py'  $null
Run-Py  'ZF55 verify'      '_zf55_verify.py'  $null
Run-Py  'ZF56 verify'      '_zf56_verify.py'  $null
Run-Py  'ZF57 verify'      '_zf57_verify.py'  $null
Run-Py  'ZF60 verify'      '_zf60_verify.py'  $null
# ZF64 本轮：JEI 说明行删除 / 进度箭头几何 / 电机声链路
Run-Py  'ZF64 verify'      '_zf64_verify.py'  $null

Write-Output ""
Write-Output "==================== 门结束 ===================="
