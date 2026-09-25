# -*- coding: utf-8 -*-
u"""_zf78_prebackup.py —— 补建 `zf78_pre` 改前件（**本轮我漏了动手前备份**，见 MANIFEST 的如实说明）

做法（照 ZF65 那条先例）：把本轮的每一次编辑**反向套用**回当前文件，得到"改前件"。
每一条反向替换都断言**正好命中 1 次**，不中就不写（宁可空手，也不要把文件改花）。

配套的忠实性证明在 `_zf78_precheck.py`：把这 8 份重建件换回源码树（连同删掉本轮新增的
7 个 java）编译一遍，与 **ZF77 成品 jar**（`release\\PotatoST-0.11.jar`，本轮还没重打包）
里的同名 class **逐字节比对** —— class 相同 ⇒ 逻辑一致（注释可能与我当时的措辞有差，
这一条在 MANIFEST 里如实写出来）。

用法：
    python build/zftools/_zf78_prebackup.py            # 只生成改前件 + MANIFEST
    python build/zftools/_zf78_prebackup.py --current  # 同时把"改后"的当前件抄进 新增文件\
"""
import hashlib
import io
import os
import shutil
import sys

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

ROOT = r"E:\PotatoST"
SRC = os.path.join(ROOT, "src", "main", "java", "com", "potatost", "mod")
BK = r"C:\PotatoST救援\zf78_pre"
JAVA = os.path.join(BK, "src", "main", "java", "com", "potatost", "mod")
NEW = os.path.join(BK, u"新增文件")

# 本轮新增的文件（改前**不存在**；证明忠实性时要把它们从源码树里拿掉）
NEW_JAVA = [
    "DistillationTowerStructure.java",
    "DistillationControllerBlock.java",
    "DistillationControllerBlockEntity.java",
    "DistillationOperatorBlock.java",
    "DistillationOperatorBlockEntity.java",
    "DistillationOperatorMenu.java",
    os.path.join("client", "DistillationOperatorScreen.java"),
    "DistillationCheck.java",
]

fails = []


def read(path):
    return io.open(path, encoding="utf-8").read()


def sha1(path):
    return hashlib.sha1(open(path, "rb").read()).hexdigest()


def reverse(name, pairs):
    u"""把 pairs 里的每一对 (本轮改后片段, 本轮改前片段) 反向替换回改前。"""
    path = os.path.join(SRC, name)
    if not os.path.exists(path):
        fails.append(u"%s 不存在" % name)
        return False
    text = read(path)
    for new, old in pairs:
        hits = text.count(new)
        if hits != 1:
            fails.append(u"%s：反向锚点命中 %d 次（必须 1 次）" % (name, hits))
            return False
        text = text.replace(new, old)
    dst = os.path.join(JAVA, name)
    os.makedirs(os.path.dirname(dst), exist_ok=True)
    io.open(dst, "w", encoding="utf-8", newline=u"\n").write(text)
    print(u"  [OK]   %-42s -> 改前件（%d B）" % (name, os.path.getsize(dst)))
    return True


# ================= 反向编辑表（逐条对应本轮的 edit）=================

P_MODFLUIDS_DOC = [(
    u" * 氧气 / 氢气 / 氯气 / **原油** / **分馏产物（柴油·石脑油·汽油·液化石油气）** 流体注册。",
    u" * 氧气 / 氢气 / 氯气 / **原油** 流体注册。",
)]


def modfluids_section():
    """整段「分馏产物」是插在「注册入口」之前的。"""
    path = os.path.join(SRC, "ModFluids.java")
    text = read(path)
    begin = u"    // ================= 分馏产物（0.11 ZF78）================="
    end = u"    // ================= 注册入口 ================="
    if text.count(begin) != 1 or text.count(end) != 1:
        fails.append(u"ModFluids.java：分馏产物段落锚点命中次数不对")
        return False
    i = text.index(begin)
    j = text.index(end)
    if j <= i:
        fails.append(u"ModFluids.java：段落顺序不对")
        return False
    return [(text[i:j], u"")]


P_MODITEMS_BITUMEN = None  # 运行时生成（段落较长，直接按起止标记切）


