# -*- coding: utf-8 -*-
u"""_zf114_verify.py —— ZF114 常驻校验：星轨坠 + 粗振金（0.11）

用户原话（2026-09-25）：
「加一个 星轨坠 道具 右键使用（一共四点耐久右键一次扣1点 不可附魔） 快捷栏上方显示30s红色倒计时
 10s之前再次右键可以取消 10s之后聊天栏通报倒计时 不可取消 最后1s聊天栏显示 星轨坠使用者 坐标
 作用：召唤出1个陨石 从y=200砸下来 伴随粒子效果 落地后产生7~20power的爆炸 带火
 并喷射出一些粗矿 7-12只有铁铜 12以上所有粗矿标签都有 15以上固定产出3个粗振金
 尽你所你做炫酷一点 同时不要太卡 谢谢了」
四条拍板：粗振金=新增物品 / 落点=右键那一刻的位置 / 爆炸=破坏地形+带火 / 先不给配方。

**期望值一律照上面那段话硬写**，不从被测代码里读常量（档案 §4.27：探针里出现被测常量 = 同义反复）。
真触发（右键、倒计时、陨石、爆炸、掉落档位）在探针 `Zf114Check.java` 里，必须真服务端跑。
"""
import io
import json
import os
import re
import struct
import sys

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

ROOT = r"E:\PotatoST"
JAVA = os.path.join(ROOT, r"src\main\java\com\potatost\mod")
CLIENT = os.path.join(JAVA, "client")
LANG = os.path.join(ROOT, r"src\main\resources\assets\potato_s_t\lang")
ITEM_MODELS = os.path.join(ROOT, r"src\main\resources\assets\potato_s_t\models\item")
ITEM_TEX = os.path.join(ROOT, r"src\main\resources\assets\potato_s_t\textures\item")
TAGS = os.path.join(ROOT, r"src\main\resources\data\c\tags\item")
RECIPES = os.path.join(ROOT, r"src\main\resources\data\potato_s_t\recipe")
TOOLS = os.path.join(ROOT, r"build\zftools")
DOC_EN = os.path.join(ROOT, r"docs\UpdateAnnouncement_EN.md")

EXPECT_KEYS = 482          # 四语言键数（ZF114 +15 之后的活体数字） + ZF117 进度 16 键
NEW_KEYS = 15

# 15 个新键 → 各自应有的 %s 个数（**照用户原话独立重写**：倒计时 1 个数字、
# 通报 2 个（谁 + 剩几秒）、最后警告 4 个（谁 + x y z）、下落提示 2 个（x z））
NEW_KEY_SHAPES = {
    u"gui.potato_s_t.starfall.countdown": 1,
    u"gui.potato_s_t.starfall.falling": 0,
    u"item.potato_s_t.raw_vibranium": 0,
    u"item.potato_s_t.starfall_pendant": 0,
    u"message.potato_s_t.starfall.cancelled": 0,
    u"message.potato_s_t.starfall.countdown": 2,
    u"message.potato_s_t.starfall.incoming": 2,
    u"message.potato_s_t.starfall.locked": 0,
    u"message.potato_s_t.starfall.started": 0,
    u"message.potato_s_t.starfall.warning": 4,
    u"tooltip.potato_s_t.starfall_pendant.1": 0,
    u"tooltip.potato_s_t.starfall_pendant.2": 0,
    u"tooltip.potato_s_t.starfall_pendant.3": 0,
    u"tooltip.potato_s_t.starfall_pendant.4": 0,
    u"tooltip.potato_s_t.starfall_pendant.5": 0,
}
LANGS = ("zh_cn", "en_us", "ja_jp", "ru_ru")

n_pass = 0
fails = []


def read(path):
    return io.open(path, encoding="utf-8", errors="replace").read()


def check(name, cond, detail=None):
    global n_pass
    if cond:
        n_pass += 1
    else:
        fails.append(name + (u"  ← %s" % detail if detail else u""))


def eq(name, want, got):
    check(name, want == got, u"期望 %r 实际 %r" % (want, got))


def png_header(path):
    u"""只读文件头（不解码）—— 返回 (w, h, colortype) 或 None"""
    try:
        d = open(path, "rb").read()
    except Exception:
        return None
    if len(d) < 26 or d[:8] != b"\x89PNG\r\n\x1a\n":
        return None
    if d[12:16] != b"IHDR":
        return None
    w, h = struct.unpack(">II", d[16:24])
    return w, h, d[25]


