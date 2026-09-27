# -*- coding: utf-8 -*-
u"""_zf148_falsify.py —— ZF148 反证刀（静态，**不开游戏**）：改一处 ⇒ 指定那一项必须变红 ⇒ 还原后必须回绿。

每把刀的流程都是：读原文（留 sha1）→ 改一处 → 跑目标门 → 断言输出里出现**指定的失败行** →
**逐字节还原**（ri 核 sha1）→ 再跑一次断言回到 0 失败。
⚠ 只动本轮的产物（书数据 / 语言 / 依赖声明 / 门自身），不碰别人的文件；全程逐把还原。

跑法：python build\\zftools\\_zf148_falsify.py
"""
import hashlib
import io
import os
import subprocess
import sys

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding=u"utf-8", errors=u"replace")

ROOT = r"E:\PotatoST"
ZT = os.path.join(ROOT, "build", "zftools")
V = os.path.join(ZT, u"_zf148_verify.py")
RES = os.path.join(ROOT, "src", "main", "resources")
ASSETS = os.path.join(RES, "assets", "potato_s_t")
DATA = os.path.join(RES, "data", "potato_s_t")
TOML = os.path.join(RES, "META-INF", "neoforge.mods.toml")
GRADLE = os.path.join(ROOT, "build.gradle")
DOC = os.path.join(ROOT, "docs", "开发档案.md")
HAND = os.path.join(ROOT, "docs", "多会话协作交接.md")

BOOK = os.path.join(DATA, u"patchouli_books", u"guide", u"book.json")
ENT_FAQ = os.path.join(ASSETS, u"patchouli_books", u"guide", u"en_us", u"entries", u"faq", u"fluid.json")
ENT_START = os.path.join(ASSETS, u"patchouli_books", u"guide", u"en_us", u"entries",
                         u"getting_started", u"start.json")
CAT_POWER = os.path.join(ASSETS, u"patchouli_books", u"guide", u"en_us", u"categories", u"power.json")
RECIPE = os.path.join(DATA, u"recipe", u"guide_book.json")
LANG_ZH = os.path.join(ASSETS, u"lang", u"zh_cn.json")
Z139 = os.path.join(ZT, u"_zf139_verify.py")
Z145 = os.path.join(ZT, u"_zf145_verify.py")

# (标签, 文件, 旧串, 新串, 目标门, 期望出现的失败行片段)
KNIVES = [
    (u"K1 book.json 的 model 写回带 item/ 的错写法", BOOK,
     u'"model": "potato_s_t:guide_book"', u'"model": "potato_s_t:item/guide_book"',
     V, u"B2 book.json['model']"),
    (u"K2 i18n 关掉（正文改回字面量语义）", BOOK,
     u'"i18n": true', u'"i18n": false',
     V, u"B2 book.json['i18n']"),
    (u"K3 删一个条目文件（faq/fluid.json 改名）", ENT_FAQ,
     None, None, V, u"C2 十八份条目都读得到"),
    (u"K4 条目的 icon 改成不存在的物品", CAT_POWER,
     u'"icon": "potato_s_t:terminal"', u'"icon": "potato_s_t:no_such_machine"',
     V, u"C1 分类 power"),
    (u"K5 crafting 页引用不存在的配方", ENT_START,
     u'"recipe": "potato_s_t:micro_crusher"', u'"recipe": "potato_s_t:no_such_recipe"',
     V, u"C5 每个 crafting 页的配方文件都存在"),
    (u"K6 配方产物去掉 patchouli:book 组件", RECIPE,
     u'    "components": {\n      "patchouli:book": "potato_s_t:guide"\n    }\n', u'    "components": {}\n',
     V, u"D7 产物带 patchouli:book 组件"),
    (u"K7 mods.toml 把硬依赖降成 optional", TOML,
     u'modId="patchouli"\ntype="required"', u'modId="patchouli"\ntype="optional"',
     V, u"A3 帕秋莉是 required"),
    (u"K8 build.gradle 拿掉 compileOnly 那行", GRADLE,
     u"    compileOnly files('libs/Patchouli-1.21.1-93-NEOFORGE.jar')\n", u"",
     V, u"A5 build.gradle 里有帕秋莉的 compileOnly"),
    (u"K9 语言里改掉一个手册键的值（不动生成器表）", LANG_ZH,
     u'"potato_s_t.guide.category.faq": "疑难"', u'"potato_s_t.guide.category.faq": "疑难杂症"',
     V, u"E7 五份的值与生成器表"),
    (u"K10 语言里删掉一个手册键", LANG_ZH,
     u'  "potato_s_t.guide.entry.faq.fluid.p1":', u'  "potato_s_t.guide.entry.faq.fluid.XXp1":',
     V, u"E6 手册 71 键在五份里一条不缺"),
    (u"K11 交接文档的活体数字改回去", HAND,
     u"| 语言键数 | **579 键 × 4**", u"| 语言键数 | **508 键 × 4**",
     V, u"G5 交接文档的活体数字"),
    (u"K12 档案删掉 §4.151 标题", DOC,
     u"### 4.158 【工具雷】**联动帕秋莉**这一轮踩到的四个坑（0.12 ZF148）",
     u"### 4.158x 【工具雷】联动帕秋莉这一轮踩到的四个坑",
     V, u"G1 档案里有 §4.158"),
    (u"K13 _zf139 的配方数改回 73（跟平链断一环）", Z139,
     u"check(n_recipe == 74,", u"check(n_recipe == 73,",
     V, u"H3 _zf139 配方数 = 74"),
    (u"K14 _zf145 的 E6 期望里去掉 ZF148 那 71 键（别人的门漏跟平）", Z145,
     u'        later148 = ({k for k in lang[l] if k.startswith(u"potato_s_t.guide.")}',
     u'        later148 = ({k for k in lang[l] if k.startswith(u"potato_s_t.NOPE.")}',
     Z145, u"E6"),
]

