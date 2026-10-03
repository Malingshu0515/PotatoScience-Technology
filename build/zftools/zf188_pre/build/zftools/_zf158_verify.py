# -*- coding: utf-8 -*-
r'''_zf158_verify.py —— ZF158（0.13 第四笔）**常驻校验**：热力金属换成「铜板夹银锭」+ 生成器表跟平。
  A 图纸：CCC/SSS/CCC、C=#c:plates/copper、S=#c:ingots/silver、与旧图纸互为上下颠倒、产物不变、格式合规
  B 生成器表：不再写死自家板当物品 / thermal 已是新图纸 / 模板是通用升级模板 / **可复现**（重出与盘逐字节相同）
  C 旁证：`_zf45_recipes.py --check` 0 失败、`_zf156_verify.py` 仍绿（29 处 #c:plates/*）
  D 文档与成品：§4.166 / §5 ZF158 行 / 公告 / 交接 / 哈希三处联动（打包后）

跑法：python build\zftools\_zf158_verify.py
'''
import hashlib
import io
import json
import os
import re
import shutil
import subprocess
import sys

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding=u"utf-8", errors=u"replace")

ROOT = r"E:\PotatoST"
ZT = os.path.join(ROOT, "build", "zftools")
RECIPE = os.path.join(ROOT, r"src\main\resources\data\potato_s_t\recipe")
GEN = os.path.join(ZT, u"_zf45_recipes.py")
THERMAL = os.path.join(RECIPE, u"thermal_metal.json")
PRE = os.path.join(r"C:\PotatoST救援", "zf158_pre")
TMP = os.path.join(ZT, u"_zf158_tmp")
DOC = os.path.join(ROOT, "docs", u"开发档案.md")
HAND = os.path.join(ROOT, "docs", u"多会话协作交接.md")
ANN = os.path.join(ROOT, "docs", "UpdateAnnouncement_EN.md")
METALS = [u"aluminum", u"cobalt", u"copper", u"iron", u"nickel", u"silver", u"steel"]
OUT_LINE = u'OUT = os.path.join(PROJ, "src", "main", "resources", "data", "potato_s_t", "recipe")'

passed, failed, fails = 0, 0, []


def check(cond, label, detail=u""):
    global passed, failed
    if cond:
        passed += 1
        print(u"  [OK]   " + label)
    else:
        failed += 1
        fails.append(label if not detail else u"%s（%s）" % (label, detail))
        print(u"  [FAIL] " + label + (u" —— " + detail if detail else u""))


def read(p):
    return io.open(p, encoding="utf-8", errors="replace").read() if os.path.isfile(p) else u""


def raw(p):
    with open(p, "rb") as fh:
        return fh.read()


def sha1(p):
    return hashlib.sha1(raw(p)).hexdigest()


