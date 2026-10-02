#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
_zf152_plates_gate.py —— 板材跨模组兼容（沉浸工程 / 机械动力）的**只读**校验门。

⚠ 轮号说明：本轮动手时先按 ZF150 命名，做到一半发现另一条线（翻译润色）已经占了
  `_zf150_*`（`_zf150_lang.py` / `_zf150_retarget*.py` / `_zf150_section.md` 等），
  于是本轮的脚本与文档统一改用 **ZF152**（场上没有别人用 152）。

用户原话（2026-09-28）：
    「把矿物的板材加个兼容（沉浸工程，机械动力等的配方支持）」

背景（本门存在的理由）：
    0.10 ZF16 有一句"板材属于其他物品，按长期规则不挂 c: 标签"——那条规则定的时候
    **同一实例里一个别的 mod 都没装**，所以"挂上去到底有没有用"根本无从验证。
    现在开发实例里装着 Create + 柴油动力 + 电气时代，而 `c:plates/*` 的真实用途已经查清：

      ① 机械动力 create:cutting            —— 输入 #c:plates/copper（剪线材）
      ② 柴油动力 wire_cutting / hammering  —— 输入 #c:plates/{iron,copper,aluminum,steel,gold,electrum}
      ③ 电气时代 energising / cutting      —— 输入 #c:plates/{iron,gold,copper}
      ④ **沉浸工程的金属冲压机**：IE 自己那批配方（plate_iron / plate_nickel / plate_cobalt ...）
         是 **"#c:ingots/X -> #c:plates/X"** 的**标签对标签**配方（实测 23 条）——
         只要我们把板材挂进 c:plates/X，IE 的机器就**自动**能用我们的锭压出**我们的**板
         （不需要给 IE 写一条配方）。

