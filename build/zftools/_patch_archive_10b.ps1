# ============================================================
#  _patch_archive_10b.ps1 —— 0.10 档案补丁（微型粉碎机循环音）
#
#  用法：
#     $sb = [scriptblock]::Create([IO.File]::ReadAllText('E:\PotatoST\build\zftools\_patch_archive_10b.ps1', [Text.Encoding]::UTF8))
#     & $sb
#
#  纪律同 _patch_archive_10.ps1：锚点必须恰好 1 次，否则整份放弃、一个字节都不写；
#  写回 UTF8 无 BOM；刻意不调用 exit。
# ============================================================
$path = 'E:\PotatoST\docs\开发档案.md'
$raw = [IO.File]::ReadAllText($path, [Text.Encoding]::UTF8)
$before = $raw.Length

$pairs = @(
    @{
        old = '      [ ] 同一 tick 里多罐一起结束只响一声，不会叠成五声'
        new = @'
      [ ] 同一 tick 里多罐一起结束只响一声，不会叠成五声
- [ ] **0.10 微型粉碎机循环音未在游戏内验证**（6.45s 无缝循环，做法见 §6.5）：
      [ ] 开始粉碎 → 嗡嗡声起；粉碎结束 / 断电 / 红石关机 → 声音立刻停
      [ ] **走远到听不见、再走回来**，声音应能正常起停（不会卡住不停，也不会再也响不了）
      [ ] 循环接缝处不应有周期性"咔"或音量塌陷——这正是本次转码花力气处理的地方
      [ ] 把机器挖掉 → 声音立即停（`MachineRunningSound` 的清理逻辑）
      [ ] 多台粉碎机同时工作 → 各自独立响，不会互相顶掉
'@
    },
    @{
        old = 'python E:\PotatoST\build\zftools\MakeSfx.py <输入.mp3> <输出.ogg>
```
**单声道 44100 Hz Vorbis 是硬要求**（立体声在 MC 里不吃距离衰减；采样率不对会变速变调）。
脚本自动掐掉首尾静音 + 加淡入淡出，转完**回读打印包络**，确认"有声起点 = 0.00s"。
完整联动清单见 §6.5。'
        new = 'python E:\PotatoST\build\zftools\MakeSfx.py <输入.mp3> <输出.ogg>
# 循环音（机器运行时的嗡嗡声）：切稳态段 + 接缝交叉淡化 + 响度对齐
python E:\PotatoST\build\zftools\MakeSfx.py <输入.mp3> <输出.ogg> --loop --start 0.45 --end 7.30 --crossfade 400 --target-rms 0.10
```
**单声道 44100 Hz Vorbis 是硬要求**（立体声在 MC 里不吃距离衰减；采样率不对会变速变调）。
一次性音效会自动掐首尾静音 + 加淡入淡出；循环音反过来**绝不能有淡入淡出**，改做接缝交叉淡化。
两种模式转完都会**回读打印包络**（一次性音效看"有声起点 = 0.00s"，循环音看"接缝首尾差"）。
完整联动清单与循环音的四个坑见 §6.5。'
    },
    @{
        old = '+ **硅**物品 + **灌装机完成音效**。首轮产出 BUG（`insertItem` 静默失败吞产物，见 §4.14）→ 同日修复重发 | 见 §6.2 / §6.5 |'
        new = '+ **硅**物品 + **灌装机完成音效** + **微型粉碎机循环音**。首轮产出 BUG（`insertItem` 静默失败吞产物，见 §4.14）→ 同日修复重发 | 见 §6.2 / §6.5 |'
    }
)

$bad = 0
foreach ($p in $pairs) {
    $count = ([regex]::Matches($raw, [regex]::Escape($p.old))).Count
    if ($count -ne 1) {
        Write-Output ("  [FAIL] 锚点出现 {0} 次（应为 1 次）：{1}..." -f $count, $p.old.Substring(0, [Math]::Min(50, $p.old.Length)))
        $bad++
    }
}

if ($bad -gt 0) {
    Write-Output '锚点校验未通过，档案未改动。'
} else {
    foreach ($p in $pairs) { $raw = $raw.Replace($p.old, $p.new) }
    [IO.File]::WriteAllText($path, $raw, (New-Object Text.UTF8Encoding($false)))
    Write-Output ("  [OK]   3 处替换完成：{0} 字符 -> {1} 字符" -f $before, $raw.Length)
}
