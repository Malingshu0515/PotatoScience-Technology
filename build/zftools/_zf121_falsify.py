# -*- coding: utf-8 -*-
u"""_zf121_falsify.py —— ZF121 的反证刀（K166~K177，12 把）

口径同前：先确认基线绿 → 改一处语义 ⇒ 门必须 FAIL 且**咬住指定的那条检查** ⇒ 逐字节还原 ⇒
收尾回到全绿。一把刀 300 秒超时（§4.77）。

⚠ 咬中的判据本轮**收紧成一条**：指定串必须出现在**以 `!!` 开头的那一行**里
（旧写法只查"全文里有没有这个串" —— 那个串要是恰好也出现在某条**通过**的检查名里，
就会变成假咬中）。

刀面覆盖这一轮说出口的每一句话：
  配方（热力金属个数 / 下界合金碎片个数 / **改口后不许有钻石**）、
  标签（硬质钛合金的标签文件 / 两个父标签 —— 含复现"表 ↔ 盘漂移"那把）、
  **能量常量的拆雷**（配方不许引用 MAX / 星璨钢必须自己一个数）、
  菜单（消耗槽那层门不许再拦 / 槽位数不许偷偷扩回 4）、
  语言（脚注那个数 / 键被删）。
"""
import hashlib
import io
import os
import subprocess
import sys

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

ROOT = r"E:\PotatoST"
ZT = os.path.join(ROOT, r"build\zftools")
JAVA = os.path.join(ROOT, r"src\main\java\com\potatost\mod")
LANG = os.path.join(ROOT, r"src\main\resources\assets\potato_s_t\lang")
TAGS = os.path.join(ROOT, r"src\main\resources\data\c\tags\item")
VERIFY = os.path.join(ZT, u"_zf121_verify.py")

RECIPES = os.path.join(JAVA, u"AlloySmelterRecipes.java")
BE = os.path.join(JAVA, u"AlloySmelterBlockEntity.java")
MENU = os.path.join(JAVA, u"AlloySmelterMenu.java")
ZH = os.path.join(LANG, u"zh_cn.json")
INGOTS = os.path.join(TAGS, u"ingots.json")
RAWS = os.path.join(TAGS, u"raw_materials.json")

CONSUME_LOOP = u'''        for (int k = 0; k < AlloySmelterBlockEntity.CONSUME_COUNT; k++) {
            this.addSlot(new SlotItemHandler(machineInventory, AlloySmelterBlockEntity.CONSUME_FIRST + k,
                    CONSUME_X + k * 18, CONSUME_Y));
        }'''
CONSUME_LOOP_OLD = u'''        for (int k = 0; k < AlloySmelterBlockEntity.CONSUME_COUNT; k++) {
            this.addSlot(new SlotItemHandler(machineInventory, AlloySmelterBlockEntity.CONSUME_FIRST + k,
                    CONSUME_X + k * 18, CONSUME_Y) {
                @Override
                public boolean mayPlace(ItemStack stack) {
                    return false;       // 用户：「目前放不了东西」——以后放石墨电极
                }
            });
        }'''

KNIVES = [
    dict(id="K166", why=u"第④条的热力金属从 8 个改成 7 个", path=RECIPES,
         old=u'new Need(ingot("thermal_metal"), 8)', new=u'new Need(ingot("thermal_metal"), 7)',
         expect=u"第④条：8 热力金属"),
    dict(id="K167", why=u"下界合金碎片从 2 个改成 1 个（用户给的是 2）", path=RECIPES,
         old=u"new Consume(Items.NETHERITE_SCRAP, 2)", new=u"new Consume(Items.NETHERITE_SCRAP, 1)",
         expect=u"第④条：消耗 2 下界合金碎片"),
    dict(id="K168", why=u"把用户改口删掉的钻石偷偷加回消耗品列表", path=RECIPES,
         old=u'''                        new Consume(Items.NETHERITE_SCRAP, 2)),''',
         new=u'''                        new Consume(Items.NETHERITE_SCRAP, 2),
                        new Consume(Items.DIAMOND, 1)),''',
         expect=u"用户改口后**不再**消耗钻石"),
    dict(id="K169", why=u"硬质钛合金的 c:ingots/<材料> 标签文件被删（它就放不进输入槽了）",
         path=os.path.join(TAGS, u"ingots", u"hard_titanium_alloy.json"), mode="delete",
         expect=u"c:ingots/hard_titanium_alloy 收下它"),
    dict(id="K170", why=u"父标签 c:ingots 里少掉热力金属（生成器表与盘的漂移）", path=INGOTS,
         old=u',\n    "potato_s_t:thermal_metal"', new=u"",
         expect=u"父标签 c:ingots = 12 项且逐项对"),
    dict(id="K171", why=u"**复现 ZF114 的漂移**：父标签 c:raw_materials 里少掉粗振金", path=RAWS,
         old=u',\n    "potato_s_t:raw_vibranium"', new=u"",
         expect=u"父标签 c:raw_materials 收下粗振金"),
    dict(id="K172", why=u"第④条又回去借 MAX_ENERGY_PER_TICK（下一个加配方的人会静默改它的数）",
         path=RECIPES, old=u"DURATION_TICKS, VIBRANIUM_ENERGY_PER_TICK));",
         new=u"DURATION_TICKS, MAX_ENERGY_PER_TICK));",
         expect=u"没有任何配方**直接引用 MAX_ENERGY_PER_TICK"),
    dict(id="K173", why=u"星璨钢那条又回去借 MAX_ENERGY_PER_TICK（12000 会偷偷变 14500）",
         path=RECIPES, old=u"DURATION_TICKS, STAR_STEEL_ENERGY_PER_TICK));",
         new=u"DURATION_TICKS, MAX_ENERGY_PER_TICK));",
         expect=u"四条配方各自的每 tick 耗电 = 800 / 800 / 12000 / 14500"),
    dict(id="K174", why=u"**复现 ZF111 的老问题**：菜单那层把消耗槽重新拦死（mayPlace=false）",
         path=MENU, old=CONSUME_LOOP, new=CONSUME_LOOP_OLD,
         expect=u"菜单：消耗槽那一圈"),
    dict(id="K175", why=u"**复现我第一版的扩槽**：消耗槽偷偷扩回 4 个", path=BE,
         old=u"public static final int CONSUME_COUNT = 2;",
         new=u"public static final int CONSUME_COUNT = 4;",
         expect=u"CONSUME_COUNT = 2（用户改口后**没有**扩槽）"),
    dict(id="K176", why=u"语言脚注里的 14500 被改回 12000", path=ZH,
         old=u"14500 FE/t", new=u"12000 FE/t", expect=u"zh_cn：脚注写了 14500"),
    dict(id="K177", why=u"四语言里把合金炉那条 tooltip 键整个删掉", path=ZH, mode="line",
         old=u'"tooltip.potato_s_t.alloy_smelter":', expect=u"zh_cn：改前件里的键一个都没少"),
]

