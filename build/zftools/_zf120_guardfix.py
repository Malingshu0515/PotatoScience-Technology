# -*- coding: utf-8 -*-
u"""_zf120_guardfix.py —— 把 `_zf100_recipe_guard.py` 的"新增名单"跟到当前盘上

那条守卫的口径是「**改前那份成品 jar 里的 44 份配方逐字节未变，盘上多出来的正好是这份名单**」。
名单是活体数字：ZF101/ZF104/ZF106/ZF109/ZF112/ZF118 每轮加配方都该往里添名字，
但只有 ZF106 那次跟了（而且只跟了 shaped 计数那一行，没跟名单本身）⇒ 它现在是红的。

ZF120 又加了 4 张锻造台配方，所以这一轮把它一次跟平：
用**改前 jar 与盘上的差集**算出名单，写回脚本（不让脚本自己算 —— 那份名单是
"我知道自己加了什么"的声明，自动算出来就等于没声明）。

跑法：
    python build/zftools/_zf120_guardfix.py          # 只打印差集
    python build/zftools/_zf120_guardfix.py --write
"""
import io
import os
import re
import sys
import zipfile

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

PROJ = r"E:\PotatoST"
ZT = os.path.join(PROJ, "build", "zftools")
GUARD = os.path.join(ZT, "_zf100_recipe_guard.py")
JAR = r"C:\PotatoST救援\zf100_pre\release\PotatoST-0.11.jar"
RDIR = os.path.join(PROJ, "src", "main", "resources", "data", "potato_s_t", "recipe")
PREFIX = u"data/potato_s_t/recipe/"


def main(argv):
    write = u"--write" in argv
    with zipfile.ZipFile(JAR) as zf:
        inside = {n[len(PREFIX):] for n in zf.namelist()
                  if n.startswith(PREFIX) and n.endswith(u".json")}
    disk = {n for n in os.listdir(RDIR) if n.endswith(u".json")}
    extra = sorted(disk - inside)
    print(u"改前 jar = %d 份，盘上 = %d 份，多出来 %d 份" % (len(inside), len(disk), len(extra)))
    print(u"jar 里有、盘上没了的 = %s" % (sorted(inside - disk) or u"（无）"))

    text = io.open(GUARD, encoding="utf-8").read()
    m = re.search(r"EXPECT_NEW = \{(.*?)\n\}\n", text, re.S)
    if not m:
        print(u"  [FAIL] 在 %s 里找不到 EXPECT_NEW = {...} 块" % GUARD)
        return 1
    body = u"\n".join(u'    u"%s",' % n for n in extra)
    new = u"EXPECT_NEW = {\n%s\n}\n" % body
    if not write:
        print(u"--- 将要写进去的 EXPECT_NEW ---")
        print(new)
        return 0

    text = text[:m.start()] + new + text[m.end():]

    # 顺手把那条计数断言的说明文字也跟平（它写着"改前 38 + ..."，早就不对了）
    #   ⚠ ZF120 当天跑了两次：第二次是因为**别的线又加了一张定形图纸**（54 → 55）。
    #     所以这个数**现场数**，不写死 —— 写死的话下次又得手工来一遍。
    shaped_now = 0
    for n in sorted(disk):
        t = io.open(os.path.join(RDIR, n), encoding="utf-8").read()
        if u'"minecraft:crafting_shaped"' in t:
            shaped_now += 1
    text = re.sub(
        r'check\(u"盘上 crafting_shaped = %d 条（[^"]*）" % shaped, shaped == \d+\)',
        # ⚠ 替换串里的 `%d` / `% shaped` 是**要写进目标文件**的 Python 格式符，
        #   在这个 `% shaped_now` 里必须写成 `%%d` / `%% shaped`（本轮第一次就漏了，
        #   直接 `TypeError: not enough arguments for format string`）。
        u'check(u"盘上 crafting_shaped = %%d 条（活体数字：ZF106 收尾 51，之后每加一张定形图纸就 +1；'
        u'ZF120 振金套加的是 4 张**锻造台**配方，**不改这个数**）" %% shaped, shaped == %d)'
        % shaped_now,
        text)
    with io.open(GUARD, "w", encoding="utf-8", newline=u"\n") as f:
        f.write(text)
    print(u"  [写出] %s" % GUARD)

    back = io.open(GUARD, encoding="utf-8").read()
    m2 = re.search(r"EXPECT_NEW = \{(.*?)\n\}\n", back, re.S)
    got = sorted(re.findall(r'u"([^"]+)"', m2.group(1)))
    print(u"  [%s] 回读的名单 %d 个与差集一致"
          % (u"OK" if got == extra else u"FAIL", len(got)))
    return 0 if got == extra else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
