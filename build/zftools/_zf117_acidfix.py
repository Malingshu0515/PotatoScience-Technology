# -*- coding: utf-8 -*-
u"""_zf117_acidfix.py —— 顺手补上 **ZF115 漏掉的第四处**（数值只改值、键一个不动）

用户原话（ZF115）：「锂电池构造间 硫酸消耗和储罐容量都先改成原来的十分之一吧」

ZF115 我改了：常数（10 → 1 mB/t、8000 → 800 mB）、四语言**介绍**（tooltip）、探针字面量、
`_zf112_verify.py` 的断言、反证刀 K133/K134。
**漏了**：界面状态灯那四句 `…status.no_acid`（悬停时念出来的话）在四份语言里都还写着
「每 tick 要 10 mB（一炉 6000 mB）」—— 机器实际按 1 mB/t 扣，玩家看到的却是 10。
根因：`_zf112_verify.py` 只钉了**介绍**里的数字，没钉**状态文案**里的数字。
（同时发现 `LithiumBatteryPlantBlockEntity` 的类 javadoc ②③ 也是旧的，
 且 ZF115 那次补丁把新旧两段 javadoc **叠在一起**了 —— 一并清掉，只留真的那段。）

本脚本干四件事（每件都「定位 → 替换 → 立刻回读断言」，并发环境不整份覆盖）：
  ① 四语言 `gui.potato_s_t.lithium_battery_plant.status.no_acid`：10/6000 → 1/600；
  ② `LithiumBatteryPlantBlockEntity.java`：类 javadoc ②③ 对到现数 + 删掉重复那段；
  ③ `MachineRecipes.java` / `LithiumBatteryPlantMenu.java` 里两处过期注释；
  ④ `_zf112_verify.py` 增加**状态文案数字**的常驻检查（这才是"下一次不会再漏"的东西）。
"""
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
LANG = os.path.join(ROOT, r"src\main\resources\assets\potato_s_t\lang")
JAVA = os.path.join(ROOT, r"src\main\java\com\potatost\mod")
TOOLS = os.path.join(ROOT, r"build\zftools")
KEY = u"gui.potato_s_t.lithium_battery_plant.status.no_acid"

EXPECT_OLD = {
    "zh_cn.json": u"硫酸不够：每 tick 要 10 mB（一炉 6000 mB）",
    "en_us.json": u"Not enough sulfuric acid: 10 mB per tick (6000 mB per batch)",
    "ja_jp.json": u"硫酸が足りません：毎 tick 10 mB（1 バッチ 6000 mB）",
    "ru_ru.json": u"Не хватает серной кислоты: 10 mB за тик (6000 mB на партию)",
}
EXPECT_NEW = {
    "zh_cn.json": u"硫酸不够：每 tick 要 1 mB（一炉 600 mB）",
    "en_us.json": u"Not enough sulfuric acid: 1 mB per tick (600 mB per batch)",
    "ja_jp.json": u"硫酸が足りません：毎 tick 1 mB（1 バッチ 600 mB）",
    "ru_ru.json": u"Не хватает серной кислоты: 1 mB за тик (600 mB на партию)",
}

fails = []
notes = []


def read(p):
    return io.open(p, encoding="utf-8").read()


def write(p, text):
    io.open(p, "w", encoding="utf-8", newline=u"").write(text)


def sub_once(path, old, new, label):
    u"""唯一锚点替换；锚点不唯一或压根没有 ⇒ 记失败、**不写盘**"""
    raw = read(path)
    n = raw.count(old)
    if n != 1:
        fails.append(u"%s：锚点出现 %d 次（要求正好 1 次）—— %s" % (os.path.basename(path), n, label))
        return False
    text = raw.replace(old, new, 1)
    if text == raw:
        fails.append(u"%s：替换后无变化 —— %s" % (os.path.basename(path), label))
        return False
    write(path, text)
    back = read(path)
    if new not in back or old in back:
        fails.append(u"%s：回读断言失败 —— %s" % (os.path.basename(path), label))
        return False
    notes.append(u"%s：%s" % (os.path.basename(path), label))
    return True


def fix_lang():
    for name in sorted(EXPECT_OLD):
        p = os.path.join(LANG, name)
        raw = read(p)
        data = json.loads(raw)
        cur = data.get(KEY)
        old, new = EXPECT_OLD[name], EXPECT_NEW[name]
        if cur == new:
            notes.append(u"%s：状态文案已经是新值，跳过" % name)
            continue
        if cur != old:
            fails.append(u"%s：状态文案既不是旧值也不是新值 ⇒ 停手（盘上：%s）" % (name, cur))
            continue
        line_old = u'    %s:  %s,' % (json.dumps(KEY, ensure_ascii=False),
                                      json.dumps(old, ensure_ascii=False))
        line_new = u'    %s:  %s,' % (json.dumps(KEY, ensure_ascii=False),
                                      json.dumps(new, ensure_ascii=False))
        if raw.count(line_old) != 1:
            fails.append(u"%s：状态文案那一行不是唯一锚点（先看一眼盘上格式）" % name)
            continue
        text = raw.replace(line_old, line_new, 1)
        back = json.loads(text)
        diff = [k for k in data if back.get(k) != data[k]]
        if diff != [KEY]:
            fails.append(u"%s：除了那一个键还动了 %s" % (name, diff))
            continue
        if len(back) != len(data):
            fails.append(u"%s：键数变了 %d → %d" % (name, len(data), len(back)))
            continue
        write(p, text)
        if json.loads(read(p)).get(KEY) != new:
            fails.append(u"%s：回读后还是旧值" % name)
            continue
        notes.append(u"%s：状态文案 10/6000 → 1/600（键数仍 %d）" % (name, len(back)))


