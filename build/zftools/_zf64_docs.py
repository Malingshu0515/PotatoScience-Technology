# -*- coding: utf-8 -*-
"""_zf64_docs.py —— ZF64 档案落笔（JEI 说明行删除 / 进度箭头 / 合金炉循环电机声）"""
import io
import sys

DOC = r"E:\PotatoST\docs\开发档案.md"

ROW = u'''| ZF64 | **新建 `zf64_pre`**（10 个改前件：`MachineRecipes` / `AlloySmelterBlockEntity` / `AlloySmelterMenu` / `client/AlloySmelterScreen` / `sound/ModSounds` / `sounds.json` / 4 个 lang） | 0.10：**用户三件事一次做完**（原话：「所有的这种文字可以删掉 给玩家看没必要列出来 还占空间 不美观 然后就是正在熔炼什么的箭头（同时也是进度条）然后后面的是工作时的音效 如果不是单声道调为单声道」+ 一张 JEI 说明行的截图 + 一段 ogg 素材）。① **删掉 JEI 那条标签判定说明**（ZF62 我自己加的「输入按通用锭标签（c:ingots）判定：别的 mod 的铝锭/钛锭/银锭一样能用」）⇒ 合金炉那条配方只剩 **耗时 / 耗电** 两行，四语言的 `gui.potato_s_t.jei.tag_inputs` 键一并删掉（lang 203 → **202**）；**立规矩**：JEI 说明行只放客观数值（写进 §6.9）。② **合金炉界面加进度箭头**（"同时也是进度条"）：新写 `client/gui/parts/ProgressArrowPart.java`（零贴图、全 `gg.fill`；杆宽 = 横截面一半**且两侧留白相等**，箭头长 = 半个横截面宽 ⇒ 斜边 45°），挂在输入排与输出排之间那 24px 空档里（`ARROW_X/Y/W/H = 59/38/22/22`、中线 x=70 与两排槽位中线重合），菜单补 `getProgress()` / `getProgressMax()`（走既有的 `ContainerData[DATA_PROGRESS]`）。**朝向选向下**（这台机器输入排在上、输出排在下，朝右会指向消耗槽），部件两种朝向都支持，要改只动界面里一行。③ **运行中循环电机声**：素材是用户给的 freesound #453361，**原文件 44100 Hz 立体声 8.75s**、用户要求"不是单声道就转单声道" ⇒ `MakeSfx.py --loop --crossfade 400 --target-rms 0.10` 做成 **单声道 8.27s / RMS 0.1003 / 峰值 0.304 / 接缝首尾差 0.0008**；新增 `ModSounds.ALLOY_SMELTER_RUNNING` + `sounds.json`；BE 新增 **`running` 标记**（"这一 tick 真的扣电、推进了进度"才算 —— 断电停住就不响，与粉碎机/液压机一致），只在翻转时 `sync()`，`running` 写进 `saveAdditional`（`getUpdateTag` 才带得出去），`tick()` 拆双端、`clientTick()` 里一句 `MachineRunningSound.update(...)`。**验证**：探针 `AlloySoundCheck` 在真服务端 **22 项全 [OK]**（注册表/双端 ticker/成型机器上的 running 语义：没电不响、真实 ticker 走一遍响、断电停住进度不丢、原料拿走归零、更新包读回来、`ContainerData` 三个索引）；新写常驻 `_zf64_verify.py`（**48 项**：JEI 文字清干净 + ogg 规格 + 箭头几何按像素算不压槽位/能量条/在面板内/中线重合 + Python 复刻出预览图 `build/zftools/zf64_arrow_preview.png`）。反证 3 处：`ARROW_Y=30` ⇒ **2 FAIL**（压到 in1/in2/in3）、`--ogg` 指向原立体声素材 ⇒ **2 FAIL**（非单声道 + RMS 0.0448）、拿掉自愈的 `!disassembling` 守卫 ⇒ `_zf56_verify.py` **精确 1 FAIL**。⚠ **一笔自己的失误**：ZF64 把 `serverTick()` 拆成两层（正文挪进 `serverTickBody()`）⇒ ZF56 那道常驻校验按字面量切方法段，**当场报 2 条假 FAIL**；修法是"修锚点、不放宽断言"并**再反证一次**（§4.36） | 见 §9 |'''

