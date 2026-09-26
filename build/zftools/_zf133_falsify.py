# -*- coding: utf-8 -*-
"""_zf133_falsify.py —— ZF133 的反证：**每条断言都得能被咬掉**

做法照 ZF114/Z121 那两轮：往产品代码里**故意注入一个改动** ⇒ `_zf133_verify.py`
必须**恰好报出对应的那一条**（其余照旧全绿）⇒ 断电（还原）。

⚠ 为什么反证只能打**静态**那一半：探针要真跑一次服务端（约 40 秒），
   一轮反证打 8 刀就是 8 次 build+run。所以这里的判据是
   "`_zf133_verify.py` 的第 N 条红掉"，探针那一半的等价物是
   `check/zf133_axe_probe.log` 里那些 `[FAIL]` 的**存在性**（探针本身已经证明它会红——
   第一轮它抓出了"修理材料不对"这条真缺陷）。

用法：
    python build\\zftools\\_zf133_falsify.py            # 跑全部（自动还原）
    python build\\zftools\\_zf133_falsify.py --list     # 只看刀
"""
import hashlib
import io
import os
import subprocess
import sys

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
ROOT = r"E:\PotatoST"
JAVA = os.path.join(ROOT, r"src\main\java\com\potatost\mod")
VERIFY = os.path.join(ROOT, r"build\zftools\_zf133_verify.py")

AXE = os.path.join(JAVA, "StarSteelAxeItem.java")
SHOCK = os.path.join(JAVA, "ShockwaveManager.java")
TIERS = os.path.join(JAVA, "ModTiers.java")

# (编号, 说明, 文件, 原文, 改成, 期望红掉的那一条的**特征串**)
KNIVES = [
    ("K1", "夜晚不再免耐久（删掉早退）", AXE,
     "        if (!level.isClientSide && isNight(level)) {\n            return true;\n        }\n",
     "",
     "A9"),

    ("K2", "花费从 120 改成 60", AXE,
     "SHOCKWAVE_COST = 120",
     "SHOCKWAVE_COST = 60",
     "A5"),

    ("K3", "冷却从 15 秒改成 30 秒", AXE,
     "SHOCKWAVE_COOLDOWN_TICKS = 20 * 15",
     "SHOCKWAVE_COOLDOWN_TICKS = 20 * 30",
     "A6"),

    ("K4", "冷却门禁拆掉（冷却中也能出手）", AXE,
     "        if (player.getCooldowns().isOnCooldown(this)) {\n            return InteractionResultHolder.pass(stack);\n        }\n",
     "",
     "A12"),

    ("K5", "闲置上限从 200 tick 改成 400（10 秒变 20 秒）", SHOCK,
     "IDLE_LIMIT_TICKS = 200",
     "IDLE_LIMIT_TICKS = 400",
     "B3"),

    ("K6", "滚动窗口退化成一次性计时（拆到也不清零）", SHOCK,
     "            wave.sinceBreak = 0;",
     "            wave.sinceBreak = wave.sinceBreak;",
     "B12"),

    ("K7", "宽度从 6 改成 8（用户给的数被改掉）", SHOCK,
     "WIDTH = 6;",
     "WIDTH = 8;",
     "B1"),

    ("K8", "「挖不动就停」的判据去掉（撞墙也不停）", SHOCK,
     "                if (!owner.getMainHandItem().isCorrectToolForDrops(state)) {\n                    blocked = true;\n                }",
     "                if (false) {\n                    blocked = true;\n                }",
     "B10"),

    ("K9", "挖掘等级从钻石改成下界合金", TIERS,
     "BlockTags.INCORRECT_FOR_DIAMOND_TOOL, 22)",
     "BlockTags.INCORRECT_FOR_NETHERITE_TOOL, 22)",
     "A2"),
]


def sha(p):
    return hashlib.sha1(open(p, "rb").read()).hexdigest()


def run_verify():
    """跑常驻校验，返回 (失败条数, 失败行拼接)。"""
    env = dict(os.environ, PYTHONIOENCODING="utf-8")
    r = subprocess.run([sys.executable, VERIFY], capture_output=True, env=env)
    out = r.stdout.decode("utf-8", "replace")
    fails = [l.strip() for l in out.split("\n") if "[FAIL]" in l]
    return len(fails), "\n".join(fails), out


def main():
    if "--list" in sys.argv:
        for k in KNIVES:
            print("%s %s" % (k[0], k[1]))
        return

    print("=" * 78)
    print("先跑一遍**未注入**的基线（必须 0 失败，否则反证没有意义）")
    print("=" * 78)
    base_fails, base_lines, _ = run_verify()
    print("基线失败 = %d" % base_fails)
    if base_fails:
        print(base_lines)
        print("⚠ 基线不干净，反证结果不可信 —— 先修到全绿再跑")
        return 2

    originals = {p: io.open(p, encoding="utf-8").read() for p in (AXE, SHOCK, TIERS)}
    hashes = {p: sha(p) for p in originals}
    verdicts = []
    try:
        for kid, desc, path, old, new, expect in KNIVES:
            s = originals[path]
            n = s.count(old)
            if n != 1:
                verdicts.append((kid, desc, "ANCHOR x%d" % n, False))
                print("[SKIP] %s %s —— 锚点出现 %d 次" % (kid, desc, n))
                continue
            io.open(path, "w", encoding="utf-8", newline="\n").write(s.replace(old, new, 1))
            fails, lines, _ = run_verify()
            hit = expect in lines
            verdicts.append((kid, desc, "红 %d 条，含 %s = %s" % (fails, expect, hit), hit))
            print("[%s] %s %s —— %s" % ("咬住" if hit else "**没咬住**", kid, desc,
                                        "失败 %d 条，%s %s" % (fails, expect, "命中" if hit else "没命中")))
            if lines:
                for l in lines.split("\n")[:4]:
                    print("        " + l[:150])
            io.open(path, "w", encoding="utf-8", newline="\n").write(originals[path])
            # 每刀之后立刻核哈希还原干净，否则后面几刀全在脏底上跑
            if sha(path) != hashes[path]:
                print("  [FAIL] 还原不干净：%s" % path)
                return 3
    finally:
        for p, s in originals.items():
            io.open(p, "w", encoding="utf-8", newline="\n").write(s)

    print("=" * 78)
    print("还原后复核")
    print("=" * 78)
    for p in originals:
        print("  %s %s" % ("[OK ]" if sha(p) == hashes[p] else "[FAIL]", p))
    after_fails, _, _ = run_verify()
    print("还原后失败 = %d（应为 0）" % after_fails)

    caught = sum(1 for v in verdicts if v[3])
    print("=" * 78)
    print("反证结果：%d / %d 刀咬住" % (caught, len(verdicts)))
    for kid, desc, info, hit in verdicts:
        print("  %s %s %s —— %s" % ("[OK ]" if hit else "[FAIL]", kid, desc, info))
    return 0 if caught == len(verdicts) and after_fails == 0 else 1


sys.exit(main())
