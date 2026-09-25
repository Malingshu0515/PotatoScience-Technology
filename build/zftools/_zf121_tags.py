# -*- coding: utf-8 -*-
u"""_zf121_tags.py —— 把「硬质钛合金 / 热力金属」挂进 c: 通用锭标签（0.11 ZF121）

**为什么非挂不可**（这是用户那条配方能不能跑起来的前提，不是"顺手加的"）：
用户要的输入是「1 硬质钛合金 + 8 热力金属 + 2 高碳钢 + 3 银锭 + 12 金锭」，而合金冶炼炉的
5 个输入槽**只收 `#c:ingots`**（ZF49 用户原话「五个输入槽（只能接受锭标签）」）。

改前盘上 `data/c/tags/item/ingots.json` 只有 10 项：铝/钴/镍/银/铀/钛/高碳钢/轻质钛合金/
星璨钢/振金锭 —— **硬质钛合金（ZF104 加的）与热力金属（ZF45 加的）都不在里面**
（ZF104 当年只把它当"产物"用，没给它挂标签；热力金属当年只有加热装置一个下游）。
⇒ 不挂标签：这两样**放不进输入槽**，配方永远开不了工，而静态检查完全看不出来
（表里写的只是个 TagKey，跟 ZF111 踩的 `c:ingots/netherite` 是同一类坑）。

口径（项目长期规则「以后的矿物、合金、矿物锭默认兼容别的 mod」）：两样都按**合金/锭**走
同一套 —— `c:ingots/<材料>` + 扁平的 `c:<材料>_ingots`，并进父标签 `c:ingots`。

⚠ **顺带补掉两处「表 ↔ 盘」漂移（§4.93 第 3 次）**：第一次跑生成器时实测
`c:ingots` 少了 `vibranium_ingot`（ZF119 手写的）、`c:raw_materials` 少了 `raw_vibranium`
（ZF114 手写的）—— 两轮都是**直接改父标签 JSON、没登记进 ALLOYS/METALS 表**。
本轮把振金登记进 METALS（锭 + 粗矿，没有矿石方块），那三份手写文件从此由生成器拥有。

跑法：
    python build\\zftools\\_zf121_tags.py             # 只校验（不动盘）
    python build\\zftools\\_zf121_tags.py --check     # 同上，但把生成器再跑一遍看反向体检
    python build\\zftools\\_zf121_tags.py --write     # 打补丁 + 重跑生成器
"""
import io
import json
import os
import subprocess
import sys

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

ROOT = r"E:\PotatoST"
TOOLS = os.path.join(ROOT, "build", "zftools")
GEN = os.path.join(TOOLS, "GenCommonTags.py")
LOG = os.path.join(TOOLS, "_zf121_tags.log")
TAGS = os.path.join(ROOT, "src", "main", "resources", "data", "c", "tags", "item")

VIB_METALS = u'    ("vibranium", "vibranium_ingot", "raw_vibranium", []),'

OLD = u'''ALLOYS = [("steel", "high_carbon_steel"),
          ("titanium_alloy", "light_titanium_alloy"),
          ("star_steel", "star_steel_ingot")]'''

NEW = u'''ALLOYS = [("steel", "high_carbon_steel"),
          ("titanium_alloy", "light_titanium_alloy"),
          ("star_steel", "star_steel_ingot"),
          # 0.11 ZF121 追加「硬质钛合金」「热力金属」—— 用户给的**振金锭配方**把它们当输入锭用
          # （c:ingots/hard_titanium_alloy ×1、c:ingots/thermal_metal ×8）。
          # 不挂这一套，合金炉的输入槽（只收 #c:ingots）就放不进这两样，配方永远开不了工，
          # 而静态检查看不出来（表里只是个 TagKey —— 与 ZF111 的 c:ingots/netherite 同一类坑）。
          # 注意副作用：挂进 c:ingots ⇒ **合金炉的输入槽也会收它们**（与轻质钛合金同一条口径，有意）。
          ("hard_titanium_alloy", "hard_titanium_alloy"),
          ("thermal_metal", "thermal_metal")]'''