OLD9 = u'''- [ ] **ZF62：等用户试合金炉配方**（成品 `d62a8e42…`）。铝锭 + 钛锭 + 银锭各 1 → 1 轻质钛合金，
      30 秒、5800 FE/t（**一件 348 万 FE**）。要看的：① 三样锭放进 5 个输入槽能不能开工；
      ② 30 秒后产出 1 个、原料各扣 1；③ **中途断电**（拔掉发电机）进度会不会白费 —— 现在的行为是
      **停住不清零**；④ JEI 里有没有「合金炉主控」这一页。'''

NEW9 = u'''- [ ] **ZF62/ZF63/ZF64：等用户试合金炉**（ZF64 后的新成品是你手上这一版）。铝锭 + 钛锭 + 银锭各 1 →
      1 轻质钛合金，30 秒、**800 FE/t**（一件 **480,000 FE**）。要看的：① 三样锭放进 5 个输入槽能不能开工、
      30 秒后产出 1 个、原料各扣 1；② **中途断电**时进度**停住不清零**；③ 界面里**那支向下的箭头**（同时是进度条）
      跟着走、开工时填色；④ **开工有电机声、断电/停工没声**（音效要耳朵验，服务端探针只能验到"标记对不对"）。
      ✅ 用户 2026-09-19 的截图**侧证**了 JEI 那一页在（截的就是「合金炉主控」配方的说明行）——
      但他没说过配方烧通没有，所以这条不勾掉。
- [ ] **ZF64 待你定：箭头朝向**。现在是**向下**（输入排在上、输出排在下，朝右会指向消耗槽那一侧）。
      想跟 JEI 那支一样朝右的话说一声，改一行（`AlloySmelterScreen` 里把 `Direction.DOWN` 换 `RIGHT`，
      位置常量一起挪）。预览图在 `build/zftools/zf64_arrow_preview.png`（Python 复刻同一套算式的示意图）。'''

SND_ANCHOR = u'''现成公共件：`client/sound/MachineRunningSound.java`（自带按坐标去重、方块被拆自动清理），用法一行：
`MachineRunningSound.update(be, be.isRunning(), ModSounds.XXX_RUNNING.get());`'''

SND_ADD = SND_ANCHOR + u'''

> **ZF64 实例（合金冶炼炉）**：素材是**用户直接给的**（`eaglaxle-background-motor-sound-453361`，freesound #453361），
> 原文件 **44100 Hz / 立体声 / 8.75s / RMS 0.0428** —— 立体声在 MC 里不吃距离衰减，用户的要求也很明确：
> 「如果不是单声道调为单声道」。一条命令搞定：
> `python build\\zftools\\MakeSfx.py <素材> src\\main\\resources\\assets\\potato_s_t\\sounds\\alloy_smelter_running.ogg --loop --crossfade 400 --target-rms 0.10`
> ⇒ 成品 **单声道 44100 Hz / 8.27s / RMS 0.1003 / 峰值 0.304 / 接缝首尾差 0.0008**（素材首尾本来就淡到接近 0）。
> 触发侧照上面第 4 条：BE 加 `running` 标记（**"这一 tick 真的扣电、推进了进度"才算**）、只在翻转时 `sync()`、
> `running` 必须写进 `saveAdditional()`（`getUpdateTag` 带的就是它），`clientTick()` 里调一次公共件。'''

JEI_ANCHOR = u'''> ⚠ **这些计算必须是 `static` 方法** —— `super(...)` 要在实例字段之前求值，
> 没法先算好再传给父类。'''

