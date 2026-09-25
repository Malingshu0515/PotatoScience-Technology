# ============================================================
#  _zf65_precheck_run.ps1 —— 重跑一次"改前件重建是否忠实"的取证（结论留档给归档）
#  流程：apply（换进改前件）→ compileJava → compare（与 ZF64 成品 jar 的 class 逐字节比）
#        → restore（换回 ZF65 版本）→ build（把编译产物/成品恢复成 ZF65）
#  用法：
#    $sb=[scriptblock]::Create([IO.File]::ReadAllText('E:\PotatoST\build\zftools\_zf65_precheck_run.ps1',[Text.Encoding]::UTF8)); & $sb *> 日志
# ============================================================
$ErrorActionPreference = 'Continue'
$z = 'E:\PotatoST\build\zftools'
$env:PYTHONIOENCODING = 'utf-8'

Write-Output '==== 1) apply：把"反向重建的改前件"换进源码树 ===='
& python "$z\_zf65_precheck.py" apply

Write-Output ''
Write-Output '==== 2) compileJava ===='
cmd /c "cd /d E:\PotatoST && .\gradlew.bat compileJava --offline > E:\PotatoST\build\zftools\_zf65_precheck_build.log 2>&1"
Write-Output "compile exit=$LASTEXITCODE"

Write-Output ''
Write-Output '==== 3) compare：与 ZF64 成品 jar 里的同名 class 逐字节比 ===='
& python "$z\_zf65_precheck.py" compare
Write-Output "compare exit=$LASTEXITCODE"

Write-Output ''
Write-Output '==== 4) restore：换回 ZF65 版本 ===='
& python "$z\_zf65_precheck.py" restore

Write-Output ''
Write-Output '==== 5) build：把编译产物与成品恢复成 ZF65 ===='
cmd /c "cd /d E:\PotatoST && .\gradlew.bat build --offline > E:\PotatoST\build\zftools\_zf65_restore_build.log 2>&1"
Write-Output "build exit=$LASTEXITCODE"

$b = (Get-FileHash 'E:\PotatoST\build\libs\potato_s_t-0.10.jar' -Algorithm SHA1).Hash.ToLower()
$r = (Get-FileHash 'E:\PotatoST\release\PotatoST-0.10.jar' -Algorithm SHA1).Hash.ToLower()
Write-Output "build/libs jar  = $b"
Write-Output "release jar     = $r"
if ($b -eq $r) { Write-Output 'VERDICT: 恢复成功（build 产物与已发布的 ZF65 成品一致）' }
else { Write-Output 'VERDICT: **不一致，必须人工检查**' }