# 期望落盘的 4 份新标签 + 2 份"漂移补登记"的旧标签
WANT = [(os.path.join(TAGS, "ingots", "hard_titanium_alloy.json"),
         [u"potato_s_t:hard_titanium_alloy"], u"c:ingots/hard_titanium_alloy"),
        (os.path.join(TAGS, "hard_titanium_alloy_ingots.json"),
         [u"potato_s_t:hard_titanium_alloy"], u"c:hard_titanium_alloy_ingots"),
        (os.path.join(TAGS, "ingots", "thermal_metal.json"),
         [u"potato_s_t:thermal_metal"], u"c:ingots/thermal_metal"),
        (os.path.join(TAGS, "thermal_metal_ingots.json"),
         [u"potato_s_t:thermal_metal"], u"c:thermal_metal_ingots"),
        (os.path.join(TAGS, "ingots", "vibranium.json"),
         [u"potato_s_t:vibranium_ingot"], u"c:ingots/vibranium（ZF119 手写 → 表内）"),
        (os.path.join(TAGS, "vibranium_ingots.json"),
         [u"potato_s_t:vibranium_ingot"], u"c:vibranium_ingots（ZF119 手写 → 表内）"),
        (os.path.join(TAGS, "raw_materials", "vibranium.json"),
         [u"potato_s_t:raw_vibranium"], u"c:raw_materials/vibranium（ZF114 手写 → 表内）"),
        ]

PARENT_INGOTS = os.path.join(TAGS, "ingots.json")
PARENT_RAWS = os.path.join(TAGS, "raw_materials.json")
NEED_INGOTS = [u"potato_s_t:hard_titanium_alloy", u"potato_s_t:thermal_metal",
               u"potato_s_t:vibranium_ingot"]
NEED_RAWS = [u"potato_s_t:raw_vibranium"]
EXPECT_INGOTS_N = 12
EXPECT_RAWS_N = 10


def read(p):
    return io.open(p, encoding="utf-8").read()


def write(p, text):
    io.open(p, "w", encoding="utf-8", newline=u"\n").write(text)


def run_gen():
    r = subprocess.run([sys.executable, GEN], stdout=subprocess.PIPE,
                       stderr=subprocess.STDOUT, cwd=ROOT)
    out = r.stdout.decode("utf-8", "replace")
    io.open(LOG, "w", encoding="utf-8", newline=u"\n").write(out)
    return r.returncode, out


def stale_list(out):
    u"""反向体检名单：标记行之后那些**缩进 4 空格**的条目。"""
    got, grab = [], False
    for line in out.split(u"\n"):
        if u"不是本脚本写的" in line:
            grab = True
            continue
        if grab:
            if line.startswith(u"    ") and line.strip():
                got.append(line.strip())
            else:
                break
    return got


