# -*- coding: utf-8 -*-
u"""_zf127_falsify.py —— ZF127 的反证刀（K205~K222，18 把）

口径同前：基线绿 → 改一处语义 ⇒ 门必须 FAIL 且**咬住指定的那一条** ⇒ 逐字节还原 ⇒ 收尾回到全绿。

刀面（对照用户那句原话的每一半）：
  K205 银线速率 16134 → 2048（"传输速率 16134Fe/t"没了）
  K206 capacityFor 写回 max() 版（**本轮探针真抓到的那个 bug**：铜线档被顶到 4096）
  K207 银线轴耐久 → 16（"和铜线轴一致"没了）
  K208 创造页少一行（§4.82 那口老锅）
  K209 银白色改成古铜色（"变成银白色的"没了）
  K210 WIRE_RADIUS 改粗（"一样的像素大小"没了）
  K211 银线轴走 TRANSFER_RATE（当成铜线）
  K212 读盘只认新格式（把老存档那条兜底删掉）
  K213 存盘不写 rate
  K214 拆线后不夹电量
  K215 zh_cn 的银线键换个值
  K216 只给 zh_cn 加键、别的语言不加（四份不一致）
  K217 银线配方换成铜锭（"铜的换成银的"反了）
  K218 手改 silver_wire.json（表与盘不同步，§4.93）
  K219 给银线补一张 png（"材质先不画"违背）
  K220 往轮门里的 478 改回一个（活体数字又过期）
  K221 `_zf90_verify.py` 的 15 改回 13（待画那条链断）
  K222 公告键数改回 476
"""
import hashlib
import io
import os
import re
import subprocess
import sys

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

ROOT = r"E:\PotatoST"
ZT = os.path.join(ROOT, r"build\zftools")
JAVA = os.path.join(ROOT, r"src\main\java\com\potatost\mod")
MODITEMS = os.path.join(JAVA, u"ModItems.java")
TBE = os.path.join(JAVA, u"TerminalBlockEntity.java")
TB = os.path.join(JAVA, u"TerminalBlock.java")
TR = os.path.join(JAVA, u"client", u"TerminalRenderer.java")
LANG_ZH = os.path.join(ROOT, r"src\main\resources\assets\potato_s_t\lang\zh_cn.json")
LANG_EN = os.path.join(ROOT, r"src\main\resources\assets\potato_s_t\lang\en_us.json")
RECIPE_WIRE = os.path.join(ROOT, r"src\main\resources\data\potato_s_t\recipe\silver_wire.json")
ANN = os.path.join(ROOT, r"docs\UpdateAnnouncement_EN.md")
Z100 = os.path.join(ZT, u"_zf100_verify.py")
Z90 = os.path.join(ZT, u"_zf90_verify.py")
VERIFY = os.path.join(ZT, u"_zf127_verify.py")

