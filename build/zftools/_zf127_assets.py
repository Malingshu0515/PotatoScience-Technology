# -*- coding: utf-8 -*-
u"""_zf127_assets.py —— ZF127 的模型与配方（**配方只改生成器表再 `--write`**，§4.93）

用户原话：「配方什么的都一致只不过铜的换成银的」「材质先不画」。

  ① 两个物品模型：`silver_wire` / `silver_wire_spool`
     —— 贴图**先不画** ⇒ layer0 借原版（铁粒 / 铁锭，都是银白色金属，一眼能看出是占位）；
  ② 两条配方进生成器表 `_zf45_recipes.py` 的 `RECIPES`（与铜线那两条逐字对应，只换材料）：
       `silver_wire`       ：`["SS"]`（S = `#c:ingots/silver`）⇒ 4 根
       `silver_wire_spool` ：`["WWW","WSW","WWW"]`（W = 银线、S = 空线轴）⇒ 1 个
  ③ `--write` 之前先把**整个配方目录**的 sha1 抄下来，写完逐份对 ⇒
     除了新增这两份，**别的配方一个字节都不许动**（别的线也在同一棵树上改配方）。

⚠ ⚠ 不动 `copper_wire_spool.json`：它虽然也是"线轴"，但它**不在生成器表里**（当年手写的），
  把它补进表会被 `--write` 重排键序 ⇒ 动到与本轮无关的文件、还会打到别条线"配方逐字节未变"的门。
  这条缺口如实记进 §9。

跑法：
    python build\\zftools\\_zf127_assets.py
"""
import hashlib
import io
import json
import os
import subprocess
import sys

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

ROOT = r"E:\PotatoST"
TOOLS = os.path.join(ROOT, "build", "zftools")
TABLE = os.path.join(TOOLS, "_zf45_recipes.py")
ASSETS = os.path.join(ROOT, "src", "main", "resources", "assets", "potato_s_t")
RECIPE_DIR = os.path.join(ROOT, "src", "main", "resources", "data", "potato_s_t", "recipe")

MODELS = {
    "silver_wire": u'''{
  "parent": "minecraft:item/generated",
  "textures": {
    "layer0": "minecraft:item/iron_nugget"
  }
}
''',
    "silver_wire_spool": u'''{
  "parent": "minecraft:item/generated",
  "textures": {
    "layer0": "minecraft:item/iron_ingot"
  }
}
''',
}

TABLE_ANCHOR = u'''    # 【铜锭】【铜锭】 → 4 个铜线
    dict(name="copper_wire", category="redstone", result=("potato_s_t:copper_wire", 4),
         pattern=["CC"],
         key={"C": ("tag", "c:ingots/copper")}),
'''

TABLE_ADD = TABLE_ANCHOR + u'''
    # ===== ZF127 追加（银线 / 银线轴：与铜线那两条**逐字对应**，只把铜换成银）=====
    # 「加一个银线轴 和铜线轴一致（先搞银线 配方什么的都一致只不过铜的换成银的）」
    # 【银锭】【银锭】 → 4 根银线（铜线走 c:ingots/copper，银线同一条规矩走 c:ingots/silver）
    dict(name="silver_wire", category="redstone", result=("potato_s_t:silver_wire", 4),
         pattern=["SS"],
         key={"S": ("tag", "c:ingots/silver")}),

    # 【银线】×3 / 【银线】【空线轴】【银线】 / 【银线】×3 → 1 个银线轴（＝铜线轴那张图纸）
    dict(name="silver_wire_spool", category="misc", result=("potato_s_t:silver_wire_spool", 1),
         pattern=["WWW", "WSW", "WWW"],
         key={"W": ("item", "potato_s_t:silver_wire"),
              "S": ("item", "potato_s_t:empty_spool")}),
'''

notes, fails = [], []


def sha1(p):
    return hashlib.sha1(open(p, "rb").read()).hexdigest()


def snapshot():
    out = {}
    for n in sorted(os.listdir(RECIPE_DIR)):
        if n.endswith(".json"):
            out[n] = sha1(os.path.join(RECIPE_DIR, n))
    return out


