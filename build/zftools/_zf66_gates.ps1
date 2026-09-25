# ============================================================
#  _zf66_gates.ps1 —— ZF66 交付前七项门 + 各轮盘面复核
#  用法（本机执行策略 Restricted，用 scriptblock 绕开）：
#    $sb=[scriptblock]::Create([IO.File]::ReadAllText('E:\PotatoST\build\zftools\_zf66_gates.ps1',[Text.Encoding]::UTF8)); & $sb *> 日志
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
# ⚠ ZF66 修：开关**必须**用哈希表按名字传（@{ All = $true }）。
#    以前写成 @('-All') 是"把一个字符串当位置参数"传进去 ⇒ 绑不到 [switch]$All ⇒
#    RecipeCheck 拿 '-All' 当文件名、报一句 "Cannot find path '-All'"，
#    然后**检查 0 个配方却打印"结论: 全部通过"**（与 §4.32 记的 JsonCheck 那个坑同一族）。
Run-Ps1 'RecipeCheck.ps1'  'RecipeCheck.ps1'  @{ All = $true }
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
# ZF64：JEI 说明行删除 / 进度箭头几何 / 电机声链路
Run-Py  'ZF64 verify'      '_zf64_verify.py'  $null
# ZF65：运行中标记不许卡住（循环音停不下来的那个 bug）
Run-Py  'ZF65 verify'      '_zf65_verify.py'  $null
# ZF66 本轮：钛合金剑 / 钛合金镐（贴图/模型/配方/语言/Java 数值）
Run-Py  'ZF66 verify'      '_zf66_verify.py'  $null

Write-Output ""
Write-Output "==================== 门结束 ===================="
