# -*- coding: utf-8 -*-
u"""_zf166_verify.py —— ZF166（0.13 第八笔）**常驻校验**：流体转化器（按同名 c: 标签 1:1 转流体）。

用户原话（对上一轮报告的回复）：「3.可以做」—— 指"一台把本 mod 的流体转成同标签的别的 mod 流体的机器"。

  A 方块/注册/资源：五个 java + 三处注册 + 创造页一行 + blockstate/两个 model（贴图只复用现成的，不新增 png）
  B 转化逻辑：两个罐（5000）/ RATE 50 mB/t / 30 FE/t / 2000 FE 缓冲 / 共享 c: 标签才转 /
    1:1（同一个 moved 变量）/ 只在真搬了才扣电 / 诊断状态与逻辑顺序逐条对齐 / MachineDrops 那行在
  C 配方与语言：生成器表 ↔ 盘同口径（跑一次"只校验"模式）/ 产物与图纸 / 五语 605×4 + 607 且 12 个新键非空
  D 探针/文档/成品：`_zf166_probe_utf8.txt` 全绿 / §4.172 / §5 ZF166 行 / 交接第 37 条 / 公告 / jar 内容

跑法：python build\\zftools\\_zf166_verify.py
"""
import io
import json
import os
import subprocess
import sys
import zipfile

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding=u"utf-8", errors="replace")

ROOT = r"E:\PotatoST"
ZT = os.path.join(ROOT, "build", "zftools")
JAVA = os.path.join(ROOT, r"src\main\java\com\potatost\mod")
ASSETS = os.path.join(ROOT, r"src\main\resources\assets\potato_s_t")
RECIPE = os.path.join(ROOT, r"src\main\resources\data\potato_s_t\recipe")
DOC = os.path.join(ROOT, "docs", u"开发档案.md")
HAND = os.path.join(ROOT, "docs", u"多会话协作交接.md")
ANN = os.path.join(ROOT, "docs", "UpdateAnnouncement_EN.md")
JAR = os.path.join(ROOT, "release", u"PotatoST-0.13.jar")
PROBE = os.path.join(ZT, u"_zf166_probe_utf8.txt")
LANGDIR = os.path.join(ASSETS, "lang")
LOCALES = [u"zh_cn", u"en_us", u"ja_jp", u"ru_ru", u"lzh"]
NEW_KEYS = [u"block.potato_s_t.fluid_converter", u"tooltip.potato_s_t.fluid_converter",
            u"gui.potato_s_t.fluid_converter.tank.input",
            u"gui.potato_s_t.fluid_converter.tank.output",
            u"gui.potato_s_t.fluid_converter.status.input_empty",
            u"gui.potato_s_t.fluid_converter.status.target_empty",
            u"gui.potato_s_t.fluid_converter.status.same_fluid",
            u"gui.potato_s_t.fluid_converter.status.no_shared_tag",
            u"gui.potato_s_t.fluid_converter.status.output_full",
            u"gui.potato_s_t.fluid_converter.status.no_power",
            u"gui.potato_s_t.fluid_converter.status.running",
            u"gui.potato_s_t.fluid_converter.status.idle"]

passed, failed, fails = 0, 0, []


def check(cond, label, detail=u""):
    global passed, failed
    if cond:
        passed += 1
        print(u"  [OK]   " + label)
    else:
        failed += 1
        fails.append(label if not detail else u"%s（%s）" % (label, detail))
        print(u"  [FAIL] " + label + (u" —— " + detail if detail else u""))


def read(p):
    return io.open(p, encoding="utf-8", errors="replace").read() if os.path.isfile(p) else u""


def code_only(text):
    return u"\n".join(l for l in text.split(u"\n")
                      if not l.strip().startswith((u"//", u"*", u"/*")))


print(u"=== A 段：方块 / 注册 / 资源 ===")
files = {n: read(os.path.join(JAVA, n)) for n in
         (u"FluidConverterBlock.java", u"FluidConverterBlockEntity.java", u"FluidConverterMenu.java")}
files[u"client/FluidConverterScreen.java"] = read(os.path.join(JAVA, u"client", u"FluidConverterScreen.java"))
missing = [n for n, t in files.items() if not t]
check(not missing, u"A1 方块/方块实体/菜单/界面四个 java 都在", u"缺 %s" % missing)
mb = read(os.path.join(JAVA, u"ModBlocks.java"))
check(u'BLOCKS.register("fluid_converter"' in mb and u'ITEMS.register("fluid_converter"' in mb
      and u'BLOCK_ENTITIES.register("fluid_converter"' in mb,
      u"A2 ModBlocks 里方块 + 物品 + 方块实体三处注册")
