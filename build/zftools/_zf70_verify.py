# -*- coding: utf-8 -*-
"""_zf70_verify.py —— ZF70 常驻校验：三条**老**进度（成就）

用户原话（ZF70 当时）：
  1.「新的开始！」条件=获得低级发电机、描述「简洁的电力来源 方便且够用」、图标=低级发电机；
  2.「更强劲的电源」条件=获得发电机**和**动力能源捕获器、前置=新的开始！；
  3.「入门清洁能源」条件=放置一个太阳能板、前置=新的开始！；
  没说的一律**普通成就**（frame=task）。

⚠⚠ **2026-09-25 ZF107 改了口径（本文件已同步）**：用户让"把进度做一点、引导全流程"，
于是 27 条进度成树，其中这三条被这样动过：
  · 根 `new_beginning` 的判据从**低级发电机**前移到**微型粉碎机**（第一台机器），
    图标跟着换成微型粉碎机；**标题没动**（还是「新的开始！」）；
  · 原句「简洁的电力来源 方便且够用」**整句搬给新节点 `first_power`（第一度电）** ——
    本文件 ④ 段有一条断言专门盯"这句话没丢"；
  · `stronger_power` / `clean_energy` 的**判据、图标、文案一个字没改**，
    只把父链从 `new_beginning` 改挂 `first_power`（树形更顺，玩家已得的成就不会掉）。
树级的检查（27 条、父链闭合、隐藏彩蛋、四语言 408 键…）在 `_zf107_verify.py`，本文件只管这三条。

⚠ ZF70 本轮真踩到的坑（探针第一次真触发就挂了 2 条）：
**JSON 的 requirements 是「外层 = AND，内层 = OR」**。用户说的「和」必须写成**两组各一个判据**
（`[["generator"], ["power_capturer"]]`）；写成 `[["generator","power_capturer"]]` 是「或」——
玩家只拿发电机就把成就拿了。这条静态检查就是钉它的。
（ZF107 又踩了它的**孪生兄弟**：`conditions.items` 里的多个谓词是「与」——见档案 §4.74。）

退出码 0 = 全过。
"""
import io
import json
import os
import re
import sys
import zipfile

# ⚠ 0.11 ZF109 补：本文件以前**没有**这段 —— 在 UTF-8 控制台里跑是绿的，
#    被 `_zf109_gatesnap.py` 用**管道**调起来时，`⇒`（U+21D2）按 GBK 编码直接崩
#    （UnicodeEncodeError），退出码 1 却**一行汇总都没打**。这是"假绿"：
#    常驻校验一律自己把 stdout 钉成 UTF-8（§4.50 的同族）。
try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

ROOT = r"E:\PotatoST"
RES = os.path.join(ROOT, r"src\main\resources")
ADV = os.path.join(RES, r"data\potato_s_t\advancement")
LANG = os.path.join(RES, r"assets\potato_s_t\lang")
MODBLOCKS = os.path.join(ROOT, r"src\main\java\com\potatost\mod\ModBlocks.java")
DOCS = os.path.join(ROOT, r"docs\开发档案.md")
BUILD_JAR = os.path.join(ROOT, r"build\libs\potato_s_t-0.11.jar")

# 期望（照"ZF107 之后的真相"硬写，不从 JSON 反推）
SPEC = [
    dict(file="new_beginning", parent=None, icon="potato_s_t:micro_crusher",
         criteria={"got": ("minecraft:inventory_changed", "items", "potato_s_t:micro_crusher")},
         requirements=[["got"]],
         title_zh=u"新的开始！",
         desc_zh=u"做出微型粉碎机 —— 它把矿石磨成粉，是后面一切的地基"),
    dict(file="stronger_power", parent="potato_s_t:first_power", icon="potato_s_t:generator",
         criteria={"generator": ("minecraft:inventory_changed", "items", "potato_s_t:generator"),
                   "power_capturer": ("minecraft:inventory_changed", "items", "potato_s_t:power_capturer")},
         requirements=[["generator"], ["power_capturer"]],       # ← 「和」= 两组 = AND
         title_zh=u"更强劲的电源", desc_zh=u"电生磁 磁生电...... 别问我为什么导线可以传递动力"),
    dict(file="clean_energy", parent="potato_s_t:first_power", icon="potato_s_t:solar_panel",
         criteria={"solar_panel": ("minecraft:placed_block", "block", "potato_s_t:solar_panel")},
         requirements=[["solar_panel"]],
         title_zh=u"入门清洁能源", desc_zh=u"量变产生质变"),
]

# ZF107：老根节点那句文案搬家了，搬家的目的地也一起钉住（"没丢东西"是可验证的）
# ⚠ 只钉**两个半句**、不钉标点：那句话现在盘上是润色过的逗号版（`，`），
#   钉整串会把"别人改了标点"误报成"内容丢了"（§4.30 同族：尺子别比事实更严）。
MOVED = dict(file="first_power", halves=[u"简洁的电力来源", u"方便且够用"])

