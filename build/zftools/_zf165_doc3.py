#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""ZF165 复核后的文档补充：
   ① 档案 §4.175（反射解析全部方法描述符 ⇒ 没装 Curios 的 run 配置会在启动时死）
   ② 档案 §9 的 ZF165 段补两条复核结论（装甲喷气背包 / 玩家不能关掉背饰槽）
   ③ 交接页 §5.3.3 补同一件事

全部按行锚点插入，只写这两份文件；写前留底。
"""

import io
import os
import sys

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

ARCHIVE = r"E:\PotatoST\docs\开发档案.md"
LEDGER = r"E:\PotatoST\docs\多会话协作交接.md"
STASH = r"E:\PotatoST\build\tmp\zf165"

L175 = """### 4.175 【开发环境雷】`@EventBusSubscriber` + 反射解析**全部**方法描述符 ⇒ 私有方法里的第三方类型也能让整个 run 死在启动前（0.13 ZF165）

**症状**：某个 run 配置（`runData` / `runGameTestServer` / `runJunit` …）一启动就
`NoClassDefFoundError`，而同一个类在别的 run 里一点事都没有。

**根因**（复核实测出来的，不是推理）：

1. `@EventBusSubscriber` 的自动注册会对那个类做
   `Class.forName(name, true, layer.getClassLoader())` + **`clazz.getDeclaredMethods()`**
   （`AutomaticEventSubscriber.java:55,60`）。后者要**解析该类全部方法描述符** ——
   **包括 private 方法和编译器生成的 lambda 方法**。
2. 描述符里出现了一个 classpath 上不存在的类 ⇒ `getDeclaredMethods()` 抛
   `NoClassDefFoundError`。复核用一个"描述符里放一个不存在的类型"的微实验**跑了一遍**，
   确认就是这个行为。
3. FML 那边只 `catch (Exception e)`（`:110`），**`Error` 会直接逃出去** ⇒ 整个 run 起不来。

**本轮怎么中的**：`CuriosBridge` 是 `@EventBusSubscriber`，其中四个成员的方法签名里带
`top.theillusivec4.curios.*` 类型（`registerCurio` / `starSteelHelmetCurio` /
`mekanismJetpackCurio` / `lambda$findEquipped$2`），而 Curios 在 `build.gradle` 里是
**compileOnly** —— 只进编译期 classpath，**不进运行期 classpath**。
`run/client` 与 `run/server` 恰好有 `mods/` 目录且里面有 Curios（所以一直没暴露），
而 `run/data` / `run/gameTestServer` / `run/junit` **没有 mods 目录**。

**规矩（两条，缺一不可）**：

- 「只有单个文件 import 第三方包、公开签名里不放第三方类型」**不足以**保证安全 ——
  类的注解会让 FML 反射它，而反射看的是**全部**成员，不只是 public 的。
  ⇒ 推断"没装对端会不会崩"时，判据是"**这个类有没有被 FML 反射**"，
  而不是"公开签名干不干净"。
- 这类"编译期只需要、运行期必须有"的对端，除了 `compileOnly`，还要在 `build.gradle` 里
  补一条 **`localRuntime`**（本工程顶部早就声明了这个配置，就是为了"开发运行期可见、
  **不进产物**"）：`localRuntime files('libs/curios-....jar')`。
  ⚠ **不能**写成 `implementation`/`api` —— 那会把对端的类打进我们的产物 jar。

**自检**：`_zf165_gate.py` 的 F 组盯着"有没有那条 localRuntime"与"有没有误写成
implementation/api"，F2 顺带数出带第三方类型的成员个数（本轮 = 4）。
"""

SEC9_ADD = """**复核补充的两条（`build/tmp/zf165/verify/REPORT2.md`，实跑核出来的）**：

1. **装甲喷气背包也算**：`mekanism:jetpack_armored` 与普通版是同一个 `IJetpackItem`
   实现路径，所以两件都写进了 `#curios:back`。**只要你想要普通版，说一声删一行即可。**
2. **玩家不能"关掉背饰槽"来让喷气背包失效**：`ICuriosMenu` 的 `setSlotActive(s)` 在本整合包
   15 个 jar 里**零调用方**（Curios 自己没做这个界面/命令）⇒ 背饰槽永远是"启用"状态。
   也就是说：**放进背饰槽 = 一定生效**，没有"关掉槽位就不起飞"这条退路。
