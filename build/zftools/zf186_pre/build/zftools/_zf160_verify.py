# -*- coding: utf-8 -*-
r'''_zf160_verify.py —— ZF160（0.13 第五笔）**常驻校验**：银矿脉调大 / 铝权重调小。
  A 盘上 JSON：银 size 3→10、银 count 9→12、铝 count 12→10；**其余 7 种矿逐条没动**；
    9 条矿脉除了那三个数**逐字没动**；格式合规；biome modifier 仍列 9 条
  B 真开服探针报告：注册表现查的那 7 条
  C 文档与成品：§4.168 / §5 行 / 公告 / 交接 / **jar 里**那两个数也是新值

跑法：python build\zftools\_zf160_verify.py
'''
import hashlib
import io
import json
import os
import re
import sys
import zipfile

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding=u"utf-8", errors=u"replace")

ROOT = r"E:\PotatoST"
ZT = os.path.join(ROOT, "build", "zftools")
WG = os.path.join(ROOT, r"src\main\resources\data\potato_s_t\worldgen")
CFG = os.path.join(WG, "configured_feature")
PLC = os.path.join(WG, "placed_feature")
BM = os.path.join(ROOT, r"src\main\resources\data\potato_s_t\neoforge\biome_modifier\potato_st_ores.json")
PRE = os.path.join(r"C:\PotatoST救援", "zf160_pre")
REPORT = os.path.join(ZT, u"_zf160_probe_utf8.txt")
DOC = os.path.join(ROOT, "docs", u"开发档案.md")
HAND = os.path.join(ROOT, "docs", u"多会话协作交接.md")
ANN = os.path.join(ROOT, "docs", "UpdateAnnouncement_EN.md")

ORES = ["aluminum", "cobalt", "nickel", "silver", "uranium", "manganese", "lithium",
        "wolframite", "titanium"]
EXPECT = {"aluminum": (11, 10), "cobalt": (4, 6), "nickel": (6, 8), "silver": (10, 12),
          "uranium": (10, 10), "manganese": (12, 8), "lithium": (8, 7),
          "wolframite": (4, 6), "titanium": (8, 4)}
PROBE_OK = ["A1", "A2", "A3", "A4", "A5", "A6", "A7"]

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


def git_show(rel):
    """取 git HEAD 里那份文件（世界生成的 JSON 全程是 CRLF，用二进制读再按 utf-8 解）。"""
    import subprocess
    r = subprocess.run(["git", "show", "HEAD:" + rel], cwd=ROOT, stdout=subprocess.PIPE,
                       stderr=subprocess.DEVNULL)
    return r.stdout.decode("utf-8", "replace") if r.returncode == 0 else u""


def endings(b):
    crlf = b.count(b"\r\n")
    lf = b.count(b"\n") - crlf
    return crlf, lf


def size_of(ore):
    return json.loads(read(os.path.join(CFG, u"ore_%s.json" % ore))).get("config", {}).get("size")


def count_of(ore):
    for step in json.loads(read(os.path.join(PLC, u"ore_%s_placed.json" % ore))).get("placement", []):
        if step.get("type") == "minecraft:count":
            return step.get("count")
    return None