fails, notes = [], []


def run():
    try:
        r = subprocess.run([sys.executable, VERIFY], stdout=subprocess.PIPE,
                           stderr=subprocess.STDOUT, timeout=300)
        return r.returncode, r.stdout.decode("utf-8", "replace")
    except subprocess.TimeoutExpired:
        return 99, u"**超时**"


def summary(out):
    line = [l for l in out.split(u"\n") if u"通过" in l and u"失败" in l]
    return line[-1].strip() if line else u"?"


def bitten(out, expect):
    u"""咬中 = 那条串出现在**以 `!!` 开头**的 FAIL 行里（不是"全文里出现过"）。"""
    return any(l.strip().startswith(u"!!") and expect in l for l in out.split(u"\n"))


def main():
    rc, out = run()
    print(u"基线：%s（退出码 %d）" % (summary(out), rc))
    if rc != 0:
        print(u"  [STOP] 基线不绿，先修")
        for l in out.split(u"\n"):
            if l.strip().startswith(u"!!"):
                print(u"    " + l.strip())
        return 1
    n_ok = 0
    for k in KNIVES:
        path = k["path"]
        orig = open(path, "rb").read() if os.path.exists(path) else None
        before = hashlib.sha1(orig).hexdigest() if orig is not None else u"(不存在)"
        mode = k.get("mode", "replace")
        try:
            if mode == "delete":
                os.remove(path)
            elif mode == "line":
                text = orig.decode("utf-8")
                lines = [l for l in text.split(u"\n") if not l.strip().startswith(k["old"])]
                if len(lines) == len(text.split(u"\n")):
                    fails.append(u"%s：要删的行没找到" % k["id"])
                    continue
                open(path, "wb").write(u"\n".join(lines).encode("utf-8"))
            else:
                text = orig.decode("utf-8")
                if text.count(k["old"]) != 1:
                    fails.append(u"%s：锚点命中 %d 次" % (k["id"], text.count(k["old"])))
                    continue
                open(path, "wb").write(text.replace(k["old"], k["new"], 1).encode("utf-8"))
            rc, out = run()
        finally:
            if orig is None:
                if os.path.exists(path):
                    os.remove(path)
            else:
                open(path, "wb").write(orig)
        after = hashlib.sha1(open(path, "rb").read()).hexdigest() if os.path.exists(path) else u"(不存在)"
        if after != before:
            fails.append(u"%s：还原失败" % k["id"])
            break
        if rc != 0 and bitten(out, k["expect"]):
            n_ok += 1
            print(u"  [OK]   %s %s ⇒ 咬住「%s」" % (k["id"], k["why"], k["expect"]))
        else:
            print(u"  [BAD]  %s %s（退出码 %d）" % (k["id"], k["why"], rc))
            fails.append(u"%s %s ⇒ %s" % (k["id"], k["why"],
                                          u"门还是绿的" if rc == 0 else u"咬错了检查"))
    rc, out = run()
    print(u"收尾：%s（退出码 %d）" % (summary(out), rc))
    if rc != 0:
        fails.append(u"收尾不是全绿")
    print(u"刀 = %d，咬住 = %d，失败项 = %d" % (len(KNIVES), n_ok, len(fails)))
    for f in fails:
        print(u"  !! " + f)
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())
