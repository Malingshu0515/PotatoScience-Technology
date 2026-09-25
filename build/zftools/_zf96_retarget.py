# -*- coding: utf-8 -*-
u"""_zf96_retarget.py —— 把**活体数字**一次改全（ZF96）

本轮加了 12 个语言键 / 1 条定形配方 / 1 个 JEI 分类 ⇒ 往轮那些"钉住真实数量"的校验
必须跟着走（**改锚点，绝不放宽断言** —— §4.36 立的规矩）。

逐条（每条都断言"旧串在文件里**恰好出现一次**"，多一处少一处都当场停）：

  272 → 284 键：_zf71 / _zf73_verify B11 / _zf75 C2 / _zf78 / _zf79 / _zf80 EXPECT_KEYS /
                _zf81 / _zf82（两处）/ _zf93
  35 → 36 定形配方：_zf71（craft）/ _zf95_verify（EXPECT_SHAPED）
  8 → 9 JEI 分类：_zf71
  新增配方名单：_zf73_repro NEW_OK / _zf73_verify D2 / _zf95_verify 的"本轮只新增这 5 份"

⚠ 这里只改**数字与名单**，不改任何断言的结构；改完由门与反证刀再验一遍。
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
    # ---------------- 键数 272 → 284 ----------------
    ("_zf71_verify.py",
     u'check(len(keys) == 4 and set(keys.values()) == {272} and u"272 keys each" in doc,',
     u'check(len(keys) == 4 and set(keys.values()) == {284} and u"284 keys each" in doc,'),
    ("_zf73_verify.py",
     u'check(u"B11 四语言各 272 键（ZF78 27 + ZF79 2 + ZF80 9 + ZF82 13 + ZF93 2）", '
     u'all(v == 272 for v in counts.values()), str(counts))',
     u'check(u"B11 四语言各 284 键（ZF78 27 + ZF79 2 + ZF80 9 + ZF82 13 + ZF93 2 + ZF96 12）", '
     u'all(v == 284 for v in counts.values()), str(counts))'),
    ("_zf75_verify.py",
     u'check(u"C2 四语言各 272 键（ZF93 起）", all(v == 272 for v in counts.values()), str(counts))',
     u'check(u"C2 四语言各 284 键（ZF96 起）", all(v == 284 for v in counts.values()), str(counts))'),
    ("_zf78_verify.py",
     u'check(u"四份语言键数一致且 = 272（ZF93 第二张唱片又 +2）",',
     u'check(u"四份语言键数一致且 = 284（ZF96 加氢脱硫反应仓又 +12）",'),
    ("_zf78_verify.py",
     u'len(set(counts.values())) == 1 and list(counts.values())[0] == 272)',
     u'len(set(counts.values())) == 1 and list(counts.values())[0] == 284)'),
    ("_zf79_verify.py",
     u'check(u"四份语言键数一致且 = 272（ZF93 第二张唱片 +2）",',
     u'check(u"四份语言键数一致且 = 284（ZF96 加氢脱硫反应仓 +12）",'),
    ("_zf79_verify.py",
     u'len(set(counts.values())) == 1 and list(counts.values())[0] == 272)',
     u'len(set(counts.values())) == 1 and list(counts.values())[0] == 284)'),
    ("_zf80_verify.py", u"EXPECT_KEYS = 272", u"EXPECT_KEYS = 284"),
    ("_zf81_verify.py",
     u'eq(u"语言键数（ZF93 起 272：第二张唱片 +2）", 272, len(inside))',
     u'eq(u"语言键数（ZF96 起 284：加氢脱硫反应仓 +12）", 284, len(inside))'),
    ("_zf82_verify.py", u"EXPECT_KEYS = 272", u"EXPECT_KEYS = 284"),
    ("_zf82_verify.py", u'and u"272 keys each" in ann)', u'and u"284 keys each" in ann)'),
    ("_zf93_verify.py", u"EXPECT_KEYS = 272", u"EXPECT_KEYS = 284"),
    # ---------------- 定形配方 35 → 36 ----------------
    ("_zf71_verify.py",
     u'check(craft == 35, u"合成配方 %d 条" % craft)  '
     u'# ZF95 起 35（用户给的 5 条：两张唱片 + 合金炉主控 + 分馏塔控制器/操作器）',
     u'check(craft == 36, u"合成配方 %d 条" % craft)  '
     u'# ZF96 起 36（ZF95 用户给的 5 条 + 本轮的加氢脱硫反应仓）'),
    ("_zf95_verify.py", u"EXPECT_SHAPED = 35", u"EXPECT_SHAPED = 36"),
    # ---------------- JEI 分类 8 → 9 ----------------
    ("_zf71_verify.py",
     u'check(jei == 8 and u"8 machine categories" in doc, u"JEI 机器分类 %d 个" % jei)',
     u'check(jei == 9 and u"9 machine categories" in doc, u"JEI 机器分类 %d 个" % jei)'),
    # ---------------- 新增配方名单 ----------------
    ("_zf73_repro.py",
     u'NEW_OK = {u"oil_bucket.json", u"fluid_exchanger.json",\n'
     u'          u"music_disc_jasmine_flower.json", u"music_disc_anvil_of_the_republic.json",\n'
     u'          u"alloy_smelter.json", u"distillation_controller.json", u"distillation_operator.json"}',
     u'NEW_OK = {u"oil_bucket.json", u"fluid_exchanger.json",\n'
     u'          u"music_disc_jasmine_flower.json", u"music_disc_anvil_of_the_republic.json",\n'
     u'          u"alloy_smelter.json", u"distillation_controller.json", u"distillation_operator.json",\n'
     u'          u"hydrodesulfurization_chamber.json"}'),
    ("_zf73_repro.py",
     u'# ⚠ ZF82 又加了 fluid_exchanger.json（容器换流器的合成台配方）；ZF95 又加了用户口述的 5 条\n'
     u'#   （两张唱片 + 合金炉主控 + 分馏塔控制器/操作器）——',
     u'# ⚠ ZF82 又加了 fluid_exchanger.json（容器换流器的合成台配方）；ZF95 又加了用户口述的 5 条\n'
     u'#   （两张唱片 + 合金炉主控 + 分馏塔控制器/操作器）；ZF96 再加 1 条（加氢脱硫反应仓）——'),
    ("_zf73_verify.py",
     u'        check(u"D2 只新增了预期的那些（ZF82 起含 fluid_exchanger.json；ZF95 起含 5 条口述配方）",\n'
     u'              sorted(cur - pre) == [u"alloy_smelter.json", u"distillation_controller.json",\n'
     u'                                    u"distillation_operator.json", u"fluid_exchanger.json",\n'
     u'                                    u"music_disc_anvil_of_the_republic.json",\n'
     u'                                    u"music_disc_jasmine_flower.json", u"oil_bucket.json"],\n'
     u'              u", ".join(sorted(cur - pre)))',
     u'        check(u"D2 只新增了预期的那些（ZF82 起含 fluid_exchanger.json；ZF95 起含 5 条口述配方；'
     u'ZF96 起含加氢脱硫反应仓）",\n'
     u'              sorted(cur - pre) == [u"alloy_smelter.json", u"distillation_controller.json",\n'
     u'                                    u"distillation_operator.json", u"fluid_exchanger.json",\n'
     u'                                    u"hydrodesulfurization_chamber.json",\n'
     u'                                    u"music_disc_anvil_of_the_republic.json",\n'
     u'                                    u"music_disc_jasmine_flower.json", u"oil_bucket.json"],\n'
     u'              u", ".join(sorted(cur - pre)))'),
    ("_zf73_verify.py",
     u'        #   ZF82 加 fluid_exchanger.json；ZF95 又加用户口述的 5 条（两张唱片 + 合金炉主控 +\n'
     u'        #   分馏塔控制器/操作器）。',
     u'        #   ZF82 加 fluid_exchanger.json；ZF95 又加用户口述的 5 条（两张唱片 + 合金炉主控 +\n'
     u'        #   分馏塔控制器/操作器）；ZF96 再加 1 条（加氢脱硫反应仓）。'),
    ("_zf95_verify.py",
     u'        eq(u"本轮只新增这 5 份", sorted(SPEC[i] and (i + u".json") for i in SPEC), sorted(added))',
     u'        # ⚠ ZF96 又加了 1 条（加氢脱硫反应仓）—— 名单随轮次增长，"其余逐字节未变"才是内容\n'
     u'        later = [u"hydrodesulfurization_chamber.json"]\n'
     u'        eq(u"本轮只新增这 5 份（+ 后续轮次的 %d 份）" % len(later),\n'
     u'           sorted(sorted(SPEC[i] and (i + u".json") for i in SPEC) + later), sorted(added))'),
    ("_zf95_verify.py",
     u'旧的 36 份配方一份不少、活体数字（定形配方 30 → 35）、文档、成品 jar。',
     u'旧的 36 份配方一份不少、活体数字（定形配方 ZF95 起 35、**ZF96 起 36**）、文档、成品 jar。'),
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
            check(False, u"%s：旧串出现 %d 次（要求恰好 1 次）→ %s" % (name, n, old[:60].replace(u"\n", u"\\n")))
            continue
        io.open(path, "w", encoding="utf-8", newline=u"\n").write(text.replace(old, new))
        back = io.open(path, encoding="utf-8").read()
        check(back.count(new) == 1 and back.count(old) == 0,
              u"%s：%s → %s" % (name, old[:40].replace(u"\n", u"\\n"), new[:40].replace(u"\n", u"\\n")))
    # 改完顺手复核：全仓再也搜不到那几个旧数字的活体断言
    print()
    for (name, needle) in (("_zf71_verify.py", u"craft == 35"),
                           ("_zf71_verify.py", u"jei == 8 "),
                           ("_zf80_verify.py", u"EXPECT_KEYS = 272"),
                           ("_zf95_verify.py", u"EXPECT_SHAPED = 35")):
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
