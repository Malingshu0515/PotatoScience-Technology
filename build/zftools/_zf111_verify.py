# -*- coding: utf-8 -*-
u"""_zf111_verify.py —— ZF111 常驻校验：星璨钢的合金冶炼炉配方（0.11）

用户原话：「星璨钢加合金冶炼配方 下界合金锭+4高碳钢+钴锭+银锭+铜锭 再消耗1个深层钴矿石
1个末影水晶 产出三个星璨钢钢 12000FE/t」

七段：
  ① 文件账目（改了哪 3 个 Java、探针存档在不在、钩子摘没摘）
  ② 配方表（第三条：5 输入含高碳钢 ×4、2 消耗品、产物 ×3、12000 FE/t、600 tick、7,200,000 FE）
  ③ 方块实体（消耗槽放开 + 每配方各带各的耗时/耗电 + 守卫读纯 int 常量）
  ④ JEI（MachineRecipes 把两样消耗品也画出来）
  ⑤ 四语言（**键数仍是 408**、只改了两个值、摆放图那几行与改前件逐字相同）
  ⑥ 探针的 UTF-8 报告（真游戏跑出来的那份）还在且全绿
  ⑦ 文档（§5 行 / §9 小节 / 交接文档）
"""
import hashlib
import io
import json
import os
import re
import sys

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

ROOT = r"E:\PotatoST"
JAVA = os.path.join(ROOT, r"src\main\java\com\potatost\mod")
LANG = os.path.join(ROOT, r"src\main\resources\assets\potato_s_t\lang")
BK = r"C:\PotatoST救援\zf111_pre"
DOC = os.path.join(ROOT, r"docs\开发档案.md")
HANDOFF = os.path.join(ROOT, r"docs\多会话协作交接.md")
REPORT = os.path.join(ROOT, r"build\zftools\_zf111_probe_utf8.txt")
PROBE_ARCHIVE = os.path.join(ROOT, r"build\zftools\check\Zf111Check.java")
LANGS = ["zh_cn.json", "en_us.json", "ja_jp.json", "ru_ru.json"]
EXPECT_KEYS = 478           # … + ZF112 锂电池构造间 9 键 + ZF117 进度 16 键
KEY_CONSUME = u"gui.potato_s_t.alloy_smelter.consume_slot"
KEY_TIP = u"tooltip.potato_s_t.alloy_smelter"

n_pass = 0
fails = []


def read(p):
    return io.open(p, encoding="utf-8").read()


def check(name, cond, detail=None):
    global n_pass
    if cond:
        n_pass += 1
    else:
        fails.append(name + (u"  ← %s" % detail if detail else u""))


def eq(name, want, got):
    check(name, want == got, u"期望 %r 实际 %r" % (want, got))


