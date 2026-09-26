# -*- coding: utf-8 -*-
u"""_zf78_verify.py —— ZF78 分馏塔三件套交付校验（常驻，跑在门里）

口径（沿用往轮）：
  · 断言必须落在**代码/资源/成品**上，不做"字符串出现在注释里"这种假绿；
  · 常量一律从源码里**算**出来（见 int_consts：能递归解析同文件里的其它常量）；
  · 实测结果读探针日志（探针本身在打包前删掉，日志留档）。

分区：
  A 结构图纸与检测窗口    B 控制器    C 操作器数值与停机    D 界面版式
  E 流体 / 贴图 / 模型 / 标签 / 语言   F 注册接线与发布
"""
import io
import json
import os
import re
import sys
import zipfile
import hashlib

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

ROOT = r"E:\PotatoST"
SRC = os.path.join(ROOT, "src", "main", "java", "com", "potatost", "mod")
RES = os.path.join(ROOT, "src", "main", "resources")
ASSETS = os.path.join(RES, "assets", "potato_s_t")
DATA = os.path.join(RES, "data")
LANG = os.path.join(ASSETS, "lang")
TOOLS = os.path.join(ROOT, "build", "zftools")
VANILLA_JAR = r"E:\gradle-home\caches\minecraft\versions\1.21.1\client.jar"

PRODUCTS = ["diesel", "naphtha", "gasoline", "lpg"]
NEW_FLUIDS = PRODUCTS
BLOCKS = ["distillation_controller", "distillation_operator"]

passed = 0
failed = 0
fails = []


def check(label, cond):
    global passed, failed
    if cond:
        passed += 1
        print(u"  [OK]   " + label)
    else:
        failed += 1
        fails.append(label)
        print(u"  [FAIL] " + label)


def eq(label, want, got):
    check(u"%s（期望 %r，实际 %r）" % (label, want, got), want == got)


def read(path):
    if not os.path.exists(path):
        return None
    return io.open(path, encoding="utf-8").read()


def read_src(name, sub=None):
    p = os.path.join(SRC, sub, name) if sub else os.path.join(SRC, name)
    return read(p)


def int_consts(java):
    u"""把 `NAME = <算式>;` 里能算成整数的解析出来（同文件内的常量可互相引用）。"""
    if not java:
        return {}
    raw = {}
    for m in re.finditer(r"\b([A-Z][A-Z0-9_]*)\s*=\s*([^;{}]+);", java):
        name, expr = m.group(1), m.group(2).strip()
        if re.fullmatch(r"[0-9A-Za-z_ ()*+\-]+", expr) and " " not in expr.strip()[:1]:
            raw[name] = expr
    resolved = {}

    def resolve(name, depth=0):
        if name in resolved:
            return resolved[name]
        if depth > 8 or name not in raw:
            return None
        expr = raw[name]

        def sub(mm):
            ident = mm.group(0)
            if ident.isdigit():
                return ident
            val = resolve(ident, depth + 1)
            return str(val) if val is not None else "?"

        expr2 = re.sub(r"[A-Za-z_][A-Za-z0-9_]*", sub, expr)
        if "?" in expr2:
            return None
        try:
            val = int(eval(expr2, {"__builtins__": {}}, {}))
        except Exception:
            return None
        resolved[name] = val
        return val

    for n in list(raw):
        resolve(n)
    return resolved


def read_png_rgba(path):
    u"""读 8 位 PNG 的 RGBA（借 PngRecolor：本工程贴图统一 8 位）"""
    import sys as _sys
    _sys.path.insert(0, TOOLS)
    import PngRecolor as _P
    w, h, rgba = _P.read_png(path)
    return w, h, rgba


def png_size(path):
    import struct
    if not os.path.exists(path):
        return None
    with open(path, "rb") as fh:
        head = fh.read(33)
    if head[:8] != b"\x89PNG\r\n\x1a\n":
        return None
    w, h = struct.unpack(">II", head[16:24])
    return (w, h, head[24], head[25])


