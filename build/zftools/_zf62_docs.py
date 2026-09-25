# -*- coding: utf-8 -*-
"""_zf62_docs.py —— ZF62 档案落笔（合金炉第一条配方）

四处动：① §5 加 ZF62 行 ② §9 加待办 ③ 新增 §6.16「加一条合金炉配方要动哪几处」 ④ §12.17（这台机器终于有配方了）
"""
import io
import sys

DOC = r"E:\PotatoST\docs\开发档案.md"

ROW = u'''| ZF62 | **新建 `zf62_pre`**（5 个改前件：`ModItems` / `AlloySmelterBlockEntity` / `MachineRecipes` / `PotatoSTJeiPlugin` / `GenCommonTags.py`） | 0.10：**合金冶炼炉的第一条配方**（用户原话：「铝+钛+银在合金冶炼炉 30s 5800fe/t产出一个 轻质钛合金 用钛锭的贴图」）。① **新物品 `light_titanium_alloy` 轻质钛合金**：模型 layer0 直接指 `potato_s_t:item/titanium_ingot`（照用户说的"用钛锭的贴图"，不是漏贴图）；四语言名字；进创造页；按长期规则挂 `c:ingots` + `c:ingots/titanium_alloy` + 扁平 `c:titanium_alloy_ingots`（加进 `GenCommonTags.py` 的 ALLOYS 重跑生成，**不是手改 JSON**）；② **新写 `AlloySmelterRecipes.java`**（这台机器 ZF49 立起来时用户说"先不做配方"，一直空着）：Java 表 + 懒加载（§4.1 的静态初始化雷），输入一律走 `c:ingots/<材料>` 标签 ⇒ 别的 mod 的铝/钛/银锭一样能烧；③ **配方推进写进 BE**（`craftTick()`，包级可见**是故意的**：探针能直接连调 600 次）：没成型/没配方/产物放不下 ⇒ **进度归零**；**电不够 ⇒ 进度原地不动**（停电不该把做了 29 秒的活扔掉）；④ `energy`/`progress` 进 NBT，`progress` 进 ContainerData（GUI/探针都能读）；⑤ **ZF42 静态守卫**：`worstDemand = 5800 ≤ MAX_ENERGY 32768`（本机一次只做一份、不并行），越界时控制台直接喊（英文）；⑥ **JEI 顺带就有了**：`MachineRecipes` 加一条 + `PotatoSTJeiPlugin.MACHINES` 加一行 `alloy_smelter` + 图标 —— 插件本来就是按 `machineId` 自动出分类的，不用碰 JEI 代码（新说明行 `gui.potato_s_t.jei.tag_inputs` 四语言）。探针 `AlloyRecipeCheck` **22 项全 [OK]**：缺一样原料不开工且不扣电 / 600 tick 正好扣 **3,480,000 FE**（用恒等式 `起始余额+注入−结束余额` 算，第一版我算错了账、6 条假 FAIL）/ 产物 1 个、三种原料各扣 1 / **掉电时进度停住不清零** / 拿掉原料才归零 / 产物堵住不开工不扣电。反证两次：漏掉银 + 没电就清零 ⇒ **3 FAIL**；只把"没电就清零"塞回去 ⇒ **精确 1 FAIL**（`brownout: progress HOLDS at 4 (got 0)`） | 见 §9 |
'''

SEC9 = u'''- [ ] **ZF62：等用户试合金炉配方**（成品 `d62a8e42…`）。铝锭 + 钛锭 + 银锭各 1 → 1 轻质钛合金，
      30 秒、5800 FE/t（**一件 348 万 FE**）。要看的：① 三样锭放进 5 个输入槽能不能开工；
      ② 30 秒后产出 1 个、原料各扣 1；③ **中途断电**（拔掉发电机）进度会不会白费 —— 现在的行为是
      **停住不清零**；④ JEI 里有没有「合金炉主控」这一页。
- [ ] **数字待你确认**：5800 FE/t × 30 秒 = **一件 348 万 FE**，而本模组的低级发电机只有 100 FE/t
      （要跑 9.7 小时才够一件），机器自身缓冲 32768 只够 5.6 tick ⇒ 必须**持续**供 5800 FE/t。
      这是照你给的字面值实现的；要是想调小（比如 580），说一声就改一个常数。
- [ ] 配方**一次只做一份**（不并行）。要像电力高炉那样多个输入槽同时开工也行，但得设上限
      保证 `并行数 × 5800 ≤ 32768`（最多 5 路）—— 你要就加。
'''