def moditems_section():
    path = os.path.join(SRC, "ModItems.java")
    text = read(path)
    begin = u"    // ========== 沥青（0.11 ZF78）=========="
    end = u"    // ========== 电容（0.10 ZF21）=========="
    if text.count(begin) != 1 or text.count(end) != 1:
        fails.append(u"ModItems.java：沥青段落锚点命中次数不对")
        return False
    i = text.index(begin)
    j = text.index(end)
    return [(text[i:j], u"")]


P_MODITEMS_TAB = [(
    u"""                        output.accept(ModBlocks.DISTILLATION_CONTROLLER_ITEM.get());// ← 新增（0.11 ZF78 分馏塔控制器）
                        output.accept(ModBlocks.DISTILLATION_OPERATOR_ITEM.get());// ← 新增（0.11 ZF78 分馏塔操作器）
                        output.accept(BITUMEN.get());// ← 新增（0.11 ZF78 沥青）
""",
    u"",
)]

def modblocks_section():
    u"""ModBlocks：整段 ZF78（从空行+区块标题，到文件末尾那个 `}` 之前）全删掉。

    ⚠ 第一版这里只写了一行标题当锚点 ⇒ 只删掉标题、段落全留着，**编译当场报
    「找不到符号 DistillationControllerBlockEntity」**（探针式的好处：错的重建活不过编译）。
    """
    path = os.path.join(SRC, "ModBlocks.java")
    text = read(path)
    begin = u"\n\n    // ===== 分馏塔三件套（0.11 ZF78）====="
    if text.count(begin) != 1:
        fails.append(u"ModBlocks.java：ZF78 段落起点锚点命中 %d 次" % text.count(begin))
        return []
    i = text.index(begin)
    j = text.rindex(u"\n}")
    if j <= i:
        fails.append(u"ModBlocks.java：段落与文件末尾的相对位置不对")
        return []
    return [(text[i:j], u"")]

P_MODMENUS = [(
    u"""    /** 分馏塔操作器菜单（0.11 ZF78）*/
    public static final DeferredHolder<MenuType<?>, MenuType<DistillationOperatorMenu>> DISTILLATION_OPERATOR_MENU =
            MENU_TYPES.register("distillation_operator",
                    () -> new MenuType<>(DistillationOperatorMenu::new, FeatureFlags.DEFAULT_FLAGS));

""",
    u"",
)]

P_POTATO_ST_HOOK = [(
    u"""

        // ⚠⚠ 临时探针（ZF78 实测用，**验证完必须删掉这一行 + DistillationCheck.java**）
        DistillationCheck.register();""",
    u"",
)]

P_POTATO_ST_CAP = [(
    u"""
        // ㉙ 分馏塔操作器（0.11 ZF78）：收 FE（六面）；上限是**动态的** 8096 × 塔数
        event.registerBlockEntity(
                Capabilities.EnergyStorage.BLOCK,
                ModBlocks.DISTILLATION_OPERATOR_BE.get(),
                (operator, side) -> operator.getEnergyStorage());

        // ㉚ 分馏塔操作器：5 个罐（石油 + 柴油/石脑油/汽油/液化石油气）
        //     ⚠ 灌入只有石油罐收，四个产品罐是出口 —— 逻辑在 getFluidHandler() 里
        event.registerBlockEntity(
                Capabilities.FluidHandler.BLOCK,
                ModBlocks.DISTILLATION_OPERATOR_BE.get(),
                (operator, side) -> operator.getFluidHandler());

        // ㉛ 分馏塔操作器：沥青槽位（自动化可取；只收沥青）
        event.registerBlockEntity(
                Capabilities.ItemHandler.BLOCK,
                ModBlocks.DISTILLATION_OPERATOR_BE.get(),
                (operator, side) -> operator.getInventory());

        // ⚠ 分馏塔控制器（ZF78）**故意不登记任何能力**：它不存能量、不存流体、不存物品，
        //   唯一的工作是数塔并把数量推给相邻操作器（用户原话）。
""",
    u"",
)]

P_CLIENT = [(
    u"""        event.register(ModMenus.DISTILLATION_OPERATOR_MENU.get(),
                com.potatost.mod.client.DistillationOperatorScreen::new);   // 0.11 ZF78 分馏塔操作器
""",
    u"",
)]