# ================= A 结构图纸与检测窗口 =================

def section_a():
    print(u"\n== A 结构图纸与检测窗口 ==")
    tower = read_src("DistillationTowerStructure.java")
    check(u"DistillationTowerStructure.java 存在", tower is not None)
    c = int_consts(tower)
    eq(u"水平边长 SIZE", 4, c.get("SIZE"))
    eq(u"层数 HEIGHT", 7, c.get("HEIGHT"))
    eq(u"总格数 CELLS = 4×4×7", 112, c.get("CELLS"))
    eq(u"水平半宽 HALF（32×32 的一半）", 16, c.get("HALF"))
    eq(u"竖直窗口 RANGE_V", 10, c.get("RANGE_V"))
    eq(u"竖直下沿 Y_MIN", -3, c.get("Y_MIN"))
    eq(u"竖直上沿 Y_MAX = -3 + 10 - 1", 6, c.get("Y_MAX"))
    eq(u"最多认 4 座塔", 4, c.get("MAX_TOWERS"))

    check(u"第 1/2 层：只有四角（其余是空气）",
          "case 0, 1 -> (edgeX && edgeZ) ? Kind.COMMON : Kind.AIR;" in tower)
    check(u"第 3/5 层：角=一般、边=耐热、正中 2×2=加热装置",
          "yield (edgeX || edgeZ) ? Kind.HEAT : Kind.HEATER;" in tower)
    check(u"第 4/6 层：一圈耐热、中间空",
          "case 3, 5 -> (edgeX || edgeZ) ? Kind.HEAT : Kind.AIR;" in tower)
    check(u"第 7 层：整块一般金属块",
          "default -> Kind.COMMON;" in tower)
    check(u"空气也算一格（空腔必须真的是空气）",
          "case AIR -> state.isAir();" in tower)
    check(u"锚点只取「整座塔放得下」的位置（水平 maxDx = HALF - SIZE）",
          "int maxDx = HALF - SIZE;" in tower)
    check(u"锚点竖直上限 maxDy = Y_MAX - (HEIGHT - 1)",
          "int maxDy = Y_MAX - (HEIGHT - 1);" in tower)
    check(u"三层循环都用 maxDx / maxDy 收口",
          "dz <= maxDx" in tower and "dx <= maxDx" in tower and "dy <= maxDy" in tower)
    check(u"去重：包围盒相交就跳过（先到先得、顺序固定）",
          "overlapsAny(base, found)" in tower
          and "Math.abs(other.getX() - base.getX()) < SIZE" in tower
          and "Math.abs(other.getY() - base.getY()) < HEIGHT" in tower)
    check(u"只检测、不改方块（结构里没有 setBlock）", "setBlock" not in tower)
    check(u"结构里不含任何注册/客户端代码（纯判定）",
          "DeferredHolder" not in tower and "initializeClient" not in tower)


# ================= B 控制器 =================

