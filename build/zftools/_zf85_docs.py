# -*- coding: utf-8 -*-
u"""_zf85_docs.py —— ZF85 文档：档案 §4.57（弃用覆盖搬家的雷）+ §5 ZF85 行 + §9 验收

`__NEWSHA__` / `__NEWSIZE__` / `__NEWENTRIES__` 由 `_zf85_publish.py` 填真值。
"""
import io
import os
import sys

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

DOCS = r"E:\PotatoST\docs"
fails = []


def read(p):
    if not os.path.exists(p):
        fails.append(u"缺文件：%s" % p)
        return u""
    return io.open(p, encoding="utf-8").read()


def write(p, t):
    io.open(p, "w", encoding="utf-8", newline=u"\n").write(t)


def insert_after(text, anchor, block, label):
    if text.count(anchor) != 1:
        fails.append(u"%s：锚点命中 %d 次（必须 1 次）" % (label, text.count(anchor)))
        return text
    at = text.find(anchor)
    eol = text.find(u"\n", at)
    return text[:eol + 1] + block + text[eol + 1:]


TRAP = u"""
### 4.57 【API 雷】`FluidType#initializeClient` 在 NeoForge 21.1 已"弃用并标记为移除"（0.11 ZF85）

用户在 IDE 里看到 `ModFluids.java` 挂着 **5 条红**（"重写弃用并标记为移除的方法"）+ 一堆空值注解提醒，
配一句「**这个警告和报错很烦人 … 你看看能不能优化掉**」。查下来是两件事叠在一起：

| 现象 | 真因 | 正路 |
|---|---|---|
| 5 条红：重写 `initializeClient` | NeoForge 21.1 把 `FluidType#initializeClient(Consumer<IClientFluidTypeExtensions>)` 标成弃用待删 | 改用 **`RegisterClientExtensionsEvent#registerFluidType(extensions, FluidType...)`**（mod 总线、仅客户端） |
| 一堆"未注解的形参/方法重写" | 匿名类重写了 NeoForge 里带 `@ParametersAreNonnullByDefault` / `@MethodsReturnNonnullByDefault` 的方法，而本地没标 | 在**承载注册的那个类**上补这两个类级注解（IDE 按名字识别；MC/NeoForge 自己也这么标） |

**为什么必须搬到"仅客户端"的类里**：`IClientFluidTypeExtensions` 是客户端专用类型。
原先它出现在 `ModFluids`（通用代码）里 —— 只要哪天有人从服务端路径碰到那个匿名类，
专用服务端就会 `NoClassDefFoundError`。搬进带 `@EventBusSubscriber(value = Dist.CLIENT)` 的
`PotatoSTClient` 之后，类型引用天然被关在客户端一侧。

**顺手一起清掉的"小字"**（都是 IDE 提的，但确实是代码卫生）：
① `liquidType(name, density, viscosity, temperature)` 的 `temperature` **四个调用点全传 300** ⇒ 形参收敛、内部固定 300；
② `idOf(Fluid)` / `byId(int)` / `GAS_COUNT` **从未被调用**（ZF73 起界面改用流体注册表 id）⇒ 删掉，注释里留一句"为什么删"；
③ javadoc 里一处空行被 IDE 判"将被忽略"；④ 注释里的英式 `initialiser` → 美式 `initializer`。

**规矩**：IDE 的"红"里凡属**弃用待删 API**，一律当**待还的债**处理（和 §4.44 那条"负向判定"同一性质）；
搬完要用"**改前件逐条对齐**"证明没搬丢（本轮：8 种流体的 `block/<名字>_still|_flow` 一条不差）。
"""