JEI_ADD = JEI_ANCHOR + u'''

**说明行只放客观数值（0.10 ZF64 立的规矩）**：分类底部那几行**只写"耗时 / 耗电 / 产出范围"**这类客观数值。
ZF62 我往合金炉那条配方上加过一行「输入按通用锭标签（c:ingots）判定：别的 mod 的铝锭/钛锭/银锭一样能用」，
用户看到 JEI 截图后说：**「所有的这种文字可以删掉 给玩家看没必要列出来 还占空间 不美观」** ⇒
那一行连同四语言的 `gui.potato_s_t.jei.tag_inputs` 键一起删掉（lang 203 → 202）。
**"配方怎么判定"是实现细节，玩家不用读**；想加解释性说明行时先问一句，别自己加（同 §6.10 ⑩ 那条教训）。'''

M4_ANCHOR = u'''> 想要标准像素材质就导出成 16×16 再发一次；想保留高清也可以就这么放着。

## 5. 版本与 [ZF] 流水线记录'''

M4_ADD = u'''> 想要标准像素材质就导出成 16×16 再发一次；想保留高清也可以就这么放着。

### 4.36 【方法论】改名会把**老的检查器**打成假 FAIL —— 修锚点，别放宽断言（0.10 ZF64）

ZF64 把 `AlloySmelterBlockEntity.serverTick()` 拆成两层：外层只负责"运行 ⇄ 停止"翻转时发包，
原正文整段挪进新的 `serverTickBody()`。**逻辑一个字没动**，可 ZF56 那道常驻校验**当场报 2 条 FAIL**
（`serverTick 里每秒自愈一次` / `自愈避开拆解途中`）—— 它把源码按字面量 `private void serverTick()`
切段再在段内找那两句，切到的只剩外层那 6 行空壳。

本项目里"按方法名/文本切段"的检查器到处都是（`_zf52/_zf55/_zf56/_zf57/_zf60_verify.py`），
**所以重构方法之前就要预判它**。三条做法：

1. **修锚点，不放宽断言**：改成"有 `serverTickBody()` 就锚它，否则锚 `serverTick()`"，
   两句断言**原样保留**（不是删掉、也不是退化成"整份文件里出现过"）；
2. **修完必须再反证一次**：手动拿掉自愈那句 `!this.disassembling` 守卫 ⇒ 该检查**精确 1 FAIL**
   （`[FAIL] 自愈避开拆解途中`）—— 证明换了锚点后它**仍然能失败**（对照 §4.30：不能失败的检查等于没检查）；
3. 报账要写清楚：**这是我自己重构引起的假 FAIL，不是新 bug**；但也**绝不能"看到 FAIL 就去改检查"** ——
   先确认逻辑真的没变（这次是"原正文整体搬家"，属性成立），再动检查器。

## 5. 版本与 [ZF] 流水线记录'''


def main():
    text = io.open(DOC, encoding="utf-8").read()
    before = len(text)
    problems = []

    lines = text.split(u"\n")
    out = []
    added = False
    for line in lines:
        out.append(line)
        if line.startswith(u"| ZF63 |") and not added:
            out.append(ROW)
            added = True
    if not added:
        problems.append(u"没找到 ZF63 行")
    text = u"\n".join(out)

    for name, old, new in ((u"§9 ZF62 待验条", OLD9, NEW9),
                           (u"§6.5 公共件段", SND_ANCHOR, SND_ADD),
                           (u"§6.9 static 提示段", JEI_ANCHOR, JEI_ADD),
                           (u"§4.35 尾 -> §5 之间", M4_ANCHOR, M4_ADD)):
        n = text.count(old)
        if n != 1:
            problems.append(u"%s 锚点命中 %d 次（应为 1）" % (name, n))
        else:
            text = text.replace(old, new, 1)

    if problems:
        print(u"有失败项，**不落盘**：")
        for p in problems:
            print(u"  !! " + p)
        return 1

    io.open(DOC, "w", encoding="utf-8", newline="\n").write(text)
    print(u"字数 %d -> %d（+%d）" % (before, len(text), len(text) - before))
    print(u"§5 ZF64 行 + §9 两条 + §6.5 音效实例 + §6.9 JEI 规矩 + §4.36 已写入")
    return 0


if __name__ == "__main__":
    sys.exit(main())
