# -*- coding: utf-8 -*-
u"""_zf104_verify.py —— ZF104 常驻校验：新物品「硬质钛合金」+ 稳定金属块配方 + 合金炉那条

用户原话（两条）：

  「你看看能不能加个稳定金属块配方；【高碳钢】【硬质钛合金】【高碳钢】，
    【金块】【硬质钛合金】【金块】，【高碳钢】【硬质钛合金】【高碳钢】
    其中硬质钛合金还是钛锭的贴图 合金冶炼炉配方；轻质钛合金+高碳钢+镍锭」

⚠ **活体数字（键数 / 配方数）本轮不写死**：另一条并行任务正在往四份语言里加键
  （ZF103 收尾时 335 → 现在 349 → 本轮 +1 = 398），写死就会每几分钟挂一次。
  本脚本只断言**本轮的**事实 + 「四份语言条数一致」这一条结构性事实。
"""
import io
import json
import os
import sys

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

ROOT = r"E:\PotatoST"
JAVA = os.path.join(ROOT, r"src\main\java\com\potatost\mod")
RES = os.path.join(ROOT, r"src\main\resources")
RDIR = os.path.join(RES, r"data\potato_s_t\recipe")
LANG = os.path.join(RES, r"assets\potato_s_t\lang")

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


def read(p):
    return io.open(p, encoding="utf-8").read() if os.path.exists(p) else None


def main():
    print(u"=========== ZF104 校验：硬质钛合金 + 稳定金属块配方 + 合金炉那条 ===========")

    print(u"\n== A 新物品「硬质钛合金」 ==")
    items = read(os.path.join(JAVA, "ModItems.java")) or u""
    check(u"ModItems 注册了 hard_titanium_alloy",
          u'ITEMS.register("hard_titanium_alloy"' in items)
    check(u"进了创造模式标签页", u"output.accept(HARD_TITANIUM_ALLOY.get());" in items)
    model = read(os.path.join(RES, r"assets\potato_s_t\models\item\hard_titanium_alloy.json")) or u""
    check(u"物品模型在，且**指向钛锭那张贴图**（用户原话）",
          u'"layer0": "potato_s_t:item/titanium_ingot"' in model)
    check(u"本轮**没有新增任何 PNG**（贴图是借的）",
          not os.path.exists(os.path.join(RES, r"assets\potato_s_t\textures\item\hard_titanium_alloy.png")))
    for f in (u"zh_cn.json", u"en_us.json", u"ja_jp.json", u"ru_ru.json"):
        d = json.loads(read(os.path.join(LANG, f)))
        check(u"%s 有 item.potato_s_t.hard_titanium_alloy" % f,
              u"item.potato_s_t.hard_titanium_alloy" in d)
    counts = [len(json.loads(read(os.path.join(LANG, f))))
              for f in (u"zh_cn.json", u"en_us.json", u"ja_jp.json", u"ru_ru.json")]
    check(u"四份语言条数一致（现在各 %d 条）" % counts[0], len(set(counts)) == 1)

    print(u"\n== B 稳定金属块配方（用户给的九宫格） ==")
    obj = json.loads(read(os.path.join(RDIR, "stable_metal_block.json")) or u"{}")
    eq(u"type", u"minecraft:crafting_shaped", obj.get("type"))
    eq(u"九宫格逐行", [u"SAS", u"GAG", u"SAS"], obj.get("pattern"))
    got = {k: (v.get("item") or u"#" + v.get("tag", u"")) for k, v in (obj.get("key") or {}).items()}
    eq(u"字母 → 材料",
       {u"S": u"potato_s_t:high_carbon_steel", u"A": u"potato_s_t:hard_titanium_alloy",
        u"G": u"minecraft:gold_block"}, got)
    eq(u"产物", u"potato_s_t:stable_metal_block", (obj.get("result") or {}).get("id"))
    eq(u"产物数量", 1, (obj.get("result") or {}).get("count"))
    check(u"每个字母一种材料（§4.63）", len(set(got.values())) == len(got))
    gen = read(os.path.join(ROOT, r"build\zftools\_zf45_recipes.py")) or u""
    check(u"这张图纸也在生成器表里（可复现）", u'name="stable_metal_block"' in gen)

    print(u"\n== C 合金冶炼炉那条 ==")
    recipes = read(os.path.join(JAVA, "AlloySmelterRecipes.java")) or u""
    check(u"合金炉配方表里有硬质钛合金那一支",
          u"new ItemStack(ModItems.HARD_TITANIUM_ALLOY.get())" in recipes)
    for tag, note in ((u'ingot("titanium_alloy")', u"轻质钛合金（c:ingots/titanium_alloy）"),
                      (u'ingot("steel")', u"高碳钢（c:ingots/steel）"),
                      (u'ingot("nickel")', u"镍锭（c:ingots/nickel）")):
        check(u"原料里有 %s" % note, tag in recipes)

    print(u"\n== D 未做/待办（如实记录） ==")
    print(u"    ⚠ 另一条并行任务正在改四份语言（键数一直在涨）⇒ 往轮的活体数字（键数）"
          u"本轮**没有**跟着改，等两边都停下来再一次性对账")
    print(u"    ⚠ 本轮**没跑**探针与全门：源码树里有并行任务的在途改动，门会被它的键数改动挂掉")

    print(u"\n通过 = %d   失败 = %d" % (passed, failed))
    for f in fails:
        print(u"  !! " + f)
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