ROW = (u"| ZF85 | **新建 `zf85_pre`**（12 份改前件：`ModFluids` / `PotatoSTClient` / `TankContents` / "
       u"3 个往轮校验脚本 / 3 份文档 / 旧成品 jar 与 `.sha1`；逐份核哈希、失败 0。**先抄后动手**） | "
       u"0.11：**清掉 `ModFluids.java` 在 IDE 里的 25 条警告/报错**（用户原话：「**这个警告和报错很烦人**"
       u"（不知道什么时候出现的 之前应该没有）但是貌似可以程序是正常跑的 **你看看能不能优化掉**」）。"
       u"⚠ **没有改动任何行为**：流体注册、贴图路径、桶映射、气体判定全部一字未动，改的是「这些东西写在哪、"
       u"怎么标注」。① **5 条红**：`FluidType#initializeClient` 五个匿名覆盖（三种气体 + 原油 + `liquidType` 工厂）"
       u"全删，改用 `RegisterClientExtensionsEvent#registerFluidType(...)`，注册点落在"
       u" `PotatoSTClient`（本来就带 `@EventBusSubscriber(value = Dist.CLIENT)`）—— 顺带把"
       u"`IClientFluidTypeExtensions` 这个**客户端专用类型**从通用代码里请出去（服务端加载它必炸）。"
       u"② **16 条空值注解提醒**：承接注册的类上补 `@ParametersAreNonnullByDefault` + "
       u"`@MethodsReturnNonnullByDefault`（IDE 按名字识别）。③ `liquidType` 的 `temperature` 形参"
       u"（4 个调用点全是 300）收敛掉；`idOf/byId/GAS_COUNT` 三个**从未被调用**的成员删除"
       u"（`_zf72_verify.py` 的 B8/B9 随之改成断言新事实）；注释空行与 `initialiser→initializer` 一并修。"
       u"④ **编译期警告 7 → 0**（5×initializeClient + 2×`EventBusSubscriber.bus`，后者也已被弃用）。"
       u"⑤ 校验 `_zf85_verify.py`（45 项）里最要紧的一条：**拿改前件逐条对齐 8 种流体的贴图路径**"
       u"（搬丢了就是满屏紫黑流体）。雷记进 §4.57。 |\n")

VERIFY = u"""
### ZF85（0.11）清掉 ModFluids 的 25 条警告/报错 —— 待你实测

- [ ] **IDE 里 `ModFluids.java` 应当一条问题都没有了**（红 5 条 + 黄 20 条）；`PotatoSTClient.java` 也不该再有
- [ ] **游戏里流体的外观必须和以前一模一样**（这是本轮唯一的回归风险，虽然代码只是搬家）：
      原油 / 柴油 / 石脑油 / 汽油 / 液化石油气 / 氧气 / 氢气 / 氯气 —— 八种在**世界里、桶里、操作器罐里、
      JEI 里**的贴图都要正常（**出现紫黑格或透明方块 = 搬丢了，立刻告诉我**）
- [ ] ⚠ 我这边**只能跑到服务端**（本轮用开发服务端证明"服务端加载没问题"），
      **客户端渲染只能靠你眼睛看** —— 上面那条就是为此写的

**成品**：`release\\PotatoST-0.11.jar` = `__NEWSHA__`（__NEWSIZE__ B / __NEWENTRIES__ 条目），
**作废上一版 `cd404f6beeec982dd1de2d7b2b03a60f59de7c14`**（ZF84）；0.10 成品 `84d09345…` 原样保留。
"""


def main():
    arch_p = os.path.join(DOCS, u"开发档案.md")
    arch = read(arch_p)
    if u"### 4.57" not in arch:
        anchor = u"\n\n| 版本 | 内容 |"
        if arch.count(anchor) != 1:
            fails.append(u"§4.57 插入点命中 %d 次" % arch.count(anchor))
        else:
            arch = arch.replace(anchor, u"\n" + TRAP + anchor, 1)
    if u"| ZF85 |" not in arch:
        arch = insert_after(arch, u"| ZF84 | **新建 `zf84_pre`**", ROW, u"档案 §5：ZF85 行")
    if u"### ZF85（0.11）清掉 ModFluids" not in arch:
        if arch.count(u"\n## 10. 备份策略") != 1:
            fails.append(u"档案 §9：锚点命中 %d 次" % arch.count(u"\n## 10. 备份策略"))
        else:
            arch = arch.replace(u"\n## 10. 备份策略", u"\n" + VERIFY + u"\n## 10. 备份策略", 1)
    write(arch_p, arch)
    print(u"文档改完，失败项 = %d" % len(fails))
    for f in fails:
        print(u"  !! " + f)
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())
