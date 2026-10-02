#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""ZF165：把档案 §5 那行 ZF165 与交接页第 37 条**就地更新**到复核后的真实状态
（加了装甲喷气背包 / localRuntime / §4.175 三处）。

⚠ 这是**字面替换**，不是插入：所以每一步都先断言"旧片段恰好出现 1 次"，
   并且替换后的整行长度只增不减；改前留底在 build/tmp/zf165/。
"""

import io
import os
import sys

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

ARCHIVE = r"E:\PotatoST\docs\开发档案.md"
LEDGER = r"E:\PotatoST\docs\多会话协作交接.md"
STASH = r"E:\PotatoST\build\tmp\zf165"

EDITS = [
    # ---- 档案 §5 的 ZF165 行 ----
    (ARCHIVE, "开发档案.md.before-zf165row",
     "⑫ ⚠ **本轮没重打成品**（`release\\PotatoST-0.13.jar` 里还没有这一轮）—— 下次打包必须带上，§4.159 三处联动照旧。 | 见 §9 ｜ 见 §4.173 / §4.174 |",
     "⑫ **复核（`REPORT2.md`，实跑核过）改了四处**："
     "(a) 喷气背包**两件都收**（`mekanism:jetpack` + `mekanism:jetpack_armored`，"
     "同一个 `IJetpackItem` 路径；`#curios:back` 两条都带 `required:false`）；"
     "(b) 护甲修饰符的 id **改用 Curios 传进来的那一个**（`curios:<槽位名><序号>`）—— "
     "`AttributeInstance#removeModifier` 只按 `modifier.id()` 删（原版 `AttributeInstance:114-123`），"
     "自造固定 id 在 `head` 只有 1 格时没事、一旦被调成 ≥2 格两个头盔会互相顶掉；"
     "(c) `build.gradle` 除 `compileOnly` 外**还要一条 `localRuntime`**："
     "本类带 `@EventBusSubscriber`，FML 会对它 `getDeclaredMethods()`，而反射解析**全部**方法描述符"
     "（私有的也算，本类有 4 个成员带 Curios 类型）⇒ 没有 mods 目录的 "
     "`runData`/`runGameTestServer`/`runJunit` 会在启动时 `NoClassDefFoundError`"
     "（FML 只 catch `Exception`）；立 **§4.175**；"
     "(d) 复核确认**玩家无法把背饰槽关掉**（`setSlotActive(s)` 在本整合包 15 个 jar 里零调用方）"
     "⇒ \"放进背饰槽 = 一定生效\"，也能确认**装饰槽那条路不可达**"
     "（Curios 自带的 10 个槽 JSON 都没写 `add_cosmetic`）。"
     "⑬ ⚠ **本轮没重打成品**（`release\\PotatoST-0.13.jar` 里还没有这一轮）—— 下次打包必须带上，"
     "§4.159 三处联动照旧。 | 见 §9 ｜ 见 §4.173 / §4.174 / §4.175 |"),
    # ---- 交接页第 37 条 ----
    (LEDGER, "多会话协作交接.md.before-zf165item",
     "⑥ ⚠ **本轮没重打成品**（`release\\PotatoST-0.13.jar` 里还没有这一轮）——\n    下次打包必须带上，§4.159 三处联动照旧。",
     "⑥ **复核（`REPORT2.md`）改了四处**：喷气背包**普通版+装甲版都收**；护甲修饰符 id 改用 Curios "
     "传进来的那个（`AttributeInstance#removeModifier` 只按 id 删）；`build.gradle` 多了 "
     "`localRuntime`（本类带 `@EventBusSubscriber`，FML 反射全部方法描述符 ⇒ 没装 Curios 的 run 会"
     "`NoClassDefFoundError`，立 **§4.175**）；确认玩家**无法**关掉背饰槽。\n"
     "    ⑦ ⚠ **本轮没重打成品**（`release\\PotatoST-0.13.jar` 里还没有这一轮）——\n"
     "    下次打包必须带上，§4.159 三处联动照旧。"),
]


def main():
    for path, backup_name, old, new in EDITS:
        src = io.open(path, "r", encoding="utf-8", newline="").read()
        n = src.count(old)
        if n != 1:
            print("!! %s：旧片段出现 %d 次（必须恰好 1 次），停手" % (os.path.basename(path), n))
            return 2
        if new in src:
            print("!! %s：新片段已在，拒绝重复改" % os.path.basename(path))
            return 3
        os.makedirs(STASH, exist_ok=True)
        bak = os.path.join(STASH, backup_name)
        if not os.path.exists(bak):
            io.open(bak, "w", encoding="utf-8", newline="").write(src)
            print("留底 -> " + bak)
        out = src.replace(old, new, 1)
        # 只增不减的护栏：整份文件长度必须变大
        if len(out) <= len(src):
            print("!! %s：改完没变长，异常，停手" % os.path.basename(path))
            return 4
        io.open(path, "w", encoding="utf-8", newline="").write(out)
        print("已更新 %s 的一处（+%d 字节）" % (os.path.basename(path), len(out) - len(src)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
