# ============================================================
#  _zf104_gates.ps1 —— ZF104（两套盔甲 + 星璨钢锭）交付前门检查
#  用法（本机执行策略 Restricted，用 scriptblock 绕过）：
#    $sb=[scriptblock]::Create([IO.File]::ReadAllText('E:\PotatoST\build\zftools\_zf104_gates.ps1',[Text.Encoding]::UTF8)); & $sb *> 日志
#
#  ⚠ 整份写（用文件工具），不让 PowerShell 字符串替换（§4.53）。跑完用 `_zf104_gatecount.py` 核段数。
#  ⚠ ZF104 相对 ZF102 多两段：`ZF104 verify` 与 `ZF104 falsify`
#    （脚本声明 60 段 + 门结束 = 日志 61 段）。
#  ⚠ 这段注释里的数字**以前就写错了**：ZF106 之后盘上其实是 **59** 段（注释写 61）。
#    ZF120 本轮再加两段（`ZF120 verify` + `ZF120 falsify`）⇒ **现在就 61 段** + 门结束 = 日志 62 段。
#    （数字以 `_zf104_gatecount.py` 现场数的为准 —— 它数的是这个文件里的 `Run-*` 行。）
#  ⚠ `Audit.ps1` 的 A 项在本轮**第一次真的抓到我**：`ModArmorMaterials` 里
#    一个 import 只在 javadoc 里出现 —— 该类已删。见 ZF104 那一行。
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
Run-Py  'ToolLint.py'      'ToolLint.py'      $null
Run-Ps1 'LangCheck.ps1'    'LangCheck.ps1'    $null
Run-Ps1 'RecipeCheck.ps1'  'RecipeCheck.ps1'  @{ All = $true }
Run-Py  'ModelCheck.py'    'ModelCheck.py'    $null
Run-Py  'TextureCheck.py'  'TextureCheck.py'  $null
Run-Py  'JsonCheck.py'     'JsonCheck.py'     @('E:\PotatoST\src\main\resources')
Run-Py  'SoundCheck.py'    'SoundCheck.py'    $null
Run-Py  'ZF54 verify'      '_zf54_verify.py'  $null
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
Run-Py  'ZF70 verify'      '_zf70_verify.py'  $null
Run-Py  'ZF71 verify'      '_zf71_verify.py'  $null
Run-Py  'ZF72 vanilla evidence' '_zf72_vanilla_evidence.py' $null
Run-Py  'ZF72 verify'      '_zf72_verify.py'  $null
Run-Py  'ZF73 repro'       '_zf73_repro.py'   $null
Run-Py  'ZF73 verify'      '_zf73_verify.py'  $null
Run-Py  'ZF74 verify'      '_zf74_verify.py'  $null
Run-Py  'ZF75 verify'      '_zf75_verify.py'  $null
Run-Py  'ZF78 verify'      '_zf78_verify.py'  $null
Run-Py  'ZF79 verify'      '_zf79_verify.py'  $null
Run-Py  'ZF80 verify'      '_zf80_verify.py'  $null
Run-Py  'ZF81 verify'      '_zf81_verify.py'  $null
Run-Py  'ZF82 verify'      '_zf82_verify.py'  $null
Run-Py  'ZF83 verify'      '_zf83_verify.py'  $null
Run-Py  'ZF84 verify'      '_zf84_verify.py'  $null
Run-Py  'ZF85 verify'      '_zf85_verify.py'  $null
Run-Py  'ZF86 verify'      '_zf86_verify.py'  $null
Run-Py  'ZF88 verify'      '_zf88_verify.py'  $null
Run-Py  'ZF89 verify'      '_zf89_verify.py'  $null
Run-Py  'ZF90 verify'      '_zf90_verify.py'  $null
Run-Py  'ZF91 verify'      '_zf91_verify.py'  $null
Run-Py  'ZF92 verify'      '_zf92_verify.py'  $null
Run-Py  'ZF93 verify'      '_zf93_verify.py'  $null
Run-Py  'ZF94 verify'      '_zf94_verify.py'  $null
Run-Py  'ZF94 obj diff'    '_zf94_diff.py'    $null
Run-Py  'ZF95 verify'      '_zf95_verify.py'  $null
Run-Py  'ZF96 verify'      '_zf96_verify.py'  $null
Run-Py  'ZF97 verify'      '_zf97_verify.py'  $null
Run-Py  'ZF98 verify'      '_zf98_verify.py'  $null
Run-Py  'ZF99 verify'      '_zf99_verify.py'  $null
Run-Py  'ZF100 recipe guard' '_zf100_recipe_guard.py' $null
Run-Py  'ZF100 verify'     '_zf100_verify.py' $null
Run-Py  'ZF101 verify'     '_zf101_verify.py' $null
Run-Py  'ZF102 verify'     '_zf102_verify.py' $null
# ZF104 本轮：两套盔甲 + 星璨钢锭（数值/材料/套装效果/虚空救援/四语言/贴图/标签）
Run-Py  'ZF104 verify'     '_zf103_verify.py' $null
# ZF106 本轮追加：8 张盔甲图纸（逐格对照原版铁套 + 材料 + 盘上总数）
Run-Py  'ZF106 recipes'    '_zf106_recipes_check.py' $null
# ZF120 本轮：振金套（下界合金数值 / 无限耐久 + 附魔光效 / 三条套装效果 / 借原版铁套 / 4 张锻造台配方）
Run-Py  'ZF120 verify'     '_zf120_verify.py' $null
# 本轮自己的反证刀：23 刀（K1~K23），每刀都必须被抓到，逐刀还原回全绿
Run-Py  'ZF120 falsify'    '_zf120_falsify.py' $null
# 本轮自己的反证刀：8 刀（K1~K8），每刀都必须被抓到，逐刀还原回全绿
Run-Py  'ZF104 falsify'    '_zf103_falsify.py' $null
# 反证刀（历史 77 刀）：每刀都要被抓到。逐刀还原回全绿
Run-Py  'falsify'          '_zf78_falsify.py' $null
# 门自己也要自证：段数 + 日志里不许有 traceback（§4.53 的兄弟）
Run-Py  'gatecount'        '_zf104_gatecount.py' $null

Write-Output ""
Write-Output "==================== 门结束 ===================="