"""

LEDGER_ADD = """**复核补的一刀（0.13 ZF165，见档案 §4.175）**：`CuriosBridge` 带 `@EventBusSubscriber`，
FML 会对它 `getDeclaredMethods()`，而反射要解析**全部**方法描述符（私有的也算）——
本类有 4 个成员签名里带 Curios 类型 ⇒ `build.gradle` 里除了 `compileOnly`
**还必须**有一条 `localRuntime files('libs/curios-....jar')`，否则
`runData`/`runGameTestServer`/`runJunit` 这些**没有 mods 目录**的 run 会在启动时
`NoClassDefFoundError`（FML 只 catch `Exception`，`Error` 直接逃出去）。
⚠ 别写成 `implementation`（会把 Curios 打进产物）；`_zf165_gate.py` F 组两条一起盯着。
"""


def insert_after(path, anchor_prefix, block, backup_name, label):
    src = io.open(path, "r", encoding="utf-8", newline="").read()
    if "\r\n" in src:
        print("!! %s 是 CRLF，停手" % path)
        return False
    lines = src.split("\n")
    idx = [i for i, l in enumerate(lines) if l.startswith(anchor_prefix)]
    if len(idx) != 1:
        print("!! %s 的锚点 %r 不唯一（%d 处）" % (path, anchor_prefix, len(idx)))
        return False
    os.makedirs(STASH, exist_ok=True)
    bak = os.path.join(STASH, backup_name)
    if not os.path.exists(bak):
        io.open(bak, "w", encoding="utf-8", newline="").write(src)
        print("留底 -> " + bak)
    if block.split("\n")[0] in src:
        print("!! %s 已经有这段了，拒绝重复插入" % label)
        return False
    lines[idx[0]:idx[0]] = block.split("\n") + [""]
    io.open(path, "w", encoding="utf-8", newline="").write("\n".join(lines))
    print("已插入 %s（%s）" % (label, os.path.basename(path)))
    return True


def main():
    ok = True
    # ① §4.175：插在 §4.174 那一节之后（找它后面第一个 "### " 或 "## "）
    src = io.open(ARCHIVE, "r", encoding="utf-8", newline="").read()
    if "### 4.175 " in src:
        print("!! 已经有 §4.175 了")
    else:
        lines = src.split("\n")
        idx = [i for i, l in enumerate(lines) if l.startswith("### 4.174 ")]
        if len(idx) != 1:
            print("!! §4.174 锚点不唯一：%d" % len(idx))
            ok = False
        else:
            j = idx[0] + 1
            while j < len(lines) and not lines[j].startswith("### ") and not lines[j].startswith("## "):
                j += 1
            os.makedirs(STASH, exist_ok=True)
            bak = os.path.join(STASH, "开发档案.md.before-zf175")
            if not os.path.exists(bak):
                io.open(bak, "w", encoding="utf-8", newline="").write(src)
            lines[j:j] = [""] + L175.split("\n")
            io.open(ARCHIVE, "w", encoding="utf-8", newline="").write("\n".join(lines))
            print("已插入 §4.175（开发档案.md）")

    # ② §9 的 ZF165 段补两条
    if "装甲喷气背包也算" in io.open(ARCHIVE, "r", encoding="utf-8").read():
        print("!! §9 的补充已在")
    else:
        lines = io.open(ARCHIVE, "r", encoding="utf-8", newline="").read().split("\n")
        idx = [i for i, l in enumerate(lines) if l.startswith("### ZF165（0.13）")]
        if len(idx) != 1:
            print("!! §9 ZF165 锚点不唯一：%d" % len(idx))
            ok = False
        else:
            j = idx[0] + 1
            while j < len(lines) and not lines[j].startswith("### ") and not lines[j].startswith("## "):
                j += 1
            lines[j:j] = [""] + SEC9_ADD.split("\n")
            io.open(ARCHIVE, "w", encoding="utf-8", newline="").write("\n".join(lines))
            print("已补 §9 的两条复核结论")

    # ③ 交接页 §5.3.3 补一刀：插在 §5.3.3 正文末尾（下一个 "## " 或 "### " 之前）
    if "复核补的一刀" in io.open(LEDGER, "r", encoding="utf-8").read():
        print("!! 交接页的补充已在")
    else:
        lines = io.open(LEDGER, "r", encoding="utf-8", newline="").read().split("\n")
        idx = [i for i, l in enumerate(lines) if l.startswith("### 5.3.3 ZF165")]
        if len(idx) != 1:
            print("!! §5.3.3 锚点不唯一：%d" % len(idx))
            ok = False
        else:
            j = idx[0] + 1
            while j < len(lines) and not lines[j].startswith("### ") and not lines[j].startswith("## "):
                j += 1
            os.makedirs(STASH, exist_ok=True)
            bak = os.path.join(STASH, "多会话协作交接.md.before-zf175")
            if not os.path.exists(bak):
                io.open(bak, "w", encoding="utf-8", newline="").write(
                    io.open(LEDGER, "r", encoding="utf-8", newline="").read())
            lines[j:j] = [""] + LEDGER_ADD.split("\n")
            io.open(LEDGER, "w", encoding="utf-8", newline="").write("\n".join(lines))
            print("已补交接页 §5.3.3")

    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
