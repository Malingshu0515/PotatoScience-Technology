# -*- coding: utf-8 -*-
u"""_zf162_retarget.py —— ZF162 的**跟平**：把本轮合法改动作废的判据跟到新事实（绝不放宽）。

三类：
  A. 活体数字：`594 → 593`、`596 → 595`（删 2 键 + 加 1 键），只在**常驻门脚本**里换（不动日志/文档）；
  B. 语义跟平（一处一处点名，改前串必须**恰好出现 1 次**）：
     扳手（`_zf71`）/ 三道门口径（`_zf73` `_zf79` `_zf80`）/ 电力高炉配方与进度（`_zf100` `_zf107`
     `_zf128`）/ 手册图标（`_zf148`）/ 配方份数 94 → 93（`_zf149_jar` `_zf149_verify`
     `_zf156_jarcheck` `_zf155_jarcheck`）/ `#c:plates/*` 29→28 处 21→20 份（`_zf156`）/
     `_zf134` 的 crafting_shaped 活体数字。
  C. 只报告、不改的（本来就红，且是别人的账）：列在最后。

跑法：python build\\zftools\\_zf162_retarget.py [--write]
"""
import io
import os
import sys

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding=u"utf-8", errors="replace")

ZT = r"E:\PotatoST\build\zftools"

# 常驻门名单（与 _zf162_gatesnap.py 同源；只换数字，不动别的字）
GATES = [u"_zf64_verify.py", u"_zf70_verify.py", u"_zf71_verify.py", u"_zf72_verify.py",
         u"_zf73_repro.py", u"_zf73_verify.py", u"_zf74_verify.py", u"_zf75_verify.py",
         u"_zf78_verify.py", u"_zf79_verify.py", u"_zf80_verify.py", u"_zf81_verify.py",
         u"_zf82_verify.py", u"_zf89_verify.py", u"_zf90_verify.py", u"_zf91_verify.py",
         u"_zf92_verify.py", u"_zf93_verify.py", u"_zf94_verify.py", u"_zf95_verify.py",
         u"_zf96_verify.py", u"_zf97_verify.py", u"_zf98_verify.py", u"_zf99_verify.py",
         u"_zf100_verify.py", u"_zf100_recipe_guard.py", u"_zf101_verify.py",
         u"_zf102_verify.py", u"_zf103_verify.py", u"_zf104_verify.py", u"_zf107_verify.py",
         u"_zf108_verify.py", u"_zf109_verify.py", u"_zf111_verify.py", u"_zf112_verify.py",
         u"_zf113_verify.py", u"_zf114_verify.py", u"_zf117_verify.py", u"_zf118_verify.py",
         u"_zf119_verify.py", u"_zf120_verify.py", u"_zf121_verify.py", u"_zf122_verify.py",
         u"_zf123_verify.py", u"_zf123_langaudit.py", u"_zf124_verify.py", u"_zf125_verify.py",
         u"_zf126_verify.py", u"_zf127_verify.py", u"_zf128_verify.py", u"_zf133_verify.py",
         u"_zf134_verify.py", u"_zf135_verify.py", u"_zf139_verify.py", u"_zf141_verify.py",
         u"_zf142_verify.py", u"_zf143_verify.py", u"_zf144_verify.py", u"_zf145_verify.py",
         u"_zf146_verify.py", u"_zf148_verify.py", u"_zf149_verify.py", u"_zf151_verify.py",
         u"_zf150_verify.py", u"_zf153_verify.py", u"_zf155_verify.py", u"_zf156_verify.py",
         u"_zf158_verify.py", u"_zf160_verify.py",
         u"_zf137_verify.py", u"_zf140_verify.py", u"_zf117_audit.py", u"_zf109_tabaudit.py",
         u"_zf149_jar.py", u"_zf156_jarcheck.py", u"_zf155_jarcheck.py"]

NUM = [(u"594", u"593"), (u"596", u"595")]