def main():
    print("=" * 78)
    print(u"_zf158_verify.py —— ZF158：热力金属 = 铜板夹银锭 + 生成器表跟平")
    print("=" * 78)

    # ---------------- A 图纸 ----------------
    print(u"--- A 图纸")
    t = read(THERMAL)
    try:
        d = json.loads(t)
    except Exception as exc:
        d = {}
        check(False, u"A1 thermal_metal.json 是合法 JSON", str(exc))
    if d:
        check(u"type" in d and d[u"type"] == u"minecraft:crafting_shaped",
              u"A1 仍是 crafting_shaped（只换图纸、没换配方类型）")
        check(d.get(u"pattern") == [u"CCC", u"SSS", u"CCC"],
              u"A2 pattern = CCC / SSS / CCC（外圈铜板、中行银锭）", u"实际 %s" % d.get(u"pattern"))
        key = d.get(u"key", {})
        check(key.get(u"C", {}).get(u"tag") == u"c:plates/copper",
              u"A3 C = #c:plates/copper（**标签**，跨 mod 兼容不倒退）", u"实际 %s" % key.get(u"C"))
        check(key.get(u"S", {}).get(u"tag") == u"c:ingots/silver",
              u"A4 S = #c:ingots/silver", u"实际 %s" % key.get(u"S"))
        check(d.get(u"result", {}).get(u"id") == u"potato_s_t:thermal_metal"
              and d.get(u"result", {}).get(u"count") == 1,
              u"A5 产物不变（热力金属 ×1）", u"实际 %s" % d.get(u"result"))
        # 与改前件互为上下颠倒
        old = json.loads(read(os.path.join(PRE, r"src\main\resources\data\potato_s_t\recipe\thermal_metal.json")) or u"{}")
        check(old.get(u"pattern") == [u"SSS", u"CCC", u"SSS"]
              and old.get(u"key") == key,
              u"A6 与改前图纸正好互为上下颠倒（key 一个字没改）",
              u"改前 %s" % old.get(u"pattern"))
    b = raw(THERMAL)
    check(not b.startswith(b"\xef\xbb\xbf") and b"\r" not in b and b.endswith(b"\n"),
          u"A7 无 BOM / 纯 LF / 结尾有换行（.gitattributes `* -text`）")

    # ---------------- B 生成器表 ----------------
    print(u"--- B 生成器表（那 35 份 JSON 的唯一来源）")
    gen = read(GEN)
    item_hits = re.findall(u'"item", "potato_s_t:(?:' + u"|".join(METALS) + u')_plate"', gen)
    check(not item_hits, u"B1 表里不再有「自家板当物品」（ZF156 的账已跟平）",
          u"还剩 %d 处" % len(item_hits))
    check(u'pattern=["CCC", "SSS", "CCC"]' in gen, u"B2 表里 thermal_metal 已是新图纸")
    check(u'\u94dc\u677f\u6059\u94f6\u952d' in gen, u"B3 表里那条注释点明了「铜板夹银锭」")
    check(u'SMITHING_TEMPLATE = u"potato_s_t:universal_upgrade_template"' in gen,
          u"B4 表的锻造模板常量 = 通用升级模板（ZF155 的账已跟平）")
    # 可复现：把表复制到临时目录跑一遍 --write，产物必须与盘上逐字节相同
    ok, detail = reproduce(gen)
    check(ok, u"B5 可复现：表重出一遍，产物与盘上**逐字节相同**", detail)

    # ---------------- C 旁证 ----------------
    print(u"--- C 旁证")
    # ⚠ 这个生成器的"只校验"模式就是**不带参数**跑（它的文档写 `--check`，但 argparse 里其实没有这个开关
    #   —— 第一版照着文档写了 `--check`，结果 rc=2「unrecognized arguments」，被自己的门抓住）。
    # ⚠ 它的 stdout **没**转 UTF-8（§4.50 同族：这台机器控制台是 GBK）⇒ 解码要按 GBK 试，不然
    #   "失败项 = 0" 这句话根本 match 不到（第一版就是这么假红的）。
    r = subprocess.run([sys.executable, GEN], cwd=ROOT,
                       stdout=subprocess.PIPE, stderr=subprocess.STDOUT, timeout=600)
    out = u""
    for enc in ("gbk", "utf-8"):
        try:
            out = r.stdout.decode(enc)
            break
        except Exception:
            continue
    else:
        out = r.stdout.decode("utf-8", "replace")
    check(r.returncode == 0 and u"失败项 = 0" in out,
          u"C1 `_zf45_recipes.py --check` 0 失败",
          u"rc=%d %s" % (r.returncode, [l for l in out.split(u"\n") if u"FAIL" in l][:2]))
    v156 = os.path.join(ZT, u"_zf156_verify.py")
    r2 = subprocess.run([sys.executable, v156], cwd=ROOT, stdout=subprocess.PIPE,
                        stderr=subprocess.STDOUT, timeout=900)
    out2 = r2.stdout.decode("utf-8", "replace")
    check(r2.returncode == 0, u"C2 ZF156 的常驻门仍全绿（图纸换了但 29 处 #c:plates/* 没动）",
          u"rc=%d" % r2.returncode)

    # ---------------- D 文档与成品 ----------------
    print(u"--- D 文档与成品")
    doc, hand, ann = read(DOC), read(HAND), read(ANN)
    check(u"### 4.166" in doc, u"D1 档案 §4.166 一节")
    check(u"| ZF158 |" in doc, u"D2 档案 §5 有 ZF158 行")
    check(u"## New in 0.13 ZF158" in ann, u"D3 英文公告有 ZF158 那一条")
    check(u"ZF158" in hand, u"D4 交接文档提到 ZF158")
    jar = os.path.join(ROOT, u"release", u"PotatoST-0.13.jar")
    if os.path.isfile(jar):
        h = sha1(jar)
        check(h in ann and h in hand, u"D5 成品哈希三处联动（公告 + 交接）", h[:12])
        import zipfile
        try:
            z = zipfile.ZipFile(jar)
            packed = json.loads(z.read(u"data/potato_s_t/recipe/thermal_metal.json").decode("utf-8"))
            check(packed.get(u"pattern") == [u"CCC", u"SSS", u"CCC"],
                  u"D6 **jar 里**那张图纸也是铜板夹银锭（成品真的带上了这一笔）",
                  u"jar 里 %s" % packed.get(u"pattern"))
        except Exception as exc:
            check(False, u"D6 jar 里读 thermal_metal.json", str(exc))
    else:
        print(u"  [SKIP] release\\PotatoST-0.13.jar 还没重打（D5/D6 打包后再跑）")

    print("=" * 78)
    print(u"通过 %d 项 / 失败 %d 项" % (passed, failed))
    for f in fails:
        print(u"  !! " + f)
    return 1 if failed else 0


def reproduce(gen):
    """把生成器复制一份、只改 OUT 到临时目录跑 --write，再与盘上逐字节比。"""
    if os.path.isdir(TMP):
        shutil.rmtree(TMP)
    os.makedirs(TMP)
    if gen.count(OUT_LINE) != 1:
        return False, u"OUT 那行锚点命中 %d 次" % gen.count(OUT_LINE)
    tmp_gen = os.path.join(TMP, u"_gen_tmp.py")
    io.open(tmp_gen, "w", encoding="utf-8", newline=u"").write(
        gen.replace(OUT_LINE, u'OUT = r"%s"' % TMP))
    r = subprocess.run([sys.executable, tmp_gen, u"--write"], cwd=ROOT,
                       stdout=subprocess.PIPE, stderr=subprocess.STDOUT, timeout=600)
    if r.returncode != 0:
        return False, u"临时生成器 rc=%d" % r.returncode
    diff, same = [], 0
    for fn in sorted(os.listdir(TMP)):
        if not fn.endswith(u".json"):
            continue
        a = os.path.join(TMP, fn)
        c = os.path.join(RECIPE, fn)
        if not os.path.isfile(c):
            diff.append(fn + u"（盘上没有）")
        elif sha1(a) != sha1(c):
            diff.append(fn)
        else:
            same += 1
    shutil.rmtree(TMP)
    if diff:
        return False, u"%d 份对不上：%s" % (len(diff), u", ".join(diff[:6]))
    return True, u"%d 份逐字节相同" % same


if __name__ == u"__main__":
    sys.exit(main())
