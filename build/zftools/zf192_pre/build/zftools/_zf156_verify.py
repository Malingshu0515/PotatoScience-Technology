# -*- coding: utf-8 -*-
r'''_zf156_verify.py —— ZF156（0.13）**常驻校验**：三个小修。
  A ① 端子连线：区块卸载不再断对端 / 真挖掉仍然断 / 原版调用顺序（反编译源）
  B ② 手册只发一次：附件 + copyOnDeath + 注册 + 老标记只读迁移
  C ③ 金属板：配方原料改成 #c:plates/*、产物一字未动、标签收得住自家板
  D 版本与文档：0.13 / §4.164 / §5 行 / §9 / 英文公告 / 交接
  E 探针报告：真开服那 20 来项（含负对照）

跑法：python build\zftools\_zf156_verify.py
'''
import hashlib
import io
import json
import os
import re
import sys

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding=u"utf-8", errors="replace")

ROOT = r"E:\PotatoST"
JAVA = os.path.join(ROOT, "src", "main", "java", "com", "potatost", "mod")
RES = os.path.join(ROOT, "src", "main", "resources")
DATA = os.path.join(RES, "data", "potato_s_t")
RECIPE = os.path.join(DATA, "recipe")
ZT = os.path.join(ROOT, "build", "zftools")
PRE = os.path.join(r"C:\PotatoST救援", "zf156_pre")
DOC = os.path.join(ROOT, "docs", "开发档案.md")
HAND = os.path.join(ROOT, "docs", "多会话协作交接.md")
ANN = os.path.join(ROOT, "docs", "UpdateAnnouncement_EN.md")
REPORT = os.path.join(ZT, u"_zf156_probe_utf8.txt")
SRC = os.path.join(ROOT, r"build\neoForm\neoFormJoined1.21.1-20240808.144430\steps\transformSource\transformed")

METALS = [u"aluminum", u"cobalt", u"copper", u"iron", u"nickel", u"silver", u"steel"]
PROBE_OK = [u"A1", u"A2", u"A3", u"A4", u"A5", u"B1", u"B2", u"B3", u"B4", u"B5", u"B6", u"B7",
            u"C1", u"C2", u"C3", u"C4", u"C5", u"C6", u"C7", u"C8"]

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
    return io.open(p, encoding=u"utf-8", errors=u"replace").read() if os.path.isfile(p) else u""


def raw(p):
    with open(p, "rb") as fh:
        return fh.read()


def code_has(text, needle):
    """只看**代码行**：整行注释、块注释行、或 needle 前面就是 `//` 的，一律不算。

    ⚠ 这个口径是反证刀 K3/K4/K6 逼出来的：第一版的判据是纯 `in`，
    于是"把那一行**注释掉**"（`// other.removeConnection(...)`）照样能骗过门 ——
    注释里还留着那段字面量。门要判的是"这行代码在不在"，不是"这段字在不在"。
    """
    for line in text.splitlines():
        s = line.strip()
        if s.startswith(u"//") or s.startswith(u"*") or s.startswith(u"/*"):
            continue
        i = line.find(needle)
        if i < 0:
            continue
        if u"//" in line[:i]:
            continue
        return True
    return False


def sha1(p):
    return hashlib.sha1(raw(p)).hexdigest()


def recipe_files():
    out = []
    for dirpath, _d, filenames in os.walk(RECIPE):
        for fn in filenames:
            if fn.endswith(u".json"):
                out.append(os.path.join(dirpath, fn))
    return out