def energy_bar_old():
    u"""EnergyBarPart：把本轮"上限改 supplier"的重构整个反回去（原文取自本轮 edit 的 old_string）。"""
    new = u"""    private final IntSupplier amount;
    private final IntSupplier max;
    private final int color;
    private final boolean vertical;

    public EnergyBarPart(int x, int y, int w, int h, IntSupplier amount, int max) {
        this(x, y, w, h, amount, max, DEFAULT_COLOR, true);
    }

    public EnergyBarPart(int x, int y, int w, int h, IntSupplier amount, int max, int color, boolean vertical) {
        this(x, y, w, h, amount, () -> max, color, vertical);
    }

    /**
     * 上限会随结构变化的机器用这个重载（0.11 ZF78 分馏塔操作器：上限 = 8096 FE × 分馏塔数）。
     *
     * <p>与固定上限那两版行为完全一样，区别只是每帧重新读一次上限。</p>
     */
    public EnergyBarPart(int x, int y, int w, int h, IntSupplier amount, IntSupplier max) {
        this(x, y, w, h, amount, max, DEFAULT_COLOR, true);
    }

    public EnergyBarPart(int x, int y, int w, int h, IntSupplier amount, IntSupplier max,
                         int color, boolean vertical) {
        this.x = x;
        this.y = y;
        this.w = w;
        this.h = h;
        this.amount = amount;
        this.max = max;
        this.color = color;
        this.vertical = vertical;
    }

    @Override
    public void render(MachineScreen<?> screen, GuiGraphics gg) {
        int ax = screen.left() + this.x;
        int ay = screen.top() + this.y;

        gg.fill(ax - 1, ay - 1, ax + this.w + 1, ay + this.h + 1, BORDER);
        gg.fill(ax, ay, ax + this.w, ay + this.h, TROUGH);

        int amt = this.amount.getAsInt();
        int maxNow = this.max.getAsInt();
        if (amt <= 0 || maxNow <= 0) {
            return;
        }
        int fill = (int) ((long) (this.vertical ? this.h : this.w) * Math.min(amt, maxNow) / maxNow);
        if (fill <= 0) {
            return;
        }
        if (this.vertical) {
            gg.fill(ax, ay + this.h - fill, ax + this.w, ay + this.h, this.color);
        } else {
            gg.fill(ax, ay, ax + fill, ay + this.h, this.color);
        }
    }

    @Override
    public void tooltip(MachineScreen<?> screen, GuiGraphics gg, int mouseX, int mouseY) {
        if (!screen.hovering(mouseX, mouseY, this.x, this.y, this.w, this.h)) {
            return;
        }
        gg.renderTooltip(screen.font(), Component.translatable("gui.potato_s_t.energy",
                this.amount.getAsInt(), this.max.getAsInt()), mouseX, mouseY);
    }
}"""
    old = u"""    private final IntSupplier amount;
    private final int max;
    private final int color;
    private final boolean vertical;

    public EnergyBarPart(int x, int y, int w, int h, IntSupplier amount, int max) {
        this(x, y, w, h, amount, max, DEFAULT_COLOR, true);
    }

    public EnergyBarPart(int x, int y, int w, int h, IntSupplier amount, int max, int color, boolean vertical) {
        this.x = x;
        this.y = y;
        this.w = w;
        this.h = h;
        this.amount = amount;
        this.max = max;
        this.color = color;
        this.vertical = vertical;
    }

    @Override
    public void render(MachineScreen<?> screen, GuiGraphics gg) {
        int ax = screen.left() + this.x;
        int ay = screen.top() + this.y;

        gg.fill(ax - 1, ay - 1, ax + this.w + 1, ay + this.h + 1, BORDER);
        gg.fill(ax, ay, ax + this.w, ay + this.h, TROUGH);

        int amt = this.amount.getAsInt();
        if (amt <= 0 || this.max <= 0) {
            return;
        }
        int fill = (int) ((long) (this.vertical ? this.h : this.w) * Math.min(amt, this.max) / this.max);
        if (fill <= 0) {
            return;
        }
        if (this.vertical) {
            gg.fill(ax, ay + this.h - fill, ax + this.w, ay + this.h, this.color);
        } else {
            gg.fill(ax, ay, ax + fill, ay + this.h, this.color);
        }
    }

    @Override
    public void tooltip(MachineScreen<?> screen, GuiGraphics gg, int mouseX, int mouseY) {
        if (!screen.hovering(mouseX, mouseY, this.x, this.y, this.w, this.h)) {
            return;
        }
        gg.renderTooltip(screen.font(), Component.translatable("gui.potato_s_t.energy",
                this.amount.getAsInt(), this.max), mouseX, mouseY);
    }
}"""
    return [(new, old)]


