# -*- coding: utf-8 -*-
u"""_zf109_falsify.py —— ZF109 的反证刀（K99~K120）

口径（§4.17 / §4.77）：
  · 先跑一遍校验器确认**基线是绿的**（不绿就不动刀，先修）；
  · 每把刀：**改一处语义** ⇒ 跑 `_zf109_verify.py` ⇒ 必须 **FAIL**（退出码非 0），
    而且失败输出里要出现**指定的那条检查**（证明咬住的是对的那一条，不是碰巧别的红了）；
  · 每把刀跑完**逐字节还原**（比对 sha1），再跑下一把；
  · 收尾再跑一次校验器，必须回到全绿；
  · 一把刀 180 秒超时（§4.77：校验器卡死不算"咬住了"）。

⚠ 本脚本会临时改真文件，**跑之前确认没有别的会话线在同时改同一批文件**。
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
RES = os.path.join(ROOT, r"src\main\resources")
ASSETS = os.path.join(RES, r"assets\potato_s_t")
DATA = os.path.join(RES, r"data\potato_s_t")
VERIFY = os.path.join(ZT, u"_zf109_verify.py")

BE = os.path.join(JAVA, "OilPumpBlockEntity.java")
DEP = os.path.join(JAVA, "OilfieldDepletion.java")
LAMP = os.path.join(JAVA, r"client\gui\parts\StatusLampPart.java")
SCR = os.path.join(JAVA, r"client\OilPumpScreen.java")
MNU = os.path.join(JAVA, "OilPumpMenu.java")
REC = os.path.join(DATA, r"recipe\oil_pump.json")
TAG = os.path.join(RES, r"data\minecraft\tags\block\mineable\pickaxe.json")
BLOCKMODEL = os.path.join(ASSETS, r"models\block\oil_pump.json")
PNG = os.path.join(ASSETS, r"textures\block\oil_pump.png")
ZH = os.path.join(ASSETS, r"lang\zh_cn.json")
EN = os.path.join(ASSETS, r"lang\en_us.json")
ANN = os.path.join(ROOT, r"docs\UpdateAnnouncement_EN.md")
REPORT = os.path.join(ZT, u"_zf109_probe_utf8.txt")

# (编号, 说明, 文件, 原文, 新文, 失败输出里必须出现的字样)
KNIVES = [
    ("K99", u"耗能公式少乘一个 n（8n²+80n → 8n²+80）", BE,
     u"return 8 * chains * chains + 80 * chains;", u"return 8 * chains * chains + 80;",
     u"耗能公式 n=1"),
    ("K100", u"罐容 25B → 20B", BE,
     u"public static final int TANK_CAPACITY = 25 * 1000;",
     u"public static final int TANK_CAPACITY = 20 * 1000;", u"常量 TANK_CAPACITY"),
    ("K101", u"配方第一行改成三块硬质钛合金", REC,
     u"    \"ATA\",", u"    \"AAA\",", u"九宫格三行"),
    ("K102", u"配方产物改成空气分离器", REC,
     u"    \"id\": \"potato_s_t:oil_pump\",", u"    \"id\": \"potato_s_t:air_separator\",",
     u"产物 = oil_pump ×1"),
    ("K103", u"转换范围 10 区块 → 4 区块", BE,
     u"public static final int CONVERT_CHUNKS = 10;",
     u"public static final int CONVERT_CHUNKS = 4;", u"常量 CONVERT_CHUNKS"),
    ("K104", u"群系门禁认错群系（海洋油田 → 咸水河）", BE,
     u"server.getBiome(this.worldPosition).is(SaltyRiverBiomeSource.OCEAN_OILFIELD)",
     u"server.getBiome(this.worldPosition).is(SaltyRiverBiomeSource.SALTY_RIVER)",
     u"只在海洋油田开工"),
    ("K105", u"下探不再要求 waterlogged（干链子也算）", BE,
     u"&& state.getValue(ChainBlock.WATERLOGGED))", u"&& true)",
     u"含水锁链 = 原版锁链 + WATERLOGGED"),
    ("K106", u"下探上限 64 → 256 格", BE,
     u"public static final int MAX_CHAIN_SCAN = 64;",
     u"public static final int MAX_CHAIN_SCAN = 256;", u"常量 MAX_CHAIN_SCAN"),
    ("K107", u"状态灯 16 号的后缀接到 1 号（empty）", LAMP,
     u"case OilPumpBlockEntity.STATUS_NO_CHAIN -> \"no_chain\";",
     u"case OilPumpBlockEntity.STATUS_NO_CHAIN -> \"empty\";", u"灯：16 号的后缀 no_chain"),
    ("K108", u"zh_cn 少一个采油机键", ZH,
     u"    \"block.potato_s_t.oil_pump\":  \"采油机\",\n", u"", u"zh_cn.json 键数"),
    ("K109", u"en_us 的 chains 那行少一个 %s", EN,
     u"\"Waterlogged chains: %s\"", u"\"Waterlogged chains\"", u"chains 那行有 1 个"),
    ("K110", u"贴图换成 12 色噪声（糊图）", PNG, u"", u"", u"颜色数 ≤ 8"),
    ("K111", u"贴图换成 32×32", PNG, u"", u"", u"贴图 16×16"),
    ("K112", u"挖掘标签漏挂采油机", TAG,
     u"    \"potato_s_t:oil_pump\"\n", u"", u"挖掘标签里有"),
    ("K113", u"状态码 15 改成 14（撞酸性反应室的号）", BE,
     u"public static final int STATUS_NOT_OILFIELD = 15;",
     u"public static final int STATUS_NOT_OILFIELD = 14;", u"采油机自己声明了 15 号"),
    ("K114", u"转换后不通知客户端（删 resendBiomesForChunks）", DEP,
     u"        level.getChunkSource().chunkMap.resendBiomesForChunks(loaded);\n", u"",
     u"resendBiomesForChunks"),
    ("K115", u"转换后不标脏（不落盘）", DEP,
     u"chunk.fillBiomesFromNoise(resolver, sampler);\n            chunk.setUnsaved(true);",
     u"chunk.fillBiomesFromNoise(resolver, sampler);\n            chunk.setUnsaved(false);",
     u"setUnsaved(true)"),
    ("K116", u"resolver 把区域外也改成目标（抹平整根柱子）", DEP,
     u"                return current;", u"                return target;",
     u"resolver 只改海洋油田、别的原样返回"),
    ("K117", u"状态灯前缀接回微型粉碎机的", SCR,
     u"STATUS_KEY_PREFIX = \"gui.potato_s_t.oil_pump.status.\";",
     u"STATUS_KEY_PREFIX = \"gui.potato_s_t.micro_crusher.status.\";",
     u"工作指示灯用自己的文案前缀"),
    ("K118", u"界面里塞一个能量条（用户说不要）", SCR,
     u"import com.potatost.mod.client.gui.parts.StatusLampPart;",
     u"import com.potatost.mod.client.gui.parts.StatusLampPart;\n"
     u"import com.potatost.mod.client.gui.parts.EnergyBarPart;",
     u"界面里没有能量条"),
    ("K119", u"方块模型父级写错", BLOCKMODEL,
     u"\"parent\": \"minecraft:block/cube_all\"", u"\"parent\": \"minecraft:block/cube\"",
     u"方块模型父级"),
    ("K120", u"菜单偷偷开一个机器槽", MNU,
     u"super(ModMenus.OIL_PUMP_MENU.get(), containerId, OilPumpBlockEntity.SLOT_COUNT, access);",
     u"super(ModMenus.OIL_PUMP_MENU.get(), containerId, 1, access);",
     u"机器槽数 = SLOT_COUNT"),
    ("K121", u"探针报告改成不绿（伪造证据）", REPORT,
     u"verdict: ALL OK", u"verdict: **1 FAILED**", u"报告是全绿"),
]

fails = []


def sha1b(b):
    return hashlib.sha1(b).hexdigest()


def run_verify():
    try:
        r = subprocess.run([sys.executable, VERIFY], stdout=subprocess.PIPE,
                           stderr=subprocess.STDOUT, timeout=180)
        return r.returncode, r.stdout.decode("utf-8", "replace")
    except subprocess.TimeoutExpired:
        return 99, u"**超时 180 秒**"


def noise_png(w=16, h=16, colors=12):
    import struct
    import zlib
    raw = b""
    for y in range(h):
        raw += b"\x00"
        for x in range(w):
            i = (y * w + x) % colors
            raw += struct.pack("4B", (i * 20) & 255, (i * 37) & 255, (i * 53) & 255, 255)

    def chunk(tag, data):
        c = tag + data
        return struct.pack(">I", len(data)) + c + struct.pack(">I", zlib.crc32(c) & 0xFFFFFFFF)
    return (b"\x89PNG\r\n\x1a\n"
            + chunk(b"IHDR", struct.pack(">IIBBBBB", w, h, 8, 6, 0, 0, 0))
            + chunk(b"IDAT", zlib.compress(raw, 9))
            + chunk(b"IEND", b""))


def main():
    print(u"== 基线 ==")
    rc, out = run_verify()
    if rc != 0:
        print(u"  [STOP] 基线不是绿的（退出码 %d）—— 先修再动刀" % rc)
        for line in out.split(u"\n"):
            if line.strip().startswith(u"!!"):
                print(u"    " + line.strip())
        return 1
    line = [l for l in out.split(u"\n") if u"通过" in l and u"失败" in l]
    print(u"  基线绿：%s" % (line[-1].strip() if line else u"?"))

    n_ok = 0
    for kid, why, path, old, new, expect in KNIVES:
        if not os.path.exists(path):
            fails.append(u"%s：目标文件不在 %s" % (kid, path))
            continue
        orig = open(path, "rb").read()
        before = sha1b(orig)
        if old:
            text = orig.decode("utf-8")
            if text.count(old) != 1:
                fails.append(u"%s：原文命中 %d 次（要求 1 次）—— 锚点过时了"
                             % (kid, text.count(old)))
                continue
            open(path, "wb").write(text.replace(old, new, 1).encode("utf-8"))
        elif kid == "K110":
            open(path, "wb").write(noise_png(16, 16, 12))
        elif kid == "K111":
            open(path, "wb").write(noise_png(32, 32, 4))
        else:
            fails.append(u"%s：没有定义改法" % kid)
            continue

        rc, out = run_verify()
        back = sha1b(open(path, "rb").read())
        open(path, "wb").write(orig)
        restored = sha1b(open(path, "rb").read()) == before
        if not restored:
            fails.append(u"%s：**还原失败**（哈希对不上）" % kid)
            break
        caught = (rc != 0) and (expect in out)
        if caught:
            n_ok += 1
            print(u"  [OK]   %s %s ⇒ 校验器 FAIL 且咬住「%s」" % (kid, why, expect))
        else:
            if rc == 0:
                fails.append(u"%s %s ⇒ **校验器还是绿的（这把刀没咬住）**" % (kid, why))
            else:
                fails.append(u"%s %s ⇒ 红了但咬错的检查（没出现「%s」）" % (kid, why, expect))
            print(u"  [BAD]  %s %s（退出码 %d）" % (kid, why, rc))
            for l in out.split(u"\n"):
                if l.strip().startswith(u"!!"):
                    print(u"         %s" % l.strip()[:110])

    print(u"\n== 收尾：还原后必须回到全绿 ==")
    rc, out = run_verify()
    line = [l for l in out.split(u"\n") if u"通过" in l and u"失败" in l]
    print(u"  %s（退出码 %d）" % (line[-1].strip() if line else u"?", rc))
    if rc != 0:
        fails.append(u"收尾不是全绿")
        for l in out.split(u"\n"):
            if l.strip().startswith(u"!!"):
                print(u"    " + l.strip())

    print(u"\n刀 = %d 把，咬住 = %d，失败项 = %d" % (len(KNIVES), n_ok, len(fails)))
    for f in fails:
        print(u"  !! " + f)
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())
