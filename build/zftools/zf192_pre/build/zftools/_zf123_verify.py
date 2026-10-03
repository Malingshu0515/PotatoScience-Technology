# -*- coding: utf-8 -*-
u"""_zf123_verify.py —— ZF123 常驻校验：JEI 那个"一崩全没"的客户端雷（0.11）

用户实测报的两件事：
  ① 「jei看不到合金冶炼炉的配方了」—— 病根 = `PotatoSTJeiPlugin.MACHINES` 12 台，
     `iconFor()` 只有 11 个 case（ZF112 加 `lithium_battery_plant` 时漏了）
     ⇒ 返回空物品 ⇒ JEI 抛异常 ⇒ **整个插件的分类与配方一起被丢弃**。
  ② 「星璨钢貌似还只有英文名称了」—— 盘上四项体检全绿（见 §四），按"待用户补线索"处理。

五段：
  ① 文件账目（改前件 106 份、回读证明、点名件）
  ② **JEI 插件**（MACHINES ↔ iconFor 一一对应、兜底、横幅 —— 本轮的账）
  ③ 历史证据（改前件里那两份客户端日志：前一场绿 / 后一场红 ⇒ 边界 = ZF112 的 22:19 提交）
  ④ 语言体检（直接跑 `_zf123_langaudit.py`：键集合 / 英文值 / 重复键 / 注册 id 全查）
  ⑤ 文档
"""
import glob
import hashlib
import io
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
JEI = os.path.join(ROOT, r"src\main\java\com\potatost\mod\client\jei\PotatoSTJeiPlugin.java")
LANG_AUDIT = os.path.join(TOOLS, u"_zf123_langaudit.py")
DOC = os.path.join(ROOT, r"docs\开发档案.md")
HANDOFF = os.path.join(ROOT, r"docs\多会话协作交接.md")
BK = r"C:\PotatoST救援\zf123_pre"
LOG_OK = os.path.join(BK, r"run\client\logs\2026-09-25-1.log.gz")
LOG_BAD = os.path.join(BK, r"run\client\logs\2026-09-25-2.log.gz")

n_pass = 0
fails = []


def read(p):
    return io.open(p, encoding="utf-8").read()


def check(name, cond, detail=None):
    global n_pass
    if cond:
        n_pass += 1
    else:
        fails.append(name + (u"  ← %s" % detail if detail else u""))


def eq(name, want, got):
    check(name, want == got, u"期望 %r 实际 %r" % (want, got))


def gunzip_text(p):
    u"""读 .log.gz；不在就返回 None（§4.77 族：不许抛栈把校验器搞崩）。"""
    if not os.path.exists(p):
        return None
    try:
        import gzip
        return gzip.open(p, "rt", encoding="utf-8", errors="replace").read()
    except Exception:
        return None