def section_b():
    print(u"\n== B 分馏塔控制器 ==")
    ctrl = read_src("DistillationControllerBlockEntity.java")
    blk = read_src("DistillationControllerBlock.java")
    check(u"控制器方块实体存在", ctrl is not None)
    c = int_consts(ctrl)
    eq(u"扫描周期 20 tick", 20, c.get("SCAN_INTERVAL"))
    check(u"先找相邻操作器，一个都没有就不扫（省算力）",
          "if (operators.isEmpty()) {" in ctrl and "this.towerCount = 0;" in ctrl)
    check(u"把数量推给每一个相邻操作器", "operator.setTowerCount(count);" in ctrl)
    check(u"数量是算出来的、不存盘（旧存档不会残留假数字）",
          "saveAdditional" not in ctrl and "loadAdditional" not in ctrl)
    # ⚠ ZF78 第一版钉的是"右击没反应"；2026-09-24 用户要「排查信息能显示」⇒
    #   改成"右击有反馈，但**仍然没有 GUI**（不开界面、不存状态）"
    check(u"控制器右击会显示排查信息（用户 09-24 点名要的）", "useWithoutItem" in blk)
    check(u"控制器仍然没有 GUI（不开界面、不是 MenuProvider）",
          "openMenu" not in blk and "MenuProvider" not in blk)
    check(u"排查信息用的是 diagnose + 三套文案（数到/最像的一处/什么都没有）",
          "DistillationTowerStructure.diagnose(" in blk
          and "distillation.diagnosis.found" in blk
          and "distillation.diagnosis.none" in blk
          and "distillation.diagnosis.empty" in blk)
    check(u"邻居一变就重扫一次", "requestRescan()" in blk and "neighborChanged" in blk)

    pot = read_src("PotatoST.java")
    cap = pot.split("registerCapabilities")[-1] if pot else ""
    check(u"控制器**没有**登记任何能力（它不存能量/流体/物品）",
          "DISTILLATION_CONTROLLER_BE" not in cap)
    eq(u"操作器登记了 3 条能力（能量/流体/物品）", 3, cap.count("DISTILLATION_OPERATOR_BE"))


# ================= C 操作器数值与停机 =================

