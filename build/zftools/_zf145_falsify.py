# -*- coding: utf-8 -*-
r'''_zf145_falsify.py —— ZF145 的**反证刀**：把 `_zf145_verify.py` 挨个咬一遍。

一把刀 = 一次"把盘上改坏一点点"，判据**必须**当场变红并说出**该说的那句话**；
然后逐字节还原、复核还原成功。刀咬不住 = 判据是空的（比没有更糟）。

⚠ 三条设计约束（抄前几轮）：
  ① 刀只改**数据/文档文本**，`_zf145_verify.py` 也只读文本 ⇒ 秒级、不碰 `build\classes`（§4.11）；
  ② 每把刀先备份再改，改完断言"命中次数 == 1"（防锚点漂移，§4.6）；
  ③ 每把刀认**期望的失败项名字**（不是"只要变红就算"）。

跑法：python build\zftools\_zf145_falsify.py [--only K301]
'''
import hashlib
import io
import os
import shutil
import subprocess
import sys

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

ROOT = r"E:\PotatoST"
ZT = os.path.join(ROOT, "build", "zftools")
ADV = r"src\main\resources\data\potato_s_t\advancement"
TAG = r"src\main\resources\data\potato_s_t\tags\damage_type\star_steel_slash.json"
LANG = r"src\main\resources\assets\potato_s_t\lang"
DOC = r"docs\开发档案.md"
HAND = r"docs\多会话协作交接.md"
ANN = r"docs\UpdateAnnouncement_EN.md"
TOOLS = r"build\zftools"
BAK = os.path.join(ZT, "_zf145_falsify_bak")
VERIFY = os.path.join(ZT, u"_zf145_verify.py")

# (刀号, 一句话, [(相对路径, 旧文本, 新文本)…], 期望出现在 FAIL 行里的子串)
# 旧文本 = None 表示"整份删掉"（只用于新建件）
KNIVES = [
    ("K301", u"把振金锭那条挂到 hard_alloy 上（父链错）",
     [(ADV + r"\vibranium.json", u'"parent": "potato_s_t:star_steel",',
       u'"parent": "potato_s_t:hard_alloy",')],
     u"B6 vibranium 的父链"),
    ("K302", u"星璨钢工具那条改成「与」（5 个组）",
     [(ADV + r"\star_steel_tools.json",
       u'    [\n      "got0",\n      "got1",\n      "got2",\n      "got3",\n      "got4"\n    ]\n',
       u'    [\n      "got0"\n    ],\n    [\n      "got1"\n    ],\n    [\n      "got2"\n    ],\n'
       u'    [\n      "got3"\n    ],\n    [\n      "got4"\n    ]\n')],
     u"C5 star_steel_tools 的 requirement 组数"),
    ("K303", u"振金套改成「或」（1 个组）",
     [(ADV + r"\vibranium_armor.json",
       u'    [\n      "got0"\n    ],\n    [\n      "got1"\n    ],\n    [\n      "got2"\n    ],\n'
       u'    [\n      "got3"\n    ]\n',
       u'    [\n      "got0",\n      "got1",\n      "got2",\n      "got3"\n    ]\n')],
     u"C5 vibranium_armor 的 requirement 组数"),
    ("K304", u"振金锭那条的框 goal → task",
     [(ADV + r"\vibranium.json", u'"frame": "goal",', u'"frame": "task",')],
     u"C1 vibranium 的 frame"),
    ("K305", u"银线那条的图标换成银线（不是线轴）",
     [(ADV + r"\silver_wire.json", u'"id": "potato_s_t:silver_wire_spool"',
       u'"id": "potato_s_t:silver_wire"')],
     u"C3 silver_wire 的图标"),
    ("K306", u"把星仪图之章那条藏起来",
     # ⚠ `hidden` 在 display 段里是**最后一个键** ⇒ 它后面**没有逗号**（第一版写成带逗号，锚点命中 0 次）
     [(ADV + r"\star_chart_tome.json", u'"hidden": false', u'"hidden": true')],
     u"C2 star_chart_tome 的 hidden"),
    ("K307", u"把一条老节点（salt.json）整个删掉",
     [(ADV + r"\salt.json", None, None)],
     u"A1 advancement 目录正好 43 份"),
    ("K308", u"偷偷改一个老节点的字节（salt.json 加一个空格）",
     [(ADV + r"\salt.json", u'"frame": "task",', u'"frame": "task", ')],
     u"A4 另 35 份老节点"),
    ("K309", u"伤害类型标签里写成另一个 id",
     [(TAG, u'"potato_s_t:star_steel_slash"', u'"potato_s_t:star_steel_slash2"')],
     u"D2 标签内容逐字节"),
    ("K310", u"星辉斩那条的 triggered 换成 inventory_changed",
     [(ADV + r"\star_steel_slash.json", u'"trigger": "minecraft:player_killed_entity",',
       u'"trigger": "minecraft:inventory_changed",')],
     u"C14 星辉斩的触发器"),
    ("K311", u"killing_blow 的标签名写错",
     [(ADV + r"\star_steel_slash.json", u'"id": "potato_s_t:star_steel_slash"',
       u'"id": "potato_s_t:star_steel_slashed"')],
     u"C15 星辉斩的 killing_blow 标签"),
    ("K312", u"改掉本轮新加的一个语言键的值（银线那条说明）",
     [(LANG + r"\zh_cn.json",
       u'"advancements.potato_s_t.silver_wire.description": "2 银锭',
       u'"advancements.potato_s_t.silver_wire.description": "2 银锭（被改了）')],
     u"E8 zh_cn：本轮新加的 16 个键的值指纹"),
    ("K313", u"把 `_zf107_verify.py` 的 EXPECT_NODES 打回 35",
     [(TOOLS + r"\_zf107_verify.py", u"EXPECT_NODES = 43", u"EXPECT_NODES = 35")],
     u"F2 _zf107_verify.py 的 EXPECT_NODES = 43"),
    ("K314", u"把 `_zf141_verify.py` 的 KEYS 打回 492",
     [(TOOLS + r"\_zf141_verify.py", u"KEYS = 508", u"KEYS = 492")],
     u"F1 _zf141_verify.py 的键数跟到 508"),
    ("K315", u"把 `_zf93_verify.py` 的成品靶子动一下（本轮没打包，必须保持 487）",
     [(TOOLS + r"\_zf93_verify.py", u"RELEASE_KEYS = 487", u"RELEASE_KEYS = 492")],
     u"F6 成品 jar 的键数靶子"),
    ("K316", u"探针报告里塞一条 [FAIL]",
     [(TOOLS + r"\_zf145_probe_utf8.txt", u"verdict: ALL OK",
       u"  [FAIL] 手工插进去的一行\nverdict: ALL OK")],
     u"G3 报告里没有 [FAIL]"),
    ("K317", u"把探针钩子塞回 PotatoST.java",
     [(r"src\main\java\com\potatost\mod\PotatoST.java",
       u"        net.neoforged.neoforge.common.NeoForge.EVENT_BUS.addListener(StarfallRitualManager::onPlayerLogin);\n",
       u"        net.neoforged.neoforge.common.NeoForge.EVENT_BUS.addListener(StarfallRitualManager::onPlayerLogin);\n"
       u"        Zf145Check.register();\n")],
     u"G7 PotatoST.java 里没有残留钩子"),
    ("K318", u"交接文档的键数打回 492",
     [(HAND, u"| 语言键数 | **508 键 × 4**", u"| 语言键数 | **492 键 × 4**")],
     u"H5 交接文档的活体数字是 508 键 × 4"),
    ("K319", u"英文公告的键数打回 492",
     [(ANN, u"(508 keys each)", u"(492 keys each)")],
     u"H8 英文公告的键数跟到 508"),
    ("K320", u"交接文档的进度条数打回 42",
     [(HAND, u"| 进度（成就） | **43 条**", u"| 进度（成就） | **42 条**")],
     u"H6 交接文档写着 43 条进度"),
]


