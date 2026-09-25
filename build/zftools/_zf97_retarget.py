# -*- coding: utf-8 -*-
u"""_zf97_retarget.py —— 把**活体数字**一次改全（ZF97）

本轮加了 19 个语言键 / 2 条定形配方 / 2 个 JEI 分类 / **2 种流体** ⇒ 往轮那些
"钉住真实数量"的校验必须跟着走（**改锚点，绝不放宽断言** —— §4.36）。

逐条（每条都断言"旧串在文件里**恰好出现一次**"，多一处少一处都当场停）：

  流体数 8 → 10：_zf71（fl）/ _zf73_verify A14（6 → 10）/ _zf74_verify B1（6 → 10）
  键数 284 → 303：_zf71 / _zf73_verify B11 / _zf75 C2 / _zf78 / _zf79 / _zf80 /
                  _zf81 / _zf82（两处）/ _zf93 / _zf96
  定形配方 36 → 38：_zf71（craft）/ _zf95_verify（EXPECT_SHAPED）/ _zf96（EXPECT_SHAPED）
  JEI 分类 9 → 11：_zf71 / _zf96（EXPECT_JEI）
  c: 流体标签：_zf74_verify 的 want 表（gaseous 6 → 10 条）+ 新增两份标签
  新增配方名单：_zf73_repro NEW_OK / _zf73_verify D2 / _zf95_verify 的 later
"""
import io
import os
import sys

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

TOOLS = r"E:\PotatoST\build\zftools"

