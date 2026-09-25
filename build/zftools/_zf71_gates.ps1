# ============================================================
#  _zf71_gates.ps1 —— ZF71 交付前门检查（**文档轮：不动 jar**）+ 各轮盘面复核 + 本轮校验
#  用法（本机执行策略 Restricted，用 scriptblock 绕开）：
#    $sb=[scriptblock]::Create([IO.File]::ReadAllText('E:\PotatoST\build\zftools\_zf71_gates.ps1',[Text.Encoding]::UTF8)); & $sb *> 日志
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
# 第 9 道门：工具脚本自检（语法 + 阶段脚本硬规矩）—— 放最前面，语法错早发现
Run-Py  'ToolLint.py'      'ToolLint.py'      $null
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
Run-Py  'ZF67 verify'      '_zf67_verify.py'  $null
Run-Py  'ZF69 verify'      '_zf69_verify.py'  $null
Run-Py  'ZF69 repro'       '_zf69_repro.py'   $null
Run-Py  'ZF69 texcount'    '_zf69_texcount.py' $null
# ZF70：三个进度（含 requirements 的「和」必须是两组 —— §4.42）
Run-Py  'ZF70 verify'      '_zf70_verify.py'  $null
# ZF71 本轮：英文公告的**事实核对**（公告里每个数 == 代码常量；本轮不动 jar）
Run-Py  'ZF71 verify'      '_zf71_verify.py'  $null

Write-Output ""
Write-Output "==================== 门结束 ===================="
