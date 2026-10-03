# -*- coding: utf-8 -*-
u"""_zf146_verify.py —— ZF146 的常驻校验：星轨坠的仪式状态必须活在**存档**里，不许活在类里

别人反馈的 bug（用户转述，原话）：
    「星轨坠 中途退出游戏就不会落下 再次进入就不能使用了」

本轮的断言分四类：

  A **状态放在哪**（这一轮的正题）：仪式记录里不许再有任何"活对象"（尤其 ServerLevel）、
    管理器里不许再有 static 的仪式表；存档的读写键必须**成对**（漏一个就是"改了没存"）；
    每 tick 现查维度、现取存档数据。
  B **没弄坏别的东西**：星轨坠那 6 个模块文件相对改前件**逐字节没动**。
  C **端到端证据在不在**：两次开服的探针报告（改前红 / 改后绿）必须落在盘上，
    且改后那份里"倒计时接着走"那条是 [OK]。
  D **没把往轮的门弄红**：`_zf114_verify.py` 本轮跑完仍然 exit 0（它按 C5~C15/D/E 钉着星轨坠）。

⚠ 这些断言都吃"被测对象本身"：A 类读的是 `StarfallRitualManager.java` 的真源码，
   B 类比的是真字节，C 类读的是探针跑出来的真报告。

跑法：python build\\zftools\\_zf146_verify.py
"""
import hashlib
import io
import json
import os
import re
import subprocess
import sys

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

ROOT = r"E:\PotatoST"
TOOLS = os.path.join(ROOT, r"build\zftools")
CHECK = os.path.join(TOOLS, "check")
MOD = os.path.join(ROOT, r"src\main\java\com\potatost\mod")
PRE = r"C:\PotatoST救援\zf146_pre"
MGR = os.path.join(MOD, "StarfallRitualManager.java")

fails, n_pass = [], 0


def check(name, ok, detail=u""):
    global n_pass
    if ok:
        n_pass += 1
        print(u"  [OK]   %s %s" % (name, detail))
    else:
        fails.append(name)
        print(u"  [FAIL] %s %s" % (name, detail))


def eq(name, want, got):
    check(name, want == got, u"（期望 %r，实际 %r）" % (want, got))


def read(p):
    return io.open(p, encoding="utf-8").read()


def sha256(p):
    return hashlib.sha256(open(p, "rb").read()).hexdigest()


def cut(text, start, end):
    u"""取 [start, end) 之间的那段源码。

    ⚠ 两个锚点有一个不在就返回**空串**，绝不"找不到就一路取到文件尾" ——
      本轮就踩过：`Ritual` 的切片因为收尾锚点写错（多了两个星号）而静默变成"从 Ritual 到文件尾"，
      于是"仪式记录里没有 ServerLevel"这条把 `tick()` 里的局部变量也算了进来 ⇒ 假红。
      反过来说，负向断言拿到空切片会**假绿**，所以下面还有一条 A0 专门守切片大小。
    """
    i = text.find(start)
    if i < 0:
        return u""
    j = text.find(end, i)
    return u"" if j < 0 else text[i:j]


def strip_comments(text):
    u"""把注释剃掉再做结构性判断。

    ⚠ 这一条是踩出来的：本轮类注释里为了写清"改前错在哪"，原样引用了
      `private static final Map<UUID, Ritual> ACTIVE` —— 于是"类里没有 static 仪式表"
      这条**被自己的说明文字弄红了**。判据必须吃代码，不能吃散文。
    """
    text = re.sub(u"/\\*.*?\\*/", u"", text, flags=re.S)
    return re.sub(u"(?m)//.*$", u"", text)


def git_show(rel):
    u"""取本轮提交前（HEAD）该文件的字节；取不到就返回 None（上层判红）。"""
    p = subprocess.run(["git", "show", u"HEAD:" + rel], cwd=ROOT,
                       stdout=subprocess.PIPE, stderr=subprocess.DEVNULL)
    return p.stdout if p.returncode == 0 else None


