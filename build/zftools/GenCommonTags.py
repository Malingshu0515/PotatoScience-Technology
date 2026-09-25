# -*- coding: utf-8 -*-
"""GenCommonTags.py —— 生成 `data/c/tags/**` 下的 c: 通用标签文件（0.10 ZF13）

**为什么要脚本而不是手打**：项目规则是「**以后的矿物、合金、矿物锭默认兼容别的 mod**」（用户指令）。
每加一种矿就要挂 6~7 个标签文件（锭的嵌套+扁平、粗矿、矿石的 item+block、还有两个 ores_in_ground），
手打迟早漏。改完 `METALS` / `ALLOYS` 重跑本脚本即可，`Audit.ps1` 的 **J 项**会核对结果。

跑法：
    python E:\\PotatoST\\build\\zftools\\GenCommonTags.py            # 生成
    python E:\\PotatoST\\build\\zftools\\GenCommonTags.py --dry      # 只看要写哪些文件

**格式约定**（0.10 解包核实，写错就等于没写）：
  - 标签文件路径 = `data/<标签命名空间>/tags/<注册表>/<标签路径>.json`
    我们是往 **`c`** 这个命名空间里加东西 ⇒ **`data/c/tags/item/...`**（不是 `data/potato_s_t/`！）
  - `item` / `block` 是**单数**（1.20.5 起；1.20.1 及以前是复数的 `items`/`blocks`）
  - 标签文件跨 mod **合并**，`replace` 默认 false，所以别写 replace
  - 扁平写法（`c:steel_ingots`）与嵌套写法（`c:ingots/steel`）**同时存在**于生态里
    （ad_astra / createbigcannons 两种都发），所以两种都生成
"""
import io
import json
import os
import sys

# 0.11 ZF121：控制台默认 GBK，脚本里那句 "⚠ 这些 c: 标签文件不是本脚本写的" 一 print 就
# UnicodeEncodeError **崩在反向体检那一行** —— 文件其实都写完了，但"多不多余"这条结论永远看不到
# （本轮就踩了：崩掉之后 4 条冗余文件一条都没报出来）。别的 zf 脚本都有这段，补上。
try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

MODID = "potato_s_t"
ROOT = os.path.join("E:\\PotatoST", "src", "main", "resources", "data", "c", "tags")

# (材料名, 锭物品id 或 None, 粗矿物品id 或 None, [矿石方块 id...])
METALS = [
    ("aluminum", "aluminum_ingot", "raw_aluminum", ["aluminum_ore"]),
    ("cobalt", "cobalt_ingot", "raw_cobalt", ["cobalt_ore", "deepslate_cobalt_ore"]),
    ("nickel", "nickel_ingot", "raw_nickel", ["nickel_ore", "deepslate_nickel_ore"]),
    ("silver", "silver_ingot", "raw_silver", ["silver_ore", "deepslate_silver_ore"]),
    ("uranium", "uranium_ingot", "raw_uranium", ["uranium_ore", "deepslate_uranium_ore"]),
    ("manganese", None, "raw_manganese", ["manganese_ore", "deepslate_manganese_ore"]),
    # 锂（0.10 ZF15）：没有锭，只有矿石 + 粗锂 —— 正好落在「矿物默认兼容」的口径内
    ("lithium", None, "raw_lithium", ["lithium_ore"]),
    # 钨（0.10 ZF46）：黑钨矿 + 粗钨，同样**没有锭**（用户指定"目前不可以被任何东西冶炼"）。
    # 标签名用 tungsten（材料名）而不是 wolframite（矿物名）：粗钨那个物品叫 raw_tungsten，
    # 别的 mod 的钨矿/粗钨只要挂 c:ores/tungsten / c:raw_materials/tungsten 就能对上。
    ("tungsten", None, "raw_tungsten", ["wolframite_ore", "deepslate_wolframite_ore"]),
    # 钛（0.10 ZF48）：**有锭**（钛粉进电力高炉烧出来）⇒ 锭/粗矿/矿石三类标签都挂。
    # 「稀有度比黄金略高」是世界生成的事，与标签无关。
    ("titanium", "titanium_ingot", "raw_titanium", ["titanium_ore", "deepslate_titanium_ore"]),
    # 振金（0.11 ZF121 补登记）：**有锭（ZF119）也有粗振金（ZF114）**，但**没有矿石方块**
    # （粗振金是星轨坠的陨石砸出来的）⇒ 粗矿那一栏有值、矿石那一栏是空表。
    #
    # ⚠ **这一条补的是"表 ↔ 盘"的漂移（§4.93 第 3 次）**：ZF114 手写了
    # `raw_materials/vibranium.json` + 往 `raw_materials.json` 里加了一行，ZF119 手写了
    # `ingots/vibranium.json` / `vibranium_ingots.json` + 往 `ingots.json` 里加了一行，
    # **两次都没登记到这张表里**。后果：只要有人重跑一次本脚本，父标签里那两行就被抹掉
    # （ZF121 第一跑实测：`c:ingots` 10 → 11 项却**少了** vibranium_ingot、
    # `c:raw_materials` 10 → 9 项**少了** raw_vibranium），而且反向体检会把那 3 份
    # 手写文件报成"多余文件"。登记进来之后，这三份由本脚本拥有，怎么重跑都不会漂。
    ("vibranium", "vibranium_ingot", "raw_vibranium", []),
]

