# 0.09 档案补丁：版本记录 + §11 代码标准
$ErrorActionPreference = 'Stop'
$p = 'E:\PotatoST\docs\开发档案.md'
$t = [IO.File]::ReadAllText($p, [Text.Encoding]::UTF8)
$nl = if ($t -match "`r`n") { "`r`n" } else { "`n" }

$pairs = New-Object System.Collections.Generic.List[object]

$pairs.Add(@{ n = 'P1 头部版本'
  o = '> 最后更新：2026-09-17　对应版本：**0.08-alpha**'
  w = '> 最后更新：2026-09-17　对应版本：**0.09-alpha**' })

$pairs.Add(@{ n = 'P2 版本表'
  o = '| **0.08-alpha** | **修 BUG**：破坏机器时物品栏内容物被吞——灌装机 / 电解器 / 晒盐机 **三台全中** |'
  w = '| **0.08-alpha** | **修 BUG**：破坏机器时物品栏内容物被吞——灌装机 / 电解器 / 晒盐机 **三台全中** |' + $nl +
      '| **0.09-alpha** | **代码质量**：提取 `MachineEnergyStorage`（去掉 3 份重复匿名实现）、清理未用导入、建立可执行代码标准（§11） |' })

$pairs.Add(@{ n = 'P3 流水线表'
  o = '| ZF8 | `zf9_pre` | 0.08：**修「破坏机器吞物品」**——新增 `MachineDrops`，三台机器补 `onRemove` 掉落 | 见 §4.13 |'
  w = '| ZF8 | `zf9_pre` | 0.08：**修「破坏机器吞物品」**——新增 `MachineDrops`，三台机器补 `onRemove` 掉落 | 见 §4.13 |' + $nl +
      '| ZF9 | （未单独备份） | 0.09：代码审计 + `MachineEnergyStorage` 提取 + **建立代码标准** | 见 §11 |' })

# ---------- §11 代码标准 ----------
$s11 = @(
  '',
  '---',
  '',
  '## 11. 代码标准（0.09 起执行）',
  '',
  '> 散文标准会腐烂，所以本节规则**全部由 `build\zftools\Audit.ps1` 机械检查**。',
  '> 交付前跑一遍，**失败项必须先修再打包**。',
  '',
  '### 11.1 交付前必跑的四个检查（一个都不能跳）',
  '',
  '| 脚本 | 查什么 | 通过标准 |',
  '|---|---|---|',
  '| `Audit.ps1` | 代码标准总检（下面 A~G 七项） | 失败项 = 0 |',
  '| `LangCheck.ps1` | 多语言键集 / 占位符签名 / BOM / 漏翻 | 失败项 = 0 |',
  '| `RecipeCheck.ps1` | 配方结构不变量（含空格空槽） | 失败项 = 0 |',
  '| `JsonCheck.java` | JSON 语法（真解析器，**不用** `ConvertFrom-Json` 下结论） | 全部 `[OK]` |',
  '',
  '跑法统一用 scriptblock 绕开 Restricted 执行策略：',
  '```powershell',
  '$sb = [scriptblock]::Create([IO.File]::ReadAllText($路径, [Text.Encoding]::UTF8))',
  '& $sb',
  '```',
  '',
  '### 11.2 硬性规则（违反 = Audit 失败，必须修）',
  '',
  '1. **未使用的 import 一律删除**（A 项）',
  '2. **带物品栏的方块实体，其方块必须实现 `onRemove` + `MachineDrops.dropInventory`**（B 项）',
  '   —— 这条是 0.08「吞物品」事故的机械化防线，见 §4.13',
  '3. **多语言键集必须完全一致且不带 BOM**（C 项）—— 见 §6.4',
  '4. **用户可见文本一律走 lang 文件**，Java 里不得出现硬编码中文（E 项）',
  '',
  '### 11.3 软性规则（Audit 报 WARN，人工判断）',
  '',
  '5. **匿名 `IEnergyStorage` 基准数 = 5**（D 项）。新机器优先用 `MachineEnergyStorage.receiveOnly(...)`；',
  '   只有语义确实不同（只放 / 无限 / 动态容量 / 按模式 / 按电量）才允许自己实现。',
  '   超基准说明又出现了复制粘贴。',
  '6. **文件 > 400 行提示拆分**（G 项）。当前偏大：`FluidPumpBlockEntity` 572 行、`ElectrolyzerBlockEntity` 403 行',
  '7. **不留 TODO / FIXME / XXX / HACK**（F 项）——要做就做，做不了就写进本档案的 §9',
  '',
  '### 11.4 复用优先（0.09 已建立的公共件，别再各写一份）',
  '',
  '| 公共件 | 用途 | 别再做的事 |',
  '|---|---|---|',
  '| `MachineEnergyStorage.receiveOnly(cap, get, set)` | 只收不放的能量缓冲 | 别再抄匿名 `IEnergyStorage`（`set` 里要调 `setChanged()`） |',
  '| `MachineDrops.dropInventory(level, pos, handler)` | 破坏机器时掉落物品栏 | 别忘 `onRemove`；且**必须在 `super.onRemove` 之前**调用 |',
  '| `MachineScreen` + `GuiPart` / `FluidTankPart` / `DynamicFluidTankPart` / `EnergyBarPart` / `ProgressBarPart` | 机器 GUI | 别在 Screen 里手画矩形/文字 |',
  '| `TankContents` | 高压气罐的 NBT 气体读写 | 别直接摸 `CUSTOM_DATA` |',
  '| `ModSounds` + `sounds.json` | 声音注册 | — |',
  '',
  '### 11.5 审计发现但**有意未改**的事项（都写清原因，别当成遗漏）',
  '',
  '1. **`PotatoSTClient.java:32` 的 `@EventBusSubscriber(bus = Bus.MOD)` 已过时但删不得。**',
  '   NeoForge 把 `bus()` 与 `Bus` 枚举标为**待移除**。但**不能简单删掉参数**：',
  '   客户端启动日志证明不写 `bus=` 会默认挂 **GAME** 总线——',
  '   `Subscribing @EventBusSubscriber class ...PotatoSTClient; to the mod event bus of mod potato_s_t`',
  '   而 `ModEvents` / `GasTankExplosionHandler`（不写 `bus=`）的是 `to the game event bus`。',
  '   删掉会让 Screen / 按键注册**静默失效**。',
  '   正确迁移 = 去掉该注解，改在模组构造器里 `modEventBus.addListener(...)` 显式注册。',
  '   未做原因：这种静默失效**只能真进游戏开一次机器 GUI 才能确认**，属于 §4.2 那一类。',
  '',
  '2. **8 个匿名 `IEnergyStorage` 中仍有 5 个没统一** —— 语义确实不同（发电机只放带电、创造线缆无限、',
  '   泵容量动态、端子按 mode、锂电池按电量），**有意保留**，理由写在 `MachineEnergyStorage` 类注释里。',
  '   强行套同一抽象会变成"参数汤"，比重复更难维护。',
  '',
  '3. **10 个机器方块仍有约 200 行模板重复**（`codec()` / `newBlockEntity()` / `getTicker()` /',
  '   `getRenderShape()` / `getDrops()` / `useWithoutItem()`）。可提取 `AbstractMachineBlock` 基类，',
  '   但属**设计级重构**：收益是去掉约 200 行，代价是 10 台机器全部要走一遍真启动验证。留作专项。',
  '',
  '4. **`getDrops` 覆写忽略了爆炸抗性** —— 11 个方块都写死 `return List.of(new ItemStack(this))`，',
  '   所以机器**被炸也必定掉落**（原版容器走 loot table 的 `survives_explosion`，有概率不掉）。',
  '   这是**行为差异不是 BUG**，且对玩家更友好；若要改回原版语义需要给 11 个方块补 loot table JSON。',
  '',
  '### 11.6 审计方法论（可复用）',
  '',
  '0.09 的做法值得复用：**先机械化扫描，再人工读**。具体手段：',
  '- 未用 import：把 `import` 行摘掉后在文件其余部分搜简单名',
  '- 跨文件重复行：按「长度 > 28 且出现在 ≥3 个文件」聚合，一眼看出复制粘贴',
  '- **反混淆映射里数方法行数**判断原版行为（§4.13 就是靠 `ChestBlock.onRemove` 只有 3 行破的案）',
  '- lang 键交叉引用：注意**误报来源**——注册名派生的键（`item.*` / `block.*` / `fluid.*`）',
  '  代码里本来就不会出现；还有 `msg(player, "…")` 这类自定义辅助方法、以及前缀拼接（`"mode.potato_s_t." + x`）',
  '- **拿上一个版本的 release jar 当快照做 diff**（见 §8）'
) -join $nl