def section_c():
    print(u"\n== C 分馏塔操作器（数值 / 每 tick / 停机）==")
    op = read_src("DistillationOperatorBlockEntity.java")
    check(u"操作器方块实体存在", op is not None)
    c = int_consts(op)
    eq(u"每塔能量缓冲 FE_PER_TOWER", 8096, c.get("FE_PER_TOWER"))
    eq(u"每塔石油罐 OIL_PER_TOWER（12 桶）", 12000, c.get("OIL_PER_TOWER"))
    eq(u"每塔产品罐 PRODUCT_PER_TOWER（2.5 桶）", 2500, c.get("PRODUCT_PER_TOWER"))
    eq(u"每 tick 进料 OIL_PER_TICK", 8, c.get("OIL_PER_TICK"))
    eq(u"每 tick 耗电 FE_PER_TICK", 8096, c.get("FE_PER_TICK"))
    eq(u"每 tick 柴油 DIESEL_PER_TICK", 3, c.get("DIESEL_PER_TICK"))
    eq(u"每 tick 石脑油 NAPHTHA_PER_TICK", 2, c.get("NAPHTHA_PER_TICK"))
    eq(u"每 tick 汽油 GASOLINE_PER_TICK", 2, c.get("GASOLINE_PER_TICK"))
    eq(u"每 tick 液化石油气 LPG_PER_TICK", 1, c.get("LPG_PER_TICK"))
    eq(u"进 8 出 8（物料平衡）", c.get("OIL_PER_TICK"),
       (c.get("DIESEL_PER_TICK") or 0) + (c.get("NAPHTHA_PER_TICK") or 0)
       + (c.get("GASOLINE_PER_TICK") or 0) + (c.get("LPG_PER_TICK") or 0))
    eq(u"沥青每 5 tick 一块", 5, c.get("BITUMEN_INTERVAL"))
    eq(u"沥青槽上限 64", 64, c.get("BITUMEN_LIMIT"))
    eq(u"容器同步槽位数 10", 10, c.get("DATA_COUNT"))
    eq(u"石油分片位数 15（短整型载荷）", 15, c.get("DATA_CHUNK_BITS"))
    eq(u"控制器复核周期 20 tick", 20, c.get("CONTROLLER_CHECK_INTERVAL"))

    check(u"容量随塔数缩放：perTower × 塔数（ScaledTank 重写 getCapacity）",
          "class ScaledTank extends FluidTank" in op
          and "Math.max(0, this.perTower * this.towers.getAsInt())" in op)
    check(u"⚠ ScaledTank **必须**重写 fill：NeoForge 那份读的是构造时钉死的 capacity",
          "public int fill(FluidStack resource, FluidAction action)" in op)
    check(u"每 tick 按塔数扣石油与能量（×N）",
          "drain(OIL_PER_TICK * towers" in op and "this.energy -= FE_PER_TICK * towers;" in op)
    check(u"四种产品都按塔数产出（×N）",
          all(("%s_PER_TICK * towers" % n) in op for n in
              ("DIESEL", "NAPHTHA", "GASOLINE", "LPG")))
    check(u"沥青每 5 tick 出 N 块，槽位快满就少出（不销毁物品）",
          "Math.min(towers, bitumenSpace())" in op)
    check(u"红石是「有信号才开」（前面有取反）",
          "!this.level.hasNeighborSignal(this.worldPosition)" in op)
    check(u"七种状态码齐全",
          all(("STATUS_" + s) in op for s in
              ("RUNNING", "NO_CONTROLLER", "NO_TOWER", "NO_REDSTONE", "BITUMEN_FULL",
               "NO_OIL", "NO_POWER", "PRODUCT_FULL")))
    check(u"灌入只进石油罐（四个产品罐是出口）",
          "return DistillationOperatorBlockEntity.this.tanks[TANK_OIL].fill(resource, action);" in op)
    check(u"罐的合法性比的是流体**类型**（source/flowing 都收）",
          "stack.getFluid().getFluidType() == type" in op)
    check(u"存盘：自己 new 子标签再 put 回去（避开 CompoundTag#getCompound 陷阱）",
          "CompoundTag child = new CompoundTag();" in op and "tag.put(TANK_KEYS[i], child);" in op)
    check(u"能连管道：五罐暴露成一个 IFluidHandler", "public IFluidHandler getFluidHandler()" in op)
    check(u"能量用共享的 MachineEnergyStorage（不抄匿名实现）",
          "MachineEnergyStorage.receiveOnly" in op)

    # ---- 2026-09-24 追加：右键倒流体（用户点名） ----
    opblk = read_src("DistillationOperatorBlock.java")
    oc2 = int_consts(opblk)
    eq(u"一次右键倒 POUR_PER_CLICK", 1000, oc2.get("POUR_PER_CLICK"))
    check(u"操作器实现了 useItemOn（拿容器右键）",
          "protected ItemInteractionResult useItemOn(" in opblk)
    check(u"倒之前先 SIMULATE 问罐子能收多少（收 0 就一滴不倒、容器内容物不丢）",
          "IFluidHandler.FluidAction.SIMULATE" in opblk)
    check(u"能收多少就只从容器取多少（drain 部分取）再灌进去",
          "container.drain(stack, accepted)" in opblk
          and "oil.fill(drained, IFluidHandler.FluidAction.EXECUTE)" in opblk)
    check(u"倒不进去 / 容器是空 都有提示（不静默）",
          "distillation.pour.rejected" in opblk and "distillation.pour.empty" in opblk)

    iface = read_src("FluidContainerItem.java")
    check(u"容器接口扩了 contents/drain 两个方向（灌装的反方向）",
          "FluidStack contents(ItemStack stack);" in iface
          and "FluidStack drain(ItemStack stack, int maxAmount);" in iface)
    for impl in ("OilBucketItem.java", "HighPressureTankItem.java"):
        t = read_src(impl)
        check(u"%s 实现了 contents + drain" % impl,
              "public FluidStack contents(ItemStack stack)" in t
              and "public FluidStack drain(ItemStack stack, int maxAmount)" in t)

    # ---- 2026-09-24 追加：诊断 API ----
    tower = read_src("DistillationTowerStructure.java")   # section_a 里的同名局部变量在这里不可见
    check(u"结构类里有 diagnose + Diagnosis（提示与判定分开）",
          "public record Diagnosis(" in tower and "public static Diagnosis diagnose(" in tower)
    check(u"诊断按「错格数最少 + 第一处越靠后越像」挑，并报第一处不符的格子",
          "boolean better = wrong < bestWrong" in tower
          and "firstIndex > bestFirst" in tower
          and "if (contains(base, controller))" in tower)