LANGS = ["zh_cn", "en_us", "ja_jp", "ru_ru"]
fails = []
examined = 0


def check(ok, msg):
    global examined
    examined += 1
    print(("  [OK]   " if ok else "  [FAIL] ") + msg)
    if not ok:
        fails.append(msg)
    return ok


def read(path, mode="r"):
    if mode == "rb":
        with io.open(path, "rb") as fh:
            return fh.read()
    with io.open(path, encoding="utf-8") as fh:
        return fh.read()


blocks = read(MODBLOCKS)
langs = {l: json.loads(read(os.path.join(LANG, l + ".json"))) for l in LANGS}


def id_exists(item_id):
    ns, _, path = item_id.partition(":")
    if ns == "potato_s_t":
        return re.search(r'register\("%s"' % path, blocks) is not None
    return True


# ============================================================
print("== ① 三份 advancement JSON：展示 / 图标 / 前置 ==")
loaded = {}
for s in SPEC:
    p = os.path.join(ADV, s["file"] + ".json")
    if not os.path.isfile(p):
        check(False, u"缺 data/potato_s_t/advancement/%s.json" % s["file"])
        continue
    d = json.loads(read(p))
    loaded[s["file"]] = d
    print(u"  ---- %s.json" % s["file"])

    # 前置（根没有 parent）
    got_parent = d.get("parent")
    if s["parent"] is None:
        check(got_parent is None, u"%s：是根（没有 parent，实际 %s）" % (s["file"], got_parent))
        bg = d.get("display", {}).get("background")
        check(bool(bg), u"%s：根必须有标签页背景图（实际 %s）" % (s["file"], bg))
        if bg:
            rel = bg.split(":", 1)[1] if ":" in bg else bg
            check(os.path.isfile(os.path.join(RES, "assets", "potato_s_t", rel)),
                  u"%s：背景图文件真实存在（%s）" % (s["file"], rel))
    else:
        check(got_parent == s["parent"], u"%s：parent = %s（实际 %s）" % (s["file"], s["parent"], got_parent))

    disp = d.get("display", {})
    check(disp.get("frame") == "task", u"%s：frame = task（普通成就，实际 %s）" % (s["file"], disp.get("frame")))
    check(disp.get("show_toast") is True, u"%s：show_toast = true" % s["file"])
    check(disp.get("announce_to_chat") is True, u"%s：announce_to_chat = true" % s["file"])
    check(disp.get("hidden") is False, u"%s：hidden = false（不在 GUI 里藏起来）" % s["file"])
    icon = disp.get("icon", {})
    check(icon.get("id") == s["icon"] and icon.get("count") == 1,
          u"%s：图标 = %s x1（实际 %s x%s）" % (s["file"], s["icon"], icon.get("id"), icon.get("count")))
    check(id_exists(s["icon"]), u"%s：图标物品真的注册了（%s）" % (s["file"], s["icon"]))
    check(d.get("sends_telemetry_event") is False, u"%s：sends_telemetry_event = false（不给 Mojang 发遥测）" % s["file"])

# ============================================================
print()
print("== ② 判据（trigger + 条件指向的物品/方块）==")
for s in SPEC:
    d = loaded.get(s["file"])
    if not d:
        check(False, u"%s 没加载，跳过判据检查" % s["file"])
        continue
    crit = d.get("criteria", {})
    check(set(crit.keys()) == set(s["criteria"].keys()),
          u"%s：判据名 = %s（实际 %s）" % (s["file"], sorted(s["criteria"]), sorted(crit)))
    for name, (trigger, field, value) in s["criteria"].items():
        c = crit.get(name)
        if not c:
            check(False, u"%s/%s 判据缺失" % (s["file"], name))
            continue
        check(c.get("trigger") == trigger, u"%s/%s：trigger = %s（实际 %s）" % (s["file"], name, trigger, c.get("trigger")))
        got = None
        if field == "items":
            items = c.get("conditions", {}).get("items", [])
            got = items[0].get("items") if items else None
        else:
            loc = c.get("conditions", {}).get("location", [])
            got = loc[0].get("block") if loc else None
            if loc:
                check(loc[0].get("condition") == "minecraft:block_state_property",
                      u"%s/%s：方块判据必须是 block_state_property（实际 %s）" % (s["file"], name, loc[0].get("condition")))
        check(got == value, u"%s/%s：条件指向 %s（实际 %s）" % (s["file"], name, value, got))
        check(id_exists(value), u"%s/%s：那个 id 真的注册了（%s）" % (s["file"], name, value))

