# -*- coding: utf-8 -*-
u"""_zf128_gatefix.py —— 跟平"往轮判据 + 生成器"（四处）

根成就的**图标**一改，三份往轮门与一份生成器都要跟（判据强度都不放宽）：

| 落点 | 改什么 |
|---|---|
| `_zf70_verify.py` | SPEC 表里 `new_beginning` 的 `icon=` → `minecraft:poisonous_potato`（判据那行仍是 micro_crusher） |
| `_zf107_verify.py` | `D3 根节点的图标换成微型粉碎机` → 毒马铃薯（`D2` 判据那条不动） |
| `_zf124_verify.py` | 「根成就的图标仍是微型粉碎机」这条目标值换掉（ZF124 当时确实没动它，那句话是**当时**的事实） |
| `_zf107_adv.py` | `ROOT_ICON` 拆成「判据」与「图标」两个常量 —— 否则**重跑生成器会把毒马铃薯写回粉碎机**（§4.93 那条"表与盘必须一致"） |

跑法：
    python build\\zftools\\_zf128_gatefix.py
"""
import io
import os
import sys

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

TOOLS = r"E:\PotatoST\build\zftools"
notes, fails = [], []


def read(p):
    return io.open(p, encoding="utf-8", newline=u"").read()


def write(p, t):
    io.open(p, "w", encoding="utf-8", newline=u"").write(t)


def patch(name, fn, old, new, times=1):
    p = os.path.join(TOOLS, fn)
    t = read(p)
    if t.count(old) == 0 and new in t:
        notes.append(u"%s：已经是新文本（幂等跳过）" % name)
        return
    if t.count(old) != times:
        fails.append(u"%s：锚点命中 %d 次（要 %d 次）—— 停手" % (name, t.count(old), times))
        return
    write(p, t.replace(old, new, times))
    notes.append(u"%s" % name)


def main():
    # ---------- ① _zf70_verify.py ----------
    patch(u"_zf70_verify.py：SPEC 表里根成就的 icon → 毒马铃薯", u"_zf70_verify.py",
          u'''    dict(file="new_beginning", parent=None, icon="potato_s_t:micro_crusher",''',
          u'''    # ⚠ ZF128 retarget：用户把**页签/根节点的图标**换成了毒马铃薯（原版物品），
    #   而**判据**仍是微型粉碎机 —— 表里这两行从此各是各的（下一行的 criteria 一个字没动）。
    dict(file="new_beginning", parent=None, icon="minecraft:poisonous_potato",''')

    # ---------- ② _zf107_verify.py ----------
    patch(u"_zf107_verify.py：D3 图标 → 毒马铃薯", u"_zf107_verify.py",
          u'''    eq(u"D3 根节点的图标换成微型粉碎机", "potato_s_t:micro_crusher",
       new_root["display"]["icon"]["id"])''',
          u'''    # ⚠ ZF128 retarget：图标在 ZF128 换成了毒马铃薯（页签图标 = 根节点图标，同一个字段）；
    #   D2 那条**判据**仍是微型粉碎机，一个字没动。
    eq(u"D3 根节点的图标（ZF128 起是毒马铃薯）", "minecraft:poisonous_potato",
       new_root["display"]["icon"]["id"])''')

    # ---------- ③ _zf124_verify.py ----------
    patch(u"_zf124_verify.py：根成就图标那条 → 毒马铃薯", u"_zf124_verify.py",
          u'''        check(u"根成就的图标仍是微型粉碎机（用户只说了改名，没说换图标）",
              adv.get(u"display", {}).get(u"icon", {}).get(u"id") == u"potato_s_t:micro_crusher")''',
          u'''        # ⚠ ZF128 retarget：ZF124 当时"只改名、没换图标"是**当时的事实**；
        #   用户后来（ZF128）点名把图标换成毒马铃薯 ⇒ 目标值跟着走，判据强度不变。
        check(u"根成就的图标（ZF124 时是粉碎机，ZF128 起是毒马铃薯）",
              adv.get(u"display", {}).get(u"icon", {}).get(u"id") == u"minecraft:poisonous_potato")''')

    # ---------- ④ _zf107_adv.py（生成器）----------
    patch(u"_zf107_adv.py：ROOT_ICON 拆成判据 + 图标两个常量", u"_zf107_adv.py",
          u'''ROOT_ICON = "micro_crusher"''',
          u'''# ⚠ ZF128：页签图标 = 根节点图标（同一个字段）。用户把**图标**换成了毒马铃薯，
#   而**判据**仍旧是微型粉碎机 ⇒ 这两个值从此各是各的；不拆开的话，
#   将来谁重跑一次本脚本就会把图标悄悄写回粉碎机（§4.93「表与盘必须一致」）。
ROOT_ICON_CRITERION = "potato_s_t:micro_crusher"      # 判据（成就内容：做出微型粉碎机）
ROOT_ICON_DISPLAY = "minecraft:poisonous_potato"      # 页签 + 根节点画的那个图标（ZF128）''')
    patch(u"_zf107_adv.py：写盘时用那两个常量", u"_zf107_adv.py",
          u'''    obj["display"]["icon"] = {"count": 1, "id": "potato_s_t:" + ROOT_ICON}
    obj["criteria"] = {"got": {"trigger": "minecraft:inventory_changed",
                               "conditions": {"items": [{"items": "potato_s_t:" + ROOT_ICON}]}}}''',
          u'''    obj["display"]["icon"] = {"count": 1, "id": ROOT_ICON_DISPLAY}
    obj["criteria"] = {"got": {"trigger": "minecraft:inventory_changed",
                               "conditions": {"items": [{"items": ROOT_ICON_CRITERION}]}}}''')
    patch(u"_zf107_adv.py：那行打印", u"_zf107_adv.py",
          u'''    print(u"  老成就 new_beginning：根节点判据 → %s" % ROOT_ICON)''',
          u'''    print(u"  老成就 new_beginning：判据 → %s；图标 → %s"
          % (ROOT_ICON_CRITERION, ROOT_ICON_DISPLAY))''')

    # 语法自检（改了盘上的校验器/生成器，先自己 compile 一遍）
    for fn in (u"_zf70_verify.py", u"_zf107_verify.py", u"_zf124_verify.py", u"_zf107_adv.py"):
        try:
            compile(read(os.path.join(TOOLS, fn)), fn, u"exec")
        except SyntaxError as e:
            fails.append(u"%s 语法不过：%s" % (fn, e))

    print(u"\n".join(u"  [OK] " + n for n in notes))
    print(u"失败项 = %d" % len(fails))
    for f in fails:
        print(u"  !! " + f)
    return 1 if fails else 0


if __name__ == u"__main__":
    sys.exit(main())