# 合金：材料名 → 物品 id（"高碳钢"按钢算）
# 0.10 ZF62 追加「轻质钛合金」（合金炉第一条配方：铝+钛+银 → 轻质钛合金）。
# 它按**合金**处理（跟高碳钢同一类）：c:ingots + c:ingots/titanium_alloy + 扁平的 c:titanium_alloy_ingots，
# 并进 c:ingots 汇总 —— 这样合金炉的输入槽（只收 #c:ingots）也能把它再吃进去。
# 0.11 ZF103 追加「星璨钢」（用户给的金属，本轮只有"修理星璨钢套"一个用途，**没有配方**）。
# 它同样是合金/锭那一类 ⇒ 走同一套标签。注意：挂进 c:ingots 的副作用是
# **合金炉的输入槽也会收它**（输入槽只认 #c:ingots）—— 与轻质钛合金同一条口径，是有意的。
ALLOYS = [("steel", "high_carbon_steel"),
          ("titanium_alloy", "light_titanium_alloy"),
          ("star_steel", "star_steel_ingot"),
          # 0.11 ZF121 追加「硬质钛合金」「热力金属」—— 用户给的**振金锭配方**把它们当输入锭用
          # （c:ingots/hard_titanium_alloy ×1、c:ingots/thermal_metal ×8）。
          # 不挂这一套，合金炉的输入槽（只收 #c:ingots）就放不进这两样，配方永远开不了工，
          # 而静态检查看不出来（表里只是个 TagKey —— 与 ZF111 的 c:ingots/netherite 同一类坑）。
          # 注意副作用：挂进 c:ingots ⇒ **合金炉的输入槽也会收它们**（与轻质钛合金同一条口径，有意）。
          ("hard_titanium_alloy", "hard_titanium_alloy"),
          ("thermal_metal", "thermal_metal")]

# 单件：标签名 → 物品 id（硅。它有确切实证 —— Refined Storage 用 forge/c:silicon ——
# 但严格说属于"其他物品"，用户若按那个口径否决，删掉这一行重跑即可）
SINGLES = [("silicon", "silicon")]


def item(name):
    return "{0}:{1}".format(MODID, name)


def write(rel_path, values, dry):
    full = os.path.join(ROOT, rel_path.replace("/", os.sep))
    body = json.dumps({"values": values}, ensure_ascii=False, indent=2)
    text = body + "\n"
    if dry:
        print("  [dry] data/c/tags/{0}  <- {1}".format(rel_path, ", ".join(values)))
        return full
    os.makedirs(os.path.dirname(full), exist_ok=True)
    # UTF-8 无 BOM + LF（JSON 数据文件，不参与 §4.8 的换行风格约束，但保持一致更省心）
    with io.open(full, "w", encoding="utf-8", newline="\n") as fh:
        fh.write(text)
    print("  [写] data/c/tags/{0}  ({1} 项)".format(rel_path, len(values)))
    return full


def main(argv):
    dry = "--dry" in argv
    written = []

    print("== 锭（嵌套 + 扁平两种写法都发）==")
    ingots_nested, ingots_flat, all_ingots = [], [], []
    for material, ingot_id, _raw, _ores in METALS:
        if not ingot_id:
            continue
        written.append(write("item/ingots/{0}.json".format(material), [item(ingot_id)], dry))
        written.append(write("item/{0}_ingots.json".format(material), [item(ingot_id)], dry))
        all_ingots.append(item(ingot_id))
    for material, alloy_id in ALLOYS:
        written.append(write("item/ingots/{0}.json".format(material), [item(alloy_id)], dry))
        written.append(write("item/{0}_ingots.json".format(material), [item(alloy_id)], dry))
        all_ingots.append(item(alloy_id))

    print("== 粗矿 ==")
    all_raws = []
    for material, _ingot, raw_id, _ores in METALS:
        if not raw_id:
            continue
        written.append(write("item/raw_materials/{0}.json".format(material), [item(raw_id)], dry))
        all_raws.append(item(raw_id))

    print("== 矿石（item + block 两份）==")
    all_ore_items, stone_ores, deepslate_ores = [], [], []
    for material, _ingot, _raw, ores in METALS:
        if not ores:
            continue
        values = [item(o) for o in ores]
        written.append(write("item/ores/{0}.json".format(material), values, dry))
        written.append(write("block/ores/{0}.json".format(material), values, dry))
        all_ore_items.extend(values)
        for o in ores:
            (deepslate_ores if o.startswith("deepslate_") else stone_ores).append(item(o))

    print("== 矿石所在的岩石（block 标签，别的 mod 的机器靠它判掉落）==")
    written.append(write("block/ores_in_ground/stone.json", stone_ores, dry))
    written.append(write("block/ores_in_ground/deepslate.json", deepslate_ores, dry))

    print("== 单件 ==")
    for tag_name, single_id in SINGLES:
        written.append(write("item/{0}.json".format(tag_name), [item(single_id)], dry))

    print("== 大类父标签（NeoForge 只列了原版子标签，不挂这层别人查『任意锭』看不到我们）==")
    written.append(write("item/ingots.json", all_ingots, dry))
    written.append(write("item/ores.json", all_ore_items, dry))
    written.append(write("item/raw_materials.json", all_raws, dry))

    # 反向体检：data/c/tags 下有没有"我没写过"的遗留文件（改了清单后最容易残留）
    if not dry:
        expected = set(os.path.normcase(p) for p in written)
        stale = []
        for root, _dirs, files in os.walk(ROOT):
            for f in files:
                if not f.endswith(".json"):
                    continue
                full = os.path.normcase(os.path.join(root, f))
                if full not in expected:
                    stale.append(os.path.relpath(full, ROOT))
        print("")
        if stale:
            print("⚠ 这些 c: 标签文件不是本脚本写的，确认是否该删：")
            for s in stale:
                print("    " + s)
        else:
            print("反向体检：data/c/tags 下没有多余文件")

    print("")
    print("共 {0} 个标签文件{1}".format(len(written), "（dry run，未落盘）" if dry else ""))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
