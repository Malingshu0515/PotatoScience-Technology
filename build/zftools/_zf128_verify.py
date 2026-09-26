# -*- coding: utf-8 -*-
u"""_zf128_verify.py —— ZF128「成就页签图标 = 毒马铃薯」常驻校验（静态，不跑服务器）

用户原话：「成就栏换成毒马铃薯 但是成就还是粉碎机可以嘛」

五段：
  A 数据：`new_beginning.json` 的 `display.icon.id` = `minecraft:poisonous_potato`，
    而**判据**仍是 `potato_s_t:micro_crusher`、标题/描述/背景/frame/hidden/toast 一个都没动；
  B 往轮门与生成器跟平（`_zf70_verify` / `_zf107_verify` / `_zf124_verify` / `_zf107_adv`）——
    ⚠ 生成器那条最重要：不拆常量的话，谁重跑一次就会把图标写回粉碎机；
  C 树本体没被顺手改坏：35 份成就、1 个根、只有根用毒马铃薯、别的图标仍是本模组物品；
  D 连带面：公告 / 档案 §4·§5·§9 / 交接 §6；**待画贴图清单不许变**（毒马铃薯是原版物品、不是我们的模型）；
  E 反向：我们**没有**注册 `poisonous_potato` 这个物品；探针报告在盘上且全绿；`PotatoST.java` 干净且 == 改前件。

⚠ 本脚本**只读**，不改任何文件；退出码 0 = 全绿。
跑法：
    python build\\zftools\\_zf128_verify.py
"""
import glob
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
JAVA = os.path.join(ROOT, r"src\main\java\com\potatost\mod")
ADV = os.path.join(ROOT, r"src\main\resources\data\potato_s_t\advancement")
LANG = os.path.join(ROOT, r"src\main\resources\assets\potato_s_t\lang")
TOOLS = os.path.join(ROOT, r"build\zftools")
DOCS = os.path.join(ROOT, "docs")
BK = r"C:\PotatoST救援\zf128_pre"

ROOT_JSON = os.path.join(ADV, u"new_beginning.json")
POTATO = u"minecraft:poisonous_potato"
CRUSHER = u"potato_s_t:micro_crusher"

passed = 0
failed = 0
fails = []


def check(name, ok):
    global passed, failed
    if ok:
        passed += 1
        print(u"  [OK]   %s" % name)
    else:
        failed += 1
        fails.append(name)
        print(u"  [FAIL] %s" % name)
    return ok


def read(p):
    return io.open(p, encoding=u"utf-8", newline=u"").read()


def pre(rel):
    return read(os.path.join(BK, *rel.split(u"/")))


def jload(p):
    return json.loads(read(p))


# ============================================================
def part_a():
    print(u"\n===== A 数据（根成就 JSON）=====")
    raw = read(ROOT_JSON)
    adv = jload(ROOT_JSON)
    d = adv.get(u"display", {})
    check(u"A1 display.icon.id = minecraft:poisonous_potato（页签与根节点画的就是它）",
          d.get(u"icon", {}).get(u"id") == POTATO)
    check(u"A2 图标不再是微型粉碎机", d.get(u"icon", {}).get(u"id") != CRUSHER)
    check(u"A3 **判据仍是** potato_s_t:micro_crusher（「成就还是粉碎机」那一半）",
          adv["criteria"]["got"]["conditions"]["items"][0]["items"] == CRUSHER)
    check(u"A4 触发器仍是 minecraft:inventory_changed",
          adv["criteria"]["got"]["trigger"] == u"minecraft:inventory_changed")
    check(u"A5 title / description 仍是 translate 键，且键名没变",
          d.get(u"title", {}).get(u"translate") == u"advancements.potato_s_t.new_beginning.title"
          and d.get(u"description", {}).get(u"translate")
          == u"advancements.potato_s_t.new_beginning.description")
    before = json.loads(pre(u"src/main/resources/data/potato_s_t/advancement/new_beginning.json"))
    bd = before[u"display"]
    check(u"A6 background / frame / hidden / show_toast / announce 一个都没动",
          (d.get(u"background"), d.get(u"frame"), d.get(u"hidden"), d.get(u"show_toast"),
           d.get(u"announce_to_chat")) ==
          (bd.get(u"background"), bd.get(u"frame"), bd.get(u"hidden"), bd.get(u"show_toast"),
           bd.get(u"announce_to_chat")))
    check(u"A7 requirements / sends_telemetry_event 没动",
          adv.get(u"requirements") == before.get(u"requirements")
          and adv.get(u"sends_telemetry_event") == before.get(u"sends_telemetry_event"))
    check(u"A8 与改前件逐字段比：**除 display.icon.id 外完全相同**",
          {k: v for k, v in adv.items() if k != u"display"} ==
          {k: v for k, v in before.items() if k != u"display"}
          and {k: v for k, v in d.items() if k != u"icon"} ==
          {k: v for k, v in bd.items() if k != u"icon"}
          and before[u"display"][u"icon"] == {u"count": 1, u"id": CRUSHER})
    check(u"A9 文件是 LF 且没有 BOM", b"\r\n" not in open(ROOT_JSON, "rb").read()
          and not open(ROOT_JSON, "rb").read().startswith(b"\xef\xbb\xbf"))
    check(u"A10 图标那两行之外，文件大小只差固定的一点（一行替换）",
          len(raw) - len(pre(u"src/main/resources/data/potato_s_t/advancement/new_beginning.json"))
          == len(POTATO) - len(CRUSHER))