def fluid_tank_old():
    path = os.path.join(SRC, "client", "gui", "parts", "FluidTankPart.java")
    text = read(path)
    new_marker = u"    private final IntSupplier amount;\n    private final IntSupplier capacity;\n"
    old_marker = u"    private final IntSupplier amount;\n    private final int capacity;\n"
    if text.count(new_marker) != 1:
        fails.append(u"FluidTankPart.java：字段锚点命中次数不对")
        return None
    pairs = [
        (new_marker, old_marker),
        (u"""    public FluidTankPart(int x, int y, int w, int h, IntSupplier amount, int capacity,
                         Fluid fluid, Component displayName) {
        this(x, y, w, h, amount, () -> capacity, fluid, displayName);
    }

    /**
     * 容量会随结构变化的机器用这个重载（0.11 ZF78 分馏塔操作器：
     * 石油 12 桶/塔、每种产品 2.5 桶/塔）。
     */
    public FluidTankPart(int x, int y, int w, int h, IntSupplier amount, IntSupplier capacity, Fluid fluid) {
        this(x, y, w, h, amount, capacity, fluid, fluid.getFluidType().getDescription());
    }

    public FluidTankPart(int x, int y, int w, int h, IntSupplier amount, IntSupplier capacity,
                         Fluid fluid, Component displayName) {
""",
         u"""    public FluidTankPart(int x, int y, int w, int h, IntSupplier amount, int capacity,
                         Fluid fluid, Component displayName) {
"""),
        (u"""        int amt = this.amount.getAsInt();
        int capacityNow = this.capacity.getAsInt();
        if (amt <= 0 || capacityNow <= 0) {
            return;
        }
        int fill = (int) ((long) this.h * Math.min(amt, capacityNow) / capacityNow);""",
         u"""        int amt = this.amount.getAsInt();
        if (amt <= 0 || this.capacity <= 0) {
            return;
        }
        int fill = (int) ((long) this.h * Math.min(amt, this.capacity) / this.capacity);"""),
        (u"""                this.displayName, this.amount.getAsInt(), this.capacity.getAsInt()), mouseX, mouseY);""",
         u"""                this.displayName, this.amount.getAsInt(), this.capacity), mouseX, mouseY);"""),
    ]
    return pairs


def main():
    os.makedirs(JAVA, exist_ok=True)
    os.makedirs(os.path.join(JAVA, "client", "gui", "parts"), exist_ok=True)
    print(u"== 反向套用本轮编辑，生成 8 份改前件 ==")
    reverse("ModFluids.java", P_MODFLUIDS_DOC + modfluids_section())
    reverse("ModItems.java", moditems_section() + P_MODITEMS_TAB)
    reverse("ModBlocks.java", modblocks_section())
    reverse("ModMenus.java", P_MODMENUS)
    reverse("PotatoST.java", P_POTATO_ST_HOOK + P_POTATO_ST_CAP)
    reverse("PotatoSTClient.java", P_CLIENT)
    reverse(os.path.join("client", "gui", "parts", "EnergyBarPart.java"), energy_bar_old())
    pairs = fluid_tank_old()
    if pairs:
        reverse(os.path.join("client", "gui", "parts", "FluidTankPart.java"), pairs)

    if "--current" in sys.argv:
        print(u"== 把改后的当前件抄进 新增文件\\（防丢） ==")
        for name in ["ModFluids.java", "ModItems.java", "ModBlocks.java", "ModMenus.java",
                     "PotatoST.java", "PotatoSTClient.java",
                     os.path.join("client", "gui", "parts", "EnergyBarPart.java"),
                     os.path.join("client", "gui", "parts", "FluidTankPart.java")] + NEW_JAVA:
            src = os.path.join(SRC, name)
            if not os.path.exists(src):
                continue
            dst = os.path.join(NEW, "src", "main", "java", "com", "potatost", "mod", name)
            os.makedirs(os.path.dirname(dst), exist_ok=True)
            shutil.copy2(src, dst)
            print(u"  [OK]   %s" % name)

    print(u"\n失败项 = %d" % len(fails))
    for f in fails:
        print(u"  !! " + f)
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())
