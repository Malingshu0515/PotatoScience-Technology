# -*- coding: utf-8 -*-
u"""_zf124_verify.py —— ZF124 常驻校验：成就页签改名 + 创造页图标换星轨坠（0.11）

用户原话（附成就界面截图）：「把成就的 新的开始！这一分类改成 PotatoS&T
创造模式标签页换成星轨追的物品贴图」。

六段：
  ① 文件账目（改前件 105 份 + 回读 + 点名件）
  ② **成就页签**（= 根成就 `new_beginning` 的标题）：四语言都是 `PotatoS&T`、
     与创造页标题一致、JSON 里仍是 `translate` 键、键数没变、相对改前件只动了这一个值
  ③ **创造页图标**：`ModItems` 的 `.icon(...)` 换成星轨坠、铝锭不再当图标、静态序正确
  ④ 往轮门 retarget（`_zf70_verify.py` 的 `title_zh`）
  ⑤ 英文公告（成就树那行改了；ZF107 那条 changelog 历史记录**没动**）
  ⑥ 文档（§5 行 / §9 小节 / 交接）
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
ZT = os.path.join(ROOT, r"build\zftools")
LANG = os.path.join(ROOT, r"src\main\resources\assets\potato_s_t\lang")
JAVA = os.path.join(ROOT, r"src\main\java\com\potatost\mod")
ADV = os.path.join(ROOT, r"src\main\resources\data\potato_s_t\advancement")
DOC = os.path.join(ROOT, r"docs\开发档案.md")
HANDOFF = os.path.join(ROOT, r"docs\多会话协作交接.md")
DOC_EN = os.path.join(ROOT, r"docs\UpdateAnnouncement_EN.md")
BK = r"C:\PotatoST救援\zf124_pre"
LOCALES = [u"zh_cn", u"en_us", u"ja_jp", u"ru_ru"]
KEY = u"advancements.potato_s_t.new_beginning.title"
TITLE = u"PotatoS&T"

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


def jload(p):
    if not os.path.exists(p):
        return None
    try:
        return json.loads(read(p))
    except Exception:
        return None


def main():
    # ============ ① 账目 ============
    print(u"== ① 文件账目 ==")
    check(u"改前件 zf124_pre 在", os.path.isdir(BK))
    n_bk = 0
    if os.path.isdir(BK):
        for _d, _s, _fs in os.walk(BK):
            n_bk += len(_fs)
    check(u"改前件 ≥100 份", n_bk >= 100, u"实际 %d" % n_bk)
    for rel in (r"src\main\java\com\potatost\mod\ModItems.java",
                r"src\main\resources\assets\potato_s_t\lang\zh_cn.json",
                r"docs\UpdateAnnouncement_EN.md",
                r"build\zftools\_zf70_verify.py"):
        check(u"点名件在改前件里：%s" % os.path.basename(rel), os.path.exists(os.path.join(BK, rel)))

    # ============ ② 成就页签标题 ============
    print(u"\n== ② 成就页签（根成就标题）==")
    data, before = {}, {}
    for name in LOCALES:
        data[name] = jload(os.path.join(LANG, name + u".json")) or {}
        before[name] = jload(os.path.join(BK, r"src\main\resources\assets\potato_s_t\lang",
                                          name + u".json")) or {}
        eq(u"%s：标题 = %s" % (name, TITLE), TITLE, data[name].get(KEY))
        eq(u"%s：与创造页标题一致" % name, data[name].get(u"itemGroup.potato_s_t"),
           data[name].get(KEY))
        eq(u"%s：相对改前件只动了这一个值" % name, [KEY],
           [k for k in before[name] if k in data[name] and before[name][k] != data[name][k]])
        eq(u"%s：改前件里的键一个都没少" % name, [],
           [k for k in before[name] if k not in data[name]])
    counts = {k: len(v) for k, v in data.items()}
    print(u"    键数：%s" % u"、".join(u"%s=%d" % (k, counts[k]) for k in sorted(counts)))
    eq(u"四语言键数一致", 1, len(set(counts.values())))
    adv = jload(os.path.join(ADV, u"new_beginning.json"))
    if adv is None:
        check(u"根成就 JSON 可读", False)
    else:
        t = adv.get(u"display", {}).get(u"title")
        check(u"根成就 JSON 里 title 仍是 translate 键（不是字面量）",
              isinstance(t, dict) and t.get(u"translate") == KEY)
        # ⚠ ZF128 retarget：ZF124 当时"只改名、没换图标"是**当时的事实**；
        #   用户后来（ZF128）点名把图标换成毒马铃薯 ⇒ 目标值跟着走，判据强度不变。
        check(u"根成就的图标（ZF124 时是粉碎机，ZF128 起是毒马铃薯）",
              adv.get(u"display", {}).get(u"icon", {}).get(u"id") == u"minecraft:poisonous_potato")

    # ============ ③ 创造页图标 ============
    print(u"\n== ③ 创造页图标 ==")
    items = read(os.path.join(JAVA, u"ModItems.java"))
    check(u".icon(...) 用的是星轨坠",
          u".icon(() -> new ItemStack(STARFALL_PENDANT.get()))" in items)
    check(u"铝锭不再当创造页图标",
          u".icon(() -> new ItemStack(ALUMINUM_INGOT.get()))" not in items)
    i_pend = items.find(u"DeferredItem<Item> STARFALL_PENDANT =")
    i_tab = items.find(u'CREATIVE_MODE_TABS.register("potato_s_t_tab"')
    check(u"星轨坠的字段声明在创造页注册之前（静态序）", 0 <= i_pend < i_tab)
    check(u"创造页标题仍是 itemGroup.potato_s_t（与成就页签同一个名字）",
          u'.title(Component.translatable("itemGroup.potato_s_t"))' in items)
    check(u"创造页仍是同一个 id", u'"potato_s_t_tab"' in items)

    # ============ ④ 往轮门 retarget ============
    print(u"\n== ④ 往轮门 retarget ==")
    z70 = read(os.path.join(ZT, u"_zf70_verify.py"))
    check(u"_zf70 的根成就 title_zh 已改成 PotatoS&T", u'title_zh=u"PotatoS&T",' in z70)
    check(u"_zf70 表里另外两条标题一个字没动",
          u'title_zh=u"更强劲的电源"' in z70 and u'title_zh=u"入门清洁能源"' in z70)
    check(u"_zf70 里不再有旧的根标题目标值", u'title_zh=u"新的开始！",' not in z70)

    # ============ ⑤ 英文公告 ============
    print(u"\n== ⑤ 英文公告 ==")
    den = read(DOC_EN)
    check(u"成就树那行改成了 PotatoS&T",
          u"PotatoS&T                obtain a Micro Crusher" in den)
    check(u"ZF107 那条 changelog 历史记录没动（改了就是篡改当时发生的事）",
          u'**"A New Beginning!" moved earlier.**' in den)

    # ============ ⑥ 文档 ============
    print(u"\n== ⑥ 文档 ==")
    doc, hand = read(DOC), read(HANDOFF)
    check(u"档案 §5 有 ZF124 行", u"| ZF124 |" in doc)
    check(u"档案 §9 有 ZF124 小节", u"### ZF124（0.11）" in doc)
    check(u"档案里写明了「用户只说了改名」这层边界", u"没说换图标" in doc or u"用户只说了改名" in doc)
    check(u"交接文档提到 ZF124", u"ZF124" in hand)

    print(u"")
    print(u"通过 = %d   失败 = %d" % (n_pass, len(fails)))
    for f in fails:
        print(u"  !! " + f)
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())
