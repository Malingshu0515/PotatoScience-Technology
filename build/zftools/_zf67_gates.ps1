# ============================================================
#  _zf67_gates.ps1 —— ZF67 交付前七项门 + 各轮盘面复核
#  用法（本机执行策略 Restricted，用 scriptblock 绕开）：
#    $sb=[scriptblock]::Create([IO.File]::ReadAllText('E:\PotatoST\build\zftools\_zf67_gates.ps1',[Text.Encoding]::UTF8)); & $sb *> 日志
# ============================================================
$ErrorActionPreference = 'Continue'
$z = 'E:\PotatoST\build\zftools'
$env:PYTHONIOENCODING = 'utf-8'

function Run-Ps1([string]$name, [string]$file, [hashtable]$named) {
    Write-Output ""
    Write-Output "==================== $name ===================="
    $sb = [scriptblock]::Create([IO.File]::ReadAllText("$z\$file", [Text.Encoding]::UTF8))
    if ($named) { & $sb @named } else { & $sb }
}

function Run-Py([string]$name, [string]$file, [string[]]$extra) {
    Write-Output ""
    Write-Output "==================== $name ===================="
    if ($extra) { & python "$z\$file" @extra } else { & python "$z\$file" }
}

Run-Ps1 'Audit.ps1'        'Audit.ps1'        $null
Run-Ps1 'LangCheck.ps1'    'LangCheck.ps1'    $null
# ⚠ 开关必须用哈希表按名字传（§4.38：@('-All') 是字符串位置参数，绑不到 [switch]，
#    那样 RecipeCheck 会"检查 0 个配方却打印全部通过"）。
Run-Ps1 'RecipeCheck.ps1'  'RecipeCheck.ps1'  @{ All = $true }
Run-Py  'ModelCheck.py'    'ModelCheck.py'    $null
Run-Py  'TextureCheck.py'  'TextureCheck.py'  $null
# ⚠ JsonCheck.py **必须带目录**：不带参数它会"检查 0 个文件"然后退出 0（§4.32）
Run-Py  'JsonCheck.py'     'JsonCheck.py'     @('E:\PotatoST\src\main\resources')
Run-Py  'SoundCheck.py'    'SoundCheck.py'    $null
Run-Py  'ZF54 verify'      '_zf54_verify.py'  $null
Run-Py  'ZF52 verify'      '_zf52_verify.py'  $null
Run-Py  'ZF55 verify'      '_zf55_verify.py'  $null
Run-Py  'ZF56 verify'      '_zf56_verify.py'  $null
Run-Py  'ZF57 verify'      '_zf57_verify.py'  $null
Run-Py  'ZF60 verify'      '_zf60_verify.py'  $null
Run-Py  'ZF64 verify'      '_zf64_verify.py'  $null
Run-Py  'ZF65 verify'      '_zf65_verify.py'  $null
Run-Py  'ZF66 verify'      '_zf66_verify.py'  $null
# ZF67 本轮：工具必须挂原版"能附魔"的物品标签
Run-Py  'ZF67 verify'      '_zf67_verify.py'  $null

Write-Output ""
Write-Output "==================== 门结束 ===================="