fails = []
rows = []


def sha1(p):
    return hashlib.sha1(open(p, "rb").read()).hexdigest()


def run(script):
    r = subprocess.run([sys.executable, script], stdout=subprocess.PIPE,
                       stderr=subprocess.STDOUT, timeout=300)
    return r.returncode, r.stdout.decode(u"utf-8", "replace")


def main():
    for label, path, old, new, target, marker in KNIVES:
        name = os.path.basename(path)
        original = open(path, "rb").read()
        h0 = hashlib.sha1(original).hexdigest()
        try:
            if old is None:                      # K3：把文件挪走
                tmp = path + u".zf148bak"
                os.rename(path, tmp)
            else:
                text = io.open(path, encoding=u"utf-8", newline=u"").read()
                if text.count(old) != 1:
                    fails.append(u"%s：改前串命中 %d 次" % (label, text.count(old)))
                    continue
                io.open(path, u"w", encoding=u"utf-8", newline=u"").write(text.replace(old, new, 1))

            rc, out = run(target)
            # ⚠ 判据必须是「**失败行**里有这个标记」：门对同一件事既会打 [OK] 也会打 [FAIL]，
            #   只 grep 标记文本会把"绿着也命中"当成变红（本节第一版就这么误判了 K12）。
            hit = any(marker in l and (u"[FAIL]" in l or l.strip().startswith(u"!!")) for l in out.split(u"\n"))
            ok_red = (rc != 0) and hit

            # 还原（逐字节）
            if old is None:
                os.rename(path + u".zf148bak", path)
            else:
                open(path, "wb").write(original)
            h1 = sha1(path)
            restored = (h1 == h0)

            rc2, out2 = run(V if target != V else V)
            back_green = (rc2 == 0)

            rows.append((label, name, ok_red, restored, back_green))
            if not ok_red:
                fails.append(u"%s：改坏之后目标门**没红**（rc=%d，命中标记=%s）" % (label, rc, hit))
            if not restored:
                fails.append(u"%s：还原后与改前**不是逐字节相同**" % label)
            if not back_green:
                fails.append(u"%s：还原后 _zf148_verify.py 仍是红的" % label)
        except Exception as e:
            fails.append(u"%s：异常 %s" % (label, e))
            if old is None and os.path.exists(path + u".zf148bak"):
                os.rename(path + u".zf148bak", path)
            else:
                open(path, "wb").write(original)

    print(u"================ ZF148 反证刀（静态 %d 把） ================" % len(KNIVES))
    print(u"%-58s %-6s %-8s %-8s" % (u"刀", u"变红", u"逐字节还原", u"回绿"))
    for label, name, a, b, c in rows:
        print(u"%-58s %-6s %-8s %-8s" % (label[:56], u"OK" if a else u"!!", u"OK" if b else u"!!",
                                         u"OK" if c else u"!!"))
    print(u"")
    print(u"刀数 = %d   全中 = %d   失败 = %d" % (len(KNIVES), len([r for r in rows if r[2] and r[3] and r[4]]), len(fails)))
    for f in fails:
        print(u"  !! " + f)
    return 1 if fails else 0


if __name__ == u"__main__":
    sys.exit(main())