SEC616 = u'''### 6.16 加一条**合金冶炼炉**配方要动哪几处（0.10 ZF62 立的规矩）

| # | 动哪 | 干什么 |
|---|---|---|
| 1 | `AlloySmelterRecipes.build()` | 加一条 `Smelt`：`List<Need>`（标签 + 个数）+ 产物 + 耗时 + 每 tick 耗电 |
| 2 | `AlloySmelterBlockEntity.DURATION_TICKS/ENERGY_PER_TICK` | 只有**一条**配方时才用这两个常量；多条配方各带各的（`Smelt` 里已经有了） |
| 3 | **别忘 ZF42** | `并行数 × 每 tick 耗电 ≤ MAX_ENERGY(32768)`，否则"满负载永远跑不起来"。静态守卫会喊 |
| 4 | 产物物品 | `ModItems` 注册 + `models/item/<id>.json` + 四语言 + 创造页那一行 |
| 5 | 产物是"锭/合金"时 | 加进 `GenCommonTags.py` 的 `ALLOYS` 再**重跑脚本**（别手改 JSON） |
| 6 | JEI | `MachineRecipes.buildAlloySmelter()` 里会自动把 `AlloySmelterRecipes.all()` 画出来 —— **不用改**；只有加**新机器**才要动 `PotatoSTJeiPlugin.MACHINES` + `iconFor` |

'''

SEC1217 = u'''### 12.17 ZF62：合金冶炼炉终于有配方了（ZF49 说"先不做配方"，空了四轮）

用户 ZF49 立起这台机器时明确「先不做配方」，于是 ZF49~ZF61 这四轮里它一直是个**能成型、能进电、
能开界面但什么都不烧**的空壳。ZF62 给了第一条：**铝锭 + 钛锭 + 银锭 → 1 轻质钛合金，30s、5800 FE/t**。

三个值得记的点：

1. **"电不够"与"没配方"必须分开处理**：前者**停在原地**（进度保留），后者**归零**。
   一开始很容易写成"反正跑不动就清零"，那样一停电就把做了 29 秒的活扔掉 —— 反证专门验了这一条
   （把"没电就清零"塞回去 ⇒ 精确 1 条 FAIL）。
2. **一件 348 万 FE 的账**：5800 × 600。本模组自己的发电（低级发电机 100 FE/t）远远不够，
   机器缓冲 32768 只够 5.6 tick ⇒ 设计上就是"要持续大电"。数字是用户给的，照做并在 §9 里标出来。
3. **JEI 是白送的**：ZF19 那层 `MachineRecipes` 一开始就是按 `machineId` 归一数据的，
   所以这台机器加配方**没碰一行 JEI 代码**，只加了一条数据和一行机器 id。

'''


def main():
    text = io.open(DOC, encoding="utf-8").read()
    before = len(text)
    problems = []

    lines = text.split(u"\n")
    out = []
    added = False
    for line in lines:
        out.append(line)
        if line.startswith(u"| ZF61 |") and not added:
            out.append(ROW.rstrip(u"\n"))
            added = True
    if not added:
        problems.append(u"没找到 ZF61 行")
    text = u"\n".join(out)

    anchor9 = u"## 9. 待办与已知限制\n\n"
    if text.count(anchor9) != 1:
        problems.append(u"§9 标题不唯一")
    else:
        text = text.replace(anchor9, anchor9 + SEC9, 1)

    # §6.16：插在 §7 之前（§6 是"加东西要动哪些文件"的食谱区）
    anchor7 = u"## 7. "
    n7 = text.count(anchor7)
    if n7 < 1:
        problems.append(u"找不到 §7 标题")
    else:
        text = text.replace(anchor7, SEC616 + anchor7, 1)

    # §12.17：插在文件末尾（§12 是"实现细节与坑"）
    if not text.endswith(u"\n"):
        text += u"\n"
    text += SEC1217

    if problems:
        print(u"有失败项，**不落盘**：")
        for p in problems:
            print(u"  !! " + p)
        return 1

    io.open(DOC, "w", encoding="utf-8", newline="\n").write(text)
    print(u"字数 %d -> %d（+%d）" % (before, len(text), len(text) - before))
    print(u"§5 ZF62 行 / §9 / §6.16 / §12.17 已写入")
    return 0


if __name__ == "__main__":
    sys.exit(main())