check(u'register("fluid_converter"' in read(os.path.join(JAVA, u"ModMenus.java")),
      u"A3 ModMenus 注册了菜单")
check(u"FLUID_CONVERTER_MENU" in read(os.path.join(JAVA, u"PotatoSTClient.java")),
      u"A4 PotatoSTClient 注册了界面")
check(u"ModBlocks.FLUID_CONVERTER_ITEM.get()" in read(os.path.join(JAVA, u"ModItems.java")),
      u"A5 创造页有它（漏了就是「物品栏看不见、JEI 搜不到」）")
bs = read(os.path.join(ASSETS, r"blockstates\fluid_converter.json"))
mod_b = read(os.path.join(ASSETS, r"models\block\fluid_converter.json"))
mod_i = read(os.path.join(ASSETS, r"models\item\fluid_converter.json"))
ok_json = True
for t in (bs, mod_b, mod_i):
    try:
        json.loads(t)
    except Exception:      # noqa: BLE001
        ok_json = False
check(bool(bs) and bool(mod_b) and bool(mod_i) and ok_json,
      u"A6 blockstate 与两个 model 都在且能解析")
import re as _re
try:
    _texvals = json.loads(mod_b).get(u"textures", {})
except Exception:      # noqa: BLE001
    _texvals = {}
tex = sorted(set(_re.findall(u"potato_s_t:block/([a-z0-9_/]+)", json.dumps(_texvals))))
miss_tex = [t for t in tex
            if not os.path.isfile(os.path.join(ASSETS, "textures", "block", t + u".png"))]
check(bool(tex) and not miss_tex,
      u"A7 方块 model 引用的贴图都存在（本轮不新增 png，只复用现成的）", u"缺 %s" % miss_tex)

print(u"\n=== B 段：转化逻辑 ===")
be = files[u"FluidConverterBlockEntity.java"]
check(u"RATE = 50" in be and u"ENERGY_PER_TICK = 30" in be and u"MAX_ENERGY = 2000" in be
      and u"TANK_CAPACITY = 5000" in be, u"B1 四个锁定数字都在（50 mB/t / 30 FE/t / 2000 FE / 5000 mB）")
check(be.count(u"new FluidTank(") == 2, u"B2 两个流体罐", u"实际 %d" % be.count(u"new FluidTank("))
check(u'getNamespace().equals("c")' in be or u'"c".equals(' in be,
      u"B3 共享标签的判据限定在 c: 命名空间")
check(u"drain(moved" in be and u"fill(" in be and u"Math.min(" in be,
      u"B4 1:1 搬运用的同一个 moved（先算得出多少、再两边同量）")
check(u"new FluidStack(out, drained.getAmount())" in be,
      u"B4b 「转化」的落点：往输出罐灌的是**样板那种流体**（写成 fill(drained) 会因异种流体恒回 0 ⇒ 机器一动不动，见 §4.172④）")
check(u"stateOf(" in be and u"enum State" in be, u"B5 有诊断状态枚举 + stateOf()")
check(u"MachineEnergyStorage.receiveOnly(" in be, u"B6 能量走 MachineEnergyStorage.receiveOnly")
check(u"MachineDrops.dropInventory" in code_only(files[u"FluidConverterBlock.java"]),
      u"B7 onRemove 里有 MachineDrops.dropInventory（Audit B 文本级判据；本机器 0 个物品槽，调用是空转）")
check(read(os.path.join(JAVA, u"PotatoST.java")).count(u"ModBlocks.FLUID_CONVERTER_BE.get()") == 2,
      u"B9 PotatoST 里登记了两个方块能力（能量 + 流体各一次）—— 少登记一个机器就是死的",
      u"实际 %d 次" % read(os.path.join(JAVA, u"PotatoST.java")).count(u"ModBlocks.FLUID_CONVERTER_BE.get()"))
check(u"TagKey<Fluid>" in be, u"B8 标签判据用的是 TagKey<Fluid>")

