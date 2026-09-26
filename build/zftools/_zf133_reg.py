# -*- coding: utf-8 -*-
"""_zf133_reg.py —— ZF133 往**共享汇合点**里插那几行（锚点唯一 + 插后复核）

共享文件是多线汇合点，永远"加行"，不整份重写（§4.7 / §11.2）。本脚本每个改动都：
  ① 先在原文里数锚点出现次数（必须恰好 1 次，否则当场停）；
  ② 插入后复核长度增量 == 插入串长度（单段插入判据）；
  ③ 复核关键子串确实在文件里。

涉及的行：
  ModItems.java        —— import AxeItem + 注册 STAR_STEEL_AXE + 创造页一行
  PotatoST.java        —— 冲击波推进（ServerTickEvent.Post）+ 退场清理 + 手持急迫 + 数据包登记
  PotatoSTClient.java  —— 客户端 init（光墙渲染器）
"""
import io
import os
import sys

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
ROOT = r"E:\PotatoST"


def patch(rel, edits):
    path = os.path.join(ROOT, rel.replace("/", os.sep))
    s = io.open(path, encoding="utf-8").read()
    before = len(s)
    for anchor, insert in edits:
        n = s.count(anchor)
        print("  anchor x%d : %s" % (n, anchor.strip().splitlines()[0][:78]))
        assert n == 1, "锚点不是唯一（%d 次）：%r" % (n, anchor[:80])
        s = s.replace(anchor, anchor + insert)
    io.open(path, "w", encoding="utf-8", newline="\n").write(s)
    print("  %s : %d -> %d 字符（+%d）" % (rel, before, len(s), len(s) - before))
    return s


print("=" * 72)
print("ZF133 共享文件插行")
print("=" * 72)

# ---------------------------------------------------------------- ModItems
IMPORT_ANCHOR = "import net.minecraft.world.item.PickaxeItem;\n"
IMPORT_INSERT = "import net.minecraft.world.item.AxeItem;\n"

# 注册：放在 STAR_CHART_TOME 那块之后（星仪图之章是 ZF122 的尾巴，后面就是 ZF120 的振金锭）
REG_ANCHOR = """    public static final DeferredItem<Item> VIBRANIUM_INGOT =
            ITEMS.register("vibranium_ingot", () -> new Item(new Item.Properties()));
"""
REG_INSERT = """
    /**
     * 星璨钢斧（0.11 ZF133）。
     *
     * <p>用户原话：「加个星璨钢斧 贴图…（用户素材） 1192耐久 挖掘等级钻石 1：夜晚时不消耗耐久
     * 手持时获得急迫1 1s 2：shift+右键 扣除120点耐久 发射一道冲击波 15s冷却…」。</p>
     *
     * <p>数值全在 {@link ModTiers#STAR_STEEL_AXE} 里（耐久 1192 / 挖掘等级钻石），
     * 属性写法照抄原版斧那一行：{@code AxeItem.createAttributes(tier, 8.0F, -3.1F)}
     * ⇒ 游戏里显示的总伤害 = 1（玩家基础）+ 5（斧基础）+ 8.0（档位）= 14.0。</p>
     *
     * <p>贴图是用户放进 {@code build/用户素材} 的 {@code 星璨钢斧.png}（16x16 RGBA，
     * 直接就是合规规格，没有转档）⇒ {@code textures/item/star_steel_axe.png}。</p>
     *
     * <p>⚠ 与星轨坠一样：**用户没给合成配方**，现在只能从创造模式拿 —— 挂 §9 待办。</p>
     */
    public static final DeferredItem<Item> STAR_STEEL_AXE =
            ITEMS.register("star_steel_axe", () -> new StarSteelAxeItem(new Item.Properties()
                    .attributes(AxeItem.createAttributes(ModTiers.STAR_STEEL_AXE,
                            ModTiers.STAR_STEEL_DAMAGE, ModTiers.STAR_STEEL_SPEED_MODIFIER))));
"""

TAB_ANCHOR = "                        output.accept(STAR_CHART_TOME.get());// ← 新增（0.11 ZF122 星仪图之章）\n"
TAB_INSERT = "                        output.accept(STAR_STEEL_AXE.get());// ← 新增（0.11 ZF133 星璨钢斧）\n"

s = patch("src/main/java/com/potatost/mod/ModItems.java", [
    (IMPORT_ANCHOR, IMPORT_INSERT),
    (REG_ANCHOR, REG_INSERT),
    (TAB_ANCHOR, TAB_INSERT),
])
assert "StarSteelAxeItem" in s and "star_steel_axe" in s

# ---------------------------------------------------------------- PotatoST
ST_ANCHOR = """        ModEntities.ENTITY_TYPES.register(modEventBus);
        modEventBus.addListener(StarfallNetworking::register);
"""
ST_INSERT = """        // 冲击波（0.11 ZF133）：数据包登记 + 三处 game 总线监听
        //（§4.20 的判据：ServerTickEvent / PlayerEvent 都属于"世界里发生的事"，挂 game 总线）
        modEventBus.addListener(ShockwaveNetworking::register);
        net.neoforged.neoforge.common.NeoForge.EVENT_BUS.addListener(ShockwaveManager::onServerTick);
        net.neoforged.neoforge.common.NeoForge.EVENT_BUS.addListener(ShockwaveManager::onPlayerLogout);
        // 手持星璨钢斧 ⇒ 续 1 秒急迫 I（1.21 起这个事件叫 PlayerTickEvent，不在 TickEvent 里面了）
        net.neoforged.neoforge.common.NeoForge.EVENT_BUS.addListener(
                (net.neoforged.neoforge.event.tick.PlayerTickEvent.Post event) ->
                        StarSteelAxeItem.applyHoldEffect(event.getEntity()));
"""

s = patch("src/main/java/com/potatost/mod/PotatoST.java", [(ST_ANCHOR, ST_INSERT)])
assert "ShockwaveManager::onServerTick" in s and "applyHoldEffect" in s

# ---------------------------------------------------------------- PotatoSTClient
CL_ANCHOR = "        com.potatost.mod.client.SkyboxRenderer.init();\n"
CL_INSERT = ("        // 星璨钢斧的冲击波光墙（0.11 ZF133）：同样自己往 game 总线挂\n"
             "        // RenderLevelStageEvent（AFTER_ENTITIES 那一拍）。\n"
             "        com.potatost.mod.client.ShockwaveRenderer.init();\n")

s = patch("src/main/java/com/potatost/mod/PotatoSTClient.java", [(CL_ANCHOR, CL_INSERT)])
assert "ShockwaveRenderer.init()" in s

print("-" * 72)
print("三份共享文件插行完成")