def sha1(p):
    return hashlib.sha1(open(p, "rb").read()).hexdigest()


def run_verify():
    env = dict(os.environ)
    env["PYTHONIOENCODING"] = "utf-8"
    r = subprocess.run([sys.executable, VERIFY], capture_output=True, env=env, cwd=ROOT)
    out = r.stdout.decode("utf-8", "replace") + r.stderr.decode("utf-8", "replace")
    fails = [l.strip()[3:].strip() for l in out.split("\n") if l.strip().startswith(u"!!")]
    return out, fails


def main(argv):
    only = argv[argv.index(u"--only") + 1] if u"--only" in argv else None

    base_out, base_fails = run_verify()
    print(u"基线：%s" % [l for l in base_out.split(u"\n") if u"通过 =" in l][:1])
    if base_fails:
        print(u"!! 基线不是全绿（%d 项）—— 先修好再跑刀：%s"
              % (len(base_fails), u" ／ ".join(base_fails[:4])))
        return 1

    os.makedirs(BAK, exist_ok=True)
    bite, miss, notes = 0, 0, []
    for kid, title, edits, expect in KNIVES:
        if only and kid != only:
            continue
        saved = []
        try:
            for rel, old, new in edits:
                full = os.path.join(ROOT, rel)
                if not os.path.isfile(full):
                    notes.append(u"  !! %s 目标不在：%s" % (kid, rel))
                    raise IOError(rel)
                bak = os.path.join(BAK, u"%s_%s" % (kid, os.path.basename(rel)))
                shutil.copy2(full, bak)
                saved.append((full, bak))
                if old is None:                      # 整份删掉
                    os.remove(full)
                    continue
                text = io.open(full, encoding="utf-8", newline="").read()
                if text.count(old) != 1:
                    notes.append(u"  !! %s 锚点命中 %d 次：%s" % (kid, text.count(old), rel))
                    raise IOError(rel)
                io.open(full, u"w", encoding="utf-8", newline=u"").write(text.replace(old, new, 1))

            _out, fails = run_verify()
            if [f for f in fails if expect in f]:
                bite += 1
                print(u"  [咬住] %s  %s" % (kid, title))
            else:
                miss += 1
                print(u"  [漏网] %s  %s" % (kid, title))
                print(u"         期望失败项「%s」没出现；实际 %d 项：%s"
                      % (expect, len(fails), u" ／ ".join(f[:44] for f in fails[:4])))
        except Exception as e:
            miss += 1
            notes.append(u"  !! %s 自己出错：%r" % (kid, e))
            print(u"  [出错] %s  %r" % (kid, e))
        finally:
            for full, bak in saved:
                if os.path.exists(bak):
                    shutil.copy2(bak, full)
                    if sha1(full) != sha1(bak):
                        notes.append(u"  !! %s 还原失败：%s" % (kid, full))

    for n in notes:
        print(n)
    _out2, fails2 = run_verify()
    same = sorted(fails2) == sorted(base_fails)
    print(u"")
    print(u"刀 = %d，咬住 = %d，漏网 = %d" % (bite + miss, bite, miss))
    print(u"收尾：全部还原之后基线回到原样 = %s（失败 %d 项）" % (same, len(fails2)))
    return 0 if (bite > 0 and miss == 0 and same) else 1


if __name__ == u"__main__":
    sys.exit(main(sys.argv[1:]))