def write_models():
    d = os.path.join(ASSETS, "models", "item")
    for name, text in MODELS.items():
        p = os.path.join(d, name + u".json")
        if os.path.exists(p):
            fails.append(u"模型已经存在（本轮应当是新文件）：%s" % name)
            continue
        io.open(p, "w", encoding="utf-8", newline=u"\n").write(text)
        back = json.loads(io.open(p, encoding="utf-8").read())
        if back.get("textures", {}).get("layer0", u"").startswith(u"minecraft:"):
            notes.append(u"模型 %s.json（layer0 = %s，占位）" % (name, back["textures"]["layer0"]))
        else:
            fails.append(u"模型 %s.json 的 layer0 不是借来的原版贴图" % name)


def write_table():
    text = io.open(TABLE, encoding="utf-8", newline=u"").read()
    nl = u"\r\n" if u"\r\n" in text else u"\n"
    if u'silver_wire_spool' in text:
        notes.append(u"生成器表里已经有银线那两条（幂等跳过）")
        return
    o = TABLE_ANCHOR.replace(u"\n", nl)
    n = TABLE_ADD.replace(u"\n", nl)
    if text.count(o) != 1:
        fails.append(u"生成器表锚点命中 %d 次（要 1 次）—— 停手" % text.count(o))
        return
    io.open(TABLE, "w", encoding="utf-8", newline=u"").write(text.replace(o, n, 1))
    notes.append(u"生成器表 RECIPES +2 条（silver_wire / silver_wire_spool）")


def run_table(write):
    # ⚠ 生成器只认 `--write`：不带参数 = 只校验不写盘（它的 docstring 里写的 `--check`
    #   其实 argparse 没定义，传了会被当成未知参数直接退出码 2 —— 我第一版就是这么踩的）
    args = [sys.executable, TABLE] + ([u"--write"] if write else [])
    r = subprocess.run(args, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, cwd=TOOLS)
    out = r.stdout.decode("utf-8", "replace")
    tail = [l for l in out.split(u"\n") if u"定形配方" in l or u"失败项" in l or u"FAIL" in l]
    return r.returncode, tail


def main():
    before = snapshot()
    write_models()
    write_table()

    rc, tail = run_table(write=False)
    for l in tail:
        notes.append(u"[--check] " + l.strip())
    if rc != 0:
        fails.append(u"生成器表 --check 没过 ⇒ 不写盘")
        report()
        return 1

    rc, tail = run_table(write=True)
    for l in tail:
        notes.append(u"[--write] " + l.strip())
    if rc != 0:
        fails.append(u"生成器表 --write 没过")

    after = snapshot()
    new = sorted(set(after) - set(before))
    changed = sorted(n for n in set(after) & set(before) if after[n] != before[n])
    gone = sorted(set(before) - set(after))
    notes.append(u"配方目录：%d 份 → %d 份（新增 %s）" % (len(before), len(after), u"、".join(new)))
    if new != [u"silver_wire.json", u"silver_wire_spool.json"]:
        fails.append(u"新增的配方不是预期那两份：%s" % u"、".join(new))
    if changed:
        fails.append(u"**别的配方被改动了**：%s" % u"、".join(changed))
    else:
        notes.append(u"除新增那两份外，%d 份老配方逐字节未变" % len(before))
    if gone:
        fails.append(u"有配方不见了：%s" % u"、".join(gone))

    for name in (u"silver_wire.json", u"silver_wire_spool.json"):
        p = os.path.join(RECIPE_DIR, name)
        if not os.path.exists(p):
            fails.append(u"配方没写出来：%s" % name)
            continue
        j = json.loads(io.open(p, encoding="utf-8").read())
        notes.append(u"%s → %s x%d  %s" % (name, j["result"]["id"], j["result"]["count"],
                                           u" / ".join(j["pattern"])))
    report()
    return 1 if fails else 0


def report():
    print(u"\n".join(u"  [OK] " + n for n in notes))
    print(u"失败项 = %d" % len(fails))
    for f in fails:
        print(u"  !! " + f)


if __name__ == u"__main__":
    sys.exit(main())