def main():
    jei = read(JEI)

    # ============ ① 文件账目 ============
    print(u"== ① 文件账目 ==")
    check(u"改前件 zf123_pre 在", os.path.isdir(BK))
    n_bk = 0
    if os.path.isdir(BK):
        for _d, _s, _fs in os.walk(BK):
            n_bk += len(_fs)
    check(u"改前件 ≥100 份", n_bk >= 100, u"实际 %d" % n_bk)
    check(u"点名件在改前件里：PotatoSTJeiPlugin.java",
          os.path.exists(os.path.join(BK, r"src\main\java\com\potatost\mod\client\jei\PotatoSTJeiPlugin.java")))
    check(u"两份取证日志都在改前件里",
          os.path.exists(LOG_OK) and os.path.exists(LOG_BAD))

    # ============ ② JEI 插件 ============
    print(u"\n== ② JEI 插件（MACHINES ↔ iconFor）==")
    m = re.search(r"private static final List<String> MACHINES =\s*List\.of\((.*?)\);", jei, re.S)
    check(u"MACHINES 那张表在", m is not None)
    machines = re.findall(r'"([a-z_]+)"', m.group(1)) if m else []
    cases = re.findall(r'case "([a-z_]+)"', jei)
    eq(u"MACHINES 12 台", 12, len(machines))
    eq(u"iconFor 的 case 也是 12 个（一一对应 = 本轮的正题）", 12, len(cases))
    missing = [x for x in machines if x not in cases]
    extra = [x for x in cases if x not in machines]
    eq(u"每一台机器都有 icon case（漏一个 = JEI 全灭）", [], missing)
    eq(u"没有多余的 case", [], extra)
    check(u"ZF112 漏的那个补上了", u'case "lithium_battery_plant"' in jei)
    check(u"MACHINES 与 case 同序（便于人眼对账）",
          [x for x in machines] == [x for x in cases])
    check(u"没有偷偷用 fallback 物品把空 icon 掩盖掉（仍返回 ItemStack.EMPTY）",
          u"default -> ItemStack.EMPTY;" in jei)
    check(u"registerCategories 里空 icon ⇒ 只跳过这一台（记 ERROR）",
          u"JEI SKIPPED '{}'" in jei and u"skipped.add(machine);" in jei
          and u"continue;" in jei)
    check(u"registerCategories 记了 served / skipped 两张表",
          u"List<String> served = new ArrayList<>();" in jei
          and u"List<String> skipped = new ArrayList<>();" in jei)
    check(u"收尾横幅：跳过谁一眼可见",
          u"categories registered, {} SKIPPED" in jei and u"served.size()" in jei)
    check(u"registerRecipeCatalysts 也有同一道兜底",
          u"JEI catalyst SKIPPED" in jei)
    check(u"催化剂那条也用非空 icon（不再直接 iconFor 进 addRecipeCatalyst）",
          u"registration.addRecipeCatalyst(icon, TYPES.get(machine));" in jei)
    check(u"插件 UID 还是 potato_s_t:jei_plugin", u"\"jei_plugin\"" in jei)

    # ============ ③ 历史证据 ============
    print(u"\n== ③ 历史证据（改前件里的两份客户端日志）==")
    ok_txt, bad_txt = gunzip_text(LOG_OK), gunzip_text(LOG_BAD)
    if ok_txt is None or bad_txt is None:
        check(u"两份日志都读得到", False)
    else:
        check(u"2026-09-25-1（22:24 那场）**没有**这个异常（绿）",
              u"Ingredient is invalid" not in ok_txt)
        check(u"2026-09-25-2（22:30 那场）**有**这个异常（红）",
              u"Ingredient is invalid" in bad_txt)
        check(u"异常栈指向 PotatoSTJeiPlugin.registerCategories",
              u"PotatoSTJeiPlugin.registerCategories(PotatoSTJeiPlugin.java:133)" in bad_txt)
        check(u"异常栈指向 registerRecipeCatalysts（第二处）",
              u"registerRecipeCatalysts(PotatoSTJeiPlugin.java:160)" in bad_txt)
        check(u"红的那场里，最后注册成功的分类是 ammonia_synthesis_chamber（锂电前面那台）",
              u"JEI category ammonia_synthesis_chamber" in bad_txt)
        check(u"红的那场里**从来没有**锂电的分类（= 它就是要崩的那台）",
              u"JEI category lithium_battery_plant" not in bad_txt)
        check(u"红的那场里 JEI 抱怨没有注册任何分类（整个插件被丢）",
              u"There is no recipe category registered for" in bad_txt)

    # ============ ④ 语言体检 ============
    print(u"\n== ④ 语言体检（_zf123_langaudit.py）==")
    check(u"体检脚本在", os.path.exists(LANG_AUDIT))
    if os.path.exists(LANG_AUDIT):
        r = subprocess.run([sys.executable, LANG_AUDIT], stdout=subprocess.PIPE,
                           stderr=subprocess.STDOUT, timeout=180)
        out = r.stdout.decode("utf-8", "replace")
        check(u"体检全绿（键集合 / 英文值 / 重复键 / 注册 id 四项）", r.returncode == 0,
              (out.strip().split(u"\n") or [u""])[-1][:120])
    # 真判据：`item.potato_s_t.star_steel_ingot` 在 zh_cn 里必须是**中文**（用户报的"只有英文名"）
    import json as _json
    zh = _json.loads(read(os.path.join(ROOT, r"src\main\resources\assets\potato_s_t\lang\zh_cn.json")))
    en = _json.loads(read(os.path.join(ROOT, r"src\main\resources\assets\potato_s_t\lang\en_us.json")))
    key = u"item.potato_s_t.star_steel_ingot"
    eq(u"zh_cn 里 star_steel_ingot 的名字 = 星璨钢锭", u"星璨钢锭", zh.get(key))
    check(u"它与英文名不同（确实翻译过）", zh.get(key) != en.get(key))

    # ============ ⑤ 文档 ============
    print(u"\n== ⑤ 文档 ==")
    doc = read(DOC)
    hand = read(HANDOFF)
    check(u"档案 §4 有 4.101（客户端插件注册没有探针那条）", u"### 4.101" in doc)
    check(u"档案 §9 有 ZF123 小节", u"### ZF123（0.11）" in doc)
    check(u"档案里记了 ZF112 那个 22:19 的提交", u"0a286b8" in doc)
    check(u"交接文档提到 ZF123", u"ZF123" in hand)
    check(u"交接文档记了 JEI 这口锅的归属（ZF112）", u"JEI" in hand and u"ZF112" in hand)

    print(u"")
    print(u"通过 = %d   失败 = %d" % (n_pass, len(fails)))
    for f in fails:
        print(u"  !! " + f)
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())
