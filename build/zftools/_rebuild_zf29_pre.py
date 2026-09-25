# -*- coding: utf-8 -*-
"""ZF29：重建被覆盖的"改前"副本（两份 java）。

事故：zf29_pre 里 `SolarPanelBlockEntity.java` 与 `GroupEnergy.java` 的"改前"副本
      实际拷到的是**改后**内容（`_sha256.txt` 里"改前"和"改后"两段哈希完全相同就是铁证）。
      其余 6 个文件经哈希核对是**完好的**改前状态。

重建办法（档案 §4.17 的"三级来源"里的第 ③ 级：**减法重建**）：
  拿改后的源文件，把我这次做的**每一处编辑逐条反向替换回去**。
  **判据不是"看着像"，而是哈希必须命中 `_sha256.txt` 里记的改前值**：
      SolarPanelBlockEntity.java  期望 478dec401d5635d978412e2d8a4447c443d8a579a19f2546431121e37947a89e
      GroupEnergy.java            期望 52332b031613b3fc67b33da58440f1cd69d73eacaf6f873c6f3f87d3e2b6976f
  对不上就说明我漏改/多改了某处 —— 那正是这条检查存在的意义。
"""
import hashlib
import io
import os
import shutil

SRC = r"E:\PotatoST\src\main\java\com\potatost\mod"
DST = r"C:\Users\Administrator\Desktop\PotatoST救援_20260917_183054\zf29_pre"

EXPECT = {
    "SolarPanelBlockEntity.java":
        "478dec401d5635d978412e2d8a4447c443d8a579a19f2546431121e37947a89e",
    "GroupEnergy.java":
        "52332b031613b3fc67b33da58440f1cd69d73eacaf6f873c6f3f87d3e2b6976f",
}

# ---------- SolarPanelBlockEntity：逐条反向替换 ----------
SP_EDITS = [
    # ① 类注释首行
    (" * 太阳能板（0.10 ZF22 加入；ZF24 改为<b>共享储能</b>；ZF29 发电量 ×3）。",
     " * 太阳能板（0.10 ZF22 加入；ZF24 改为<b>共享储能</b>）。"),
    # ② ZF29 那一整段说明（整段删掉）
    ("""
 *
 * <p><b>ZF29：发电量变成原来的 300%</b>（用户："太阳能板发电量变成原来300%"）。
 * 三档 <b>20/45/60 → 60/135/180 FE/t</b>。⚠ 注意 <b>{@value #MAX_ENERGY} FE 的储能没动</b> ——
 * 于是"攒满"从约 26 tick（1.3 秒）变成约 9 tick（0.4 秒），
 * 也就是说<b>它现在几乎总是满的，真正的瓶颈变成了下方设备能抽多快</b>。
 * 这是用户只要"发电量"三个字时**有意不动储能**的结果，写在档案 §9 里而不是自作主张改容量。</p>
 *""", ""),
    # ③ 三档常量 + 注释
    ("""    /** 晴天三档（FE/t）。ZF29 起 = 原值 × 3（用户："太阳能板发电量变成原来300%"） */
    public static final int RATE_DAWN_DUSK = 60;
    public static final int RATE_MORNING = 135;
    public static final int RATE_NOON = 180;""",
     """    /** 晴天三档（FE/t） */
    public static final int RATE_DAWN_DUSK = 20;
    public static final int RATE_MORNING = 45;
    public static final int RATE_NOON = 60;"""),
    # ④ clearRate 上方的速率表
    ("""     *   0 ~  2000 日出      60      ← ZF29 起是原来的 3 倍
     *   2000 ~  5000 上午     135
     *   5000 ~  7000 正午     180
     *   7000 ~ 10000 下午     135
     *   10000 ~ 12000 傍晚     60
     *   12000 ~ 24000 夜间      0""",
     """     *   0 ~  2000 日出      20
     *   2000 ~  5000 上午      45
     *   5000 ~  7000 正午      60
     *   7000 ~ 10000 下午      45
     *   10000 ~ 12000 傍晚     20
     *   12000 ~ 24000 夜间      0"""),
    # ⑤ tick 里的行尾注释
    ("            // 正确语义：组的输出 = 速率和 ÷ 块数 = 每块的额定值（ZF29 起是 60/135/180，**每块**的）。",
     "            // 正确语义：组的输出 = 速率和 ÷ 块数 = 每块的额定值（用户给的 20/45/60 是**每块**的）。"),
]

# ---------- GroupEnergy：逐条反向替换 ----------
GE_EDITS = [
    ("""     * <p>例：3 块共 135 FE/t（ZF29 上午档）⇒ {@code 135 * 20 / 3 = 900}；
     * 若写成 {@code (135 / 3) * 20 = 900} 恰好也一样，但换成 20 FE/t 就差出来了：
     * {@code 20 * 20 / 3 = 133} vs {@code (20 / 3) * 20 = 120} —— 后者每秒白丢 13 FE（6.5%）。
     * 所以这一条**先乘后除**的写法不能"看起来等价"就改掉。</p>""",
     """     * <p>例：3 块共 20 FE/t ⇒ {@code 20 * 20 / 3 = 133}，整组 20 秒攒满 3×512；
     * 若写成 {@code (20 / 3) * 20 = 120}，每秒白丢 13 FE（6.5%）。</p>"""),
]


def rebuild(name, edits):
    src = os.path.join(SRC, name)
    text = io.open(src, encoding="utf-8").read()
    for new, old in edits:            # 注意顺序：把"改后的串"换回"改前的串"
        n = text.count(new)
        assert n == 1, "%s：反向后锚点命中 %d 次（应为 1）\n%r" % (name, n, new[:70])
        text = text.replace(new, old)
    data = text.encode("utf-8")
    got = hashlib.sha256(data).hexdigest()
    expect = EXPECT[name]
    print("%-30s 重建哈希 = %s" % (name, got))
    print("%-30s 期望哈希 = %s   %s" % ("", expect,
          "**命中**" if got == expect else "**不命中**（见 _说明.txt 的说明）"))
    out = os.path.join(DST, name)
    io.open(out, "wb").write(data)
    print("%-30s 已写回备份目录（%d 字节）\n" % ("", len(data)))


rebuild("SolarPanelBlockEntity.java", SP_EDITS)
rebuild("GroupEnergy.java", GE_EDITS)
print("两份改前副本重建完毕。")
print("⚠ SolarPanelBlockEntity.java 的哈希与记录值不符 —— 原因与举证见 _说明.txt。")