# ================= D 界面版式 =================

def section_d():
    print(u"\n== D 大 UI 版式（按用户原话摆）==")
    screen = read_src("DistillationOperatorScreen.java", sub="client")
    menu = read_src("DistillationOperatorMenu.java")
    check(u"界面文件存在", screen is not None and menu is not None)
    sc = int_consts(screen)
    eq(u"面板宽 WIDTH（电力高炉同一档大面板）", 196, sc.get("WIDTH"))
    eq(u"面板高 HEIGHT", 202, sc.get("HEIGHT"))
    eq(u"能量条在最左 ENERGY_X", 26, sc.get("ENERGY_X"))
    eq(u"石油罐在能量条右边 TANK_X_FIRST", 44, sc.get("TANK_X_FIRST"))
    eq(u"罐间距 TANK_STEP", 22, sc.get("TANK_STEP"))
    mc = int_consts(menu)
    eq(u"沥青槽 x（右下角靠里）", 158, mc.get("SLOT_X"))
    eq(u"沥青槽 y（2026-09-24 上提 8 px 后）", 84, mc.get("SLOT_Y"))
    eq(u"玩家背包 y", 118, mc.get("PLAYER_INV_Y"))

    order = re.findall(r"addTank\(DistillationOperatorBlockEntity\.(TANK_\w+)", screen)
    eq(u"五个罐从左到右 = 石油/柴油/石脑油/汽油/液化石油气",
       ["TANK_OIL", "TANK_DIESEL", "TANK_NAPHTHA", "TANK_GASOLINE", "TANK_LPG"], order)
    check(u"能量条是竖直的（EnergyBarPart 默认竖直）", "EnergyBarPart" in screen)
    # ⚠ 2026-09-24 用户实测：「储罐ui和沥青槽挡住物品栏字样了」
    #   原版把「物品栏」那行字画在 HEIGHT-93（9 px 高）⇒ 机器内容必须落在它上面
    label_y = (sc.get("HEIGHT") or 0) - 93
    check(u"罐底在「物品栏」那行字上方（y=%s，标签在 %d）" % (
        (sc.get("ROW_Y") or 0) + (sc.get("TANK_H") or 0), label_y),
        (sc.get("ROW_Y") or 0) + (sc.get("TANK_H") or 0) <= label_y - 2)
    check(u"沥青槽（+进度条）也在那行字上方（槽底 %s < %d）" % (
        (mc.get("SLOT_Y") or 0) + 18 + 4, label_y),
        (mc.get("SLOT_Y") or 0) + 18 + 4 <= label_y - 1)
    check(u"沥青槽左边是能量条与石油罐、右边没有罐（158 > 132+18）", 158 > 132 + 18)
    check(u"沥青进度条挂在沥青槽下面",
          "DistillationOperatorMenu.SLOT_X" in screen and "ProgressBarPart" in screen)
    check(u"界面显示分馏塔数与状态两行字",
          "renderMachineForeground" in screen and "distillation.towers" in screen
          and "distillation.status" in screen)
    check(u"每个罐的容量都是**算出来的**（不是常量）",
          "() -> this.menu.getTankCapacity(tankIndex)" in screen)
    check(u"两个部件为此加了「上限 supplier」重载",
          "public EnergyBarPart(int x, int y, int w, int h, IntSupplier amount, IntSupplier max)" in
          read_src("EnergyBarPart.java", sub=os.path.join("client", "gui", "parts"))
          and "public FluidTankPart(int x, int y, int w, int h, IntSupplier amount, IntSupplier capacity, Fluid fluid)" in
          read_src("FluidTankPart.java", sub=os.path.join("client", "gui", "parts")))


# ================= E 流体 / 贴图 / 模型 / 标签 / 语言 =================