KNIVES = [
    dict(id="K205", why=u"银线速率 16134 → 2048（和铜线一样了）", path=TBE,
         old=u"SILVER_TRANSFER_RATE = 16_134;", new=u"SILVER_TRANSFER_RATE = 2_048;",
         expect=u"B1 SILVER_TRANSFER_RATE = 16134"),
    dict(id="K206", why=u"capacityFor 写回 max() 版（**探针抓到的真 bug**：铜线档被顶成 4096）", path=TBE,
         old=u"return lineRate <= TRANSFER_RATE ? MAX_ENERGY : lineRate * 2;",
         new=u"return Math.max(MAX_ENERGY, lineRate * 2);",
         expect=u"B3 容量分档"),
    dict(id="K207", why=u"银线轴耐久 32 → 16（不再和铜线轴一致）", path=MODITEMS,
         old=u'ITEMS.register("silver_wire_spool",\n                    () -> new Item(new Item.Properties().durability(32)));',
         new=u'ITEMS.register("silver_wire_spool",\n                    () -> new Item(new Item.Properties().durability(16)));',
         expect=u"A2 银线轴登记"),
    dict(id="K208", why=u"创造页少一行（§4.82：物品栏看不见 + JEI 搜不到）", path=MODITEMS,
         old=u"                        output.accept(SILVER_WIRE_SPOOL.get());      // ← 0.11 ZF127 银线轴\n",
         new=u"",
         expect=u"A3 两个都进了创造页"),
    dict(id="K209", why=u"银白色改成古铜色（不是银白色的了）", path=TR,
         old=u"private static final float SILVER_R = 0.88F, SILVER_G = 0.91F, SILVER_B = 0.95F, SILVER_A = 0.9F;",
         new=u"private static final float SILVER_R = 0.80F, SILVER_G = 0.50F, SILVER_B = 0.20F, SILVER_A = 0.9F;",
         expect=u"C6 渲染器有银白色常量"),
    dict(id="K210", why=u"线径改粗（用户点名「像素大小一样」）", path=TR,
         old=u"WIRE_RADIUS = 0.03125D;", new=u"WIRE_RADIUS = 0.0625D;",
         expect=u"C9 **线径那一行与改前件逐字节相同**"),
    dict(id="K211", why=u"银线轴分支用 TRANSFER_RATE（当成铜线接）", path=TB,
         old=u"handleConnectionTool(level, pos, player, TerminalBlockEntity.SILVER_TRANSFER_RATE)",
         new=u"handleConnectionTool(level, pos, player, TerminalBlockEntity.TRANSFER_RATE)",
         expect=u"C1 银线轴分支在"),
    dict(id="K212", why=u"读盘只认新格式（老存档的线全掉）", path=TBE,
         old=u'''        } else {
            for (Tag entry : tag.getList("connections", Tag.TAG_LONG)) {
                this.connections.put(BlockPos.of(((LongTag) entry).getAsLong()), TRANSFER_RATE);
            }
        }''',
         new=u'''        }''',
         expect=u"B10 读盘认两种格式"),
    dict(id="K213", why=u"存盘不写 rate（银线读回来变铜线）", path=TBE,
         old=u'            c.putInt("rate", entry.getValue());\n', new=u"",
         expect=u"B11 存盘写 pos + rate"),
    dict(id="K214", why=u"拆线后不夹电量（会出现「存量 > 上限」）", path=TBE,
         old=u'''        int cap = capacity();
        if (energy > cap) {
            energy = cap;
            setChanged();
        }''',
         new=u"        int cap = capacity();",
         expect=u"B12 银线拆掉之后电量夹到新上限"),
    dict(id="K215", why=u"zh_cn 的银线键换个值（中文名不对）", path=LANG_ZH,
         old=u'"item.potato_s_t.silver_wire":  "银线"', new=u'"item.potato_s_t.silver_wire":  "银丝"',
         expect=u"E3 `item.potato_s_t.silver_wire`"),
    dict(id="K216", why=u"只给 zh_cn 加键、en_us 不加（四份键集合不一致）", path=LANG_EN,
         old=u'"item.potato_s_t.silver_wire":  "Silver Wire",\n', new=u"",
         expect=u"E1 四份各 478 键"),
    dict(id="K217", why=u"银线配方换成铜锭（「铜的换成银的」反了）", path=RECIPE_WIRE,
         old=u'"tag": "c:ingots/silver"', new=u'"tag": "c:ingots/copper"',
         expect=u"D5 银线配方 = 铜线配方"),
    dict(id="K218", why=u"手改 silver_wire.json（表与盘不同步，§4.93）", path=RECIPE_WIRE,
         old=u'"count": 4', new=u'"count": 8',
         expect=u"D8 盘上那两条 JSON == 生成器表算出来的"),
    dict(id="K219", why=u"给银线补一张 png（「材质先不画」被违背）", path=RECIPE_WIRE, mode="png",
         old=u"", new=u"",
         expect=u"D2 **没有自己的贴图 png**"),
    dict(id="K220", why=u"往轮门里的 478 改回 476（活体数字又过期）", path=Z100,
         old=u"EXPECT_KEYS = 478", new=u"EXPECT_KEYS = 476",
         expect=u"F1 常驻门里再没有裸的旧键数"),
    dict(id="K221", why=u"`_zf90_verify.py` 的 15 改回 13（待画那条链断）", path=Z90,
         old=u'check(u"`_zf71_verify.py` 的期望值同步成 15", u"n_draw == 15" in z71)',
         new=u'check(u"`_zf71_verify.py` 的期望值同步成 13", u"n_draw == 13" in z71)',
         expect=u"F4 `_zf90_verify.py` 四处都跟到 15"),
    dict(id="K222", why=u"公告键数改回 476（公告与盘上打架）", path=ANN,
         old=u"(478 keys each)", new=u"(476 keys each)",
         expect=u"F7 公告键数 = 478"),
]

fails = []
PNG = os.path.join(ROOT, r"src\main\resources\assets\potato_s_t\textures\item\silver_wire.png")


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
        if k.get("mode") == "png":
            orig = None
            try:
                io.open(PNG, "wb").write(b"\x89PNG\r\n\x1a\n" + b"\x00" * 8)
                rc, out = run()
            finally:
                if os.path.exists(PNG):
                    os.remove(PNG)
        else:
            path = k["path"]
            orig = open(path, "rb").read()
            before = hashlib.sha1(orig).hexdigest()
            try:
                text = orig.decode("utf-8")
                # ⚠ 锚点要按**这个文件自己的换行**换算（TerminalBlockEntity 是 CRLF，
                #   第一版直接拿 \n 去比 ⇒ K212/K213/K214 三条都"锚点命中 0 次"，§4.8）
                nl = u"\r\n" if u"\r\n" in text else u"\n"
                old = k["old"].replace(u"\n", nl)
                new = k["new"].replace(u"\n", nl)
                if text.count(old) != 1:
                    fails.append(u"%s：锚点命中 %d 次" % (k["id"], text.count(old)))
                    print(u"  [BAD]  %s 锚点命中 %d 次" % (k["id"], text.count(old)))
                    continue
                open(path, "wb").write(text.replace(old, new, 1).encode("utf-8"))
                rc, out = run()
            finally:
                open(path, "wb").write(orig)
            after = hashlib.sha1(open(path, "rb").read()).hexdigest()
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
    if os.path.exists(PNG):
        fails.append(u"探针留了一张 silver_wire.png 没删")
    print(u"刀 = %d，咬住 = %d，失败项 = %d" % (len(KNIVES), n_ok, len(fails)))
    for f in fails:
        print(u"  !! " + f)
    return 1 if fails else 0


if __name__ == u"__main__":
    sys.exit(main())