def main():
    java_terminal = read(os.path.join(JAVA, u"TerminalBlockEntity.java"))
    java_guide = read(os.path.join(JAVA, u"GuideBook.java"))
    java_attach = read(os.path.join(JAVA, u"ModAttachments.java"))
    java_main = read(os.path.join(JAVA, u"PotatoST.java"))

    print("=" * 78)
    print(u"_zf156_verify.py —— ZF156 / 0.13：① 端子连线 ② 手册只发一次 ③ 金属板跨 mod")
    print("=" * 78)

    # ---------------- A 端子 ----------------
    print(u"--- A ① 端子连线不再因区块卸载被断开")
    check(code_has(java_terminal, u"public void onChunkUnloaded()"),
          u"A1 TerminalBlockEntity 覆写了 onChunkUnloaded（区块卸载的判据）")
    check(code_has(java_terminal, u"this.unloadedWithChunk = true;"),
          u"A2 onChunkUnloaded 里把卸载标记置真")
    i_flag = java_terminal.find(u"if (this.unloadedWithChunk) {")
    i_side = java_terminal.find(u"if (level != null && !level.isClientSide) {")
    check(i_flag > 0 and i_side > 0 and i_flag < i_side,
          u"A3 setRemoved 里「卸载早退」排在 isClientSide 判断**之前**（客户端重收区块包也走这条路）",
          u"flag@%d side@%d" % (i_flag, i_side))
    check(code_has(java_terminal, u"other.removeConnection(this.getBlockPos());")
          and code_has(java_terminal, u"other.removePowerConnection(this.getBlockPos());"),
          u"A4 真被挖掉时**仍然**通知对端断开（FE + 动力两条都在）")
    # 反编译源（不在盘上就跳过，不算失败）
    lc = os.path.join(SRC, r"net\minecraft\world\level\chunk\LevelChunk.java")
    if os.path.isfile(lc):
        t = read(lc)
        i_un = t.find(u"BlockEntity::onChunkUnloaded")
        i_rm = t.find(u"BlockEntity::setRemoved")
        check(i_un > 0 and i_rm > 0 and i_un < i_rm,
              u"A5 反编译源：clearAllBlockEntities 先 onChunkUnloaded 再 setRemoved（本修法的地基）")
        sl = os.path.join(SRC, r"net\minecraft\server\level\ServerLevel.java")
        check(u"clearAllBlockEntities();" in read(sl),
              u"A6 反编译源：ServerLevel.unload 走的就是 clearAllBlockEntities（区块卸载那条路）")
    else:
        print(u"  [SKIP] 反编译源不在盘上（A5/A6 跳过）")

    # ---------------- B 手册 ----------------
    print(u"--- B ② 手册只发一次（附件 + copyOnDeath）")
    check(bool(java_attach), u"B1 新建 ModAttachments.java")
    check(code_has(java_attach, u"NeoForgeRegistries.Keys.ATTACHMENT_TYPES"),
          u"B2 附件表挂在 NeoForge 的 ATTACHMENT_TYPES 注册表上")
    check(code_has(java_attach, u".copyOnDeath()"),
          u"B3 声明了 copyOnDeath（死后重生也要带走 —— 没这句就会在死亡那次丢掉）")
    check(code_has(java_attach, u".serialize(Codec.BOOL)"),
          u"B4 有序列化器（copyOnDeath 要求先有 serializer，否则构造期直接抛）")
    check(code_has(java_attach, u'register("guide_given"'), u"B5 附件 id = guide_given")
    check(code_has(java_main, u"ModAttachments.ATTACHMENT_TYPES.register(modEventBus);"),
          u"B6 PotatoST 构造期把附件表注册进模组总线（§4.72 那类雷）")
    check(not code_has(java_guide, u"getPersistentData().putBoolean"),
          u"B7 GuideBook 不再往玩家持久化数据里写标记（那是会被克隆丢掉的旧机制）")
    check(code_has(java_guide, u"public static boolean shouldGive(ServerPlayer player)"),
          u"B8 「该不该发」抽成公开纯判据（探针不必真登录就能验）")
    check(code_has(java_guide, u"hasLegacyMark"),
          u"B9 0.12 老标记仍被读（老存档已经拿过书的不再补发）")
    check(code_has(java_guide, u"ModAttachments.markGiven(player);"),
          u"B10 发书那条路改走附件写入口")

    # ---------------- C 金属板 ----------------
    print(u"--- C ③ 金属板原料改挂 c:plates/*")
    item_pat = re.compile(u'"item"\\s*:\\s*"potato_s_t:(?:' + u"|".join(METALS) + u')_plate"')
    tag_pat = re.compile(u'"tag"\\s*:\\s*"c:plates/(?:' + u"|".join(METALS) + u')"')
    id_pat = re.compile(u'"id"\\s*:\\s*"potato_s_t:(?:' + u"|".join(METALS) + u')_plate"')
    n_item = n_tag = n_id = 0
    files_tag = []
    bad_fmt = []
    others_cr = []
    for p in recipe_files():
        t = read(p)
        n_item += len(item_pat.findall(t))
        k = len(tag_pat.findall(t))
        n_tag += k
        n_id += len(id_pat.findall(t))
        if k:
            files_tag.append(os.path.relpath(p, RECIPE))
        try:
            json.loads(t)
        except Exception as exc:
            bad_fmt.append(u"%s 解析失败 %s" % (os.path.relpath(p, RECIPE), exc))
        b = raw(p)
        # ⚠ 只对本轮动过的 21 份判"无 BOM / 纯 LF"：盘上**本来**就有两份别人留下的
        #   CRLF 配方（copper_wire_spool / power_cable_spool，HEAD 里就是 CRLF），
        #   那不是本轮的账 —— 这里只列出来当情报，不判红（§4.147 同族的"别把别人的账算自己头上"）。
        if b.startswith(b"\xef\xbb\xbf") or b"\r" in b:
            if k:
                bad_fmt.append(u"%s 有 BOM 或 CR" % os.path.relpath(p, RECIPE))
            else:
                others_cr.append(os.path.relpath(p, RECIPE))
    props_b = raw(os.path.join(ROOT, u"gradle.properties"))
    if props_b.startswith(b"\xef\xbb\xbf") or b"\r" in props_b:
        bad_fmt.append(u"gradle.properties 有 BOM 或 CR")
    check(n_item == 0, u"C1 配方里「写死自家板当原料」的地方 = 0", u"实际 %d 处" % n_item)
    check(n_tag == 28, u"C2 「#c:plates/<金属>」原料 = 28 处 / 20 份（ZF162 删掉电力高炉那条配方时少了 1 处）", u"实际 %d 处 / %d 份" % (n_tag, len(files_tag)))
    check(n_id == 7, u"C3 液压机那 7 份产出**一字未动**（仍是自家板 id）", u"实际 %d 处" % n_id)
    check(not bad_fmt, u"C4 本轮改过的配方 JSON：可解析 / 无 BOM / 纯 LF（.gitattributes `* -text`）",
          u"; ".join(bad_fmt[:2]))
    if others_cr:
        print(u"  [INFO] 盘上还有 %d 份**别人留下的** CRLF 配方（HEAD 里就是 CRLF，不是本轮的账）：%s"
              % (len(others_cr), u", ".join(others_cr[:4])))
    tag_dir = os.path.join(RES, r"data\c\tags\item\plates")
    missing = [m for m in METALS if not os.path.isfile(os.path.join(tag_dir, u"%s.json" % m))]
    check(not missing, u"C5 7 张 c:plates/<金属> 标签都在（否则改完直接是死配方）", u"缺 %s" % missing)
    not_in = []
    for m in METALS:
        vals = json.loads(read(os.path.join(tag_dir, u"%s.json" % m))).get("values", [])
        if u"potato_s_t:%s_plate" % m not in vals:
            not_in.append(m)
    check(not not_in, u"C6 每张标签都收着自家那块板", u"没收 %s" % not_in)
    g = subprocess_gate()
    check(g == 0, u"C7 另一条线的 `_zf152_plates_gate.py`（我们的板进别人的配方）仍然全过",
          u"退出码 %s" % g)

    # ---------------- D 版本与文档 ----------------
    print(u"--- D 版本线与文档")
    props = read(os.path.join(ROOT, u"gradle.properties"))
    check(u"mod_version=0.13" in props, u"D1 gradle.properties 的 mod_version = 0.13")
    check(len(re.findall(u"mod_version=", props)) == 1, u"D2 全工程唯一一处版本号仍在 gradle.properties")
    toml = read(os.path.join(RES, u"META-INF/neoforge.mods.toml"))
    check(u'version="${mod_version}"' in toml, u"D3 neoforge.mods.toml 仍引用 ${mod_version}")
    doc = read(DOC)
    check(u"### 4.164" in doc, u"D4 档案 §4.164 一节")
    check(u"| ZF156 |" in doc, u"D5 档案 §5 ZF156 一行")
    check(u"ZF156" in doc.split(u"§9")[-1] or u"ZF156" in doc, u"D6 档案提到 ZF156（§9 用户测试）")
    check(u"## New in 0.13 ZF156" in read(ANN), u"D7 英文公告有 0.13 ZF156 条目")
    check(u"ZF156" in read(HAND), u"D8 交接文档提到 ZF156")
    jar13 = os.path.join(ROOT, u"release", u"PotatoST-0.13.jar")
    if os.path.isfile(jar13):
        h = sha1(jar13)
        ann = read(ANN)
        hand = read(HAND)
        gate149 = read(os.path.join(ZT, u"_zf149_verify.py"))
        check(h in ann, u"D9 成品 sha1 写进英文公告", h[:12])
        check(h in hand, u"D10 成品 sha1 写进交接文档", h[:12])
        check(h in gate149, u"D11 成品 sha1 写进 _zf149_verify.py（三处联动）", h[:12])
    else:
        print(u"  [SKIP] release\\PotatoST-0.13.jar 还没打（D9~D11 打包后再跑）")

    # ---------------- E 探针 ----------------
    print(u"--- E 真开服探针报告")
    rep = read(REPORT)
    check(bool(rep), u"E1 探针报告存在（%s）" % os.path.basename(REPORT))
    if rep:
        # ⚠ 判据修正（第一版在这里写错了）：探针**写进报告的**是 `  [OK]   A2 …`
        #   （`[A156] ` 那个前缀只打在 stdout 上）—— 第一版按 `[A156] [OK] A2` 去 match，
        #   整个 E3 组会全红，而"全红"看起来像"探针挂了"。活体反证的刀先咬出来的就是这个。
        check(u"ALL OK" in rep and not re.search(u"(?m)^\\s*\\[FAIL\\]", rep),
              u"E2 探针全项 ALL OK（报告里一条 FAIL 都没有）")
        bad = []
        for code in PROBE_OK:
            if not re.search(u"(?m)^\\s*\\[OK\\]\\s+%s\\b" % code, rep):
                bad.append(code)
        check(not bad, u"E3 探针 %d 项逐条 OK（A 端子 / B 手册 / C 金属板）" % len(PROBE_OK),
              u"缺/红：%s" % u",".join(bad))

    print("=" * 78)
    print(u"通过 %d 项 / 失败 %d 项" % (passed, failed))
    for f in fails:
        print(u"  !! " + f)
    return 1 if failed else 0


def subprocess_gate():
    import subprocess
    p = os.path.join(ZT, u"_zf152_plates_gate.py")
    if not os.path.isfile(p):
        return 0
    r = subprocess.run([sys.executable, p], stdout=subprocess.PIPE, stderr=subprocess.STDOUT, timeout=300)
    return r.returncode


if __name__ == u"__main__":
    sys.exit(main())