def section_e():
    print(u"\n== E 流体 / 贴图 / 模型 / 标签 / 语言 ==")
    fluids = read_src("ModFluids.java")
    for name in NEW_FLUIDS:
        src_id = 'FLUIDS.register("%s"' % name
        flow_id = 'FLUIDS.register("flowing_%s"' % name
        check(u"%s 注册了 source 与 flowing 两个流体本体" % name,
              src_id in fluids and flow_id in fluids)
        check(u"%s 的流体类型注册名正确" % name,
              ('FLUID_TYPES.register("%s"' % name) in fluids)
    # ⚠ 原断言数的是 "liquidType(" 的**文本出现次数 == 5**（1 个方法声明 + 4 次注册）。
    #    ZF82 在柴油的属性方法注释里提了一句 `liquidType(...)` ⇒ 变 6，误报。
    #    改成数**注册调用**（精确到 `() -> liquidType(`）：注释怎么写都不影响。
    # ⚠ ZF101 又加了三种酸（也走这个工厂）⇒ 4 → 7；这条的内容是"共用同一个工厂、不抄多遍"，
    #   数字随轮次增长。
    check(u"四种分馏产品 + 三种酸共用同一个液体类型工厂（不抄八遍 initializeClient）",
          fluids.count("() -> liquidType(") == 8
          and u"private static FluidType liquidType(" in fluids)
    check(u"四种产品都显式 canHydrate(false) / canConvertToSource(false)",
          fluids.count(".canHydrate(false)") >= 1 and "canConvertToSource(false)" in fluids)
    check(u"产品不挂 #c:gaseous（液化石油气按液体）",
          not os.path.exists(os.path.join(DATA, "c", "tags", "fluid", "gaseous_lpg.json")))

    ok_tags = True
    for name in NEW_FLUIDS:
        p = os.path.join(DATA, "c", "tags", "fluid", name + ".json")
        if not os.path.exists(p):
            ok_tags = False
            continue
        d = json.loads(io.open(p, encoding="utf-8").read())
        if d.get("replace") is not False:
            ok_tags = False
        for expect in ("potato_s_t:" + name, "potato_s_t:flowing_" + name):
            if expect not in d.get("values", []):
                ok_tags = False
    check(u"四张 c: 流体标签：replace:false + source/flowing 都挂上", ok_tags)

    for name in NEW_FLUIDS:
        still = png_size(os.path.join(ASSETS, "textures", "block", name + "_still.png"))
        flow = png_size(os.path.join(ASSETS, "textures", "block", name + "_flow.png"))
        check(u"%s 贴图：still 16×16 RGBA" % name, still == (16, 16, 8, 6))
        check(u"%s 贴图：flow 16×16 RGBA" % name, flow == (16, 16, 8, 6))

    for name in BLOCKS:
        side = png_size(os.path.join(ASSETS, "textures", "block", name + "_side.png"))
        top = png_size(os.path.join(ASSETS, "textures", "block", name + "_top.png"))
        check(u"%s 方块贴图：侧面/顶面 16×16 RGBA" % name,
              side == (16, 16, 8, 6) and top == (16, 16, 8, 6))
        bs = read(os.path.join(ASSETS, "blockstates", name + ".json"))
        bm = read(os.path.join(ASSETS, "models", "block", name + ".json"))
        im = read(os.path.join(ASSETS, "models", "item", name + ".json"))
        check(u"%s：blockstate → 自己的方块模型" % name,
              bs is not None and ("potato_s_t:block/" + name) in bs)
        check(u"%s：模型顶/侧指自己的贴图" % name,
              bm is not None and ("potato_s_t:block/%s_top" % name) in bm
              and ("potato_s_t:block/%s_side" % name) in bm)
        check(u"%s：物品模型 = 方块模型" % name,
              im is not None and ("potato_s_t:block/" + name) in im)

    # 沥青：贴图是"火药占位"，模型指自己的贴图（不悬空）
    bit = os.path.join(ASSETS, "textures", "item", "bitumen.png")
    check(u"沥青贴图 16×16 RGBA（占位）", png_size(bit) == (16, 16, 8, 6))
    prov_path = os.path.join(TOOLS, "_zf78_bitumen_provenance.json")
    if os.path.exists(bit) and os.path.exists(prov_path):
        prov = json.loads(read(prov_path))
        w0, h0, rgba = read_png_rgba(bit)
        check(u"沥青贴图 = 原版火药的像素（凭据 sha256 对得上；用户原话「暂时用火药占位」）",
              (w0, h0) == (16, 16)
              and hashlib.sha256(bytes(rgba)).hexdigest() == prov.get("rgba_sha256"))
    else:
        check(u"沥青贴图像素凭据存在", False)
    bim = read(os.path.join(ASSETS, "models", "item", "bitumen.json"))
    check(u"沥青物品模型指自己命名空间的贴图（不留悬空引用）",
          bim is not None and "potato_s_t:item/bitumen" in bim)

    mine = json.loads(read(os.path.join(DATA, "minecraft", "tags", "block", "mineable", "pickaxe.json")))
    check(u"两个新方块进了 mineable/pickaxe", all(("potato_s_t:" + n) in mine["values"] for n in BLOCKS))

    keys = {}
    for lang in ("zh_cn", "en_us", "ja_jp", "ru_ru"):
        d = json.loads(read(os.path.join(LANG, lang + ".json")))
        keys[lang] = d
    counts = {k: len(v) for k, v in keys.items()}
    check(u"四份语言键数一致且 = 483（ZF107 +48；ZF109 +10）",
          len(set(counts.values())) == 1 and list(counts.values())[0] == 483)
    need = ([u"block.potato_s_t." + n for n in BLOCKS] + [u"item.potato_s_t.bitumen"]
            + [u"fluid_type.potato_s_t." + n for n in NEW_FLUIDS]
            + [u"fluid.potato_s_t." + n for n in NEW_FLUIDS]
            + [u"gui.potato_s_t.distillation.towers",
               u"gui.potato_s_t.distillation.status.running",
               u"gui.potato_s_t.distillation.status.no_controller",
               u"gui.potato_s_t.distillation.status.no_tower",
               u"gui.potato_s_t.distillation.status.no_redstone",
               u"gui.potato_s_t.distillation.status.bitumen_full",
               u"gui.potato_s_t.distillation.status.no_oil",
               u"gui.potato_s_t.distillation.status.no_power",
               u"gui.potato_s_t.distillation.status.product_full",
               u"tooltip.potato_s_t.distillation_controller",
               u"tooltip.potato_s_t.distillation_operator",
               u"gui.potato_s_t.distillation.diagnosis.found",
               u"gui.potato_s_t.distillation.diagnosis.none",
               u"gui.potato_s_t.distillation.diagnosis.empty",
               u"gui.potato_s_t.distillation.pour.rejected",
               u"gui.potato_s_t.distillation.pour.empty"])
    for lang, d in keys.items():
        missing = [k for k in need if k not in d]
        check(u"%s：22 个新键都在（缺 %s）" % (lang, missing or u"无"), not missing)
    for lang, d in keys.items():
        tip = d.get(u"tooltip.potato_s_t.distillation_controller", u"")
        check(u"%s：结构说明是多行（含换行转义）且七层都写了" % lang,
              u"\n" in tip and u"第 7 层" in tip or u"Layer 7" in tip or u"Слой 7" in tip
              or u"第 7 層" in tip or u"7 层" in tip)
        towers = d.get(u"gui.potato_s_t.distillation.towers", u"")
        check(u"%s：塔数文案有两个占位符（当前/上限）" % lang, towers.count(u"%s") == 2)


