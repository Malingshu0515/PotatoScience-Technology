# -*- coding: utf-8 -*-
u"""_zf134_live.py —— 活体数字重定目标：盘上 `crafting_shaped` 总数 **+1**（本轮加了星璨钢斧那一张）

加一张定形图纸 = 所有把"盘上定形配方总数"写死的门都要跟着走（老规矩，§4.36 族 / §4.64）。
本脚本**现场数**盘上的数，再把它写进三处：

  ① `_zf100_recipe_guard.py`  —— `shaped == N` + 那句说明文字里的数
  ② `_zf106_recipes_check.py` —— `EXPECT_SHAPED = N`
  ③ `_zf134_verify.py`        —— 本轮自己的 `EXPECT_SHAPED = N`

**只动这三处**：别的脚本（`_zf95/96/97/100/101/102_verify` 与 `_zf73_*`）停在 51 是
**交接文档里挂给「打包轮」的老账**，本轮不越界改（§10.1：只碰自己这条线）。

跑法：
    python build/zftools/_zf134_live.py            # 只报数
    python build/zftools/_zf134_live.py --write
"""
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

PROJ = r"E:\PotatoST"
ZT = os.path.join(PROJ, "build", "zftools")
RDIR = os.path.join(PROJ, r"src\main\resources\data\potato_s_t\recipe")

fails = []


def read(p):
    return io.open(p, encoding="utf-8").read()


def count_shaped():
    n = total = 0
    for name in sorted(os.listdir(RDIR)):
        if not name.endswith(u".json"):
            continue
        total += 1
        if json.loads(read(os.path.join(RDIR, name))).get(u"type") == u"minecraft:crafting_shaped":
            n += 1
    return n, total


def sub_once(text, rx, rep, where):
    u"""替换恰好一次；命中次数不对就记 FAIL 并原样返回（绝不猜）。"""
    hits = re.findall(rx, text, re.S)
    if len(hits) != 1:
        fails.append(u"%s：锚点 %s 命中 %d 次（应为 1）" % (where, rx[:46], len(hits)))
        return text
    return re.sub(rx, rep.replace(u"\\", u"\\\\"), text, count=1, flags=re.S)


def main(argv):
    write = u"--write" in argv
    shaped, total = count_shaped()
    print(u"盘上：%d 份配方，其中 crafting_shaped = **%d**" % (total, shaped))

    plan = []

    # ① 配方守卫：数字 + 说明文字
    p1 = os.path.join(ZT, u"_zf100_recipe_guard.py")
    t = read(p1)
    t = sub_once(t, r"shaped == \d+\)", u"shaped == %d)" % shaped, u"_zf100_recipe_guard.py")
    # ⚠ 替换串里要写进目标文件的 `%d` / `% shaped` 得写成 `%%d` / `%% shaped`（它们不是本次的格式符）
    label = (u'u"盘上 crafting_shaped = %%d 条（活体数字：ZF106 收尾 51；'
             u'ZF109/ZF112/ZF118/ZF122 各 +1；**ZF134 星璨钢斧 +1 = %d**；'
             u'ZF120 振金套加的是 4 张锻造台配方，不改这个数）"' % shaped)
    # ⚠ 锚点要允许**跨行**：那句说明在源码里是两个字符串字面量拼起来的
    #   （`... → "` 换行 `u"ZF118 ...）" % shaped`），用 `[^"]*` 会因为中间那个引号而匹配不到 ——
    #   所以这里用 `.` + `re.S`（`sub_once` 已经带了 `re.S`）。
    t = sub_once(t, r'u"盘上 crafting_shaped = %d 条（.*?）"', label,
                 u"_zf100_recipe_guard.py")
    plan.append((u"_zf100_recipe_guard.py", p1, t))

    # ② ZF106 的配方检查
    p2 = os.path.join(ZT, u"_zf106_recipes_check.py")
    plan.append((u"_zf106_recipes_check.py", p2,
                 sub_once(read(p2), r"EXPECT_SHAPED = \d+", u"EXPECT_SHAPED = %d" % shaped,
                          u"_zf106_recipes_check.py")))

    # ③ 本轮自己的探针
    p3 = os.path.join(ZT, u"_zf134_verify.py")
    plan.append((u"_zf134_verify.py", p3,
                 sub_once(read(p3), r"EXPECT_SHAPED = \d+", u"EXPECT_SHAPED = %d" % shaped,
                          u"_zf134_verify.py")))

    for name, path, text in plan:
        try:
            compile(text, path, "exec")
        except SyntaxError as e:
            fails.append(u"%s 改完语法坏：%s" % (name, e))
            continue
        if write:
            io.open(path, "w", encoding="utf-8", newline=u"").write(text)
        print(u"  [%s] %s → %d" % (u"写出" if write else u"将写出", name, shaped))

    if write:
        print(u"")
        for name, path, _t in plan:
            r = subprocess.run([sys.executable, path], stdout=subprocess.PIPE,
                               stderr=subprocess.STDOUT)
            tail = [l.strip() for l in r.stdout.decode("utf-8", "replace").split(u"\n")
                    if u"失败项" in l or u"失败项 =" in l or u"失败 = " in l]
            print(u"  [%s] 跑 %s：%s" % (u"OK" if r.returncode == 0 else u"FAIL", name,
                                        u" / ".join(tail[-2:]) or u"（没有汇总行）"))
            if r.returncode != 0:
                fails.append(u"%s 跑出来是红的" % name)

    print(u"\n失败项 = %d" % len(fails))
    for f in fails:
        print(u"  !! " + f)
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
