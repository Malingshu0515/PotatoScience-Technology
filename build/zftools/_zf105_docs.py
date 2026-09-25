# -*- coding: utf-8 -*-
r"""_zf105_docs.py —— ZF105 两处文档：档案 §4.72（新雷区）+ §9 的 ZF105 交付条目

⚠ 锚点唯一性先查后改（§4.6）；用 Python 三引号原文写 Markdown。
"""
import io
import sys

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

DOC = r"E:\PotatoST\docs\开发档案.md"

# ---- ① §4.72：插在 §4.71 之后（锚点 = §4.71 那段末尾那句引用块）----
A1 = u"> 这一轮的反证刀（`_zf103_falsify.py`，8 刀）**首跑就砍穿了 2 刀**（K4 韧性 1.0→0.0、K5 抽掉夜晚分支），\n> 修完探针才全绿。**\"探针自己没被反证过 = 探针不算数\"**（§4.17）。\n"
N1 = A1 + u"""

### 4.72 【致命】新注册类**必须**在模组构造期被碰一下 —— 否则"开物品栏"就是崩溃现场（0.11 ZF105）

2026-09-25 18:40:17 客户端崩溃的根因。症状极有误导性：**崩点报在 `ModItems` 里**
（`ModItems.lambda$static$44(ModItems.java:530)`），可真正的错在 `ModArmorItems`：

```
java.lang.NoClassDefFoundError: Could not initialize class com.potatost.mod.ModArmorItems
    at ModItems.lambda$static$44(ModItems.java:530)          ← 创造页在往标签页里塞物品
    ...
    at CreativeModeInventoryScreen.<init>                     ← 玩家按下 E 开物品栏那一下
（第一现场，日志里更靠前）
java.lang.ExceptionInInitializerError
    at com.potatost.mod.ModArmorItems.<clinit>(ModArmorItems.java:53)
Caused by: java.lang.IllegalStateException:
    Cannot register new entries to DeferredRegister after RegisterEvent has been fired.
```

**因果链**（每一环都可独立验证）：

| 环节 | 事实 |
|---|---|
| ① | 新类在**静态字段**里直接调 `DeferredRegister.register(...)` |
| ② | 模组构造器**一次都没提到**这个类 ⇒ JVM 把它的静态初始化**推迟**到"第一次真正访问" |
| ③ | 第一次访问来自**创造模式标签页**（`ModItems` 里那串 `output.accept(XXX.get())`），而它发生在**开物品栏**时（`CreativeModeTab.buildContents`） |
| ④ | 那一刻 `RegisterEvent` 早跑完了 ⇒ NeoForge 拒绝新登记 ⇒ `IllegalStateException` |
| ⑤ | 类初始化失败 ⇒ 之后碰它的任何代码都变 `NoClassDefFoundError` ⇒ **开物品栏必崩** |

**为什么 `PotatoSTOres` 一直没踩**：构造器里有 `PotatoSTOres.register(modEventBus)` ——
**光是这一下就会触发该类的静态初始化**，所以它的 `ORES.register(...)` 发生在窗口还开着的时候。
`ModArmorItems` 缺的正是"被碰一下"这件事。

**修法（一行 + 一个空方法）**：类里加 `public static void touch() {}`（**必须放类尾部** ——
挪到静态字段之前就不会触发字段初始化），构造器里加 `ModArmorItems.touch();`。

**证据（三层，缺一不可）**：
1. `touch()` 里留一句英文 debug 日志（文案必须英文，§4.29 的 E 项会拦中文）⇒
   真启动日志里出现 `[modloading-worker-0] ModArmorItems initialized during mod construction`
   —— 证明静态初始化发生在**模组构造线程**、不是开界面那一下；
2. 崩溃指纹 `Cannot register new entries to DeferredRegister` 在日志里**0 命中**；
3. **反向证据**：JEI 的 `ItemStackListFactory` 会遍历各个创造页，
   日志里出现 `Added 112/112 new items from 'PotatoS&T' creative tab's displayItems`
   ⇒ 走的正是崩溃那条栈（`CreativeModeTab.buildContents`），这次没炸。

**机械防线（新门 `_zf105_regcheck.py`）**：对每个 class 反汇编它的 `static {}`，
凡里有"注册动作"的就是**注册型类**，再回 `PotatoST.<init>` 的反汇编里确认该类的名字出现过。
⚠ 判据必须收全**三种形态**，否则会漏掉本次的主角：
① `DeferredRegister.register(...)`；
② `DeferredRegister$Items.register(...)` —— `createItems()` 的返回类型被 javac 编成内部子类，
   所以 `ModItems.ITEMS.register(...)` 反汇编出来是**带 `$Items` 的那个**；
③ 调**本类自己的** `register(...)` 辅助方法（`ModArmorItems` 正是这种，
   真正那 9 次注册在辅助方法体内，`static{}` 里只有 9 条 `invokestatic register:`）。
本门已把 7 个注册型类全部纳入（`ModArmorItems` / `ModArmorMaterials` / `ModBlocks` /
`ModFluids` / `ModItems` / `ModMenus` / `SaltyRiverBiomeSource`），配 2 把反证刀（K1 删调用、K2 把方法搬到类首）。

**同源教训（写在这里免得再犯）**：本轮为了这个门**先手写了一个常量池解析器**，
它把 `methods[]` 的名称索引解错（`utf8()` 全返回 `None`），判据因此"一个注册型类都扫不到"——
**工具自己先坏了，门当然全绿不了也红不了**。换成 `javap` 文本后一次就对。
与 §4.71 是同一个道理：**取证工具本身也要先被反证一次**。
"""
# ---- ② ZF105 交付条目：插在 §9 的 ZF104 条目之后 ----
A2 = u"**成品**：`release\\PotatoST-0.11.jar` = `90510e1890af79242cb41e0cda0a2f6472b12cdf`"
N2 = u"""### ZF105（0.11）修「开物品栏必崩」+ 新增注册时序门 —— 待你实测

用户原话（转述另一个 agent 的崩溃现场分析）：

  「之前崩溃了这是别的agent返还的 …… ModArmorItems 的静态字段里直接调 ModItems.ITEMS.register(...)，
    但没人在这之前碰过这个类 …… 加一个 touch() 空方法，在 PotatoST 构造器里调一行」

**结论：那份分析完全正确，证据链我独立复核过**（崩溃报告第 217 / 259 / 327 行 + `latest.log`），
根因、因果、修法三段都对；我只做了两件它没做/没条件做的事：

- [x] **修法落地 + 留证据**：`ModArmorItems.touch()`（类**尾部**，里面一句英文 debug 日志）+
      `PotatoST` 构造器里 `ModArmorItems.touch();`。日志实证：
      `[19:12:10] [modloading-worker-0] ModArmorItems initialized during mod construction ...`
      （**构造线程**，不是开界面那一下）
- [x] **另一条独立的强证据**：JEI 的 `ItemStackListFactory` 会遍历每个创造页 ——
      `Added 112/112 new items from 'PotatoS&T' creative tab's displayItems`
      走的正是崩溃那条栈（`CreativeModeTab.buildContents`），这次没炸；
      用户随后**已进世界**（日志里有 `EndDragonFight` 扫描 + 服务端 tick），说明实际可玩
- [x] **机械防线**：新门 `_zf105_regcheck.py`（7 个注册型类全纳入 + 2 把反证刀）
- [x] **同源雷区**：立 **§4.72**（含"为什么 PotatoSTOres 没踩"与"三种注册形态"两条细节）

**⚠ 我自己的两个 slip（都当场发现并修了，如实记）**

1. 反证刀 K2 第一版把 `touch()` **改名**成 `touch_MOVED_TO_TOP` ⇒ **编译就挂了**，
   而那也被我判成"门抓到了"。这是**假捕获**（拿编译失败冒充检测成功，§4.30 同型）。
   改成**真位移**（整块方法体搬到类首、代码仍编译通过）后才是有效的一刀。
2. 新门第一版**手写常量池解析器**，`methods[]` 名称索引解错 ⇒ "一个注册型类都扫不到"。
   换成 `javap` 文本重写才对 —— **取证工具自己先坏了**这件事本身差点让我把门当绿的。

**没做的（等你发话）**：本轮**仍未打包发布**。理由与 ZF104 相同：并行的另一条任务
（硬质钛合金线）还在同一棵树上改，全门里剩下的 FAIL 都是"往轮脚本锚在旧状态"那一类。
修崩溃这件事本身**已经完成且可验证**（上面三条证据）。
"""
ANCHORS = [(A1, N1, u"§4.72"), (A2, N2, u"§9 ZF105")]


def main():
    text = io.open(DOC, encoding="utf-8").read()
    bad = 0
    for a, _n, label in ANCHORS:
        n = text.count(a)
        print(u"  锚点 %-8s 命中 %d 次" % (label, n))
        if n != 1:
            bad += 1
    if bad:
        print(u"!! 有锚点不唯一，一个字节都不写")
        return 1
    for a, n, label in ANCHORS:
        text = text.replace(a, n, 1)
        print(u"  [OK]   %s 已插入" % label)
    io.open(DOC, "w", encoding="utf-8", newline=u"\n").write(text)
    print(u"写回完成（%d 字节）" % len(text))
    return 0


if __name__ == "__main__":
    sys.exit(main())