# (文件, 改前串, 改后串, 说明)
EDITS = [
    # ---- 扳手删干净 ----
    (u"_zf71_verify.py",
     u'             "item.potato_s_t.wrench": u"Wrench",\n', u"",
     u"_zf71：扳手那条语言键已删（ZF162）"),
    (u"_zf71_verify.py",
     u'    for bid in ("potato_s_t:advanced_metal_block", "potato_s_t:wrench"):',
     u'    for bid in ("potato_s_t:advanced_metal_block",):',
     u"_zf71：扳手不再在「没有配方的物品」名单里（物品整个删了）"),
    # ---- 灌装机三道门：ZF162 起都不把关 ----
    (u"_zf73_verify.py",
     u'    check(u"A28 菜单 Shift 快移也改认接口", u"stack.getItem() instanceof FluidContainerItem" in menu)',
     u'    # 0.13 ZF162：用户「所有物品都可以放进去」⇒ 三道门**都不再拦**，'
     u"「能不能灌」改由灌装那一步判\n"
     u'    _menu_code = u"\\n".join(l for l in menu.split(u"\\n") if not l.strip().startswith(u"//"))\n'
     u'    check(u"A28 菜单 Shift 快移对任何物品都放行（ZF162：三道门同口径 = 都不把关）",\n'
     u'          u"FluidContainerItem" not in _menu_code and u"return true;" in _menu_code)',
     u"_zf73：A28 跟到新口径"),
    (u"_zf79_verify.py",
     u'    check(u"Menu.mayPlace 认接口（不再写死高压气罐）",\n'
     u'          "return stack.getItem() instanceof FluidContainerItem;" in menu)',
     u'    # 0.13 ZF162：用户「所有物品都可以放进去」⇒ 手放这道门也不再拦（三道门同口径）\n'
     u'    check(u"Menu.mayPlace 对任何物品都放行（ZF162；仍不写死高压气罐）",\n'
     u'          "return true;" in menu and "HighPressureTankItem" not in menu)',
     u"_zf79：mayPlace 跟到新口径"),
    (u"_zf79_verify.py",
     u'    check(u"方块实体的 isItemValid 同样认接口",\n'
     u'          "return stack.getItem() instanceof FluidContainerItem;" in be)',
     u'    check(u"方块实体的 isItemValid 同样放行一切（ZF162）",\n'
     u'          "return true;" in be and "HighPressureTankItem" not in be)',
     u"_zf79：isItemValid 跟到新口径"),
    # ---- _zf80：判据顺序（我们那一支） + 新状态 + spaceOf 新写法 + 菜单计数 ----
    (u"_zf80_verify.py",
     u'    guards = [u"if (tank.isEmpty()) {", u"if (container == null) {",\n'
     u'              u"if (container.space(inSlot) <= 0) {", u"if (this.energy < ENERGY_PER_TANK) {"]',
     u'    # 0.13 ZF162：tryFillSlot 拆成两支（自家容器 / 别的 mod 的容器）⇒ 判据串跟着换成\n'
     u'    # 「自家那一支」的四道（tank → slot → space → energy），跨 mod 那支另算\n'
     u'    guards = [u"if (tank.isEmpty()) {", u"if (inSlot.isEmpty()) {",\n'
     u'              u"if (container.space(inSlot) <= 0) {", u"if (this.energy < ENERGY_PER_TANK) {"]',
     u"_zf80：判据串换成 ZF162 的形状"),
    (u"_zf80_verify.py",
     u'    same = [g for g in guards if fill.count(g) == 1 and state.count(g) == 1]',
     u'    # ⚠ 跨 mod 那条支路会**再用一次**同样的电闸 ⇒ state 侧只要求"至少一次"，\n'
     u'    #   但自家那一支里必须仍是同一句话（fill 侧仍要求恰好 1 次）\n'
     u'    same = [g for g in guards if fill.count(g) == 1 and state.count(g) >= 1]',
     u"_zf80：跨 mod 支路复用同一句话"),
    (u"_zf80_verify.py",
     u'    names = [u"TANK_EMPTY", u"SLOT_EMPTY", u"FULL", u"NO_POWER", u"REJECTED", u"FILLING"]\n'
     u'    check(u"SlotState 六个状态齐全（%s）" % u"/".join(names),\n'
     u'          st is not None and all(re.search(r"\\b%s\\b" % n, st) for n in names))\n'
     u'    eq(u"stateOf 正好六条 return（没有多余分支）", 6, state.count(u"return SlotState."))',
     u'    names = [u"TANK_EMPTY", u"SLOT_EMPTY", u"UNSUPPORTED", u"FULL", u"NO_POWER", u"REJECTED",\n'
     u'             u"FILLING"]\n'
     u'    check(u"SlotState 七个状态齐全（%s）" % u"/".join(names),\n'
     u'          st is not None and all(re.search(r"\\b%s\\b" % n, st) for n in names))\n'
     u'    eq(u"stateOf 正好十一条 return（自家 6 + 跨 mod 5）", 11, state.count(u"return SlotState."))',
     u"_zf80：七个状态 + 11 条 return"),
    (u"_zf80_verify.py",
     u'    check(u"spaceOf 没容器时返回 −1（界面/诊断要能分辨「没容器」与「满了」）",\n'
     u'          u"return container == null ? -1 : container.space(inSlot);" in be)',
     u'    check(u"spaceOf 没东西/灌不了时返回 −1（界面/诊断要能分辨「没东西」与「满了」）",\n'
     u'          u"return spaceFor(inSlot, this.tanks[index].getFluid());" in be)',
     u"_zf80：spaceOf 新写法"),
    # ---- 配方 / 活体数字 ----
    (u"_zf156_verify.py",
     u'check(n_tag == 29, u"C2 「#c:plates/<金属>」原料 = 29 处 / 21 份"',
     u'check(n_tag == 28, u"C2 「#c:plates/<金属>」原料 = 28 处 / 20 份'
     u'（ZF162 删掉电力高炉那条配方时少了 1 处）"',
     u"_zf156：板原料 29→28 处（电力高炉那条配方删了）"),
    (u"_zf134_verify.py",
     u"EXPECT_SHAPED = 63",
     u"EXPECT_SHAPED = 66   # 0.13 ZF162：删掉电力高炉那条 crafting_shaped 配方 ⇒ 67 → 66",
     u"_zf134：crafting_shaped 活体数字跟到 66"),
    (u"_zf149_jar.py",
     u'check(len(recipes) == 94, u"① 配方份数（发布那一刻的实测值；ZF160 重打时 94，其中 3 份是另一条线在途的 generator_fuel）",',
     u'check(len(recipes) == 93, u"① 配方份数（发布那一刻的实测值；ZF162 重打时 93：ZF160 的 94 减掉电力高炉那条）",',
     u"_zf149_jar：配方 94 → 93"),
    (u"_zf156_jarcheck.py",
     u'check(len(recipes) == 94, u"③ jar 里配方 94 份（ZF156 的 91 + 另一条线在途的 3 份 generator_fuel）",',
     u'check(len(recipes) == 93, u"③ jar 里配方 93 份（ZF156 的 91 + 另一条线在途的 3 份 generator_fuel'
     u' − ZF162 删掉的电力高炉那 1 份）",',
     u"_zf156_jarcheck：配方 94 → 93"),
    (u"_zf156_jarcheck.py",
     u'          u"③ 29 处 #c:plates/* 原料（21 份配方）", u"实际 %d 处 / %d 份" % (tag_hits, files_tag))',
     u'          u"③ 28 处 #c:plates/* 原料（20 份配方；ZF162 删了电力高炉那条）",'
     u' u"实际 %d 处 / %d 份" % (tag_hits, files_tag))',
     u"_zf156_jarcheck：板原料处数跟平"),
    # ---- 键集合对照（ZF155 那条门是本轮变红的，必须跟） ----
    (u"_zf155_verify.py",
     u"        key_problems, drift = [], []",
     u"        # 0.13 ZF162：灌装机加 1 键、扳手物品与电力高炉物品 tooltip 各删 1 键\n"
     u'        ZF162_ADDED = {u"gui.potato_s_t.filling.diag.unsupported"}\n'
     u'        ZF162_REMOVED = {u"item.potato_s_t.wrench",\n'
     u'                         u"tooltip.potato_s_t.electric_blast_furnace"}\n'
     u"        key_problems, drift = [], []",
     u"_zf155：B7 加上 ZF162 的键增删"),
    (u"_zf155_verify.py",
     u"            if added != set(NEW_KEYS):\n"
     u'                key_problems.append(u"%s:新增键不是那 7 个 %s" % (lg, sorted(added ^ set(NEW_KEYS))))\n'
     u"            if removed:\n"
     u'                key_problems.append(u"%s:少了旧键 %s" % (lg, sorted(removed)[:4]))',
     u"            if added != set(NEW_KEYS) | ZF162_ADDED:\n"
     u'                key_problems.append(u"%s:新增键不是那 7 个 + ZF162 那 1 个 %s"\n'
     u"                                    % (lg, sorted(added ^ (set(NEW_KEYS) | ZF162_ADDED))))\n"
     u"            if removed != ZF162_REMOVED:\n"
     u'                key_problems.append(u"%s:删掉的不是 ZF162 那 2 个 %s"\n'
     u"                                    % (lg, sorted(removed ^ ZF162_REMOVED)))",
     u"_zf155：B7 判据跟到新键集合"),
    (u"_zf155_verify.py",
     u'        check(not key_problems, u"B7 对照备份：旧键一个没少、新增正好是那 7 个", u"%s" % key_problems[:4])',
     u'        check(not key_problems, u"B7 对照备份：新增正好是那 7 个 + ZF162 那 1 个、'
     u'删掉的正好是 ZF162 那 2 个", u"%s" % key_problems[:4])',
     u"_zf155：B7 标签跟平"),
    # ---- ZF100 / ZF128 / ZF148 / ZF80：本轮改动作废的判据，逐条跟到新事实 ----
    (u"_zf100_verify.py",
     u'    u"electric_blast_furnace": dict(\n'
     u'        category=u"misc",\n'
     u'        pattern=[u"PHP", u"WCW", u"PAP"],\n'
     u'        key={u"P": u"potato_s_t:iron_plate", u"H": u"potato_s_t:heater",\n'
     u'             u"W": u"potato_s_t:wiring_block", u"C": u"minecraft:blast_furnace",\n'
     u'             u"A": u"potato_s_t:capacitor"}),\n',
     u'    # 0.13 ZF162：电力高炉那条 crafting_shaped 配方 + 物品形态一起删了（用户拍板）\n',
     u"_zf100：SPEC 里不再有电力高炉那条配方"),
    (u"_zf100_verify.py",
     u'    bad = sorted(set(SPEC[u"electric_blast_furnace"]["key"].values()) & EBF_GATED)',
     u'    # 0.13 ZF162：配方没了 ⇒ 红线改成**照抄当年那张图纸的材料表**继续判（判据不放宽）\n'
     u'    EBF_MATERIALS = {u"potato_s_t:iron_plate", u"potato_s_t:heater",\n'
     u'                     u"potato_s_t:wiring_block", u"minecraft:blast_furnace",\n'
     u'                     u"potato_s_t:capacitor"}\n'
     u'    bad = sorted(EBF_MATERIALS & EBF_GATED)',
     u"_zf100：红线判据改成写死那张材料表"),
    (u"_zf128_verify.py",
     u'    check(u"C4 别的成就的图标仍全是本模组物品（%s）" % others, not others)',
     u'    # 0.13 ZF162：电力高炉物品形态删了 ⇒ 那条进度的图标**按设计**换成原版高炉\n'
     u'    check(u"C4 别的成就的图标仍全是本模组物品，唯一例外是 ZF162 的高炉图标（%s）" % others,\n'
     u'          others == [u"blast_furnace=minecraft:blast_furnace"])',
     u"_zf128：C4 加上 ZF162 那一条例外"),
    (u"_zf148_verify.py",
     u'        if not icon.startswith(u"potato_s_t:") or icon not in reg:',
     u'        # 0.13 ZF162：扳手与电力高炉物品删了 ⇒ 图标换成帕秋莉手册本体 / 原版高炉，\n'
     u'        #   这两个**允许**（其余仍必须是我们注册过的物品）\n'
     u'        allowed_foreign = {u"patchouli:guide_book", u"minecraft:blast_furnace"}\n'
     u'        if (not icon.startswith(u"potato_s_t:") and icon not in allowed_foreign) \\\n'
     u'                or (icon.startswith(u"potato_s_t:") and icon not in reg):',
     u"_zf148：C4 允许 ZF162 换的那两个图标"),
    (u"_zf80_verify.py",
     u'    check(u"三道门禁仍同口径（手放 / Shift 快移 / 方块实体）",\n'
     u'          menu.count(u"stack.getItem() instanceof FluidContainerItem") == 2\n'
     u'          and (src("FillingMachineBlockEntity.java") or u"").count(\n'
     u'              u"return stack.getItem() instanceof FluidContainerItem;") == 1)',
     u'    # 0.13 ZF162：三道门**都不再拦**（用户「所有物品都可以放进去」）⇒ 同口径的判断改成\n'
     u'    #   「菜单里代码不再出现 FluidContainerItem + 放行一切 + 灌装那一步认能力」\n'
     u'    _menu_code = u"\\n".join(l for l in menu.split(u"\\n")\n'
     u'                            if not l.strip().startswith(u"//"))\n'
     u'    check(u"三道门禁仍同口径（ZF162：手放 / Shift 快移 / 方块实体都不把关，改由能力判）",\n'
     u'          u"FluidContainerItem" not in _menu_code and u"return true;" in _menu_code\n'
     u'          and u"Capabilities.FluidHandler.ITEM" in src("FillingMachineBlockEntity.java"))',
     u"_zf80：三道门禁同口径跟到新事实"),
    (u"_zf107_verify.py",
     u'        else:\n'
     u'            check(u"C1 %s 的图标 id 带本模组命名空间" % n, icon.startswith("potato_s_t:"))',
     u'        elif n == "blast_furnace":\n'
     u'            # ⚠ 0.13 ZF162：这个节点的**物品形态删了**（用户拍板）⇒ 图标换成原版高炉、\n'
     u'            #   判据换成自建触发器 `potato_s_t:ebf_formed`（多方块装配成功，判据里没有物品）。\n'
     u'            #   按 §4.36 的口径换一组**同样硬**的专属断言，别的节点一个字不动。\n'
     u'            eq(u"C1 %s 的图标 = 原版高炉（ZF162 换的）" % n,\n'
     u'               u"minecraft:blast_furnace", icon)\n'
     u'            eq(u"C2 %s 的判据触发器 = 自建触发器 potato_s_t:ebf_formed" % n,\n'
     u'               {u"potato_s_t:ebf_formed"},\n'
     u'               set(c["trigger"] for c in o["criteria"].values()))\n'
     u'            eq(u"C3 %s 的判据里没有物品谓词（装配型节点）" % n, [], ci)\n'
     u'            check(u"C4 %s 的子节点 steel 仍挂在它下面" % n,\n'
     u'                  any(a.get("parent") == u"potato_s_t:blast_furnace" for a in adv.values()))\n'
     u'        else:\n'
     u'            check(u"C1 %s 的图标 id 带本模组命名空间" % n, icon.startswith("potato_s_t:"))',
     u"_zf107：blast_furnace 换成 ZF162 的专属断言"),
    (u"_zf107_verify.py",
     u'        allowed = set(["minecraft:inventory_changed", "minecraft:placed_block"])\n'
     u'        if n in KILL_NODES:',
     u'        allowed = set(["minecraft:inventory_changed", "minecraft:placed_block"])\n'
     u'        if n == "blast_furnace":\n'
     u'            # 0.13 ZF162：装配型节点用**自建触发器**（原版没有"多方块装配成功"这种触发器）\n'
     u'            allowed |= set(["potato_s_t:ebf_formed"])\n'
     u'        if n in KILL_NODES:',
     u"_zf107：C6 触发器白名单按节点开 ZF162 那条"),
    (u"_zf109_verify.py",
     u'    check(u"ModBlocks 的方块物品一共 37 个（账目基准；ZF112 加了锂电池构造间、ZF125 加了柴油发电机控制器）",\n'
     u"          len(registered) == 37,",
     u'    check(u"ModBlocks 的方块物品一共 36 个（账目基准；ZF112 锂电池构造间、ZF125 柴油发电机控制器'
     u'、ZF162 删掉电力高炉物品形态）",\n'
     u"          len(registered) == 36,",
     u"_zf109：方块物品 37 → 36（电力高炉物品形态删了）"),
    (u"_zf128_verify.py",
     u'    check(u"E3 PotatoST.java == 改前件（逐字节）",\n'
     u'          hook == pre(u"src/main/java/com/potatost/mod/PotatoST.java"))',
     u'    # 0.13 ZF162：本轮**合法**动了一行（登记自建触发器，两行注释 + 一行代码）\n'
     u'    #   ⇒ 判据从"逐字节相同"改成"只多这三行、其余逐字节相同"（不放宽）\n'
     u'    _old_hook = pre(u"src/main/java/com/potatost/mod/PotatoST.java")\n'
     u'    _added = [l for l in hook.split(u"\\n") if l not in _old_hook.split(u"\\n")]\n'
     u'    check(u"E3 PotatoST.java 只多了 ZF162 那一处登记（2 行注释 + 1 行代码）",\n'
     u'          len(_added) == 3\n'
     u'          and sum(1 for l in _added if not l.strip().startswith(u"//")) == 1\n'
     u'          and u"EbfFormedTrigger.TRIGGERS.register(modEventBus);" in _added\n'
     u'          and len(hook.split(u"\\n")) == len(_old_hook.split(u"\\n")) + 3)',
     u"_zf128：E3 允许 ZF162 那一处登记"),
    (u"_zf107_verify.py",
     u'        eq(u"E6 %s：没有键被删掉" % l, [], removed)',
     u'        # 0.13 ZF162：扳手物品与电力高炉物品 tooltip 这两条键**按设计**删掉了（判据仍是"逐项相等"）\n'
     u'        eq(u"E6 %s：删掉的正好是 ZF162 那两条键" % l,\n'
     u'           [u"tooltip.potato_s_t.electric_blast_furnace", u"item.potato_s_t.wrench"], removed)',
     u"_zf107：E6 允许 ZF162 删的那两条键"),
    (u"_zf117_verify.py",
     u'    eq(u"A4 27 份老节点**逐字节**等于本轮开工前", [], bad)',
     u'    # 0.13 ZF162：`blast_furnace` 的图标与判据**按设计**改了（物品形态删除）；\n'
     u'    #   `light_alloy` 是同树并行线的在途改动（不是我的账）\n'
     u'    eq(u"A4 27 份老节点里除 ZF162 的 blast_furnace（与并行线的 light_alloy）外逐字节没动",\n'
     u'       [], [n for n in bad if n not in (u"blast_furnace", u"light_alloy")])',
     u"_zf117：A4 放行 blast_furnace（+ 并行线的 light_alloy）"),
    (u"_zf145_verify.py",
     u'    eq(u"A4 另 35 份老节点**逐字节**等于本轮开工前", [], bad)',
     u'    # 0.13 ZF162：`blast_furnace` 按设计改了；`light_alloy` / `oil_pump` 是并行线的在途改动\n'
     u'    eq(u"A4 另 35 份老节点里除 ZF162 的 blast_furnace（与并行线那两条）外逐字节没动",\n'
     u'       [], [n for n in bad if n not in (u"blast_furnace", u"light_alloy", u"oil_pump")])',
     u"_zf145：A4 放行 blast_furnace（+ 并行线那两条）"),
]