def main():
    print("=" * 78)
    print(u"_zf160_verify.py —— ZF160：银矿脉调大（size 3→10 / count 9→12）、铝权重调小（12→10）")
    print("=" * 78)

    print(u"--- A 盘上 JSON")
    check(size_of("silver") == 10, u"A1 银矿脉 size = 10（原版铜小脉同值；改前 3）",
          u"实际 %s" % size_of("silver"))
    check(count_of("silver") == 12, u"A2 银矿每区块 12 次（改前 9；原版铜 16）",
          u"实际 %s" % count_of("silver"))
    check(count_of("aluminum") == 10 and size_of("aluminum") == 11,
          u"A3 铝每区块 10 次（改前 12；取「调小 1~2」的 2）、size 仍 11",
          u"实际 size=%s count=%s" % (size_of("aluminum"), count_of("aluminum")))

    diffs = []
    for ore in ORES:
        if ore in ("silver", "aluminum"):
            continue
        # ⚠ 其余 7 种矿的改前状态取 **git HEAD**（它们这一刻在盘上与 HEAD 逐字节相同）：
        #   第一版拿 zf160_pre 备份比 —— 而那份备份本轮只列了要动的 5 个文件，
        #   另外 7 种矿的 JSON **根本没备份** ⇒ 读成空 ⇒ 七条全报"动了"（假红）。
        old_cfg = json.loads(git_show(r"src/main/resources/data/potato_s_t/worldgen/configured_feature/ore_%s.json" % ore) or u"{}")
        old_plc = json.loads(git_show(r"src/main/resources/data/potato_s_t/worldgen/placed_feature/ore_%s_placed.json" % ore) or u"{}")
        if old_cfg.get("config", {}).get("size") != size_of(ore):
            diffs.append(ore + "(size)")
        old_count = None
        for step in old_plc.get("placement", []):
            if step.get("type") == "minecraft:count":
                old_count = step.get("count")
        if old_count != count_of(ore):
            diffs.append(ore + "(count)")
    check(not diffs, u"A4 其余 7 种矿的 size / count **逐条没动**（与 git HEAD 比）", u"动了 %s" % diffs)

    # A5：银/铝两份 JSON 除了那三个数，逐字没动（把新旧两份里的数字各换成占位符再比）
    def norm(text, pairs):
        for old, new in pairs:
            text = text.replace(old, u"@NUM@")
            text = text.replace(new, u"@NUM@")
        return text

    pairs_silver_cfg = [(u'"size": 3', u'"size": 10')]
    pairs_silver_plc = [(u'"count": 9', u'"count": 12')]
    pairs_alum_plc = [(u'"count": 12', u'"count": 10')]
    same = True
    for rel, pairs in ((r"configured_feature\ore_silver.json", pairs_silver_cfg),
                       (r"placed_feature\ore_silver_placed.json", pairs_silver_plc),
                       (r"placed_feature\ore_aluminum_placed.json", pairs_alum_plc)):
        cur = read(os.path.join(WG, rel))
        old = read(os.path.join(PRE, r"src\main\resources\data\potato_s_t\worldgen", rel))
        if norm(cur, pairs) != norm(old, pairs):
            same = False
    check(same, u"A5 银/铝那三份 JSON 除了那三个数**逐字没动**（高度/步数/targets 都没碰）")

    fmt = []
    for rel in (r"configured_feature\ore_silver.json", r"placed_feature\ore_silver_placed.json",
                r"placed_feature\ore_aluminum_placed.json"):
        p = os.path.join(WG, rel)
        b = raw(p)
        old_b = raw(os.path.join(PRE, r"src\main\resources\data\potato_s_t\worldgen", rel)) if os.path.isfile(
            os.path.join(PRE, r"src\main\resources\data\potato_s_t\worldgen", rel)) else b""
        if b.startswith(b"\xef\xbb\xbf"):
            fmt.append(rel + u"(有 BOM)")
        # ⚠ 这三份世界生成 JSON **本来就是 CRLF**（.gitattributes 是 `* -text`，git 不会替你转）；
        #   判据是"换行风格与改前**一模一样**"，而不是"必须纯 LF"（第一版按纯 LF 判 ⇒ 三份全假红）。
        if old_b and endings(b) != endings(old_b):
            fmt.append(rel + u"(换行风格变了 %s → %s)" % (endings(old_b), endings(b)))
        if old_b and b.endswith(b"\n") != old_b.endswith(b"\n"):
            fmt.append(rel + u"(结尾换行状态变了)")
        try:
            json.loads(b.decode("utf-8"))
        except Exception as exc:
            fmt.append(rel + u"(解析失败 %s)" % exc)
    check(not fmt, u"A6 三份 JSON：可解析 / 无 BOM / 换行风格与改前一致（这三份本来就是 CRLF、结尾无换行）",
          u"%s" % fmt)

    bm = json.loads(read(BM))
    feats = bm.get("features", [])
    check(len(feats) == 9 and u"potato_s_t:ore_silver_placed" in feats
          and u"potato_s_t:ore_aluminum_placed" in feats and bm.get("step") == "underground_ores",
          u"A7 biome modifier 仍把 9 条矿脉加进 underground_ores（银/铝都在）",
          u"%d 条" % len(feats))

    print(u"--- B 真开服探针报告")
    rep = read(REPORT)
    check(bool(rep), u"B1 探针报告存在（%s）" % os.path.basename(REPORT))
    if rep:
        check(u"ALL OK" in rep and not re.search(u"(?m)^\\s*\\[FAIL\\]", rep),
              u"B2 探针全项 ALL OK（报告里一条 FAIL 都没有）")
        bad = [c for c in PROBE_OK if not re.search(u"(?m)^\\s*\\[OK\\]\\s+%s\\b" % c, rep)]
        check(not bad, u"B3 探针 A1~A7 逐条 OK（注册表现查：size/count/targets/高度/负对照）",
              u"缺/红：%s" % u",".join(bad))

    print(u"--- C 文档与成品")
    doc, hand, ann = read(DOC), read(HAND), read(ANN)
    check(u"### 4.168" in doc, u"C1 档案 §4.168 一节")
    check(u"| ZF160 |" in doc, u"C2 档案 §5 有 ZF160 行")
    check(u"## New in 0.13 ZF160" in ann, u"C3 英文公告有 ZF160 那一条")
    check(u"ZF160" in hand, u"C4 交接文档提到 ZF160")
    jar = os.path.join(ROOT, u"release", u"PotatoST-0.13.jar")
    if os.path.isfile(jar):
        h = hashlib.sha1(raw(jar)).hexdigest()
        z = zipfile.ZipFile(jar)
        jc = json.loads(z.read(u"data/potato_s_t/worldgen/configured_feature/ore_silver.json").decode("utf-8"))
        jp = json.loads(z.read(u"data/potato_s_t/worldgen/placed_feature/ore_silver_placed.json").decode("utf-8"))
        ja = json.loads(z.read(u"data/potato_s_t/worldgen/placed_feature/ore_aluminum_placed.json").decode("utf-8"))
        jcount = [s.get("count") for s in jp.get("placement", []) if s.get("type") == "minecraft:count"]
        jacount = [s.get("count") for s in ja.get("placement", []) if s.get("type") == "minecraft:count"]
        check(jc.get("config", {}).get("size") == 10 and jcount == [12] and jacount == [10],
              u"C5 **jar 里**那三个数也是新值（银 size 10 / 银 count 12 / 铝 count 10）",
              u"jar: silver.size=%s silver.count=%s alum.count=%s"
              % (jc.get("config", {}).get("size"), jcount, jacount))
        check(h in ann and h in hand, u"C6 成品哈希三处联动（公告 + 交接）", h[:12])
    else:
        print(u"  [SKIP] release\\PotatoST-0.13.jar 不在（C5/C6 打包后再跑）")

    print("=" * 78)
    print(u"通过 %d 项 / 失败 %d 项" % (passed, failed))
    for f in fails:
        print(u"  !! " + f)
    return 1 if failed else 0


if __name__ == u"__main__":
    sys.exit(main())
