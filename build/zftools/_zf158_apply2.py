# -*- coding: utf-8 -*-
u"""_zf158_apply2.py —— ZF158 第二笔（默认 dry-run）：把生成器表**彻底**跟平，再让生成器重出。

第一笔（`_zf158_apply.py`）跑生成器时暴露了一处更早的债：
  `_zf45_recipes.py` 的 `SMITHING_TEMPLATE` 还写着**下界合金升级模板**，
  而 ZF155 已经把 4 件振金护甲的模板换成了 `potato_s_t:universal_upgrade_template`
  ⇒ `--write` 一跑就把 ZF155 的改动 **revert 掉**（本轮实测：4 份文件当场被改回下界合金）。
本脚本：
  ① 先把那 4 份文件从 `zf158_pre` 备份**逐字节还原**（回 WORKTREE 应有的样子）；
  ② 改生成器：`SMITHING_TEMPLATE` → 通用升级模板，并把那段"保持原版模板不变"的注释改成现行口径；
  ③ 再跑 `--write`；
  ④ 拿整份改动与 `zf158_pre` 的清单对账：**应当只有 `thermal_metal.json` 一份不同**（这就是本轮要改的）。

跑法：python build\\zftools\\_zf158_apply2.py [--write]
"""
import hashlib
import io
import os
import shutil
import subprocess
import sys

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding=u"utf-8", errors="replace")

ROOT = r"E:\PotatoST"
ZT = os.path.join(ROOT, "build", "zftools")
GEN = os.path.join(ZT, u"_zf45_recipes.py")
RECIPE = os.path.join(ROOT, r"src\main\resources\data\potato_s_t\recipe")
PRE = os.path.join(r"C:\PotatoST救援", "zf158_pre")

RESTORE = [u"vibranium_helmet_smithing.json", u"vibranium_chestplate_smithing.json",
           u"vibranium_leggings_smithing.json", u"vibranium_boots_smithing.json"]

TPL_OLD = u'SMITHING_TEMPLATE = u"minecraft:netherite_upgrade_smithing_template"'
TPL_NEW = (u'# \u26a0 0.13 ZF155\uff1a\u7528\u6237\u8981\u6c42\u300c\u4e4b\u524d\u6240\u6709\u7684\u632f\u91d1\u88c5\u5907\u4e0b\u754c\u5408\u91d1\u6a21\u677f\u4e5f\u6539\u6210\u8fd9\u4e2a\u300d\n'
           u'#   \u21d2 \u56db\u4ef6\u632f\u91d1\u62a4\u7532\u7684\u6a21\u677f\u6362\u6210\u901a\u7528\u5347\u7ea7\u6a21\u677f\uff1b\n'
           u'#   \u26a0 ZF158 \u8865\u8d26\uff1a\u90a3\u4e00\u8f6e\u53ea\u6539\u4e86**\u76d8\u4e0a\u7684 JSON**\u3001**\u6ca1\u6539\u8fd9\u5f20\u8868**\uff0c\n'
           u'#   \u4e8e\u662f `--write` \u4e00\u8dd1\u5c31\u628a\u5b83 revert \u4e86\uff08\u672c\u8f6e\u5b9e\u6d4b\uff1a4 \u4efd\u6587\u4ef6\u5f53\u573a\u88ab\u6539\u56de\u4e0b\u754c\u5408\u91d1\uff09\u3002\n'
           u'SMITHING_TEMPLATE = u"potato_s_t:universal_upgrade_template"')
CMT_OLD = (u'#  \u26a0 template \u4fdd\u6301\u539f\u7248\u7684**\u4e0b\u754c\u5408\u91d1\u5347\u7ea7\u6a21\u677f**\u4e0d\u53d8 \u2014\u2014 \u7528\u6237\u8bf4"\u7167\u6284\u539f\u7248"\uff0c')
CMT_NEW = (u'#  \u26a0 template \u4ece ZF155 \u8d77\u662f**\u901a\u7528\u5347\u7ea7\u6a21\u677f**\uff08\u539f\u672c\u7167\u6284\u539f\u7248\u7684\u4e0b\u754c\u5408\u91d1\u6a21\u677f\uff0c\n'
           u'#  \u7528\u6237\u540e\u6765\u70b9\u540d\u300c\u4e4b\u524d\u6240\u6709\u7684\u632f\u91d1\u88c5\u5907\u4e0b\u754c\u5408\u91d1\u6a21\u677f\u4e5f\u6539\u6210\u8fd9\u4e2a\u300d\uff09\n'
           u'#  \u65e7\u8bcd\u53e5\uff1a')