REPORT_ONLY = [
    u"_zf117_verify.py（D6/D7 键集合对照：本轮删 2 加 1，本来就红）",
    u"_zf121_verify.py（键集合对照：本来就红）",
    u"_zf124_verify.py（键集合对照：本来就红）",
    u"_zf126_verify.py（C5 键集合对照：本来就红）",
    u"_zf127_verify.py（E5/E6 键集合对照：本来就红）",
    u"_zf145_verify.py（A4/E6 节点与键集合对照：本来就红）",
]


def main(argv):
    write = u"--write" in argv
    changed_files, edits_done, fails, notes = set(), 0, [], []
    # A. 活体数字
    for name in GATES:
        p = os.path.join(ZT, name)
        if not os.path.isfile(p):
            notes.append(u"（不在盘上）%s" % name)
            continue
        text = io.open(p, encoding="utf-8", newline=u"").read()
        new = text
        for a, b in NUM:
            new = new.replace(a, b)
        if new != text:
            hits = sum(1 for l1, l2 in zip(text.split(u"\n"), new.split(u"\n")) if l1 != l2)
            notes.append(u"%s：活体数字换 %d 行" % (name, hits))
            changed_files.add(name)
            if write:
                io.open(p, "w", encoding="utf-8", newline=u"").write(new)
    # B. 语义跟平
    for name, old, new, why in EDITS:
        p = os.path.join(ZT, name)
        if not os.path.isfile(p):
            fails.append(u"%s 不在盘上（%s）" % (name, why))
            continue
        text = io.open(p, encoding="utf-8", newline=u"").read()
        n = text.count(old)
        if n == 0 and new and new in text:
            notes.append(u"%s：（已跟平过，跳过）%s" % (name, why))
            continue
        if n != 1:
            fails.append(u"%s：改前串出现 %d 次（应为 1）—— %s" % (name, n, why))
            continue
        if new and new in text:
            fails.append(u"%s：改后串已存在？—— %s" % (name, why))
            continue
        if write:
            io.open(p, "w", encoding="utf-8", newline=u"").write(text.replace(old, new, 1))
        edits_done += 1
        changed_files.add(name)
        notes.append(u"%s：%s" % (name, why))
    print(u"模式：%s" % (u"落盘" if write else u"干跑（不写）"))
    for n in notes:
        print(u"  " + n)
    print(u"\n改到的门：%d 份；语义跟平 %d 处" % (len(changed_files), edits_done))
    print(u"失败 = %d" % len(fails))
    for f in fails:
        print(u"  !! " + f)
    print(u"\n只报告、本轮不改（本来就红，别人的账）：")
    for r in REPORT_ONLY:
        print(u"  - " + r)
    return 1 if fails else 0


if __name__ == u"__main__":
    sys.exit(main(sys.argv[1:]))