EDITS = [
    # ---------------- 流体数 8 → 10 ----------------
    ("_zf71_verify.py",
     u'check(fl == 8 and u"oxygen, hydrogen, chlorine" in doc, u"流体 %d 种" % fl)',
     u'check(fl == 10 and u"oxygen, hydrogen, chlorine" in doc, u"流体 %d 种" % fl)  '
     u'# ZF97 起 10（+氮气/氨气）'),
    ("_zf73_verify.py",
     u'check(u"A14 isGas 正向列举：6 个气体变体一个不少（实测 %d）" % gas_hits, gas_hits == 6)',
     u'check(u"A14 isGas 正向列举：10 个气体变体一个不少（5 种 × 2；实测 %d）" % gas_hits, '
     u'gas_hits == 10)'),
    ("_zf74_verify.py",
     u'          len(re.findall(r"fluid == \\w+\\.get\\(\\)", body)) == 6)',
     u'          len(re.findall(r"fluid == \\w+\\.get\\(\\)", body)) == 10)'),
    # ---------------- 键数 284 → 303 ----------------
    ("_zf71_verify.py",
     u'check(len(keys) == 4 and set(keys.values()) == {284} and u"284 keys each" in doc,',
     u'check(len(keys) == 4 and set(keys.values()) == {303} and u"303 keys each" in doc,'),
    ("_zf73_verify.py",
     u'check(u"B11 四语言各 284 键（ZF78 27 + ZF79 2 + ZF80 9 + ZF82 13 + ZF93 2 + ZF96 12）", '
     u'all(v == 284 for v in counts.values()), str(counts))',
     u'check(u"B11 四语言各 303 键（ZF78 27 + ZF79 2 + ZF80 9 + ZF82 13 + ZF93 2 + ZF96 12 + ZF97 19）", '
     u'all(v == 303 for v in counts.values()), str(counts))'),
    ("_zf75_verify.py",
     u'check(u"C2 四语言各 284 键（ZF96 起）", all(v == 284 for v in counts.values()), str(counts))',
     u'check(u"C2 四语言各 303 键（ZF97 起）", all(v == 303 for v in counts.values()), str(counts))'),
    ("_zf78_verify.py",
     u'check(u"四份语言键数一致且 = 284（ZF96 加氢脱硫反应仓又 +12）",',
     u'check(u"四份语言键数一致且 = 303（ZF97 两台新机器 +19）",'),
    ("_zf78_verify.py",
     u'len(set(counts.values())) == 1 and list(counts.values())[0] == 284)',
     u'len(set(counts.values())) == 1 and list(counts.values())[0] == 303)'),
    ("_zf79_verify.py",
     u'check(u"四份语言键数一致且 = 284（ZF96 加氢脱硫反应仓 +12）",',
     u'check(u"四份语言键数一致且 = 303（ZF97 两台新机器 +19）",'),
    ("_zf79_verify.py",
     u'len(set(counts.values())) == 1 and list(counts.values())[0] == 284)',
     u'len(set(counts.values())) == 1 and list(counts.values())[0] == 303)'),
    ("_zf80_verify.py", u"EXPECT_KEYS = 284", u"EXPECT_KEYS = 303"),
    ("_zf81_verify.py",
     u'eq(u"语言键数（ZF96 起 284：加氢脱硫反应仓 +12）", 284, len(inside))',
     u'eq(u"语言键数（ZF97 起 303：两台新机器 +19）", 303, len(inside))'),
    ("_zf82_verify.py", u"EXPECT_KEYS = 284", u"EXPECT_KEYS = 303"),
    ("_zf82_verify.py", u'and u"284 keys each" in ann)', u'and u"303 keys each" in ann)'),
    ("_zf93_verify.py", u"EXPECT_KEYS = 284", u"EXPECT_KEYS = 303"),
    ("_zf96_verify.py",
     u'EXPECT_KEYS = 272 + len(NEW_KEYS)      # 284',
     u'# ⚠ 活体数字：ZF96 那轮是 284（272 + 本轮 12）；ZF97 又 +19 ⇒ 303\n'
     u'EXPECT_KEYS = 303'),
    # ---------------- 定形配方 36 → 38 ----------------
    ("_zf71_verify.py",
     u'check(craft == 36, u"合成配方 %d 条" % craft)  '
     u'# ZF96 起 36（ZF95 用户给的 5 条 + 本轮的加氢脱硫反应仓）',
     u'check(craft == 38, u"合成配方 %d 条" % craft)  '
     u'# ZF97 起 38（ZF95 的 5 条 + ZF96 的加氢脱硫反应仓 + ZF97 的两台机器）'),
    ("_zf95_verify.py", u"EXPECT_SHAPED = 36", u"EXPECT_SHAPED = 38"),
    ("_zf96_verify.py", u"EXPECT_SHAPED = 36", u"EXPECT_SHAPED = 38"),
    ("_zf96_verify.py", u"EXPECT_JEI = 9", u"EXPECT_JEI = 11"),
    # ---------------- JEI 分类 9 → 11 ----------------
    ("_zf71_verify.py",
     u'check(jei == 9 and u"9 machine categories" in doc, u"JEI 机器分类 %d 个" % jei)',
     u'check(jei == 11 and u"11 machine categories" in doc, u"JEI 机器分类 %d 个" % jei)'),
    # ---------------- 新增配方名单 ----------------
    ("_zf73_repro.py",
     u'          u"hydrodesulfurization_chamber.json"}',
     u'          u"hydrodesulfurization_chamber.json",\n'
     u'          u"air_separator.json", u"ammonia_synthesis_chamber.json"}'),
    ("_zf73_repro.py",
     u'#   （两张唱片 + 合金炉主控 + 分馏塔控制器/操作器）；ZF96 再加 1 条（加氢脱硫反应仓）——',
     u'#   （两张唱片 + 合金炉主控 + 分馏塔控制器/操作器）；ZF96 加 1 条（加氢脱硫反应仓）；\n'
     u'#   ZF97 再加 2 条（空气分离器 / 氨气组成室）——'),
    ("_zf73_verify.py",
     u'                                    u"hydrodesulfurization_chamber.json",\n'
     u'                                    u"music_disc_anvil_of_the_republic.json",\n'
     u'                                    u"music_disc_jasmine_flower.json", u"oil_bucket.json"],',
     u'                                    u"hydrodesulfurization_chamber.json",\n'
     u'                                    u"music_disc_anvil_of_the_republic.json",\n'
     u'                                    u"music_disc_jasmine_flower.json", u"oil_bucket.json",\n'
     u'                                    u"air_separator.json",\n'
     u'                                    u"ammonia_synthesis_chamber.json"],'),
    ("_zf95_verify.py",
     u'        later = [u"hydrodesulfurization_chamber.json"]',
     u'        later = [u"hydrodesulfurization_chamber.json", u"air_separator.json",\n'
     u'                 u"ammonia_synthesis_chamber.json"]'),
    # ---------------- c: 流体标签（_zf74 的 want 表）----------------
    ("_zf74_verify.py",
     u'        u"gaseous.json": [u"potato_s_t:oxygen", u"potato_s_t:flowing_oxygen",\n'
     u'                          u"potato_s_t:hydrogen", u"potato_s_t:flowing_hydrogen",\n'
     u'                          u"potato_s_t:chlorine", u"potato_s_t:flowing_chlorine"],',
     u'        u"gaseous.json": [u"potato_s_t:oxygen", u"potato_s_t:flowing_oxygen",\n'
     u'                          u"potato_s_t:hydrogen", u"potato_s_t:flowing_hydrogen",\n'
     u'                          u"potato_s_t:chlorine", u"potato_s_t:flowing_chlorine",\n'
     u'                          u"potato_s_t:nitrogen", u"potato_s_t:flowing_nitrogen",\n'
     u'                          u"potato_s_t:ammonia", u"potato_s_t:flowing_ammonia"],\n'
     u'        u"nitrogen.json": [u"potato_s_t:nitrogen", u"potato_s_t:flowing_nitrogen"],\n'
     u'        u"ammonia.json": [u"potato_s_t:ammonia", u"potato_s_t:flowing_ammonia"],'),
    ("_zf74_verify.py",
     u'    print(u"\\n=== A. 5 份 c: 流体标签 ===")',
     u'    print(u"\\n=== A. 7 份 c: 流体标签（ZF97 加了 nitrogen/ammonia）===")'),
    ("_zf74_verify.py",
     u'    A. 5 份标签文件的形状（路径/`replace:false`/源+流动都挂/值正确）；',
     u'    A. 7 份标签文件的形状（路径/`replace:false`/源+流动都挂/值正确）；'),
    ("_zf74_verify.py",
     u'  B. Java：`isGas` 既认自家 3 种、也认 `#c:gaseous`；',
     u'  B. Java：`isGas` 既认自家 5 种、也认 `#c:gaseous`；'),
]