TPL_COMMENT_FALLBACK = u'**\u4e0b\u754c\u5408\u91d1\u5347\u7ea7\u6a21\u677f**'


def sha(p):
    return hashlib.sha1(open(p, "rb").read()).hexdigest()


def main(argv):
    write = u"--write" in argv
    fails = []

    # ① 还原被生成器 revert 的 4 份
    for fn in RESTORE:
        cur = os.path.join(RECIPE, fn)
        bak = os.path.join(PRE, r"src\main\resources\data\potato_s_t\recipe", fn)
        if not os.path.isfile(bak):
            fails.append(u"备份里没有 %s" % fn)
            continue
        same = os.path.isfile(cur) and sha(cur) == sha(bak)
        print(u"① %-38s 与备份%s" % (fn, u"一致（无需还原）" if same else u"不同 → 还原"))
        if not same and write:
            shutil.copy2(bak, cur)
            if sha(cur) != sha(bak):
                fails.append(u"%s 还原后哈希不一致" % fn)

    # ② 生成器：模板常量 + 注释
    gen = io.open(GEN, encoding="utf-8", newline=u"").read()
    if TPL_NEW in gen:
        print(u"② 生成器 SMITHING_TEMPLATE（已经是通用模板，幂等）")
    elif gen.count(TPL_OLD) == 1:
        gen = gen.replace(TPL_OLD, TPL_NEW, 1)
        print(u"② 生成器 SMITHING_TEMPLATE → potato_s_t:universal_upgrade_template")
    else:
        fails.append(u"SMITHING_TEMPLATE 锚点命中 %d 次" % gen.count(TPL_OLD))
    if CMT_OLD in gen:
        gen = gen.replace(CMT_OLD, CMT_NEW, 1)
        print(u"② 注释里那句「保持原版下界合金模板不变」已改成现行口径")
    elif TPL_COMMENT_FALLBACK in gen:
        print(u"② 注释（已经是现行口径或措辞再变，跳过）")
    else:
        fails.append(u"注释锚点没找到")
    if fails:
        print(u"失败 = %d" % len(fails))
        for f in fails:
            print(u"  !! " + f)
        return 1
    if not write:
        print(u"（没加 --write：只算不写）")
        return 0
    io.open(GEN, u"w", encoding="utf-8", newline=u"").write(gen)

    # ③ 再跑生成器
    print(u"③ 再跑 _zf45_recipes.py --write")
    r = subprocess.run([sys.executable, GEN, u"--write"], cwd=ROOT,
                       stdout=subprocess.PIPE, stderr=subprocess.STDOUT, timeout=600)
    out = r.stdout.decode("utf-8", "replace")
    for l in out.split(u"\n"):
        if u"定形配方" in l or u"失败项" in l:
            print(u"   " + l.strip())
    if r.returncode != 0:
        for l in out.split(u"\n"):
            if u"FAIL" in l:
                print(u"   " + l.strip()[:140])
        return 1

    # ④ 与改前件清单对账：只准 thermal_metal.json 一份不同
    print(u"④ 与 zf158_pre 清单对账（只准 thermal_metal.json 不同）")
    manifest = io.open(os.path.join(PRE, u"_manifest.txt"), encoding="utf-8").read()
    diffs = []
    for line in manifest.split(u"\n"):
        if not line.strip():
            continue
        h, rel = line.split(u"  ", 1)
        if not rel.startswith(u"src\\main\\resources\\data\\potato_s_t\\recipe\\"):
            continue
        cur = os.path.join(ROOT, rel)
        if not os.path.isfile(cur):
            diffs.append(rel + u"（不见了）")
            continue
        if sha(cur) != h:
            diffs.append(os.path.basename(rel))
    print(u"   不同的文件 %d 份：%s" % (len(diffs), u", ".join(diffs)))
    if diffs != [u"thermal_metal.json"]:
        print(u"!! 预期只有 thermal_metal.json 一份不同")
        return 1

    print(u"⑤ 新图纸：")
    print(io.open(os.path.join(RECIPE, u"thermal_metal.json"), encoding="utf-8").read())
    return 0


if __name__ == u"__main__":
    sys.exit(main(sys.argv[1:]))