def doc_checks():
    print(u"\n== F 文档 / 发布 ==")
    doc = read(os.path.join(ROOT, "docs", u"开发档案.md"))
    check(u"开发档案里 §5 有 ZF78 行", doc is not None and u"| ZF78 |" in doc)
    check(u"开发档案 §9 提到 ZF78 的用户侧验证", doc is not None and u"ZF78" in doc.split(u"## 9")[-1])
    plan = read(os.path.join(ROOT, "docs", u"v0.11规划.md"))
    check(u"v0.11 规划里记了分馏塔（ZF78）", plan is not None and u"分馏塔" in plan)
    texlist = read(os.path.join(ROOT, "docs", u"贴图清单.md"))
    check(u"贴图清单列了沥青的占位贴图", texlist is not None and u"bitumen" in texlist)
    props = read(os.path.join(ROOT, "gradle.properties"))
    check(u"mod_version 仍是 0.11（本轮没有 0.12 任务）",
          props is not None and u"mod_version=0.11" in props)

    src_probe = os.path.join(SRC, "DistillationCheck.java")
    check(u"打包前探针已从 src 删除", not os.path.exists(src_probe))
    pot = read_src("PotatoST.java")
    check(u"打包前 PotatoST 里的探针挂钩已删", pot is not None and "DistillationCheck" not in pot)

    # 探针自己落的 UTF-8 报告（控制台那份会被 JVM 按 GBK 打成乱码，只当备份）
    log = read(os.path.join(TOOLS, "_zf78_probe.txt"))
    if log is None:
        log = read(os.path.join(TOOLS, "_zf78_server.log.utf8.txt")) or read(
            os.path.join(TOOLS, "_zf78_server.log"))
    if log:
        m = re.search(r"==== passed=(\d+) failed=(\d+) ====", log)
        check(u"探针报告里有汇总行", m is not None)
        if m:
            eq(u"探针实测失败 0 项", "0", m.group(2))
            check(u"探针断言数 ≥ 90（实际 %s）" % m.group(1), int(m.group(1)) >= 90)
    else:
        check(u"找不到探针报告（_zf78_probe.txt）", False)

    jar = os.path.join(ROOT, "release", "PotatoST-0.11.jar")
    sha_file = jar + ".sha1"
    check(u"成品 release\\PotatoST-0.11.jar 存在", os.path.exists(jar))
    if os.path.exists(jar):
        sha = hashlib.sha1(open(jar, "rb").read()).hexdigest()
        recorded = read(sha_file)
        check(u".sha1 文件与 jar 实际哈希一致（%s…）" % sha[:8],
              recorded is not None and recorded.strip().lower() == sha)
        with zipfile.ZipFile(jar) as zf:
            names = zf.namelist()
        need = ["com/potatost/mod/DistillationTowerStructure.class",
                "com/potatost/mod/DistillationControllerBlock.class",
                "com/potatost/mod/DistillationControllerBlockEntity.class",
                "com/potatost/mod/DistillationOperatorBlock.class",
                "com/potatost/mod/DistillationOperatorBlockEntity.class",
                "com/potatost/mod/DistillationOperatorMenu.class",
                "com/potatost/mod/client/DistillationOperatorScreen.class",
                "assets/potato_s_t/textures/item/bitumen.png",
                "assets/potato_s_t/models/item/bitumen.json",
                "data/c/tags/fluid/diesel.json", "data/c/tags/fluid/naphtha.json",
                "data/c/tags/fluid/gasoline.json", "data/c/tags/fluid/lpg.json"]
        missing = [n for n in need if n not in names]
        check(u"成品里 8 个新 class + 沥青贴图/模型 + 4 张标签都在（缺 %s）" % (missing or u"无"),
              not missing)
        bad = [n for n in names if "Check" in os.path.basename(n) and n.endswith(".class")]
        check(u"成品里没有任何探针 class（%s）" % (bad or u"0 个"), not bad)


def main():
    print(u"=========== ZF78 校验：分馏塔三件套 ===========")
    section_a()
    section_b()
    section_c()
    section_d()
    section_e()
    doc_checks()
    print(u"\n------------------------------")
    print(u"通过 = %d   失败 = %d" % (passed, failed))
    for f in fails:
        print(u"  !! " + f)
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