fails = []
examined = 0


def check(ok, msg):
    global examined
    examined += 1
    print((u"  [OK]   " if ok else u"  [FAIL] ") + msg)
    if not ok:
        fails.append(msg)


def main():
    for (name, old, new) in EDITS:
        path = os.path.join(TOOLS, name)
        text = io.open(path, encoding="utf-8").read()
        n = text.count(old)
        if n != 1:
            check(False, u"%s：旧串出现 %d 次（要求恰好 1 次）→ %s"
                  % (name, n, old[:60].replace(u"\n", u"\\n")))
            continue
        io.open(path, "w", encoding="utf-8", newline=u"\n").write(text.replace(old, new))
        back = io.open(path, encoding="utf-8").read()
        check(back.count(new) == 1 and back.count(old) == 0,
              u"%s：%s → %s" % (name, old[:36].replace(u"\n", u"\\n"), new[:36].replace(u"\n", u"\\n")))
    print()
    for (name, needle) in (("_zf71_verify.py", u"fl == 8 "),
                           ("_zf71_verify.py", u"{284}"),
                           ("_zf71_verify.py", u"craft == 36"),
                           ("_zf71_verify.py", u"jei == 9 "),
                           ("_zf80_verify.py", u"EXPECT_KEYS = 284"),
                           ("_zf95_verify.py", u"EXPECT_SHAPED = 36"),
                           ("_zf96_verify.py", u"EXPECT_KEYS = 272 + len(NEW_KEYS)")):
        text = io.open(os.path.join(TOOLS, name), encoding="utf-8").read()
        check(needle not in text, u"%s 里已无旧值 %s" % (name, needle))
    print()
    print(u"检查项 = %d" % examined)
    print(u"失败项 = %d" % len(fails))
    for f in fails:
        print(u"   - " + f)
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())
