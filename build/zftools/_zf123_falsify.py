# -*- coding: utf-8 -*-
u"""_zf123_falsify.py —— ZF123 的反证刀（K178~K182，5 把）

口径同前：基线绿 → 改一处语义 ⇒ 门必须 FAIL 且**咬住指定的那一条**（串必须出现在以 `!!`
开头的 FAIL 行里）⇒ 逐字节还原 ⇒ 收尾回到全绿。

刀面：
  · 把补上的 `case "lithium_battery_plant"` 再删掉（**复现用户 2026-09-25 22:19 遇到的那一场**）；
  · 把 `registerCategories` 的兜底撤掉（空 icon 又直接喂给 JEI ⇒ 一崩全没）；
  · 把 `registerRecipeCatalysts` 的兜底撤掉（第二处同样的雷）；
  · 把 zh_cn 里 `star_steel_ingot` 的名字改成英文（用户报的"只有英文名"那一档）；
  · 只从 zh_cn 删掉那个键（四语言键集合不一致 ⇒ 切语言后看到原始 key）。
"""
import hashlib
import io
import os
import subprocess
import sys

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

ROOT = r"E:\PotatoST"
ZT = os.path.join(ROOT, r"build\zftools")
JEI = os.path.join(ROOT, r"src\main\java\com\potatost\mod\client\jei\PotatoSTJeiPlugin.java")
ZH = os.path.join(ROOT, r"src\main\resources\assets\potato_s_t\lang\zh_cn.json")
VERIFY = os.path.join(ZT, u"_zf123_verify.py")

CASE_LINE = u'''            case "lithium_battery_plant" -> new ItemStack(ModBlocks.LITHIUM_BATTERY_PLANT_ITEM.get());
'''
BOOL = u'''            ItemStack icon = iconFor(machine);
            if (icon.isEmpty()) {
                LOGGER.error("[potato_s_t] JEI SKIPPED '{}': iconFor() 没有这一台的 case（返回了空物品）"
                        + " —— 补 PotatoSTJeiPlugin.iconFor 的 switch，否则这一台在 JEI 里搜不到", machine);
                skipped.add(machine);
                continue;
            }
'''
CAT = u'''            ItemStack icon = iconFor(machine);
            if (icon.isEmpty()) {
                LOGGER.error("[potato_s_t] JEI catalyst SKIPPED '{}'（iconFor 空物品）", machine);
                continue;
            }
'''

KNIVES = [
    dict(id="K178", why=u"**复现用户遇到的那一场**：把锂电机的 icon case 再删掉",
         path=JEI, old=CASE_LINE, new=u"",
         expect=u"每一台机器都有 icon case"),
    dict(id="K179", why=u"撤掉 registerCategories 的兜底（空 icon 又直接喂给 JEI ⇒ 一崩全没）",
         path=JEI, old=BOOL, new=u"",
         expect=u"registerCategories 里空 icon ⇒ 只跳过这一台"),
    dict(id="K180", why=u"撤掉 registerRecipeCatalysts 的兜底（第二处同样的雷）",
         path=JEI, old=CAT, new=u"",
         expect=u"registerRecipeCatalysts 也有同一道兜底"),
    dict(id="K181", why=u"把 zh_cn 里星璨钢锭的名字改成英文（用户报的那一档）",
         path=ZH, mode="resub",
         # ⚠ 用正则而不是字面量：这一行的缩进/冒号后空格被别的脚本改过两次（2 空格 → 4 空格），
         #   写死字面量的刀会在别人重排格式后"锚点命中 0 次"（K181 第一版就是这么假红的）。
         old_re=u'("item\\.potato_s_t\\.star_steel_ingot"\\s*:\\s*)"星璨钢锭"',
         new_re=u'\\1"Star Steel Ingot"',
         expect=u"zh_cn 里 star_steel_ingot 的名字 = 星璨钢锭"),
    dict(id="K182", why=u"只从 zh_cn 删掉星璨钢锭那个键（四语言键集合不一致）",
         path=ZH, mode="line", old=u'"item.potato_s_t.star_steel_ingot":',
         expect=u"体检全绿"),
]

fails = []


def run():
    try:
        r = subprocess.run([sys.executable, VERIFY], stdout=subprocess.PIPE,
                           stderr=subprocess.STDOUT, timeout=300)
        return r.returncode, r.stdout.decode("utf-8", "replace")
    except subprocess.TimeoutExpired:
        return 99, u"**超时**"


def summary(out):
    line = [l for l in out.split(u"\n") if u"通过" in l and u"失败" in l]
    return line[-1].strip() if line else u"?"


def bitten(out, expect):
    return any(l.strip().startswith(u"!!") and expect in l for l in out.split(u"\n"))


def main():
    rc, out = run()
    print(u"基线：%s（退出码 %d）" % (summary(out), rc))
    if rc != 0:
        print(u"  [STOP] 基线不绿，先修")
        for l in out.split(u"\n"):
            if l.strip().startswith(u"!!"):
                print(u"    " + l.strip())
        return 1
    n_ok = 0
    for k in KNIVES:
        path = k["path"]
        orig = open(path, "rb").read()
        before = hashlib.sha1(orig).hexdigest()
        try:
            if k.get("mode") == "resub":
                import re as _re
                text = orig.decode("utf-8")
                new_text, n_sub = _re.subn(k["old_re"], k["new_re"], text, count=1)
                if n_sub != 1:
                    fails.append(u"%s：正则命中 %d 次" % (k["id"], n_sub))
                    continue
                open(path, "wb").write(new_text.encode("utf-8"))
            elif k.get("mode") == "line":
                text = orig.decode("utf-8")
                lines = [l for l in text.split(u"\n") if not l.strip().startswith(k["old"])]
                if len(lines) == len(text.split(u"\n")):
                    fails.append(u"%s：要删的行没找到" % k["id"])
                    continue
                open(path, "wb").write(u"\n".join(lines).encode("utf-8"))
            else:
                text = orig.decode("utf-8")
                if text.count(k["old"]) != 1:
                    fails.append(u"%s：锚点命中 %d 次" % (k["id"], text.count(k["old"])))
                    continue
                open(path, "wb").write(text.replace(k["old"], k["new"], 1).encode("utf-8"))
            rc, out = run()
        finally:
            open(path, "wb").write(orig)
        after = hashlib.sha1(open(path, "rb").read()).hexdigest()
        if after != before:
            fails.append(u"%s：还原失败" % k["id"])
            break
        if rc != 0 and bitten(out, k["expect"]):
            n_ok += 1
            print(u"  [OK]   %s %s ⇒ 咬住「%s」" % (k["id"], k["why"], k["expect"]))
        else:
            print(u"  [BAD]  %s %s（退出码 %d）" % (k["id"], k["why"], rc))
            fails.append(u"%s %s ⇒ %s" % (k["id"], k["why"],
                                          u"门还是绿的" if rc == 0 else u"咬错了检查"))
    rc, out = run()
    print(u"收尾：%s（退出码 %d）" % (summary(out), rc))
    if rc != 0:
        fails.append(u"收尾不是全绿")
    print(u"刀 = %d，咬住 = %d，失败项 = %d" % (len(KNIVES), n_ok, len(fails)))
    for f in fails:
        print(u"  !! " + f)
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())