def part_b():
    print(u"\n===== B 往轮门与生成器跟平 =====")
    z70 = read(os.path.join(TOOLS, u"_zf70_verify.py"))
    z107 = read(os.path.join(TOOLS, u"_zf107_verify.py"))
    z124 = read(os.path.join(TOOLS, u"_zf124_verify.py"))
    adv = read(os.path.join(TOOLS, u"_zf107_adv.py"))
    check(u"B1 `_zf70_verify.py`：SPEC 里根成就的 icon 跟到毒马铃薯，判据那行仍是粉碎机",
          u'icon="minecraft:poisonous_potato",' in z70
          and u'"items", "potato_s_t:micro_crusher"' in z70)
    check(u"B2 `_zf107_verify.py`：D3 跟到毒马铃薯，D2 仍是粉碎机",
          u'"minecraft:poisonous_potato"' in z107 and u'"potato_s_t:micro_crusher"' in z107
          and u'"D3 \u6839\u8282\u70b9\u7684\u56fe\u6807\uff08ZF128 \u8d77\u662f\u6bd2\u9a6c\u94c3\u85af\uff09"'
          in z107)
    check(u"B3 `_zf124_verify.py`：根成就图标那条目标值跟到毒马铃薯",
          u'== u"minecraft:poisonous_potato")' in z124)
    check(u"B4 `_zf107_adv.py`：判据与图标拆成两个常量",
          u'ROOT_ICON_CRITERION = "potato_s_t:micro_crusher"' in adv
          and u'ROOT_ICON_DISPLAY = "minecraft:poisonous_potato"' in adv)
    check(u"B5 `_zf107_adv.py`：写盘时用那两个常量（**重跑不会把图标写回粉碎机**）",
          u'obj["display"]["icon"] = {"count": 1, "id": ROOT_ICON_DISPLAY}' in adv
          and u'"items": [{"items": ROOT_ICON_CRITERION}]' in adv
          and u'"potato_s_t:" + ROOT_ICON' not in adv)
    ok_syntax = True
    for fn in (u"_zf70_verify.py", u"_zf107_verify.py", u"_zf124_verify.py", u"_zf107_adv.py"):
        try:
            compile(read(os.path.join(TOOLS, fn)), fn, u"exec")
        except SyntaxError:
            ok_syntax = False
    check(u"B6 这四份改完都还能编译", ok_syntax)


def part_c():
    print(u"\n===== C 树本体没被顺手改坏 =====")
    files = sorted(glob.glob(os.path.join(ADV, u"*.json")))
    check(u"C1 成就文件仍是 35 份（实际 %d）" % len(files), len(files) == 35)
    roots = []
    potatoes = []
    others = []
    for p in files:
        a = jload(p)
        name = os.path.basename(p)[:-5]
        if u"parent" not in a:
            roots.append(name)
        icon = a.get(u"display", {}).get(u"icon", {}).get(u"id", u"")
        if icon == POTATO:
            potatoes.append(name)
        if name != u"new_beginning" and not icon.startswith(u"potato_s_t:"):
            others.append(name + u"=" + icon)
    check(u"C2 恰好 1 个根、还是 new_beginning（实际 %s）" % roots, roots == [u"new_beginning"])
    check(u"C3 只有根那条用毒马铃薯（实际 %s）" % potatoes, potatoes == [u"new_beginning"])
    check(u"C4 别的成就的图标仍全是本模组物品（%s）" % others, not others)
    check(u"C5 语言文件里那两个键还在（标题/描述没被删）",
          all(u"advancements.potato_s_t.new_beginning.title" in jload(
              os.path.join(LANG, loc + u".json")) for loc in
              (u"zh_cn", u"en_us", u"ja_jp", u"ru_ru")))