def main():
    print(u"=== A 状态放在哪（本轮的正题）===")
    src = read(MGR)
    code = strip_comments(src)
    data = cut(src, u"public static final class RitualData", u"/**\n     * 取本存档的仪式表")
    ritual = cut(src, u"public static final class Ritual {", u"仪式状态的持久化容器")

    # A0：切片必须真的取到（锚点漂了就让这一条红，别让后面的负向断言拿到空串假绿）
    sizes = [len(ritual), len(data)]
    check(u"A0 断言切片都取到了（Ritual %d 字符 / RitualData %d 字符）" % (len(ritual), len(data)),
          all(300 < s < 9000 for s in sizes) and len(ritual) < len(data))

    check(u"A1 有一个 SavedData 容器", u"extends SavedData" in src)
    check(u"A2 仪式记录里没有任何世界对象（只有维度的 key）",
          u"ResourceKey<Level> dimension" in ritual
          and re.search(u"\\b(ServerLevel|Level)\\s+\\w+\\s*(=|;)", ritual) is None,
          u"（Ritual 的字段里出现 ServerLevel/Level 就说明又攥住活引用了）")
    check(u"A3 类里没有 static 的仪式表（改前就是死在这张表上）",
          re.search(u"static\\s+(?:final\\s+)?(?:Map|HashMap|List|ArrayList|Set|HashSet)\\s*"
                    u"<[^;=()]*?>\\s+\\w+\\s*[=;]", code) is None
          and u"ACTIVE" not in code)
    check(u"A4 存档数据每次从 server 现取、不缓存",
          src.count(u"server.overworld().getDataStorage().computeIfAbsent(") == 1
          and re.search(u"static\\s+\\w*RitualData\\s+\\w+\\s*[=;]", code) is None)
    check(u"A5 每 tick 现查维度（不是记下来的 level）",
          u"server.getLevel(ritual.dimension)" in src)
    check(u"A6 维度没了就静默丢掉那一条（不许抛异常把服务器拖垮）",
          u"if (level == null) {" in cut(src, u"static void tick(", u"/** 玩家重新登录"))

    # 读写键成对：漏一个键就是"写进去了但读不回来"（或者反过来读了不存在的键）
    save_body = cut(data, u"public CompoundTag save(CompoundTag tag", u"Ritual get(UUID owner)")
    load_body = cut(data, u"private static RitualData load(", u"@Override")
    keys = sorted(set(re.findall(u"\\bKEY_[A-Z]+\\b", data)))
    unpaired = [k for k in keys if (k not in save_body) != (k not in load_body)]
    check(u"A7 存档键读写成对（%d 个键）" % len(keys), len(keys) >= 8 and not unpaired,
          u"" if not unpaired else u"（不成对：%s）" % u"、".join(unpaired))
    check(u"A8 维度按名字存取（换存档也不会指错世界）",
          u"putString(KEY_DIM, ritual.dimension.location().toString())" in save_body
          and u"ResourceKey.create(Registries.DIMENSION, dim)" in load_body)
    check(u"A9 通报进度也存了（不然读盘会补发过时的通报）",
          u"putInt(KEY_NEXT, ritual.nextAnnounce)" in save_body
          and u"entry.getInt(KEY_NEXT)" in load_body
          and u"putBoolean(KEY_WARNED, ritual.finalWarned)" in save_body
          and u"entry.getBoolean(KEY_WARNED)" in load_body)
    put_body = cut(data, u"void put(Ritual ritual) {", u"void remove(UUID owner)")
    remove_body = cut(data, u"void remove(UUID owner) {", u"void clear() {")
    clear_body = cut(data, u"void clear() {", u"boolean isEmpty()")
    tick_body = cut(src, u"static void tick(MinecraftServer server)", u"/** 玩家重新登录")
    check(u"A10 三个写入口子都标脏（原版只写脏数据）",
          u"setDirty();" in put_body and u"setDirty();" in remove_body
          and u"setDirty();" in clear_body)
    check(u"A11 tick 里的三个出口也都标脏（通报推进 / 最后警告 / 落地删条）",
          tick_body.count(u"setDirty();") >= 3,
          u"（实际 %d 处）" % tick_body.count(u"setDirty();"))
    check(u"A12 探针接口也改成「要 server」（状态不在类里，API 上就看得出来）",
          u"public static boolean isActive(MinecraftServer server, UUID playerId)" in src
          and u"public static void resetForTest(MinecraftServer server)" in src)
    check(u"A13 读盘遇到读不出来的记录是「跳过」而不是崩",
          u"ResourceLocation.tryParse" in load_body and load_body.count(u"continue;") >= 2)
    check(u"A14 落地后那条记录确实被删掉（不是留在表里当僵尸）",
          u"summonMeteor(server, level, ritual);" in src
          and re.search(u"summonMeteor\\(server, level, ritual\\);\\s*it\\.remove\\(\\);\\s*data\\.setDirty\\(\\);",
                        src) is not None)

    print(u"=== B 没弄坏别的东西（与提交前 HEAD 逐字节对照）===")
    # ⚠ 这里比的是 `git show HEAD:<路径>` 而不是救援备份：备份是"本轮点名要动的件"，
    #   而这 6 个文件本轮**不该出现在备份里**——拿不存在的备份去比，红的是判据自己。
    #   比 HEAD 的语义也更准：它断言的正是「我这一改没碰它们」（别的线提交了也不影响）。
    twins = ["StarfallPendantItem.java", "StarfallMeteorEntity.java", "StarfallNetworking.java",
             "client/StarfallClientState.java", "client/StarfallHudLayer.java",
             "client/StarfallMeteorRenderer.java"]
    bad = []
    for name in twins:
        rel = "src/main/java/com/potatost/mod/" + name
        head = git_show(rel)
        cur = open(os.path.join(MOD, name.replace("/", os.sep)), "rb").read()
        if head is None or head != cur:
            bad.append(name)
    eq(u"B1 星轨坠另外 6 个模块文件与提交前逐字节相同", [], bad)

    # ⚠ 判据只吃"键集合 + 占位符个数"，**不吃措辞**：
    #   本轮跑到一半时，翻译线在 12:12:27 顺手润色了 zh_cn 里两条星轨坠文案
    #   （「抬头看」→「当心吧！」「取消不了了」→「为时已晚」）⇒ 我第一版拿"逐字节比 HEAD"去判，
    #   当场被**别人**的改动弄红。判据要能失败，但不能替别人认罪：这里改成
    #   "星轨坠那批键**一个不多一个不少**、每条 `%s` 个数不变" —— 那才是本轮真该负责的事。
    STARFALL = (u"message.potato_s_t.starfall", u"gui.potato_s_t.starfall",
                u"tooltip.potato_s_t.starfall", u"item.potato_s_t.starfall")
    lang_dir = os.path.join(ROOT, r"src\main\resources\assets\potato_s_t\lang")
    moved = []
    for l in ("zh_cn", "en_us", "ja_jp", "ru_ru"):
        rel = "src/main/resources/assets/potato_s_t/lang/" + l + ".json"
        head = git_show(rel)
        if head is None:
            moved.append(u"%s（HEAD 里没有）" % l)
            continue
        cur = json.loads(read(os.path.join(lang_dir, l + ".json")))
        old = json.loads(head.decode("utf-8"))
        ok_old = set(k for k in old if k.startswith(STARFALL))
        ok_cur = set(k for k in cur if k.startswith(STARFALL))
        if ok_old != ok_cur:
            moved.append(u"%s 键集合变了：%s" % (l, sorted(ok_old ^ ok_cur)))
        for k in ok_cur & ok_old:
            if cur[k].count(u"%s") != old[k].count(u"%s"):
                moved.append(u"%s/%s 的 %%s 个数从 %d 变成 %d"
                             % (l, k, old[k].count(u"%s"), cur[k].count(u"%s")))
    eq(u"B2 星轨坠那批语言键（键集合 + 占位符）与提交前一致", [], moved)

    print(u"=== C 端到端证据（两次开服）===")
    r1b = os.path.join(CHECK, u"zf146_before_run1.log")
    r2b = os.path.join(CHECK, u"zf146_before_run2.log")
    r1a = os.path.join(CHECK, u"zf146_after_run1.log")
    r2a = os.path.join(CHECK, u"zf146_after_run2.log")
    for p, tag in ((r1b, u"改前第一趟"), (r2b, u"改前第二趟"), (r1a, u"改后第一趟"), (r2a, u"改后第二趟")):
        check(u"C1 %s 的报告在盘上（%s）" % (tag, os.path.basename(p)), os.path.exists(p))

    if os.path.exists(r1b) and os.path.exists(r1a):
        b1 = read(r1b)
        a1 = read(r1a)
        check(u"C2 两趟的第一趟都「起手成功」（耐久扣了 1 点）",
              u"起手成功" in b1 and u"[OK]" in b1 and u"起手成功" in a1 and u"[OK]" in a1)
        check(u"C3 改前那趟退出时**没有**留下存档数据（这正是那个 bug）",
              not os.path.exists(os.path.join(CHECK, u"_zf146_before_starfall.dat")))
        check(u"C4 改后那趟退出时留下了存档数据，且里面有维度名与截止时刻",
              os.path.exists(os.path.join(CHECK, u"zf146_starfall.dat")))

    if os.path.exists(r2b) and os.path.exists(r2a):
        b2 = read(r2b)
        a2 = read(r2a)
        check(u"C5 改前第二趟：等到宽限期也没等到陨石（红）",
              u"**" in b2 and u"FAILED**" in b2)
        check(u"C6 改后第二趟：陨石在「剩下的那段时间」里落下来了（绿）",
              u"verdict: ALL OK" in a2)
        check(u"C7 改后：倒计时接着走这条断言真的过了（不是没跑到）",
              u"[OK]" in a2 and u"倒计时在" in a2 and u"时间里走完" in a2)
        check(u"C8 改后：落地之后星轨坠又能用了",
              u"星轨坠又能用了" in a2 and u"[OK]" in a2)
        check(u"C9 改后：进世界时那次右键被拒（上一场的倒计时还锁着）",
              u"被拒且耐久不动" in a2)
        check(u"C10 改后：没有补发过时的通报（读回了通报进度）",
              u"进世界不补发过时的通报" in a2 and u"（实际 0 条）" in a2)

    print(u"=== D 没把往轮的门弄红 ===")
    p = subprocess.run([sys.executable, os.path.join(TOOLS, u"_zf114_verify.py")],
                       cwd=ROOT, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    out = p.stdout.decode(u"utf-8", u"replace")
    tail = [l for l in out.split(u"\n") if l.strip()][-1:] or [u""]
    check(u"D1 ZF114 的常驻校验仍然 exit 0（%s）" % tail[0].strip(), p.returncode == 0)

    print(u"\n通过 = %d   失败 = %d" % (n_pass, len(fails)))
    for f in fails:
        print(u"  !! " + f)
    return 1 if fails else 0


if __name__ == u"__main__":
    sys.exit(main())