def main(argv):
    do_write = "--write" in argv
    do_check = "--check" in argv or do_write
    fails = []

    gen = read(GEN)
    has_alloys = u'"hard_titanium_alloy", "hard_titanium_alloy")' in gen
    has_vib = VIB_METALS in gen

    if not do_write:
        print(u"== 只校验（--write 才动盘）==")
        print(u"  GenCommonTags.py 已登记硬质钛合金/热力金属：%s" % (u"是" if has_alloys else u"否"))
        print(u"  GenCommonTags.py 已登记振金（漂移补账）：%s" % (u"是" if has_vib else u"否"))
        print(u"  盘上 7 份应有标签：%d/7 在" % sum(1 for p, _v, _n in WANT if os.path.exists(p)))
        if has_alloys and has_vib:
            print(u"  提示：要复核生成器输出请跑 --check")
        return 0

    # ---- ① 打补丁 ----
    if not has_alloys:
        if gen.count(OLD) != 1:
            print(u"  [STOP] ALLOYS 那段匹配到 %d 次（应为 1）—— 不动盘" % gen.count(OLD))
            return 1
        gen = gen.replace(OLD, NEW, 1)
        write(GEN, gen)
        print(u"  [改] GenCommonTags.py：ALLOYS 追加 hard_titanium_alloy / thermal_metal")
    else:
        print(u"  [跳过] ALLOYS 已经改过（幂等）")
    if not has_vib:
        anchor = u'    ("titanium", "titanium_ingot", "raw_titanium", ["titanium_ore", "deepslate_titanium_ore"]),\n]'
        if gen.count(anchor) != 1:
            print(u"  [STOP] METALS 尾部那段匹配到 %d 次（应为 1）—— 不动盘" % gen.count(anchor))
            return 1
        note = (u'    ("titanium", "titanium_ingot", "raw_titanium", '
                u'["titanium_ore", "deepslate_titanium_ore"]),\n'
                u'    # 振金（0.11 ZF121 补登记）：**有锭（ZF119）也有粗振金（ZF114）**，'
                u'但**没有矿石方块**\n'
                u'    # （粗振金是星轨坠的陨石砸出来的）⇒ 粗矿那一栏有值、矿石那一栏是空表。\n'
                u'    #\n'
                u'    # ⚠ **这一条补的是"表 ↔ 盘"的漂移（§4.93 第 3 次）**：ZF114 手写了\n'
                u'    # `raw_materials/vibranium.json` + 往 `raw_materials.json` 里加了一行，'
                u'ZF119 手写了\n'
                u'    # `ingots/vibranium.json` / `vibranium_ingots.json` + 往 `ingots.json` 里加了一行，\n'
                u'    # **两次都没登记到这张表里**。后果：只要有人重跑一次本脚本，父标签里那两行就被抹掉\n'
                u'    # （ZF121 第一跑实测：`c:ingots` 少 vibranium_ingot、'
                u'`c:raw_materials` 少 raw_vibranium），\n'
                u'    # 而且反向体检会把那 3 份手写文件报成"多余文件"。登记进来之后由本脚本拥有，'
                u'怎么重跑都不会漂。\n'
                + VIB_METALS + u'\n]')
        gen = gen.replace(anchor, note, 1)
        write(GEN, gen)
        print(u"  [改] GenCommonTags.py：METALS 追加 vibranium（漂移补账）")
    else:
        print(u"  [跳过] METALS 已登记振金（幂等）")

    # ---- ② 重跑生成器 ----
    rc, out = run_gen()
    print(u"---- GenCommonTags.py 输出（全文见 %s）----" % os.path.relpath(LOG, ROOT))
    for line in out.split(u"\n"):
        if u"ingots.json" in line or u"raw_materials.json" in line or u"不是本脚本" in line \
                or u"个标签文件" in line:
            print(u"  " + line.rstrip())
    print(u"----------------------------------------")
    if rc != 0:
        fails.append(u"生成器退出码 %d" % rc)

    # ---- ③ 反向体检：item/block 类一份都不许是手写的 ----
    stale = stale_list(out)
    bad = [s for s in stale if not s.replace(u"\\", u"/").startswith(u"fluid/")]
    if bad:
        fails.append(u"仍有手写的 item/block 标签：%s" % u"、".join(bad))
    print(u"反向体检：手写的 item/block 标签 %d 份（放行的 fluid 那 %d 份不归本脚本管）"
          % (len(bad), len(stale) - len(bad)))

    # ---- ④ 校验落盘结果 ----
    for p, want, name in WANT:
        if not os.path.exists(p):
            fails.append(u"%s 没生成（%s）" % (name, os.path.relpath(p, ROOT)))
            continue
        got = json.loads(read(p)).get(u"values")
        if got != want:
            fails.append(u"%s 内容不对：%r" % (name, got))
    ivals = json.loads(read(PARENT_INGOTS)).get(u"values", [])
    rvals = json.loads(read(PARENT_RAWS)).get(u"values", [])
    if len(ivals) != EXPECT_INGOTS_N:
        fails.append(u"父标签 c:ingots 应有 %d 项，实际 %d 项" % (EXPECT_INGOTS_N, len(ivals)))
    if len(rvals) != EXPECT_RAWS_N:
        fails.append(u"父标签 c:raw_materials 应有 %d 项，实际 %d 项" % (EXPECT_RAWS_N, len(rvals)))
    for v in NEED_INGOTS:
        if v not in ivals:
            fails.append(u"父标签 c:ingots 里没有 %s" % v)
    for v in NEED_RAWS:
        if v not in rvals:
            fails.append(u"父标签 c:raw_materials 里没有 %s" % v)
    print(u"父标签 c:ingots（%d）：%s" % (len(ivals), u"、".join(ivals)))
    print(u"父标签 c:raw_materials（%d）：%s" % (len(rvals), u"、".join(rvals)))

    n_pass = len(WANT) + 4 + (1 if not bad else 0)
    print(u"")
    print(u"通过 = %d   失败 = %d" % (n_pass - len(fails), len(fails)))
    for f in fails:
        print(u"  !! " + f)
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