print(u"\n=== C 段：配方与语言 ===")
rec = read(os.path.join(RECIPE, u"fluid_converter.json"))
check(bool(rec), u"C1 盘上有 recipe/fluid_converter.json")
if rec:
    o = json.loads(rec)
    check((o.get(u"result") or {}).get(u"id") == u"potato_s_t:fluid_converter",
          u"C2 配方产物 = potato_s_t:fluid_converter", str(o.get(u"result")))
    pat = o.get(u"pattern") or []
    check(len(pat) == 3 and all(len(p) == 3 for p in pat), u"C3 图纸是 3×3", str(pat))
r = subprocess.run([sys.executable, os.path.join(ZT, u"_zf45_recipes.py")],
                   stdout=subprocess.PIPE, stderr=subprocess.STDOUT, timeout=180)
check(r.returncode == 0, u"C4 生成器表「只校验」模式 0 失败（表 ↔ 盘同口径）",
      r.stdout.decode("gbk", "replace").strip().split(u"\n")[-1][:80])
counts = {}
for lg in LOCALES:
    p = os.path.join(LANGDIR, lg + u".json")
    if os.path.isfile(p):
        counts[lg] = json.loads(io.open(p, encoding="utf-8").read())
check(counts.get(u"zh_cn") and len(counts[u"zh_cn"]) >= 605 and len(counts.get(u"lzh") or {}) >= 607
      and all(k in counts[u"zh_cn"] for k in NEW_KEYS),
      u"C5 五语键数 ≥ 605×4 + 607 且本机那 12 个键都在（盘上数字不钉死：别的线随时在加；产物里是 605/607）",
      repr({k: len(v) for k, v in counts.items()}))
bad = [(lg, k) for lg in LOCALES for k in NEW_KEYS
       if not (counts.get(lg) or {}).get(k, u"").strip()]
check(not bad, u"C6 12 个新键在五份语言里都非空", u"%s" % bad[:4])
n_recipe = sum(len([f for f in fs if f.endswith(u".json")]) for _r, _d, fs in os.walk(RECIPE))
check(n_recipe >= 94 and os.path.isfile(os.path.join(RECIPE, u"fluid_converter.json")),
      u"C7 盘上有流体转化器那条配方，且配方总数 ≥ 94"
      u"（别的线随时在加配方，所以这里不把盘上数字钉死；**产物里**才是死数 94）",
      u"实际 %d" % n_recipe)

print(u"\n=== D 段：探针 / 文档 / 成品 ===")
rep = read(PROBE)
check(u"失败 = 0" in rep and u"通过 = " in rep, u"D1 探针报告全绿",
      rep.strip().split(u"\n")[-1] if rep else u"（没有报告）")
check(u"1:1" in rep or u"1：1" in rep, u"D1b 报告里有 1:1 的实测")
check(u"### 4.172 " in read(DOC) and u"| ZF166 |" in read(DOC), u"D2 档案 §4.172 + §5 ZF166 行")
check(u"37. **ZF166 的账" in read(HAND), u"D3 交接 §6 第 37 条")
check(u"## New in 0.13 ZF166" in read(ANN), u"D4 英文公告有 ZF166 段")
if os.path.isfile(JAR):
    zjar = zipfile.ZipFile(JAR)
    names = zjar.namelist()
    check(u"com/potatost/mod/FluidConverterBlockEntity.class" in names, u"D5 产物里有流体转化器的 class")
    check(len([n for n in names if n.startswith(u"data/potato_s_t/recipe/") and n.endswith(u".json")]) == 94,
          u"D6 产物里配方 94 份")
    # D7：产物里的**资源**也要齐（processResources 万一没带上，机器在游戏里就是隐形的）
    assets_need = [u"assets/potato_s_t/blockstates/fluid_converter.json",
                   u"assets/potato_s_t/models/block/fluid_converter.json",
                   u"assets/potato_s_t/models/item/fluid_converter.json"]
    miss_a = [a for a in assets_need if a not in names]
    check(not miss_a, u"D7 产物里 blockstate + 两个 model 都在", u"缺 %s" % miss_a)
    jar_lang = json.loads(zjar.read(u"assets/potato_s_t/lang/zh_cn.json").decode("utf-8"))
    miss_k = [k for k in NEW_KEYS if k not in jar_lang]
    check(not miss_k, u"D8 产物里的 zh_cn 有本机那 12 个键（玩家看到的不是键名）", u"缺 %s" % miss_k)
else:
    check(False, u"D0 成品 jar 不在")

print(u"\n通过 = %d   失败 = %d" % (passed, failed))
for f in fails:
    print(u"  !! " + f)
sys.exit(1 if failed else 0)