def part_d():
    print(u"\n===== D 连带面 =====")
    ann = read(os.path.join(DOCS, u"UpdateAnnouncement_EN.md"))
    arc = read(os.path.join(DOCS, u"开发档案.md"))
    hand = read(os.path.join(DOCS, u"多会话协作交接.md"))
    listing = read(os.path.join(DOCS, u"贴图清单.md"))
    check(u"D1 英文公告里写了这次换图标（ZF128 + poisonous potato）",
          u"ZF128" in ann and u"poisonous potato" in ann)
    check(u"D2 档案 §5 有 ZF128 那一行", u"| ZF128 |" in arc)
    check(u"D3 档案 §9 有 ZF128 小节", u"### ZF128（0.11）" in arc)
    check(u"D4 档案 §4 记了这条事实（§4.110：页签图标 = 根节点图标）", u"### 4.110" in arc)
    check(u"D5 交接文档 §6 有第 20 条（ZF128）", u"20. **ZF128 的账" in hand)
    # ⚠ 数改成**问 TextureCheck 现数**：素材线每画一张它就动一次（本轮期间银线那两张刚到）
    import subprocess as _sp
    _r = _sp.run([sys.executable, os.path.join(TOOLS, u"TextureCheck.py")],
                 stdout=_sp.PIPE, stderr=_sp.STDOUT, cwd=TOOLS,
                 env=dict(os.environ, PYTHONIOENCODING=u"utf-8"))
    _m = re.search(r"待画\s*=\s*(\d+)", _r.stdout.decode(u"utf-8", u"replace"))
    _n = int(_m.group(1)) if _m else -1
    check(u"D6 待画贴图清单的表头 == TextureCheck 现数（%d 个）—— 本轮的改动不碰贴图" % _n,
          _n > 0 and (u"## 待画（%d 个" % _n) in listing)
    _potato_tex = os.path.join(ROOT, u"src", u"main", u"resources", u"assets", u"potato_s_t",
                               u"textures", u"item", u"poisonous_potato.png")
    check(u"D6b 我们**没有**为毒马铃薯画贴图（用的是原版物品）", not os.path.exists(_potato_tex))
    check(u"D7 语言键数仍是 478 ×4（本轮不加键）",
          all(len(jload(os.path.join(LANG, loc + u".json"))) == 478 for loc in
              (u"zh_cn", u"en_us", u"ja_jp", u"ru_ru")))


def part_e():
    print(u"\n===== E 反向 =====")
    src = u""
    for fn in (u"ModItems.java", u"ModBlocks.java"):
        src += read(os.path.join(JAVA, fn))
    check(u"E1 我们**没有**注册 poisonous_potato 这个物品（用的是原版的）",
          u'"poisonous_potato"' not in src)
    hook = read(os.path.join(JAVA, u"PotatoST.java"))
    check(u"E2 PotatoST.java 里没有探针残留", u"Zf128Check" not in hook)
    check(u"E3 PotatoST.java == 改前件（逐字节）",
          hook == pre(u"src/main/java/com/potatost/mod/PotatoST.java"))
    probe = os.path.join(TOOLS, u"_zf128_probe_utf8.txt")
    if os.path.exists(probe):
        text = read(probe)
        import re
        m = re.search(r"通过 (\d+)", text)
        check(u"E4 探针报告在盘上且**全绿**（%s 项）" % (m.group(1) if m else u"?"),
              u"全绿" in text and m is not None and int(m.group(1)) >= 15)
    else:
        check(u"E4 探针报告在盘上", False)
    check(u"E5 探针源文件已存档到 check/（先抄再删）",
          os.path.exists(os.path.join(TOOLS, u"check", u"Zf128Check.java")))
    check(u"E6 探针源文件不在 src 里", not os.path.exists(os.path.join(JAVA, u"Zf128Check.java")))


def main():
    part_a()
    part_b()
    part_c()
    part_d()
    part_e()
    print(u"\n------------------------------")
    print(u"通过 = %d   失败 = %d" % (passed, failed))
    for f in fails:
        print(u"  !! " + f)
    return 1 if failed else 0


if __name__ == u"__main__":
    sys.exit(main())
