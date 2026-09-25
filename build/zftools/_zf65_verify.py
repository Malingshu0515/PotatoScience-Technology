# -*- coding: utf-8 -*-
"""_zf65_verify.py —— ZF65 常驻校验：**运行中标记不许卡住**

用户 2026-09-19 实测报的 bug：「冶炼中的合金炉被破坏，循环音效还在响，重新创建刷新一下才好」。
根因：挖掉外壳任意一格走 `AlloySmelterPartBlock.onRemove → master.disassemble(pos) → setFormed(false)`，
**控制器方块本身还在**；ZF64 那版把 `running` 的清零写在 `craftTick()` 里，而 `formed == false` 之后
每 tick 都走不到 `craftTick()` ⇒ `running` 永远停在 true ⇒ 客户端一直收到"在烧" ⇒ 循环音停不下来。

所以这一轮钉两条不变式（外加公共件的两条防呆）：

  ① **`serverTickBody()` 里必须在 `if (this.formed)` 分支之前就把 `running` 清零**
     —— 缺了它 / 挪进分支里 = 又变成"拆解之后停不下来"；
  ② **真实 ticker 跑一 tick 之后，`disassemble()` 过的机器 `running` 必须是假**
     （这条在探针 `AlloySoundStopCheck` 里量，本脚本只做静态那半 + 回归）；
  ③ 公共件 `MachineRunningSound`：从 ACTIVE 表里摘掉实例之前必须先 `stop()`；
     `tick()` 除了 `isRemoved()` 还要看"那格还是不是这个方块实体"（挖掉就没有 tick 来纠正了）。

退出码 0 = 全过。
"""
import io
import os
import re
import sys

ROOT = r"E:\PotatoST"
MOD = os.path.join(ROOT, r"src\main\java\com\potatost\mod")

fails = []


def check(ok, msg):
    print(("  [OK]   " if ok else "  [FAIL] ") + msg)
    if not ok:
        fails.append(msg)
    return ok


def read(path):
    with io.open(path, encoding="utf-8") as fh:
        return fh.read()


def body_of(src, method):
    # 不限定修饰符：craftTick() 是**包级可见**（故意留给探针直连调），写成 private 开头匹配不到
    m = re.search(r"\n    [^\n]*\b%s\s*\([^)]*\)\s*\{" % re.escape(method), src)
    if not m:
        return ""
    start = m.end()
    end = src.find("\n    }", start)
    return src[start:end if end > 0 else len(src)]


be = read(os.path.join(MOD, "AlloySmelterBlockEntity.java"))
snd = read(os.path.join(MOD, r"client\sound\MachineRunningSound.java"))

print("== ① running 的每 tick 清零必须在 formed 分支之外/之前 ==")
tick_body = body_of(be, "serverTickBody")
check(bool(tick_body), "找到 serverTickBody() 正文")
i_reset = tick_body.find("this.running = false;")
i_formed = tick_body.find("if (this.formed)")
check(i_reset >= 0, "serverTickBody() 里有 `this.running = false;`（拆解那条路不经过 craftTick）")
check(i_formed >= 0, "serverTickBody() 里有成型分支 `if (this.formed)`")
check(i_reset >= 0 and i_formed >= 0 and i_reset < i_formed,
      "它在成型分支**之前**（@%d < @%d）—— 挪进分支里就等于没修" % (i_reset, i_formed))

print()
print("== ② craftTick 仍然只在『真的推进』时才置真 ==")
craft = body_of(be, "craftTick")
check("this.running = true;" in craft, "craftTick() 里扣电推进之后置真")
i_true = craft.find("this.running = true;")
i_energy = craft.find("this.energy -= ENERGY_PER_TICK;")
check(i_energy >= 0 and i_true > i_energy, "置真在扣电之后（不是『有配方就算在烧』）")

print()
print("== ③ 公共件 MachineRunningSound 的两条防呆 ==")
check(re.search(r"s\.stop\(\);\s*\n\s*ACTIVE\.remove\(key\)", snd) is not None,
      "从 ACTIVE 摘掉旧实例之前先 stop()（删表 ≠ 消音）")
check("level.getBlockEntity(this.pos) != this.be" in snd,
      "tick() 除了 isRemoved() 还看『那格是不是还是这个 BE』")
check("level.isLoaded(this.pos)" in snd,
      "...并且用 isLoaded 挡住『区块没加载』的误判（否则走远一点就静音）")

print()
print("== ④ 回归：ZF64 那条链子不许被这次修改弄坏 ==")
check(re.search(r"clientTick\(\)\s*\{\s*MachineRunningSound\.update\(this, this\.running,"
                r"\s*ModSounds\.ALLOY_SMELTER_RUNNING\.get\(\)\);", be) is not None,
      "客户端仍然按 running 驱动循环音")
check(re.search(r"tag\.putBoolean\(\"running\"", be) is not None, "running 仍然进 NBT（更新包要带）")
check(re.search(r"if \(before != this\.running\) \{\s*sync\(\);", be) is not None,
      "serverTick 仍然只在翻转时发包")
check(re.search(r"private void serverTick\(\)\s*\{", be) is not None, "serverTick() 那层包装还在")

print()
print("失败项 = %d" % len(fails))
for m in fails:
    print("   - " + m)
sys.exit(1 if fails else 0)
