# -*- coding: utf-8 -*-
u"""_zf118_recipe.py —— ZF118：把「星轨坠」加进**生成器表**并重跑生成 JSON

用户原话：「星轨坠配方；中间一个下界之星 上下左右各一个星璨钢 四角放岩浆块」

图纸（3×3，逐格照抄）：

    【岩浆块】  【星璨钢锭】  【岩浆块】
    【星璨钢锭】 【下界之星】  【星璨钢锭】
    【岩浆块】  【星璨钢锭】  【岩浆块】

规矩（档案 §5「不要手写 JSON」）：配方只在 `_zf45_recipes.py` 的表里写一份，
再 `--write` 生成 JSON —— 这样白拿两样机械核对：**id 真的存在**（本模组查注册、
原版查 client.jar 的物品模型）+ **表与 JSON 逐字节一致**（`_zf69_verify.py` 那一族门在盯）。

本脚本干四件事（每件都「定位 → 替换 → 立刻回读」）：
  ① 表尾插一条（锚点：星璨钢靴子那条 + 表的收尾 `]`）；
  ② 跑 `_zf45_recipes.py --write`；
  ③ 断言**除新配方外**没有任何配方文件被动过（与 zf118_pre 的哈希逐份比）；
  ④ 断言新 JSON 的 pattern/key/result 就是用户那张图纸（独立再读一遍 JSON，不靠表）。
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
GEN = os.path.join(ROOT, r"build\zftools\_zf45_recipes.py")
RDIR = os.path.join(ROOT, r"src\main\resources\data\potato_s_t\recipe")
NEWJSON = os.path.join(RDIR, "starfall_pendant.json")
BK = r"C:\PotatoST救援\zf118_pre"

ANCHOR = (u'         pattern=["X X", "X X"],\n'
          u'         key={"X": ("item", "potato_s_t:star_steel_ingot")}),\n'
          u']\n')
ENTRY = (u'\n'
         u'    # ===== ZF118 追加（用户原话：「星轨坠配方；中间一个下界之星 上下左右各一个星璨钢\n'
         u'    #      四角放岩浆块」）=====\n'
         u'    # 【岩浆块】【星璨钢锭】【岩浆块】 / 【星璨钢锭】【下界之星】【星璨钢锭】 /\n'
         u'    # 【岩浆块】【星璨钢锭】【岩浆块】 → 星轨坠\n'
         u'    dict(name="starfall_pendant", category="misc",\n'
         u'         result=("potato_s_t:starfall_pendant", 1),\n'
         u'         pattern=["MSM", "SNS", "MSM"],\n'
         u'         key={"M": ("item", "minecraft:magma_block"),\n'
         u'              "S": ("item", "potato_s_t:star_steel_ingot"),\n'
         u'              "N": ("item", "minecraft:nether_star")}),\n')

fails, notes = [], []


def read(p):
    return io.open(p, encoding="utf-8").read()


def sha1(p):
    return hashlib.sha1(open(p, "rb").read()).hexdigest()


def main():
    # ---------- ① 表尾插一条 ----------
    gen = read(GEN)
    if u'name="starfall_pendant"' in gen:
        notes.append(u"生成器表里已经有 starfall_pendant 了，跳过插入")
    else:
        if gen.count(ANCHOR) != 1:
            fails.append(u"表尾锚点出现 %d 次（要求 1）" % gen.count(ANCHOR))
        else:
            tail = (u'         pattern=["X X", "X X"],\n'
                    u'         key={"X": ("item", "potato_s_t:star_steel_ingot")}),\n')
            gen = gen.replace(ANCHOR, tail + ENTRY + u']\n', 1)
            io.open(GEN, "w", encoding="utf-8", newline=u"").write(gen)
            back = read(GEN)
            if u'name="starfall_pendant"' not in back or u'"MSM", "SNS", "MSM"' not in back:
                fails.append(u"回读：表里没看到新条目")
            else:
                compile(back, GEN, "exec")
                notes.append(u"生成器表加了一条 starfall_pendant（锚点唯一）")
        # 表里现在几条 + 文件头那句"表里现在 N 条"要不要跟着改
        n = read(GEN).count(u'dict(name=')
        old = read(GEN)
        import re
        m = re.search(u'表里现在 (\\d+) 条', old)
        if m and int(m.group(1)) != n:
            new = old.replace(m.group(0), u"表里现在 %d 条" % n, 1)
            io.open(GEN, "w", encoding="utf-8", newline=u"").write(new)
            notes.append(u"生成器文件头「表里现在 %d 条」→ %d 条" % (int(m.group(1)), n))
        elif not m:
            notes.append(u"（生成器文件头没有「表里现在 N 条」那句，跳过；表里 %d 条）" % n)

    # ---------- ② 跑生成器 ----------
    r = subprocess.run([sys.executable, GEN, "--write"], stdout=subprocess.PIPE,
                       stderr=subprocess.STDOUT, timeout=180)
    out = r.stdout.decode("utf-8", "replace")
    if r.returncode != 0:
        fails.append(u"生成器 --write 退出码 %d：\n%s" % (r.returncode, out[-1500:]))
    else:
        notes.append(u"生成器 --write 退出码 0")
    for l in out.split(u"\n"):
        if u"starfall_pendant" in l or u"失败项" in l or u"配方 " in l:
            notes.append(u"    " + l.strip())

    # ---------- ③ 除新配方外，一份都不许动 ----------
    changed = []
    for name in sorted(os.listdir(RDIR)):
        if not name.endswith(".json") or name == "starfall_pendant.json":
            continue
        cur = os.path.join(RDIR, name)
        old = os.path.join(BK, r"src\main\resources\data\potato_s_t\recipe", name)
        if not os.path.exists(old):
            fails.append(u"改前件里没有 %s（本轮前它就该在盘上）" % name)
            continue
        if sha1(cur) != sha1(old):
            changed.append(name)
    if changed:
        fails.append(u"生成器把别的配方改了！%s" % changed)
    else:
        n_old = len([n for n in os.listdir(RDIR)
                     if n.endswith(".json") and n != "starfall_pendant.json"])
        notes.append(u"旧配方 %d 份逐字节未变（只新增 starfall_pendant.json）" % n_old)

    # ---------- ④ 新 JSON 就是那张图纸 ----------
    if not os.path.exists(NEWJSON):
        fails.append(u"新配方 JSON 没生成：%s" % NEWJSON)
    else:
        obj = json.loads(read(NEWJSON))
        want_pattern = ["MSM", "SNS", "MSM"]
        want_key = {"M": "minecraft:magma_block",
                    "S": "potato_s_t:star_steel_ingot",
                    "N": "minecraft:nether_star"}
        if obj.get("pattern") != want_pattern:
            fails.append(u"pattern 不对：%s" % obj.get("pattern"))
        if {k: v.get("item") for k, v in obj.get("key", {}).items()} != want_key:
            fails.append(u"key 不对：%s" % obj.get("key"))
        if obj.get("result") != {"id": "potato_s_t:starfall_pendant", "count": 1}:
            fails.append(u"result 不对：%s" % obj.get("result"))
        if obj.get("type") != "minecraft:crafting_shaped":
            fails.append(u"type 不对：%s" % obj.get("type"))
        if not fails:
            notes.append(u"新 JSON：%s 图纸正确（%s）"
                         % (obj.get("type"), u" / ".join(obj["pattern"])))

    print(u"\n".join(u"  [OK] " + n for n in notes))
    print(u"\n失败项 = %d" % len(fails))
    for f in fails:
        print(u"  !! " + f)
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())
