# -*- coding: utf-8 -*-
u"""_zf73_repro.py —— 复现性证据：加一条配方，**别的配方一个字节都没动**

做法：拿 §10 备份 `zf73_pre` 里的配方目录（改前 34 份）与当前 34+N 份逐份比 SHA1。
期望：34 份**逐字节相同**、新增的**只有** `oil_bucket.json`（1 份）。
这条断言的价值：证明"配方生成器重跑一遍不会顺手改坏别人的配方"（ZF69 立的口径）。
"""
import hashlib
import io
import os
import sys

PROJ = r"E:\PotatoST"
PRE = r"C:\PotatoST救援\zf73_pre"
REL = os.path.join(u"src", u"main", u"resources", u"data", u"potato_s_t", u"recipe")
# ⚠ ZF82 又加了 fluid_exchanger.json（容器换流器的合成台配方）；ZF95 又加了用户口述的 5 条
#   （两张唱片 + 合金炉主控 + 分馏塔控制器/操作器）；ZF96 加 1 条（加氢脱硫反应仓）；
#   ZF97 再加 2 条（空气分离器 / 氨气组成室）——
#   「其余那些份逐字节未变」才是这条的真正内容，新增名单随轮次增长。
NEW_OK = {u"oil_bucket.json", u"fluid_exchanger.json",
          u"music_disc_jasmine_flower.json", u"music_disc_anvil_of_the_republic.json",
          u"alloy_smelter.json", u"distillation_controller.json", u"distillation_operator.json",
          u"hydrodesulfurization_chamber.json",
          u"air_separator.json", u"ammonia_synthesis_chamber.json",
          u"lithium_battery.json", u"electric_blast_furnace.json",
          u"combustion_chamber.json", u"acidic_reaction_chamber.json"}

fails = []


def sha1(path):
    h = hashlib.sha1()
    with io.open(path, "rb") as fh:
        h.update(fh.read())
    return h.hexdigest()


def main():
    pre_dir = os.path.join(PRE, REL)
    cur_dir = os.path.join(PROJ, REL)
    if not os.path.isdir(pre_dir):
        print(u"!! 找不到改前备份目录：%s" % pre_dir)
        return 1
    pre = {n for n in os.listdir(pre_dir) if n.endswith(u".json")}
    cur = {n for n in os.listdir(cur_dir) if n.endswith(u".json")}
    same = 0
    for name in sorted(pre):
        if name not in cur:
            fails.append(u"改前有、现在没了: %s" % name)
            continue
        a, b = sha1(os.path.join(pre_dir, name)), sha1(os.path.join(cur_dir, name))
        if a == b:
            same += 1
        else:
            fails.append(u"内容变了: %s  (%s -> %s)" % (name, a[:12], b[:12]))
    added = sorted(cur - pre)
    for name in added:
        if name not in NEW_OK:
            fails.append(u"多出不在预期内的配方: %s" % name)

    print(u"改前配方 %d 份 / 现在 %d 份" % (len(pre), len(cur)))
    print(u"逐字节相同 = %d / %d" % (same, len(pre)))
    print(u"新增 = %s" % (u", ".join(added) if added else u"（无）"))
    if added == sorted(NEW_OK) and same == len(pre) and not fails:
        print(u"\n[OK] 除新增的 %s 外，其余 %d 份配方**逐字节没动**" % (added[0], same))
    else:
        print(u"\n[FAIL] 复现性不成立")
    for f in fails:
        print(u"  !! " + f)
    print(u"\n失败项 = %d" % len(fails))
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())
