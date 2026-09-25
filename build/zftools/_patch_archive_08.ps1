# 一次性档案补丁脚本（0.08 吞物品修复留档）
# 用法：$sb = [scriptblock]::Create([IO.File]::ReadAllText($路径, [Text.Encoding]::UTF8)); & $sb
$ErrorActionPreference = 'Stop'
$p = 'E:\PotatoST\docs\开发档案.md'
$t = [IO.File]::ReadAllText($p, [Text.Encoding]::UTF8)
$nl = if ($t -match "`r`n") { "`r`n" } else { "`n" }
Write-Output ("文件换行风格 = " + $(if ($nl -eq "`r`n") { 'CRLF' } else { 'LF' }))

$pairs = New-Object System.Collections.Generic.List[object]

# P1 头部版本
$pairs.Add(@{ n = 'P1 头部版本'
  o = '> 最后更新：2026-09-17　对应版本：**0.07-alpha**'
  w = '> 最后更新：2026-09-17　对应版本：**0.08-alpha**' })

# P2 版本表新增 0.08
$pairs.Add(@{ n = 'P2 版本表'
  o = '| **0.07-alpha** | **多语言**：`en_us` 对齐中文新措辞；**新增 `ja_jp` / `ru_ru`**（各 103 键） |'
  w = '| **0.07-alpha** | **多语言**：`en_us` 对齐中文新措辞；**新增 `ja_jp` / `ru_ru`**（各 103 键） |' + $nl +
      '| **0.08-alpha** | **修 BUG**：破坏机器时物品栏内容物被吞——灌装机 / 电解器 / 晒盐机 **三台全中** |' })

# P3 流水线表新增 ZF8
$pairs.Add(@{ n = 'P3 流水线表'
  o = '| ZF7 | `zf8_pre` | 0.07：语言——`en_us` 同步中文新措辞（氢气危险提示），新增 `ja_jp` / `ru_ru` | 见 §6.4 |'
  w = '| ZF7 | `zf8_pre` | 0.07：语言——`en_us` 同步中文新措辞（氢气危险提示），新增 `ja_jp` / `ru_ru` | 见 §6.4 |' + $nl +
      '| ZF8 | `zf9_pre` | 0.08：**修「破坏机器吞物品」**——新增 `MachineDrops`，三台机器补 `onRemove` 掉落 | 见 §4.13 |' })

# P4 新增 §4.13 雷区
$p4body = @(
  '### 4.13 【致命】自带物品栏的方块实体**不会**自动掉落内容物',
  '',
  '**根因**：原版**根本没有**「容器方块自动掉落内容」的通用机制。',
  '在反混淆映射里数一数就能证明：`ChestBlock` / `BarrelBlock` / `DispenserBlock` / `HopperBlock` /',
  '`ShulkerBoxBlock` / `AbstractFurnaceBlock` 的 `onRemove` 都只有 **2~3 行**，内容是同一个套路：',
  '',
  '```java',
  '@Override',
  'protected void onRemove(BlockState state, Level level, BlockPos pos, BlockState newState, boolean movedByPiston) {',
  '    Containers.dropContentsOnDestroy(state, newState, level, pos);',
  '    super.onRemove(state, level, pos, newState, movedByPiston);',
  '}',
  '```',
  '',
  '而 **`BaseEntityBlock` 并未覆写 `onRemove`**（映射里它只有 `<init>` / `codec` / `getRenderShape` /',
  '`triggerEvent` / `getMenuProvider` / `createTickerHelper`）。所以方块实体自己不处理 = 内容物直接消失。',
  '',
  '**第二层坑**：NeoForge 的 `ItemStackHandler` **不是**原版 `Container`，',
  '所以照抄 `Containers.dropContentsOnDestroy` 也**没用**——它内部判的是 `blockEntity instanceof Container`。',
  '',
  '**出血记录**：0.03 引入灌装机时埋下，0.04~0.07 一直存在，直到用户发现「灌装机里有物品时破坏，物品消失不掉落」。',
  '排查后确认**三台**机器全中（`FillingMachine` / `Electrolyzer` / `SaltDryer`，即全部带 `ItemStackHandler` 的方块）。',
  '全项目唯一做对的是 `LithiumBatteryBlock`（`onRemove` 里调 `handleRemoval` 均分能量）。',
  '',
  '**正确写法**（0.08 起统一走 `MachineDrops.dropInventory`）：',
  '',
  '```java',
  '@Override',
  'protected void onRemove(BlockState state, Level level, BlockPos pos, BlockState newState, boolean movedByPiston) {',
  '    if (!state.is(newState.getBlock()) && level.getBlockEntity(pos) instanceof XxxBlockEntity be) {',
  '        MachineDrops.dropInventory(level, pos, be.getInventory());',
  '    }',
  '    super.onRemove(state, level, pos, newState, movedByPiston);',
  '}',
  '```',
  '',
  '**两个必须记住的次序/边界**：',
  '1. **必须在 `super.onRemove` 之前取方块实体**——super 会把 BE 从区块里移除，之后 `getBlockEntity(pos)` 返回 `null`',
  '2. `MachineDrops` 内部对 `level.isClientSide` 直接返回，避免客户端生成幽灵掉落物',
  '',
  '**这条修好以后覆盖的破坏路径**：徒手/工具挖掉、爆炸、活塞推动、被其他方块替换（`!state.is(newState.getBlock())` 守卫）。',
  '',
  '**仍然会丢的东西（已知、未修、符合多数模组惯例）**：机器内部**流体**（灌装机 5×5000 mB、电解器 3 罐、',
  '泵缓冲、测试储罐）与**储能 FE** 在破坏时归零。原版没有「掉落流体」的概念，要保留得把流体写进掉落方块的 NBT。',
  '',
  '---'
) -join $nl
$pairs.Add(@{ n = 'P4 §4.13'
  o = '---' + $nl + $nl + '## 5. 版本与 [ZF] 流水线记录'
  w = $p4body + $nl + $nl + '## 5. 版本与 [ZF] 流水线记录' })

