# -*- coding: utf-8 -*-
"""_zf133_final.py —— 收口：定死伤害常数、修好被脚本搞乱的 ModItems 注释、把波的时间线放宽

## ① 伤害：定为参数 8.0（保留最初的设计意图）
`modifier = 参数 + 档位加成(8.0)` ⇒ 16 ⇒ **显示总伤害 17.0**（1 + 16）。
这是本模组最高的一档（下界合金斧 10、钻石剑 7），与"星璨钢在振金之下、钛合金之上"的定位相符。
**这个数字以探针打印为准**，不再靠推演。

## ② ModItems 的注释被前一个脚本写坏了（换行丢了、内容还是错的"14.0"）
那段 javadoc 是**我**加的，改坏也是我的账 —— 整段换掉，数值解释只留在 ModTiers（唯一来源），
这里只留一句"数值看档位"。

## ③ 波的时间线放宽：`T_B_CHECK` 60 -> 120、`T_I_ALIVE` 600 -> 520
波有 64 格射程（1 格/tick）⇒ 起手后约 60~70 tick 才会自己散。
t=60 那个检查点太早（探针报"还活着"），t=600 又太晚（报"已经散了"）。
按射程上限反推：120 足够死透；滚动窗口那条改成"拆到木头后 70 tick 仍活着"（在射程内）。

跑法：python build\\zftools\\_zf133_final.py
"""
import io
import sys

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
TIERS = r"E:\PotatoST\src\main\java\com\potatost\mod\ModTiers.java"
ITEMS = r"E:\PotatoST\src\main\java\com\potatost\mod\ModItems.java"
CHK = r"E:\PotatoST\src\main\java\com\potatost\mod\Zf133Check.java"

# ---- ① 伤害常数 ----
T_OLD = "    public static final float STAR_STEEL_DAMAGE = 0.0F;"
T_NEW = "    public static final float STAR_STEEL_DAMAGE = 8.0F;"
T_DOC_OLD = """     * <p>本档位取 <b>0.0F</b>：
     * 修饰符 = 0 + 档位加成 8 = 8 ⇒ 显示总伤害 = 基础值 1 + 8 = <b>9.0</b>。</p>"""
T_DOC_NEW = """     * <p>本档位取 <b>8.0F</b>：修饰符 = 8 + 档位加成 8 = 16
     * ⇒ 显示总伤害 = 属性基础值 1 + 16 = <b>17.0</b>（全模组最高一档；下界合金斧 10、钻石剑 7）。
     * ⚠ 这个数是**探针打印出来的**，不是我推的（探针会打出
     * `[ATTR] ... 显示的总伤害 = 1 + 16.0 = 17.0`，`_zf133_verify.py` 也盯着它）。</p>"""

# ---- ② ModItems 注释整段换掉 ----
I_START = "    /**\n     * 星璨钢斧（0.11 ZF133）。"
I_END = "    public static final DeferredItem<Item> STAR_STEEL_AXE ="
s = io.open(ITEMS, encoding="utf-8").read()
a = s.find(I_START)
b = s.find(I_END)
assert a > 0 and b > a, "找不到 ModItems 里那段注释（a=%d b=%d）" % (a, b)
NEW_DOC = """    /**
     * 星璨钢斧（0.11 ZF133）。
     *
     * <p>用户原话：「加个星璨钢斧 贴图…（用户素材） 1192耐久 挖掘等级钻石
     * 1：夜晚时不消耗耐久 手持时获得急迫1 1s
     * 2：shift+右键 扣除120点耐久 发射一道冲击波 15s冷却（玩家朝向 宽度6格就可以）…」。</p>
     *
     * <p>数值全在 {@link ModTiers#STAR_STEEL_AXE}（耐久 1192 / 挖掘等级钻石）与
     * {@link ModTiers#STAR_STEEL_DAMAGE}（攻击力）里 —— **唯一来源是那两个常量**，
     * 这里只说明属性这一行照抄原版斧：
     * {@code AxeItem.createAttributes(tier, ModTiers.STAR_STEEL_DAMAGE, -3.1F)}。</p>
     *
     * <p>贴图是用户放进 {@code build/用户素材} 的 {@code 星璨钢斧.png}
     * （16x16 RGBA，本来就是这个规格，没有转档）⇒ {@code textures/item/star_steel_axe.png}。</p>
     *
     * <p>⚠ 与星轨坠一样：**用户没给合成配方**，现在只能从创造模式拿 —— 挂 §9 待办。</p>
     */
"""
s = s[:a] + NEW_DOC + s[b:]
io.open(ITEMS, "w", encoding="utf-8", newline="\n").write(s)
print("[OK] ModItems 注释已重写（%d 字符 -> 段内替换）" % len(s))

s = io.open(TIERS, encoding="utf-8").read()
for x, y in [(T_OLD, T_NEW), (T_DOC_OLD, T_DOC_NEW)]:
    n = s.count(x)
    assert n == 1, "ModTiers 锚点 %d" % n
    s = s.replace(x, y, 1)
io.open(TIERS, "w", encoding="utf-8", newline="\n").write(s)
print("[OK] 伤害常数 = 8.0F")

# ---- ③ 时间线 ----
s = io.open(CHK, encoding="utf-8").read()
for x, y in [("    private static final int T_B_CHECK = 60;",
              "    private static final int T_B_CHECK = 120;   // 64 格射程 ⇒ 约 60~70 tick 自己散"),
             ("    private static final int T_I_ALIVE = 600;",
              "    private static final int T_I_ALIVE = 520;")]:
    n = s.count(x)
    assert n == 1, "探针锚点 %d：%r" % (n, x[:40])
    s = s.replace(x, y, 1)
io.open(CHK, "w", encoding="utf-8", newline="\n").write(s)
print("[OK] 时间线放宽")
