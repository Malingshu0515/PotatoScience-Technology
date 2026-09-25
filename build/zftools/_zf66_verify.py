# -*- coding: utf-8 -*-
"""_zf66_verify.py —— ZF66 常驻校验：钛合金剑 / 钛合金镐的"资产那一半"

服务端探针 `AlloyToolCheck` 量的是**行为**（耐久/伤害/挖掘等级/配方能不能摆出来）；
这个脚本量的是**盘上的文件**——它俩刚好互补，而且这里全是"坏了也不报错"的坏法：

  ① 贴图：中文原名必须已经改成 ASCII（§4.24），而且是**真 PNG 16×16 带透明底**；
  ② 模型：工具要用 `item/handheld`（用 `item/generated` 的话拿在手里是"平铺"的），layer0 必须指向自己那张；
  ③ 配方：形状照原版（剑 1×3 竖排、镐 3+2），原料 = 轻质钛合金 + 木棍，**每行字符数必须一致且 ≤3**（§6.13）；
  ④ 语言：四份文件键数一致、两个物品键都在、**不许有 `tooltip.potato_s_t.titanium_alloy*`**
     （用户：「工具就不需要 shift 查看详细介绍了」）；
  ⑤ Java 侧：两个 id 在 ModItems 里注册、进了创造页；ModTiers 里的数值是用户给的（字面量），
     而且**修理材料必须是懒取的**（静态字段里直接 `.get()` 会撞 §4.1 那条未绑定崩溃）。

退出码 0 = 全过。
"""
import io
import json
import os
import re
import struct
import sys

ROOT = r"E:\PotatoST"
ASSETS = os.path.join(ROOT, r"src\main\resources\assets\potato_s_t")
DATA = os.path.join(ROOT, r"src\main\resources\data\potato_s_t")
LANG = os.path.join(ASSETS, "lang")
JAVA = os.path.join(ROOT, r"src\main\java\com\potatost\mod")

IDS = ["titanium_alloy_sword", "titanium_alloy_pickaxe"]
MATERIAL = "potato_s_t:light_titanium_alloy"

fails = []


def check(ok, msg):
    print(("  [OK]   " if ok else "  [FAIL] ") + msg)
    if not ok:
        fails.append(msg)
    return ok


def read(path):
    with io.open(path, encoding="utf-8") as fh:
        return fh.read()


def read_png_header(path):
    b = io.open(path, "rb").read()
    if b[:8] != b"\x89PNG\r\n\x1a\n":
        return None
    w, h = struct.unpack(">II", b[16:24])
    return w, h, b[25]          # 25 = colorType（6 = RGBA）


print("== ① 贴图（用户给的，已改名成 ASCII）==")
tex_dir = os.path.join(ASSETS, "textures", "item")
for i in IDS:
    p = os.path.join(tex_dir, i + ".png")
    if not os.path.isfile(p):
        check(False, "缺贴图 %s.png" % i)
        continue
    head = read_png_header(p)
    ok = head is not None and head[0] == 16 and head[1] == 16 and head[2] == 6
    check(ok, "textures/item/%s.png 是真 PNG 16x16 RGBA（读到 %s）" % (i, head))
leftover = [f for f in os.listdir(tex_dir) if any(ord(c) > 127 for c in f)]
check(not leftover, "textures/item 下没有中文文件名了（还剩 %s）" % (leftover or "无"))
# 自带的小解码器查"真有透明像素"
sys.path.insert(0, os.path.join(ROOT, r"build\zftools"))
import _zf66_png  # noqa: E402
for i in IDS:
    w, h, ctype, px = _zf66_png.read_png(os.path.join(tex_dir, i + ".png"))
    trans = sum(1 for p in px if p[3] == 0)
    check(trans > 0, "%s.png 有 %d 个全透明像素（物品贴图必须是透明底）" % (i, trans))

print()
print("== ② 模型（handheld + 指向自己的贴图）==")
for i in IDS:
    p = os.path.join(ASSETS, "models", "item", i + ".json")
    if not os.path.isfile(p):
        check(False, "缺模型 models/item/%s.json" % i)
        continue
    m = json.loads(read(p))
    check(m.get("parent") == "minecraft:item/handheld",
          "%s.json parent = item/handheld（工具拿在手里才不是平铺的）" % i)
    want = "potato_s_t:item/" + i
    check(m.get("textures", {}).get("layer0") == want, "%s.json layer0 = %s" % (i, want))