def fix_javadoc():
    be = os.path.join(JAVA, "LithiumBatteryPlantBlockEntity.java")
    sub_once(be,
             u" * <p><b>② 酸按 tick 扣、料最后扣</b>：硫酸 <b>每 tick 10 mB</b>（用户指定），\n"
             u" * 一炉 30 秒 ⇒ 一件共 <b>6000 mB</b> 硫酸；",
             u" * <p><b>② 酸按 tick 扣、料最后扣</b>：硫酸 <b>每 tick 1 mB</b>"
             u"（用户原话「每t消耗10mb硫酸」，0.11 ZF115 又要求砍到原来的十分之一），\n"
             u" * 一炉 30 秒 ⇒ 一件共 <b>600 mB</b> 硫酸；",
             u"类 javadoc ② 的酸账对到 1 mB/t · 600 mB/炉")
    sub_once(be,
             u" * <p><b>③ 硫酸罐容量 2000 mB 是我定的</b>（用户没给）：够缓冲 200 tick 的连续消耗，",
             u" * <p><b>③ 硫酸罐容量 800 mB 是我定的</b>（用户没给）：够缓冲 800 tick 的连续消耗，",
             u"类 javadoc ③ 的罐容量对到 800")
    # 删掉 ZF115 那次补丁留下的**旧 javadoc 副本**（新旧两段叠在一起了）
    stale = (u"    /**\n"
             u"     * 硫酸罐容量。用户没给 ⇒ 取 <b>8000 mB</b>。\n"
             u"     *\n"
             u"     * <p>⚠ 第一版我取的是 2000，<b>探针当场把这条打回来了</b>："
             u"一炉要 6000 mB（10 mB/t × 600 t），\n"
             u"     * 罐子装不下一炉 ⇒ 玩家必须先架好持续供酸的管道才敢开机，装满一罐连半炉都跑不完。\n"
             u"     * 8000 = 一炉 6000 再留 2000 的余量，<b>装满一罐就能空手走开</b>。</p>\n"
             u"    /**\n")
    sub_once(be, stale, u"    /**\n", u"删掉 ZF115 留下的重复 javadoc 段（8000 那版）")

    mr = os.path.join(JAVA, "MachineRecipes.java")
    sub_once(mr,
             u"硫酸按<b>一炉总量</b>画（10 mB/t × 600 t = 6000 mB），",
             u"硫酸按<b>一炉总量</b>画（1 mB/t × 600 t = 600 mB），",
             u"JEI 注释里的酸账")
    mn = os.path.join(JAVA, "LithiumBatteryPlantMenu.java")
    sub_once(mn,
             u'    /** 供界面显示"每 tick 10 mB"。 */',
             u"    /** 供界面显示「每 tick 1 mB」。 */",
             u"菜单里 getAcidPerTick 的注释")


def add_gate():
    u"""往 `_zf112_verify.py` 里插一段常驻检查：**状态文案里的数字**（上一轮漏的就是它）"""
    p = os.path.join(TOOLS, "_zf112_verify.py")
    raw = read(p)
    marker = u"# ZF117-CHECK-6.5"
    if marker in raw:
        notes.append(u"_zf112_verify.py：状态文案检查已在，跳过")
        return
    anchor = u"    # ⑦ 探针 + 文档\n"
    if raw.count(anchor) != 1:
        fails.append(u"_zf112_verify.py：⑦ 段锚点出现 %d 次" % raw.count(anchor))
        return
    block = (
        u"    # ZF117-CHECK-6.5 状态灯文案里的数字（⚠ ZF115 只改了**介绍**里的数，\n"
        u"    #     状态灯那句还写着 10 mB / 6000 mB —— 玩家悬停看到的正是这一句）\n"
        u"    print(u\"\\n== 6.5 状态文案里的酸账 ==\")\n"
        u"    for name in LANGS:\n"
        u"        v = json.loads(read(os.path.join(LANG, name))).get(\n"
        u"            u\"gui.potato_s_t.lithium_battery_plant.status.no_acid\", u\"\")\n"
        u"        check(u\"%s 的状态文案念的是每 tick 1 mB（现在：%s）\" % (name, v), u\"1 mB\" in v)\n"
        u"        check(u\"%s 的状态文案念的是一炉 600 mB\" % name, u\"600 mB\" in v)\n"
        u"        check(u\"%s 的状态文案里再也没有 10 mB / 6000 mB\" % name,\n"
        u"              u\"10 mB\" not in v and u\"6000 mB\" not in v)\n"
        u"\n")
    text = raw.replace(anchor, block + anchor, 1)
    compile(text, p, "exec")
    write(p, text)
    if marker not in read(p):
        fails.append(u"_zf112_verify.py：回读后找不到新段")
        return
    notes.append(u"_zf112_verify.py：插入 6.5 状态文案检查（4 语言 × 3 条 = 12 条）")


def main():
    fix_lang()
    fix_javadoc()
    add_gate()
    print(u"\n".join(u"  [OK] " + n for n in notes))
    print(u"\n失败项 = %d" % len(fails))
    for f in fails:
        print(u"  !! " + f)
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())
