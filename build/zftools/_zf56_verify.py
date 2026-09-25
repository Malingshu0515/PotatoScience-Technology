# -*- coding: utf-8 -*-
"""_zf56_verify.py —— 主控 ≠ 大盒子：模型必须跟着成型状态走

用户原话：「**不是主控变成4x5x4是合金炉！合金炉成型后模型！**」
ZF54 把 OBJ 直接挂在 `facing` 上 ⇒ 一放下主控就是个 4×5×4 大盒子。这里把"改对了"钉成断言：

  ① Java 里必须有 `formed` 方块状态、默认 false、并注册进 stateDefinition；
  ② blockstate 必须有 `formed=false`（→ 主控那个 cube_all 模型，**且那个模型不能是 obj**）
     与 4 个 `facing=X,formed=true`（→ 四份 OBJ）；
  ③ 物品模型必须还是主控那个小方块（`models/item/alloy_smelter.json` 指向 block/alloy_smelter）；
  ④ 成型时切状态、拆解时切回来，而且 **`setFormed(false)` 必须在 `disassemble` 的 try 内**
     （放到 finally 之后 = 拆完外壳是完整的 ⇒ 当场自动重新成型，机器白拆）；
  ⑤ 切状态前必须确认"那格还是控制器"（否则挖控制器的那条路会把方块复活）；
  ⑥ 每秒自愈一次（方块状态与 NBT 对不上时拉回来）。
"""
import io
import json
import os
import re
import sys

PROJ = r"E:\PotatoST"
JAVA = os.path.join(PROJ, "src", "main", "java", "com", "potatost", "mod")
ASSETS = os.path.join(PROJ, "src", "main", "resources", "assets", "potato_s_t")
FACINGS = ("north", "east", "south", "west")

fails = []


def check(cond, msg):
    print((u"  [OK]   " if cond else u"  [FAIL] ") + msg)
    if not cond:
        fails.append(msg)


def read(path):
    return io.open(path, encoding="utf-8").read()


def main():
    src_block = read(os.path.join(JAVA, "AlloySmelterBlock.java"))
    src_be = read(os.path.join(JAVA, "AlloySmelterBlockEntity.java"))
    bs = json.loads(read(os.path.join(ASSETS, "blockstates", "alloy_smelter.json")))
    variants = bs["variants"]

    # ---------- ① Java 里的方块状态 ----------
    print(u"① 方块状态 formed")
    check('BooleanProperty FORMED = BooleanProperty.create("formed")' in src_block,
          u"AlloySmelterBlock 声明了 formed 方块状态")
    check("builder.add(FACING, FORMED);" in src_block, u"formed 注册进 createBlockStateDefinition")
    check(".setValue(FORMED, false)" in src_block, u"默认值 false（放下就是主控小方块）")

    # ---------- ② blockstate 两个变体 ----------
    print(u"\n② blockstate：未成型是小方块，成型才是 4 份 OBJ")
    check("formed=false" in variants, u"有 formed=false 变体")
    plain = variants.get("formed=false", {}).get("model")
    check(plain == "potato_s_t:block/alloy_smelter",
          u"formed=false -> block/alloy_smelter（读到 %s）" % plain)
    for facing in FACINGS:
        key = "facing=%s,formed=true" % facing
        got = variants.get(key, {}).get("model")
        check(got == "potato_s_t:block/alloy_smelter_" + facing,
              u"%s -> block/alloy_smelter_%s（读到 %s）" % (key, facing, got))
    check(sorted(variants) == sorted(["formed=false"] + ["facing=%s,formed=true" % f for f in FACINGS]),
          u"变体正好 5 条，没有多余的（%s）" % sorted(variants))

    # 那个"小方块"模型绝不能是 obj
    plain_model = json.loads(read(os.path.join(ASSETS, "models", "block", "alloy_smelter.json")))
    check("loader" not in plain_model, u"block/alloy_smelter 不是 neoforge:obj（就是个普通立方体）")
    check(plain_model.get("parent") == "minecraft:block/cube_all",
          u"block/alloy_smelter 是 cube_all")
    check(plain_model.get("textures", {}).get("all") == "potato_s_t:block/alloy_smelter",
          u"block/alloy_smelter 用主控那张贴图")
    for facing in FACINGS:
        one = json.loads(read(os.path.join(ASSETS, "models", "block",
                                          "alloy_smelter_%s.json" % facing)))
        check(one.get("loader") == "neoforge:obj", u"alloy_smelter_%s 是 obj" % facing)

    # ---------- ③ 物品模型 ----------
    print(u"\n③ 物品 = 主控小方块")
    item = json.loads(read(os.path.join(ASSETS, "models", "item", "alloy_smelter.json")))
    check(item.get("parent") == "potato_s_t:block/alloy_smelter",
          u"models/item/alloy_smelter.json 还是指向主控小方块")

    # ---------- ④⑤⑥ 方块实体这一侧 ----------
    print(u"\n④ 切换时机 / 防复活 / 自愈")
    check("private void applyFormedState()" in src_be, u"有 applyFormedState()")
    check("state.setValue(AlloySmelterBlock.FORMED, this.formed)" in src_be,
          u"applyFormedState 真的换方块状态")
    check("if (!state.is(ModBlocks.ALLOY_SMELTER.get()))" in src_be,
          u"切状态前确认那格还是控制器（防「复活」）")

    body = src_be.split("public void disassemble(BlockPos skip)")[1].split("\n    /**")[0]
    i_set = body.find("setFormed(false);")
    i_fin = body.find("} finally {")
    check(i_set >= 0, u"disassemble 里真的调了 setFormed(false)")
    check(i_set >= 0 and i_fin >= 0 and i_set < i_fin,
          u"setFormed(false) 在 try 内（@%d）而不是 finally 之后（@%d）" % (i_set, i_fin))
    check("setFormed(false);" not in body.split("} finally {")[1],
          u"finally 之后没有再调一次 setFormed(false)")

    # ZF64 重构：服务端 tick 被拆成 serverTick()（只管"运行 ⇄ 停止"翻转时发包）+ serverTickBody()（原正文）。
    # 自愈那两句于是搬进了 serverTickBody —— 锚点跟着搬，**断言本身不放宽**（2026-09-19 记录）。
    anchor = u"private void serverTickBody()" if u"private void serverTickBody()" in src_be \
        else u"private void serverTick()"
    tick = src_be.split(anchor)[1].split("\n    }")[0]
    check("applyFormedState();" in tick, u"服务端 tick 里每秒自愈一次")
    check("!this.disassembling" in tick, u"自愈避开拆解途中")

    print(u"\n------------------------------")
    print(u"失败项 = %d" % len(fails))
    print(u"结论: " + (u"通过" if not fails else u"有失败项"))
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())