print()
print("== ③ 配方（形状照原版，锭换成轻质钛合金）==")
SHAPES = {
    "titanium_alloy_sword": ["X", "X", "S"],
    "titanium_alloy_pickaxe": ["XXX", " S ", " S "],
}
for i in IDS:
    p = os.path.join(DATA, "recipe", i + ".json")
    if not os.path.isfile(p):
        check(False, "缺配方 recipe/%s.json" % i)
        continue
    r = json.loads(read(p))
    check(r.get("type") == "minecraft:crafting_shaped", "%s 是 crafting_shaped" % i)
    pattern = r.get("pattern", [])
    check(pattern == SHAPES[i], "%s 的形状 = %s（原版那种）" % (i, SHAPES[i]))
    lens = sorted({len(row) for row in pattern})
    check(len(lens) == 1 and lens[0] <= 3,
          "%s 每行字符数一致且 ≤3（读到 %s，§6.13）" % (i, lens))
    key = r.get("key", {})
    check(key.get("X", {}).get("item") == MATERIAL, "%s 的 X = 轻质钛合金（用户：『锭换成轻质钛合金』）" % i)
    check(key.get("S", {}).get("item") == "minecraft:stick", "%s 的 S = 木棍（照原版）" % i)
    letters = {c for row in pattern for c in row if c != " "}
    check(letters <= set(key), "%s 的图案字符都在 key 里（%s vs %s）" % (i, sorted(letters), sorted(key)))
    res = r.get("result", {})
    check(res.get("id") == "potato_s_t:" + i and res.get("count") == 1, "%s 产出 1 个自己" % i)

print()
print("== ④ 语言（四份一致 + 没有 Shift 说明键）==")
langs = {n: json.loads(read(os.path.join(LANG, n + ".json"))) for n in ("zh_cn", "en_us", "ja_jp", "ru_ru")}
base = set(langs["zh_cn"])
for n, d in langs.items():
    check(set(d) == base, "%s.json 键集合与 zh_cn 一致（%d 键）" % (n, len(d)))
for i in IDS:
    key = "item.potato_s_t." + i
    for n, d in langs.items():
        check(key in d and d[key].strip() != "", "%s.json 有 %s = %s" % (n, key, d.get(key)))
banned = [k for k in base if "tooltip.potato_s_t.titanium_alloy" in k]
check(not banned, "没有给工具加 Shift 说明键（%s）" % (banned or "无"))

print()
print("== ⑤ Java 侧：注册 / 创造页 / 数值 / 懒取修理材料 ==")
items = read(os.path.join(JAVA, "ModItems.java"))
for i in IDS:
    check(re.search(r'ITEMS\.register\("%s"' % i, items) is not None, "ModItems 注册了 %s" % i)
    check("output.accept(%s.get());" % i.upper() in items, "创造页里有 %s" % i.upper())
tiers = read(os.path.join(JAVA, "ModTiers.java"))
for frag, why in (("2048", "剑耐久 2048"), ("4219", "镐耐久 4219"),
                  ("2.5F", "剑伤害加成 2.5（⇒ 显示 6.5）"), ("2.0F", "镐伤害加成 2.0（⇒ 显示 4）"),
                  ("25", "附魔权重 25（金 22，比它高一点）"),
                  ("INCORRECT_FOR_NETHERITE_TOOL", "挖掘等级 = 下界合金"), ("9.0F", "挖掘速度 9.0")):
    check(frag in tiers, "ModTiers 里有 %s（%s）" % (frag, why))
check(re.search(r"private static Ingredient repair\(\)\s*\{\s*return Ingredient\.of\(ModItems\.LIGHT_TITANIUM_ALLOY\.get\(\)\);",
                tiers) is not None,
      "修理材料是懒取的（写在方法里）—— 静态字段里直接 .get() 会撞 §4.1")
# 静态字段初始化里不许出现 .get()（那就是"注册表还没填完就取值"）
bad_static = [l.strip() for l in tiers.split("\n")
              if re.match(r"\s*(public|private|protected)?\s*static final .*=.*ModItems\..*\.get\(\)", l)]
check(not bad_static, "ModTiers 的静态字段初始化里没有 ModItems...get()（%s）" % (bad_static or "无"))

print()
print("失败项 = %d" % len(fails))
for m in fails:
    print("   - " + m)
sys.exit(1 if fails else 0)