$lastLine = '  确认等价再删除；并保证实例 mods 里同名 mod 的 jar **有且只有 1 个**'
$pairs.Add(@{ n = 'P4 §11 代码标准'
  o = $lastLine
  w = $lastLine + $nl + $s11 })

# ---------- §9 待办 ----------
$pairs.Add(@{ n = 'P5 §9 待办'
  o = '- [ ] **0.08 的「吞物品」修复未在游戏内验证**——需实测：往 灌装机 / 电解器 / 晒盐机 里放物品 → 挖掉 →'
  w = '- [ ] **0.09 的能量重构未在游戏内验证**——三台机器（灌装机 / 电解器 / 晒盐机）应仍能正常充电、能量条显示正常' + $nl +
      '- [ ] **0.09 遗留迁移**：`@EventBusSubscriber(bus = Bus.MOD)` 改成构造器里显式 `addListener`（见 §11.5，需真启动验证 GUI）' + $nl +
      '- [ ] **0.08 的「吞物品」修复未在游戏内验证**——需实测：往 灌装机 / 电解器 / 晒盐机 里放物品 → 挖掉 →' })

$fail = 0
foreach ($x in $pairs) {
    $c = ([regex]::Matches($t, [regex]::Escape($x.o))).Count
    if ($c -ne 1) { Write-Output ("  [FAIL] {0}: 锚点出现 {1} 次（须为 1）" -f $x.n, $c); $fail++; continue }
    $t = $t.Replace($x.o, $x.w)
    Write-Output ("  [OK]   {0}" -f $x.n)
}
if ($fail -gt 0) { Write-Output '有失败项，未写盘'; return }

[IO.File]::WriteAllText($p, $t, (New-Object System.Text.UTF8Encoding($false)))
$lines = $t -split "`r?`n"
$fences = @($lines | Where-Object { $_ -match '^\s*```' })
$open = $false; foreach ($l in $fences) { if ($l -match '^```\S') { $open = $true } else { $open = -not $open } }
Write-Output ("`n已写盘：{0} 行 / {1} B" -f $lines.Count, (Get-Item $p).Length)
Write-Output ("二级章节 = {0}   三级小节 = {1}   代码围栏 = {2}（配平={3}）" -f `
  (($lines | Where-Object { $_ -match '^## ' }).Count), `
  (($lines | Where-Object { $_ -match '^### ' }).Count), `
  $fences.Count, (-not $open))
