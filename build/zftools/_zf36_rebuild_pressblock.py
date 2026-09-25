# -*- coding: utf-8 -*-
"""把 `HydraulicPressBlock.java` 的**改前**版本补进 zf36_pre。

⚠ 诚实记录：它**不在** `_zf36_backup.ps1` 的清单里 —— 那个清单是我在动手前写的，
  当时还没意识到"加循环音效"必须同时改方块的 `getTicker`（原实现客户端 `return null`）。
  这是 §10 那个老毛病的**第五次**，但这次是**在改完立刻发现、并且能精确反向重建**的。

重建办法（来源等级 ③ 的加强版：**逐字节反向替换**）：
  ZF36 对这份文件的编辑只有一处 —— 把"客户端 return null"的那段换成双端 ticker，
  用的正是 `edit` 工具的 `old_string` / `new_string`。两个串都是逐字节已知的，
  所以拿当前文件做一次**精确反向替换**就能还原改前内容，不存在"凭印象重写"的成分。

验证：
  ① 反向替换后必须含 `if (level.isClientSide) { return null; }`（改前特征）
  ② 把重建件塞回源码树编译，取 `HydraulicPressBlock.class`，
     与 `zf35_pre\\_改后_PotatoST-0.10.jar` 里的同名 class **逐字节比对** ——
     javac 会把行号写进 LineNumberTable，所以**字节相同 = 重建件连空行位置都对**。
"""
import hashlib
import io
import os
import sys

PROJ = r"E:\PotatoST"
BK = r"C:\Users\Administrator\Desktop\PotatoST救援_20260917_183054\zf36_pre"
SRC = os.path.join(PROJ, r"src\main\java\com\potatost\mod\HydraulicPressBlock.java")

# 与 `edit` 调用里的两个串逐字节一致
NEW_BLOCK = u"""/**
 * 液压机方块（0.10 ZF30）：普通方块模型（对称无朝向），右键开 GUI。
 *
 * <p>与微型粉碎机同一个骨架：{@code codec()}（1.20.5 起 {@code BaseEntityBlock} 的抽象方法）、
 * 双端 tick、右键开菜单、{@code onRemove} 掉出内容物。</p>
 *
 * <p><b>⚠ 双端 tick 是 0.10 ZF36 改的，理由值得记：</b>ZF30 时这台机器没有音效，所以
 * {@code getTicker} 在客户端直接 {@code return null}（"省一次每 tick 的空转"）。
 * ZF36 给它加了循环液压声之后，<b>忘记把这里改回双端</b> ⇒ 客户端根本没有 ticker，
 * {@code HydraulicPressBlockEntity.tick} 的客户端分支永远不执行 ⇒
 * <b>注册、sounds.json、ogg 文件全部正确，游戏里却一点声音都没有，而且不报任何错</b>。
 * 与微型粉碎机 / 电解器 / 发电机同一个写法。</p>
 */
public class HydraulicPressBlock extends BaseEntityBlock {

    public HydraulicPressBlock(Properties properties) {
        super(properties);
    }

    @Override
    protected MapCodec<? extends BaseEntityBlock> codec() {
        return simpleCodec(HydraulicPressBlock::new);
    }

    @Override
    public BlockEntity newBlockEntity(BlockPos pos, BlockState state) {
        return new HydraulicPressBlockEntity(pos, state);
    }

    /** 双端都要 tick：客户端那一侧负责驱动"运行中"的循环液压声（{@code MachineRunningSound}）。 */
    @Override
    public <T extends BlockEntity> BlockEntityTicker<T> getTicker(Level level, BlockState state,
                                                                  BlockEntityType<T> type) {
        return createTickerHelper(type, ModBlocks.HYDRAULIC_PRESS_BE.get(), HydraulicPressBlockEntity::tick);
    }"""

OLD_BLOCK = u"""/**
 * 液压机方块（0.10 ZF30）：普通方块模型（对称无朝向），右键开 GUI。
 *
 * <p>与微型粉碎机同一个骨架：{@code codec()}（1.20.5 起 {@code BaseEntityBlock} 的抽象方法）、
 * 服务端 tick、右键开菜单、{@code onRemove} 掉出内容物。这里没有循环音效，所以
 * <b>只需要服务端 tick</b>（客户端不注册 ticker，省一次每 tick 的空转）。</p>
 */
public class HydraulicPressBlock extends BaseEntityBlock {

    public HydraulicPressBlock(Properties properties) {
        super(properties);
    }

    @Override
    protected MapCodec<? extends BaseEntityBlock> codec() {
        return simpleCodec(HydraulicPressBlock::new);
    }

    @Override
    public BlockEntity newBlockEntity(BlockPos pos, BlockState state) {
        return new HydraulicPressBlockEntity(pos, state);
    }

    /** 只有服务端 tick（压板是纯服务端逻辑，客户端没有要驱动的东西）。 */
    @Override
    public <T extends BlockEntity> BlockEntityTicker<T> getTicker(Level level, BlockState state,
                                                                  BlockEntityType<T> type) {
        if (level.isClientSide) {
            return null;
        }
        return createTickerHelper(type, ModBlocks.HYDRAULIC_PRESS_BE.get(), HydraulicPressBlockEntity::tick);
    }"""

text = io.open(SRC, encoding="utf-8", newline="").read()

if text.count(NEW_BLOCK) != 1:
    print("[FAIL] 当前文件里找不到唯一的新块（count=%d），不猜，停" % text.count(NEW_BLOCK))
    sys.exit(1)
if text.count(OLD_BLOCK) != 0:
    print("[FAIL] 当前文件里竟然已有旧块，说明文件不是我以为的状态，停")
    sys.exit(1)

before = text.replace(NEW_BLOCK, OLD_BLOCK, 1)
if "if (level.isClientSide) {\n            return null;\n        }" not in before:
    print("[FAIL] 反向替换后没看到改前特征 `if (level.isClientSide) { return null; }`")
    sys.exit(1)

dst = os.path.join(BK, "HydraulicPressBlock.java")
with io.open(dst, "w", encoding="utf-8", newline="") as f:
    f.write(before)
print("[OK] 已写出重建件 %s（%d 字节）" % (dst, os.path.getsize(dst)))
print("  改前行数 = %d" % before.count("\n"))
print("  当前行数 = %d" % text.count("\n"))
print("  行数差   = %d（新增的 javadoc 与双端 ticker 说明）" % (text.count("\n") - before.count("\n")))


def sha(p):
    return hashlib.sha256(io.open(p, "rb").read()).hexdigest()


print("  重建件 SHA256 = " + sha(dst))
# 顺手把当前（改后）版本也留一份，便于 diff
with io.open(os.path.join(BK, "改后_HydraulicPressBlock.java"), "w", encoding="utf-8", newline="") as f:
    f.write(text)
print("[OK] 已写出改后副本 改后_HydraulicPressBlock.java")