# ============================================================
print()
print("== ③ requirements：『和』必须是两组（外层 AND / 内层 OR）==")
for s in SPEC:
    d = loaded.get(s["file"])
    if not d:
        continue
    req = d.get("requirements")
    check(req == s["requirements"],
          u"%s：requirements = %s（实际 %s）" % (s["file"], s["requirements"], req))
    if req and len(s["criteria"]) > 1:
        # 语义不变式：多个判据的成就，每个判据各成一组，才等于"全部都要"
        check(len(req) == len(s["criteria"]) and all(len(g) == 1 for g in req),
              u"%s：%d 个判据 ⇒ requirements 必须是 %d 组、每组 1 个（否则内层 OR 会变成『或』）"
              % (s["file"], len(s["criteria"]), len(s["criteria"])))
    # 反向断言：不许出现"整张表就是一组、组里多个判据"这种 OR 写法
    if req and len(s["criteria"]) > 1:
        check(not any(len(g) > 1 for g in req),
              u"%s：没有任何一组塞了多个判据（那会变成『或』—— 本轮真踩过）" % s["file"])

# ============================================================
print()
print("== ④ 语言：四语言都有标题/描述，且中文逐字等于用户原话 ==")
for s in SPEC:
    kt = "advancements.potato_s_t.%s.title" % s["file"]
    kd = "advancements.potato_s_t.%s.description" % s["file"]
    for l in LANGS:
        check(bool(langs[l].get(kt)), u"%s：%s 在 %s 里有值" % (l, kt, l))
        check(bool(langs[l].get(kd)), u"%s：%s 在 %s 里有值" % (l, kd, l))
    check(langs["zh_cn"].get(kt) == s["title_zh"],
          u"%s：中文标题逐字等于用户原话（%s）" % (s["file"], s["title_zh"]))
    check(langs["zh_cn"].get(kd) == s["desc_zh"],
          u"%s：中文描述逐字等于约定文案（%s）" % (s["file"], s["desc_zh"]))

# --- ZF107 追加：老根节点那句话**搬家没丢** ---
print()
print(u"== ④b ZF107：原「简洁的电力来源 方便且够用」搬到了 first_power（一句没丢）==")
_p = os.path.join(ADV, MOVED["file"] + ".json")
check(os.path.isfile(_p), u"first_power.json 存在")
if os.path.isfile(_p):
    _d = json.loads(read(_p))
    _k = "advancements.potato_s_t.%s.description" % MOVED["file"]
    check(all(h in langs["zh_cn"].get(_k, u"") for h in MOVED["halves"]),
          u"first_power 的中文说明里含「%s」（实际 %s）"
          % (u"」+「".join(MOVED["halves"]), langs["zh_cn"].get(_k)))
    check(_d.get("parent") == "potato_s_t:new_beginning",
          u"first_power 挂在根下面（实际 %s）" % _d.get("parent"))
    check(_d.get("display", {}).get("icon", {}).get("id") == "potato_s_t:low_generator",
          u"first_power 的图标是低级发电机（实际 %s）"
          % _d.get("display", {}).get("icon", {}).get("id"))

# ============================================================
print()
print("== ⑤ 产物 jar ==")
if not os.path.isfile(BUILD_JAR):
    check(False, u"找不到 %s（先跑 build）" % BUILD_JAR)
else:
    with zipfile.ZipFile(BUILD_JAR) as z:
        names = z.namelist()
        for s in SPEC:
            rel = "data/potato_s_t/advancement/%s.json" % s["file"]
            if rel not in names:
                check(False, u"jar 里缺 %s" % rel)
                continue
            check(z.read(rel) == read(os.path.join(ADV, s["file"] + ".json"), "rb"),
                  u"jar 里 %s 与源文件逐字节一致" % rel)
        check(not [n for n in names if "Check" in n], u"jar 里没混进探针类（实际 %s）" % [n for n in names if "Check" in n])
        for l in LANGS:
            check("assets/potato_s_t/lang/%s.json" % l in names, u"jar 里有 %s.json" % l)
    release = os.path.join(ROOT, r"release\PotatoST-0.10.jar")
    if os.path.isfile(release):
        import hashlib
        h = lambda p: hashlib.sha1(read(p, "rb")).hexdigest()
        same = h(release) == h(BUILD_JAR)
        print(u"     [INFO] release 成品与 build 产物%s（%s）"
              % (u"一致" if same else u"**还不一致**（出成品前正常）", h(release)[:12]))

# ============================================================
print()
print("== ⑥ 档案跟上了 ==")
docs = read(DOCS)
check(re.search(r"\|\s*ZF70\s*\|", docs) is not None, u"§5 表里有 ZF70 这一行")
# 口径：档案里必须有一句话同时点明「外层 AND」和「内层 OR」
# （⚠ 第一版这条写成了查死串 "外层 = AND"，而档案里写的是「外层 AND / 内层 OR」——
#   检查过严等于把措辞当成事实，改成按语义查：同一行里 外层/内层/AND/OR 四个词都在）
semantic_lines = [ln for ln in docs.split("\n")
                  if u"外层" in ln and u"内层" in ln and "AND" in ln and "OR" in ln]
check(bool(semantic_lines),
      u"档案里记了 requirements 的 AND/OR 语义（§4.42，命中 %d 行）" % len(semantic_lines))

print()
print(u"检查项 = %d" % examined)
print(u"失败项 = %d" % len(fails))
for m in fails:
    print(u"   - " + m)
sys.exit(1 if fails else 0)