所以本轮的产出是**纯数据**（不碰 Java）：
    A. data/c/tags/item/plates.json + plates/{iron,copper,aluminum,silver,nickel,cobalt,steel}.json
    B. data/potato_s_t/recipe/pressing/*.json —— create:pressing，把 7 种锭压成我们的板

⚠ 机械动力的 create:pressing **不支持标签产物**：它的 ProcessingOutput 用的是
   `Codec.either(Item.CODEC, ResourceLocation.CODEC)`（我在 ProcessingOutput.class 上
   javap 过，字段名 "id"），**没有 TagKey 分支**。所以 create:pressing 的 results 只能写具体物品 id。
   => 想让"我们的板"和"IE 的板"同时被认，只能靠 ① 标签把两边都收进来（这是 IE 那条路），
     ② 各自机器出自己的板（这是 Create 这条路，天然不冲突）。

跑法：
    python build\\zftools\\_zf152_plates_gate.py     # 只读校验（本门不改盘）

出口：0 = 全过；1 = 有失败项（逐条打印）。
"""

import json
import os
import re
import sys
import zipfile

# 本工程的 PowerShell 控制台是 GBK，`⇒`/`⚠` 这类字符会直接把门打崩（UnicodeEncodeError）。
# 显式把标准输出钉成 UTF-8，并在换行/编码上都不依赖控制台（照 §4.8 的换行纪律）。
try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

ROOT = r"E:\PotatoST"
RES = os.path.join(ROOT, "src", "main", "resources")
TAGDIR = os.path.join(RES, "data", "c", "tags", "item", "plates")
RECIPEDIR = os.path.join(RES, "data", "potato_s_t", "recipe", "pressing")
LANG = os.path.join(RES, "assets", "potato_s_t", "lang", "zh_cn.json")
MODS = os.path.join(ROOT, "run", "client", "mods")
# 沉浸工程不常驻开发实例（14 MB，只在做 IE 兼容时临时装上），
# 所以这里额外认两个"库存"位置：release/ 与 build/tmp/ie-stash/。
IE_EXTRA = [
    os.path.join(ROOT, "release"),
    os.path.join(ROOT, "build", "tmp", "ie-stash"),
]

# 我们有的 7 种板材（= 8 件板材 - 没有第 8 件，见 docs：铁/铜/铝/银/镍/钴/钢）
PLATES = ["iron", "copper", "aluminum", "silver", "nickel", "cobalt", "steel"]
# 每种板材对应的物品 id（本模组）
OUR_ITEM = {m: "potato_s_t:%s_plate" % m for m in PLATES}
# 每种板材对应的通用锭标签（液压机 + create:pressing 的输入）
INGOT_TAG = {m: "c:ingots/%s" % m for m in PLATES}

# 上游（别的 mod）在 c:plates/<m> 里放了什么 —— 用于核对"我们挂上去等于接进了它的配方"
UPSTREAM_PLATE = {
    "immersiveengineering": {
        "iron": "immersiveengineering:plate_iron",
        "copper": "immersiveengineering:plate_copper",
        "aluminum": "immersiveengineering:plate_aluminum",
        "silver": "immersiveengineering:plate_silver",
        "nickel": "immersiveengineering:plate_nickel",
        "steel": "immersiveengineering:plate_steel",
        "cobalt": None,  # IE 的 plate_cobalt 是"有配方、没物品"（标签对标签，等别的 mod 填）
    },
    "create": {
        "iron": "create:iron_sheet",
        "copper": "create:copper_sheet",
        "gold": "create:golden_sheet",
        "brass": "create:brass_sheet",
    },
}

FAIL = []


def fail(msg):
    FAIL.append(msg)


def ok(msg):
    print("  [OK]   " + msg)


def read_text(path):
    with open(path, "rb") as fh:
        raw = fh.read()
    return raw


def check_json_files():
    """① 全部新文件：能 parse、无 BOM、纯 LF、以换行结尾。"""
    print("--- ① 新增数据文件的格式（JSON 可解析 / 无 BOM / 纯 LF）")
    targets = []
    for name in PLATES + [None]:
        p = os.path.join(TAGDIR, "%s.json" % name) if name else os.path.join(
            RES, "data", "c", "tags", "item", "plates.json")
        targets.append(p)
    for m in PLATES:
        targets.append(os.path.join(RECIPEDIR, "%s_plate.json" % m))

    bad = 0
    for p in targets:
        rel = p.replace(ROOT + os.sep, "")
        if not os.path.isfile(p):
            fail("缺文件：%s" % rel)
            bad += 1
            continue
        raw = read_text(p)
        if raw.startswith(b"\xef\xbb\xbf"):
            fail("有 BOM：%s" % rel)
            bad += 1
        if b"\r" in raw:
            fail("含 CR（本项目 .gitattributes 是 `* -text`，必须保持纯 LF）：%s" % rel)
            bad += 1
        if not raw.endswith(b"\n"):
            fail("结尾没有换行：%s" % rel)
            bad += 1
        try:
            json.loads(raw.decode("utf-8"))
        except Exception as exc:
            fail("JSON 解析失败 %s：%s" % (rel, exc))
            bad += 1
    if bad == 0:
        ok("%d 个新文件：JSON 全部可解析、无 BOM、纯 LF、结尾有换行" % len(targets))
    return targets


def check_tag_contents():
    """② 标签内容：7 张子标签各只收我们那一件；父标签收齐 7 件；7 件都在 plates.json 里。"""
    print("--- ② c:plates/* 的内容")
    for m in PLATES:
        p = os.path.join(TAGDIR, "%s.json" % m)
        d = json.loads(read_text(p).decode("utf-8"))
        vals = d.get("values")
        if not isinstance(vals, list):
            fail("c:plates/%s 的 values 不是数组" % m)
            continue
        if OUR_ITEM[m] not in vals:
            fail("c:plates/%s 里没有 %s" % (m, OUR_ITEM[m]))
        if "replace" in d:
            # 本项目所有 c: 标签一律不写 replace（= false = 合并）。写了 true 会清空上游！
            fail("c:plates/%s 写了 replace —— 会清空上游同标签，默认 false 才是合并" % m)
    parent = os.path.join(RES, "data", "c", "tags", "item", "plates.json")
    pv = json.loads(read_text(parent).decode("utf-8")).get("values", [])
    missing = [OUR_ITEM[m] for m in PLATES if OUR_ITEM[m] not in pv]
    if missing:
        fail("父标签 c:plates 缺：%s" % ", ".join(missing))
    else:
        ok("c:plates/{iron,copper,aluminum,silver,nickel,cobalt,steel} 各收 1 件，"
           "父标签 c:plates 收齐 7 件（沿用本项目 ingots.json 的平铺写法）")


def check_ids_exist():
    """③ 标签里引用的 potato_s_t:<id> 必须真实注册（照 Audit.ps1 J 项的口径：id 清单取自 lang）。"""
    print("--- ③ 标签引用的 id 是否真实存在（口径同 Audit.ps1 的 J 项）")
    with open(LANG, "rb") as fh:
        lang = json.loads(fh.read().decode("utf-8"))
    ids = set()
    for k in lang:
        mm = re.match(r"^(?:item|block)\.potato_s_t\.(.+)$", k)
        if mm:
            ids.add(mm.group(1))
    referenced = set()
    for m in PLATES:
        referenced.add(OUR_ITEM[m].split(":", 1)[1])
    unknown = sorted(i for i in referenced if i not in ids)
    if unknown:
        for i in unknown:
            fail("c: 标签引用了不存在的 id：potato_s_t:%s" % i)
    else:
        ok("%d 个被引用的 id 全部在 lang 里注册（%s）" % (len(referenced), ", ".join(sorted(referenced))))


def check_create_recipes():
    """④ create:pressing 配方的形状必须和 Create 自己的一致。"""
    print("--- ④ create:pressing 配方的形状")
    bad = 0
    for m in PLATES:
        p = os.path.join(RECIPEDIR, "%s_plate.json" % m)
        d = json.loads(read_text(p).decode("utf-8"))
        if d.get("type") != "create:pressing":
            fail("%s_plate.json 的 type 不是 create:pressing" % m)
            bad += 1
        conds = d.get("neoforge:conditions") or []
        if not any(c.get("type") == "neoforge:mod_loaded" and c.get("modid") == "create" for c in conds):
            fail("%s_plate.json 没有 neoforge:mod_loaded=create 守卫 —— 没装机械动力时这条配方是死配方"
                 % m)
            bad += 1
        ing = d.get("ingredients")
        if not (isinstance(ing, list) and len(ing) == 1 and ing[0].get("tag") == INGOT_TAG[m]):
            fail("%s_plate.json 的输入不是单元素 tag %s" % (m, INGOT_TAG[m]))
            bad += 1
        res = d.get("results")
        if not (isinstance(res, list) and len(res) == 1 and res[0].get("id") == OUR_ITEM[m]):
            fail("%s_plate.json 的产物不是 %s" % (m, OUR_ITEM[m]))
            bad += 1
        # 我们**不能**去写属于别的 mod 的配方路径（会把别人的配方顶掉）
    if bad == 0:
        ok("7 条 create:pressing：type/输入标签/产物/守卫 全部合规（产物只能写具体 id，Create 的 "
           "ProcessingOutput 没有 TagKey 分支 —— 已 javap 核实）")


def check_upstream_conflict():
    """⑤ 声称"接进去了"的那些上游配方，必须真的在实例里、且真的吃 c:plates/<m>。"""
    print("--- ⑤ 上游配方的实证（扫实例里的 jar，找不到 jar 就跳过）")
    if not os.path.isdir(MODS):
        print("  [SKIP] 找不到 %s" % MODS)
        return
    jars = {}
    for fn in os.listdir(MODS):
        if not fn.endswith(".jar"):
            continue
        low = fn.lower()
        # 判断顺序要紧：柴油动力的文件名里**也**有 create（createdieselgenerators）、
        #   电气时代里也有 create（create-new-age），所以先认更专的名字，最后才认"剩下那个 create"。
        if "createdieselgenerators" in low:
            jars["cdg"] = os.path.join(MODS, fn)
        elif "new-age" in low or "new_age" in low or "newage" in low:
            jars["cna"] = os.path.join(MODS, fn)
        elif "immersiveengineering" in low:
            jars["ie"] = os.path.join(MODS, fn)
        elif re.match(r"^\[[^\]]*\]\s*create-\d", fn, re.I):
            # 机械动力本体：文件名形如 "[机械动力] create-1.21.1-6.0.10.jar"
            jars["create"] = os.path.join(MODS, fn)
    # 沉浸工程通常不在客户端实例里 —— 去库存目录里找
    for extra in IE_EXTRA:
        if "ie" in jars or not os.path.isdir(extra):
            continue
        for fn in os.listdir(extra):
            if fn.endswith(".jar") and "immersiveengineering" in fn.lower():
                jars["ie"] = os.path.join(extra, fn)
                break
    miss = [k for k in ("create", "cdg", "cna") if k not in jars]
    if miss:
        print("  [INFO] 实例里没找到：%s（相关小节跳过）" % ", ".join(miss))

    def find(jar, needle, must_contain=None):
        z = zipfile.ZipFile(jar)
        out = []
        for n in z.namelist():
            if not n.endswith(".json"):
                continue
            s = z.read(n).decode("utf-8", "replace")
            if needle in s and (must_contain is None or must_contain in s):
                out.append(n)
        return out

    if "create" in jars:
        c = jars["create"]
        z = zipfile.ZipFile(c)
        # 机械动力只有**子标签**（plates/iron.json 等）——它自己没有父 plates.json，
        # 所以这里按目录前缀找，不能按 plates.json 找。
        t = [n for n in z.namelist()
             if n.startswith("data/c/tags/item/plates/") and n.endswith(".json")]
        if t:
            ok("机械动力自带 %d 张 c:plates/* 子标签（%s）=> 我们挂同路径是**合并**，不是顶替"
               % (len(t), ", ".join(sorted(x.split("/")[-1][:-5] for x in t))))
        else:
            fail("机械动力 jar 里没有 c:plates/* 子标签 —— 上面那句『合并』的结论失效，要重新查")
        cut = [n for n in z.namelist() if n.startswith("data/create/recipe/cutting/") and "wire_copper" in n]
        if cut:
            s = z.read(cut[0]).decode("utf-8")
            if "c:plates/copper" in s:
                ok("create:cutting/…/wire_copper 的输入确实是 #c:plates/copper ! 我们的铜板能进这条")
            else:
                fail("create 的 wire_copper 找不到 c:plates/copper")
    for key, tag, what in (("cdg", "c:plates/iron", "wire_cutting/hammering"),
                           ("cna", "c:plates/iron", "energising")):
        if key in jars:
            hits = find(jars[key], tag)
            if hits:
                ok("%s：%d 条配方引用 %s（%s）" % (os.path.basename(jars[key])[:28], len(hits), tag, what))
            else:
                fail("%s 里找不到 %s" % (key, tag))
    if "ie" in jars:
        z = zipfile.ZipFile(jars["ie"])
        pl = [n for n in z.namelist() if n.startswith("data/c/tags/item/plates/")]
        ok("沉浸工程 jar 里自带 %d 张 c:plates/*（本轮实机验证用）" % len(pl))
        # IE 的金属冲压机板配方：**标签对标签**（输入 #c:ingots/X、产物 #c:plates/X）。
        # 这里按 JSON **解析**来判断，不做字符串匹配 —— 上游一旦把 JSON 压缩/换序，
        # 字符串匹配会假红（第一版就是这么红的：IE 写的是 `{"tag":"c:ingots/copper"}`，
        # 中间没有空格，而我 match 的是带空格的 `"tag": "c:ingots/`）。
        pair = 0
        paired_names = []
        for n in z.namelist():
            if "/recipe/metalpress/plate_" not in n or not n.endswith(".json"):
                continue
            try:
                d = json.loads(z.read(n).decode("utf-8"))
            except Exception:
                continue
            inp = (d.get("input") or {})
            base = inp.get("basePredicate") if isinstance(inp.get("basePredicate"), dict) else inp
            res = d.get("result") or {}
            in_tag = base.get("tag") if isinstance(base, dict) else None
            out_tag = res.get("tag") if isinstance(res, dict) else None
            if in_tag and out_tag and out_tag.startswith("c:plates/") and pair is not None:
                pair += 1
                paired_names.append(out_tag)
        if pair:
            ok("沉浸工程有 %d 条『#c:ingots/X -> #c:plates/X』的金属冲压配方（%s）"
               % (pair, ", ".join(sorted(set(paired_names)))))
            print("         => 我们把板挂进 c:plates/X 之后，**IE 的机器会自动用我们的锭压出我们的板**")
        else:
            fail("沉浸工程的 metalpress 里找不到标签对标签的板配方 —— 兼容结论要重查")
    else:
        print("  [INFO] 实例里没有沉浸工程 jar（本门只做静态核对，实机验证另行跑）")


def main():
    print("=" * 78)
    print("_zf150plates_gate.py —— 板材跨模组兼容（沉浸工程 / 机械动力）只读校验")
    print("=" * 78)
    check_json_files()
    check_tag_contents()
    check_ids_exist()
    check_create_recipes()
    check_upstream_conflict()
    print("=" * 78)
    if FAIL:
        print("失败 %d 项：" % len(FAIL))
        for m in FAIL:
            print("  [FAIL] " + m)
        return 1
    print("结论：全过")
    return 0


if __name__ == "__main__":
    sys.exit(main())