def main():
    global n_pass
    j = lambda name: read(os.path.join(JAVA, name))
    c = lambda name: read(os.path.join(CLIENT, name))

    # ============ A 文件存在 ============
    for name in ("ModEntities.java", "StarfallPendantItem.java", "StarfallRitualManager.java",
                 "StarfallMeteorEntity.java", "StarfallNetworking.java"):
        check(u"A1 主包有 %s" % name, os.path.exists(os.path.join(JAVA, name)))
    for name in ("StarfallClientState.java", "StarfallHudLayer.java", "StarfallMeteorRenderer.java"):
        check(u"A2 客户端包有 %s" % name, os.path.exists(os.path.join(CLIENT, name)))
    for name in ("starfall_pendant", "raw_vibranium"):
        check(u"A3 有物品模型 %s.json" % name, os.path.exists(os.path.join(ITEM_MODELS, name + u".json")))
        check(u"A4 有物品贴图 %s.png" % name, os.path.exists(os.path.join(ITEM_TEX, name + u".png")))
    check(u"A5 有 c:raw_materials/vibranium 标签", os.path.exists(os.path.join(TAGS, u"raw_materials", u"vibranium.json")))

    # ============ B 注册与装配 ============
    mod = j("PotatoST.java")
    ctor = mod.split(u"private void registerCapabilities")[0]      # 只看构造器那一段
    check(u"B1 构造期注册 ModEntities（§4.72 的触碰）",
          u"ModEntities.ENTITY_TYPES.register(modEventBus)" in ctor)
    check(u"B2 注册了数据包处理器", u"addListener(StarfallNetworking::register)" in ctor)
    check(u"B3 倒计时挂在 game 总线（NeoForge.EVENT_BUS）",
          u"NeoForge.EVENT_BUS.addListener(StarfallRitualManager::onServerTick)" in ctor)
    check(u"B4 登录补发同步也挂了", u"NeoForge.EVENT_BUS.addListener(StarfallRitualManager::onPlayerLogin)" in ctor)
    cli = j("PotatoSTClient.java")
    check(u"B5 注册了陨石实体渲染器",
          u"registerEntityRenderer(ModEntities.STARFALL_METEOR.get()" in cli)
    check(u"B6 HUD 挂在快捷栏那一层之上",
          u"registerAbove(VanillaGuiLayers.HOTBAR" in cli)
    items = j("ModItems.java")
    check(u"B7 注册了 starfall_pendant", u'ITEMS.register("starfall_pendant"' in items)
    check(u"B8 注册了 raw_vibranium", u'ITEMS.register("raw_vibranium"' in items)
    check(u"B9 两个都在创造页里",
          u"output.accept(STARFALL_PENDANT.get())" in items and u"output.accept(RAW_VIBRANIUM.get())" in items)

    # ============ C 用户规格逐条（数值照原话硬写）============
    pendant = j("StarfallPendantItem.java")
    check(u"C1 耐久 4 点", u"DURABILITY = 4" in pendant and u"durability(StarfallPendantItem.DURABILITY)" in items)
    check(u"C2 右键扣 1 点且只在起手成功时扣",
          u"stack.hurtAndBreak(1," in pendant and u"Outcome.STARTED" in pendant)
    check(u"C3 不可附魔（isEnchantable false + 附魔值 0）",
          re.search(u"isEnchantable\\(ItemStack[^)]*\\)\\s*\\{\\s*return false;", pendant) is not None
          and re.search(u"getEnchantmentValue\\(\\)\\s*\\{\\s*return 0;", pendant) is not None)
    enchant_hits = []
    enc_dir = os.path.join(ROOT, r"src\main\resources\data\minecraft\tags\item", u"enchantable")
    for base, _dirs, files in os.walk(enc_dir):
        for f in files:
            if u"starfall" in read(os.path.join(base, f)):
                enchant_hits.append(f)
    eq(u"C4 没有任何 enchantable 标签收它", [], enchant_hits)

    ritu = j("StarfallRitualManager.java")
    check(u"C5 倒计时 30 秒（600 tick）", u"TOTAL_TICKS = 20 * 30" in ritu)
    check(u"C6 前 10 秒可取消（200 tick）", u"CANCEL_TICKS = 20 * 10" in ritu)
    check(u"C7 取消窗口的判据是「剩余 > 总时长 - 可取消时长」",
          u"current.endTick - now > TOTAL_TICKS - CANCEL_TICKS" in ritu)
    check(u"C8 威力区间 7~20", u"MIN_POWER = 7" in ritu and u"MAX_POWER = 20" in ritu)
    check(u"C9 12 以上才走粗矿标签", u"TAG_POWER = 12" in ritu)
    check(u"C10 15 以上固定 3 个粗振金", u"VIBRANIUM_POWER = 15" in ritu and u"VIBRANIUM_COUNT = 3" in ritu)
    check(u"C11 通报节点 = 剩余 20/15/10/5/3/2 秒",
          re.search(u"ANNOUNCE_SECONDS = \\{20, 15, 10, 5, 3, 2\\}", ritu) is not None)
    check(u"C12 最后 1 秒那条带使用者 + 三个坐标（4 个占位符）",
          u"message.potato_s_t.starfall.warning" in ritu and u"floor(ritual.x), floor(ritual.y), floor(ritual.z)" in ritu)
    check(u"C13 落点固定在右键那一刻（构造器里一次性取 x/y/z）",
          u"this.x = player.getX();" in ritu and u"this.z = player.getZ();" in ritu)
    meteor = j("StarfallMeteorEntity.java")
    check(u"C14 从 y=200 砸下来", u"SPAWN_Y = 200.0D" in meteor and u"StarfallMeteorEntity.SPAWN_Y" in ritu)
    check(u"C15 点名的铁/铜是原版粗铁粗铜",
          u"Items.RAW_IRON" in ritu and u"Items.RAW_COPPER" in ritu)

    # ============ D 语义与顺序（这些是"能失败"的检查）============
    impact_body = ritu.split(u"static void impact(")[1].split(u"static List<ItemStack> rollLoot")[0]
    i_explode = impact_body.find(u"level.explode(")
    i_spawn = impact_body.find(u"new ItemEntity(")
    check(u"D1 先爆炸、后撒矿物（物品不会被自己的爆炸清掉）",
          i_explode >= 0 and i_spawn > i_explode, u"explode@%d spawn@%d" % (i_explode, i_spawn))
    check(u"D2 爆炸带火（第 6 个实参 true）且破坏地形（BLOCK）",
          re.search(u"level\\.explode\\([^;]*?, true, Level\\.ExplosionInteraction\\.BLOCK\\)", impact_body) is not None)
    loot = ritu.split(u"static List<ItemStack> rollLoot")[1].split(u"private static Item pickRawOre")[0]
    iron_branch = loot.split(u"pickRawOre(random)")[0]
    check(u"D3 7~12 那一档只出铁/铜（不碰粗矿标签）",
          u"Items.RAW_IRON" in iron_branch and u"Items.RAW_COPPER" in iron_branch)
    check(u"D4 15 以上那一档用常量 3（不写死数字）", u"VIBRANIUM_COUNT" in loot)
    tick_body = meteor.split(u"public void tick()")[1]
    check(u"D5 落地即引爆并自毁",
          re.search(u"StarfallRitualManager\\.impact\\([^;]*?\\);\\s*this\\.discard\\(\\);", tick_body) is not None)
    check(u"D6 兜底寿命存在（20 秒没落地就自毁）", u"MAX_LIFE_TICKS" in meteor)
    net = j("StarfallNetworking.java")
    check(u"D7 只有 S2C（playToClient），不需要 C2S", u"playToClient(" in net and u"playToServer(" not in net)
    check(u"D8 阶段常量三个：CLEAR/START/FALLING",
          u"PHASE_CLEAR = 0" in net and u"PHASE_START = 1" in net and u"PHASE_FALLING = 2" in net)

    # ============ E 「不要太卡」============
    check(u"E1 尾迹每 tick 火焰 8 颗 / 浓烟 3 团（照代码硬写）",
          u"ParticleTypes.FLAME, x, y, z, 8," in meteor and u"ParticleTypes.LARGE_SMOKE, x, y + 0.6D, z, 3," in meteor)
    check(u"E2 熔岩与末地烛是抽稀的（%3 / %5）",
          u"this.tickCount % 3 == 0" in meteor and u"this.tickCount % 5 == 0" in meteor)
    check(u"E3 爆炸用原版 level.explode（不自己遍历方块）",
          u"level.explode(" in ritu and u"destroyBlock(" not in ritu)

    # ============ F 资源 ============
    for name in ("starfall_pendant", "raw_vibranium"):
        head = png_header(os.path.join(ITEM_TEX, name + u".png"))
        if head is None:
            check(u"F1 %s.png 是真 PNG" % name, False, u"文件头不是 PNG")
            continue
        w, h, ctype = head
        eq(u"F1 %s.png 是 16×16 RGBA" % name, (16, 16, 6), (w, h, ctype))
        model = json.loads(read(os.path.join(ITEM_MODELS, name + u".json")))
        eq(u"F2 %s 模型 layer0 指向自己" % name, u"potato_s_t:item/" + name,
           model.get(u"textures", {}).get(u"layer0"))
    tag = json.loads(read(os.path.join(TAGS, u"raw_materials", u"vibranium.json")))
    eq(u"F3 粗振金的 c: 标签内容", [u"potato_s_t:raw_vibranium"], tag.get(u"values"))
    parent = json.loads(read(os.path.join(TAGS, u"raw_materials.json")))
    check(u"F4 父标签 c:raw_materials 收下粗振金", u"potato_s_t:raw_vibranium" in parent.get(u"values", []))
    # ⚠ ZF118（用户：「星轨坠配方；中间一个下界之星 上下左右各一个星璨钢 四角放岩浆块」）
    #   ⇒ 星轨坠**现在有配方了**：这条 F5 原来断言"两样都没有配方"，现在只一半成立 ——
    #     星轨坠必须有（ZF118 的图纸，走生成器表 `_zf45_recipes.py` 生成）；
    #     粗振金仍然没有（「先不给」对它依然有效）。两条判据分开写。
    check(u"F5 星轨坠现在**有**配方（ZF118 用户给的图纸）",
          os.path.exists(os.path.join(RECIPES, u"starfall_pendant.json")))
    # ⚠ ZF121：粗振金仍然没有**数据包**配方，但它现在是**合金冶炼炉**那条振金配方的
    #   消耗品（1 个）⇒ 措辞补一句，判据不动。
    check(u"F5b 粗振金仍然没有数据包配方（它现在是合金炉的消耗品 · ZF121）",
          not os.path.exists(os.path.join(RECIPES, u"raw_vibranium.json")))

    # ============ G 四语言 ============
    # ⚠ 先各自解析、解析失败就报**命名失败**而不是抛栈：校验脚本自己崩掉的话，
    #    外面既看不到"哪条断言挂了"、也分不清"检查跑了且失败"还是"检查根本没跑完"
    #    （ZF114 反证 J11 就是这么暴露出来的：删掉最后一条键 ⇒ JSON 非法 ⇒ 崩栈 ⇒ 假绿）。
    lang = {}
    broken = []
    for l in LANGS:
        try:
            lang[l] = json.loads(read(os.path.join(LANG, l + u".json")))
        except Exception as exc:
            broken.append(l)
            check(u"G0 %s.json 能被真解析器读出来" % l, False, u"%s" % exc)
    if broken:
        print(u"通过 = %d   失败 = %d（因为有语言文件解析不了，G1~G6 没跑）" % (n_pass, len(fails)))
        for f in fails:
            print(u"  !! " + f)
        return 1

    eq(u"G1 四语言键数一致且 = %d" % EXPECT_KEYS, [EXPECT_KEYS] * 4, [len(lang[l]) for l in LANGS])
    base = set(lang["zh_cn"].keys())
    for l in LANGS[1:]:
        eq(u"G2 %s 的键集合与 zh_cn 一致" % l, set(), base ^ set(lang[l].keys()))
    for key, shape in NEW_KEY_SHAPES.items():
        for l in LANGS:
            value = lang[l].get(key)
            if value is None:
                check(u"G3 %s / %s 存在" % (l, key), False)
                continue
            eq(u"G3 %s / %s 的占位符个数" % (l, key), shape, value.count(u"%s"))
            check(u"G4 %s / %s 没有 ASCII 双引号" % (l, key), u'"' not in value)
    eq(u"G5 新增键正好 %d 个" % NEW_KEYS, NEW_KEYS, len(NEW_KEY_SHAPES))
    check(u"G6 英文公告已跟到 %d 键" % EXPECT_KEYS, u"(%d keys each)" % EXPECT_KEYS in read(DOC_EN))

    # ============ H 活体数字 ============
    stale = []
    for f in sorted(os.listdir(TOOLS)):
        if not re.match(r"^_zf\d+_verify\.py$", f):
            continue
        if f == u"_zf114_verify.py":
            continue          # 本文件的断言名里就写着那个旧数字（"已无旧键数 417"），不算残留
        if re.search(r"\b417\b", read(os.path.join(TOOLS, f))):
            stale.append(f)
    eq(u"H1 往轮校验里已无旧键数 417", [], stale)

    # ============ I 文档 ============
    doc = read(os.path.join(ROOT, r"docs\开发档案.md"))
    check(u"I1 档案 §5 有 ZF114 的行", u"| ZF114 | **新建 `zf114_pre`**" in doc)
    check(u"I2 档案 §9 有 ZF114 的小节", u"### ZF114（0.11）星轨坠 + 粗振金" in doc)
    check(u"I3 档案写明了本轮的新 SHA1", u"303c5d468b96826ef6836b0a4e54ccb8a539557c" in doc)
    check(u"I4 档案写明了上一版 SHA1 作废", u"90510e1890af79242cb41e0cda0a2f6472b12cdf` 作废" in doc)
    check(u"I5 档案记了 §4.88（c:raw_materials 含原版三项）", u"### 4.88 【数据事实】" in doc)

    print(u"通过 = %d   失败 = %d" % (n_pass, len(fails)))
    for f in fails:
        print(u"  !! " + f)
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())