# P5 §6.2 补提醒
$p5body = @(
  '**⚠ 有物品栏的机器（用 `ItemStackHandler`）：必须自己写 `onRemove` 掉落内容，否则破坏即吞物品！**',
  '原版没有通用机制，见 §4.13；统一用 `MachineDrops.dropInventory(level, pos, be.getInventory())`，',
  '且**必须在 `super.onRemove` 之前**调用。',
  '',
  '### 6.3 加一个**合成配方**（0.05 实例）'
) -join $nl
$pairs.Add(@{ n = 'P5 §6.2'
  o = '### 6.3 加一个**合成配方**（0.05 实例）'
  w = $p5body })

# P6 §9 待办
$p6new = @(
  '- [x] ~~0.07 的 日/俄语言文件未在游戏内切语言目视过~~ → **已验证**（2026-09-17，用户确认「没问题」）',
  '- [ ] **0.08 的「吞物品」修复未在游戏内验证**——需实测：往 灌装机 / 电解器 / 晒盐机 里放物品 → 挖掉 →',
  '      物品应掉出来；**气罐里的气体也要还在**（验证 custom data 有没有跟着掉落物走）'
) -join $nl
$pairs.Add(@{ n = 'P6 §9'
  o = '- [ ] 0.07 的 **日/俄语言文件未在游戏内切语言目视过**。静态校验已全过'
  w = $p6new })

$fail = 0
foreach ($x in $pairs) {
  $c = ([regex]::Matches($t, [regex]::Escape($x.o))).Count
  if ($c -ne 1) { Write-Output ("  [FAIL] {0}: 锚点出现 {1} 次（须为 1）" -f $x.n, $c); $fail++; continue }
  $t = $t.Replace($x.o, $x.w)
  Write-Output ("  [OK]   {0}" -f $x.n)
}
if ($fail -gt 0) { Write-Output "有失败项，未写盘"; return }

[IO.File]::WriteAllText($p, $t, (New-Object System.Text.UTF8Encoding($false)))
$lines = $t -split "`r?`n"
$fences = @($lines | Where-Object { $_ -match '^\s*```' })
$open = $false; foreach ($l in $fences) { if ($l -match '^```\S') { $open = $true } else { $open = -not $open } }
Write-Output ("`n已写盘：{0} 行 / {1} B" -f $lines.Count, (Get-Item $p).Length)
Write-Output ("代码围栏 = {0} 个（偶数={1}）  配平 = {2}" -f $fences.Count, ($fences.Count % 2 -eq 0), (-not $open))
Write-Output ("二级章节 = " + (($lines | Where-Object { $_ -match '^## ' }).Count) + "   三级小节 = " + (($lines | Where-Object { $_ -match '^### ' }).Count))
