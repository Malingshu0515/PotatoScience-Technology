# ============================================================
#  _zf81_gates.ps1 —— ZF81（0.11 电解器 100 → 1000 FE/t）交付前门检查 + 往轮盘面复核 + 本轮校验
#  用法（本机执行策略 Restricted，用 scriptblock 绕开）：
#    $sb=[scriptblock]::Create([IO.File]::ReadAllText('E:\PotatoST\build\zftools\_zf81_gates.ps1',[Text.Encoding]::UTF8)); & $sb *> 日志
#
#  ⚠ 这个文件必须**整份写**（用文件工具），不许用 PowerShell 的字符串替换去改：
#     ZF81 第一版就是这么生的，结果有 6 个 Run 行被并进了注释里（那几道门压根没跑），
#     而且中文注释被写成了乱码。教训记进档案 §4.53。
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
# ⚠ 开关必须用哈希表按名字传（§4.38：@('-All') 是字符串位置参数，绑不到 [switch]）
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
# ZF69 的复现性脚本：数据源（桌面 zf69_pre）已被删进回收站 ⇒ 现在**响亮报 SKIP**（不再是假绿）
Run-Py  'ZF69 repro'       '_zf69_repro.py'   $null
Run-Py  'ZF69 texcount'    '_zf69_texcount.py' $null
Run-Py  'ZF70 verify'      '_zf70_verify.py'  $null
# ZF71 公告核对（**活体**：公告里的数必须等于当前代码/资源）
Run-Py  'ZF71 verify'      '_zf71_verify.py'  $null
Run-Py  'ZF72 vanilla evidence' '_zf72_vanilla_evidence.py' $null
Run-Py  'ZF72 verify'      '_zf72_verify.py'  $null
# ZF73：① 复现性（除新增那一份，其余配方逐字节没动）② 交付校验
Run-Py  'ZF73 repro'       '_zf73_repro.py'   $null
Run-Py  'ZF73 verify'      '_zf73_verify.py'  $null
# ZF74：流体 c: 通用标签
Run-Py  'ZF74 verify'      '_zf74_verify.py'  $null
# ZF75(+ZF76/ZF77 扩到 38 项)：世界生成（地表油田 + 海洋油田群系）
Run-Py  'ZF75 verify'      '_zf75_verify.py'  $null
# ZF78：分馏塔三件套（结构 / 控制器 / 操作器 / 4 流体 / 沥青 / 大 UI）
Run-Py  'ZF78 verify'      '_zf78_verify.py'  $null
# ZF79：柏油块（12 沥青 → 1 块）+ 电力高炉新材质 + 灌装机手放门禁 + JEI 箭头
Run-Py  'ZF79 verify'      '_zf79_verify.py'  $null
# ZF80：灌装机手倒（拿容器右键倒进罐）+ 逐槽诊断（空手 Shift 右键）
Run-Py  'ZF80 verify'      '_zf80_verify.py'  $null
# ZF81 本轮：电解器能耗 100 → 1000 FE/t
Run-Py  'ZF81 verify'      '_zf81_verify.py'  $null
# 反证台：19 刀（含 ZF80 五刀 + ZF81 两刀）—— 每刀都要被抓到、逐刀还原回全绿
Run-Py  'falsify'          '_zf78_falsify.py' $null

Write-Output ""
Write-Output "==================== 门结束 ===================="