def main():
    recipes = read(os.path.join(JAVA, "AlloySmelterRecipes.java"))
    be = read(os.path.join(JAVA, "AlloySmelterBlockEntity.java"))
    mr = read(os.path.join(JAVA, "MachineRecipes.java"))
    potato = read(os.path.join(JAVA, "PotatoST.java"))

    # ============ ① 文件账目 ============
    print(u"== ① 文件账目 ==")
    check(u"改前件 zf111_pre 在", os.path.isdir(BK))
    n_bk = 0
    if os.path.isdir(BK):
        for _d, _s, _fs in os.walk(BK):
            n_bk += len(_fs)
    check(u"改前件抄了 ≥100 份", n_bk >= 100, u"实际 %d" % n_bk)
    check(u"探针钩子已摘（PotatoST 里不许留 Zf111Check）", u"Zf111Check" not in potato)
    check(u"探针源文件已从 src 删掉",
          not os.path.exists(os.path.join(JAVA, "Zf111Check.java")))
    check(u"探针存档在 build/zftools/check/（先抄后删）", os.path.exists(PROBE_ARCHIVE))
    if os.path.exists(PROBE_ARCHIVE):
        eq(u"探针存档 sha1", "add48fb5ea165cb380545b2c844c833e3c9d8df9",
           hashlib.sha1(open(PROBE_ARCHIVE, "rb").read()).hexdigest())

    # ============ ② 配方表 ============
    print(u"\n== ② 配方表 ==")
    check(u"新增 Consume 记录（消耗品按具体物品认）",
          "public record Consume(Item item, int count)" in recipes)
    check(u"Smelt 多了 consumes 字段",
          "public record Smelt(List<Need> needs, List<Consume> consumes, ItemStack result," in recipes)
    # ⚠ ZF121 retarget：这个常量是**全表最贵那条**的每 tick 耗电（活体数字）。
    #   振金那条 14500 比星璨钢的 12000 更贵 ⇒ 常量必须跟着走，判据本身没放宽。
    check(u"MAX_ENERGY_PER_TICK = 14500（纯 int 常量，静态守卫能读）",
          "public static final int MAX_ENERGY_PER_TICK = 14_500;" in recipes)
    check(u"第三条配方：下界合金标签", 'new Need(ingot("netherite"), 1)' in recipes)
    check(u"第三条配方：高碳钢 ×4", 'new Need(ingot("steel"), 4)' in recipes)
    check(u"第三条配方：钴锭", 'new Need(ingot("cobalt"), 1)' in recipes)
    check(u"第三条配方：银锭", 'new Need(ingot("silver"), 1)' in recipes)
    check(u"第三条配方：铜锭", 'new Need(ingot("copper"), 1)' in recipes)
    check(u"消耗品：1 个深层钴矿石",
          "new Consume(PotatoSTOres.DEEPSLATE_COBALT_ORE.get().asItem(), 1)" in recipes)
    check(u"消耗品：1 个末影水晶", "new Consume(Items.END_CRYSTAL, 1)" in recipes)
    check(u"产物：3 个星璨钢锭",
          "new ItemStack(ModArmorItems.STAR_STEEL_INGOT.get(), 3)" in recipes)
    # ⚠ ZF121 retarget：这条配方原来借的是 MAX_ENERGY_PER_TICK（"全表最贵那条"那个活体数字），
    #   本轮的振金那条把它抬高 ⇒ 星璨钢会跟着从 12000 变成 14500（§4.100）⇒ 已拆成自己的常量。
    #   判据没放宽：仍然要求它引用**一个具体的每 tick 耗电常量**。
    check(u"这条配方用自己的 STAR_STEEL_ENERGY_PER_TICK（12000，不是 800、也不借 MAX）",
          "DURATION_TICKS, STAR_STEEL_ENERGY_PER_TICK));" in recipes)
    check(u"前两条配方的消耗品是空 List.of()", recipes.count(u"List.of(),\n") >= 2
          or recipes.count(u"                List.of(),") >= 2)
    check(u"注释写明了时长是我按本机规格补的（30 秒 = 7,200,000 FE）",
          u"7,200,000" in recipes and u"时长用户没给" in recipes)
    check(u"注释写明 netherite/copper 走 NeoForge 的标签", u"c:ingots/netherite" in recipes)
    check(u"表仍是懒加载（§4.1）", "if (table == null)" in recipes)

    # ============ ③ 方块实体 ============
    print(u"\n== ③ 方块实体 ==")
    check(u"消耗槽注释改成已放开", u"0.11 ZF111 起放开" in be)
    check(u"消耗槽 isItemValid 走 isConsumable", "return isConsumable(stack);" in be)
    check(u"isConsumable 只认配方点名的消耗品",
          "private static boolean isConsumable(ItemStack stack)" in be
          and "if (stack.is(consume.item()))" in be)
    check(u"countInConsumes 在", "private int countInConsumes(Item item)" in be)
    check(u"findRecipe 也查消耗品", "countInConsumes(consume.item()) < consume.count()" in be)
    check(u"consumeIngredients 扣消耗品",
          "for (AlloySmelterRecipes.Consume consume : smelt.consumes())" in be)
    check(u"craftTick 读这条配方自己的每 tick 耗电",
          "int cost = smelt.energyPerTick();" in be and "this.energy -= cost;" in be)
    check(u"craftTick 读这条配方自己的时长",
          "if (this.progress >= smelt.durationTicks()) {" in be)
    check(u"craftTick 里不再用全局 ENERGY_PER_TICK",
          "ENERGY_PER_TICK" not in be.split("void craftTick()")[1].split("private void resetProgress")[0])
    check(u"静态守卫读 MAX_ENERGY_PER_TICK（纯 int，不碰懒加载的表）",
          "long worstDemand = AlloySmelterRecipes.MAX_ENERGY_PER_TICK;" in be)
    # ⚠ ZF121 retarget：同一条活体数字（最贵那条 12000 → 14500）。
    check(u"14500 ≤ 储能 32768（写在类注释里）", "14500 ≤ 32768" in be)

    # ============ ④ JEI ============
    print(u"\n== ④ JEI ==")
    check(u"MachineRecipes 把消耗品也画进输入",
          "for (AlloySmelterRecipes.Consume consume : smelt.consumes()) {" in mr)
    check(u"JEI 没加新说明行（说明行只放客观数值那条规矩）",
          "jei.tag_inputs" not in mr)

    # ============ ⑤ 四语言 ============
    print(u"\n== ⑤ 四语言 ==")
    for name in LANGS:
        now = json.loads(read(os.path.join(LANG, name)))
        before = json.loads(read(os.path.join(BK, r"src\main\resources\assets\potato_s_t\lang", name)))
        eq(u"%s 键数仍是 408（本环一个键都没加/删）" % name, EXPECT_KEYS, len(now))
        # ⚠ ZF112 起改成「相对顺序」：后一轮会在中间插键，键序必然变
        now_keys = list(now)
        eq(u"%s 改前件那份键序仍是今天键序的子序列（相对顺序没乱）" % name,
           list(before), [k for k in now_keys if k in before])
        eq(u"%s 除这两个键外一个值都没动" % name, [],
           [k for k in before if k not in (KEY_CONSUME, KEY_TIP) and before[k] != now[k]])
        check(u"%s：消耗槽不再是「未开放」" % name,
              u"open yet" not in now[KEY_CONSUME] and u"未开放" not in now[KEY_CONSUME]
              and u"未開放" not in now[KEY_CONSUME] and u"не открыт" not in now[KEY_CONSUME])
        tip_before = before[KEY_TIP].split(u"\n")
        tip_now = now[KEY_TIP].split(u"\n")
        eq(u"%s：介绍行数没变（≤20 是 _zf55 的红线）" % name, len(tip_before), len(tip_now))
        eq(u"%s：摆放图那几行逐字未动" % name, tip_before[:-1], tip_now[:-1])
        check(u"%s：脚注写了 12000" % name, u"12000" in tip_now[-1])
        check(u"%s：整条介绍仍写着 32768（_zf55 会查）" % name, u"32768" in u"\n".join(tip_now))
        check(u"%s：整条介绍仍写着 58（_zf55 会查）" % name, u"58" in u"\n".join(tip_now))
        check(u"%s：脚注里没有 ASCII 双引号" % name, u"\"" not in tip_now[-1])

    # ============ ⑥ 探针报告 ============
    print(u"\n== ⑥ 探针报告 ==")
    check(u"探针 UTF-8 报告在盘上", os.path.exists(REPORT))
    if os.path.exists(REPORT):
        rep = read(REPORT)
        check(u"报告是全绿（verdict: ALL OK）", "verdict: ALL OK" in rep)
        check(u"报告里没有 [FAIL]", "[FAIL]" not in rep)
        check(u"报告里记了五个锭标签那一节", u"c:ingots/netherite 非空" in rep)
        check(u"报告里记了「每 tick 正好 12000 FE」", u"每 tick 正好 12000 FE" in rep)
        check(u"报告里记了一轮总耗电", "7200000" in rep or "7,200,000" in rep)

    # ============ ⑦ 文档 ============
    print(u"\n== ⑦ 文档 ==")
    doc = read(DOC)
    hand = read(HANDOFF)
    check(u"档案 §5 有 ZF111 行", u"| ZF111 |" in doc)
    check(u"档案 §9 有 ZF111 小节", u"ZF111（0.11）" in doc)
    check(u"档案里写明了时长是补的（12000 × 600）", u"7,200,000" in doc)
    check(u"交接文档提到了 ZF111", u"ZF111" in hand)

    print(u"")
    print(u"通过 = %d   失败 = %d" % (n_pass, len(fails)))
    for f in fails:
        print(u"  !! " + f)
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())
