# -*- coding: utf-8 -*-
u"""_zf128_gatefix2.py —— 全门快照抓出来的**两处**新红（一处是本轮的账，一处是素材线的账）

跑完 `_zf128_gatesnap.py` 后，比 ZF127 轮末多红了 4 份。逐条查清来源：

| 门 | 谁的责任 | 症状 | 怎么收 |
|---|---|---|---|
| `_zf107_verify.py` | **本轮（我）** | C1/C2/C5 是三条**泛化**判据（"图标带本模组命名空间 / 图标是模组注册的物品 / 图标 ∈ 判据物品"）——根节点换成原版毒马铃薯之后它们当然不成立 | 给 `new_beginning` 开一条**同样硬**的专属判据（点名毒马铃薯 + **图标与判据物品必须不同**），其余 34 条一个字不动 |
| `_zf125_verify.py` | **素材线** | E3 断言控制器方块模型的 `textures.all` == 那张占位图；素材线（ZF128 期间）把它改成 `cube_bottom_top`，顶/底换成新画的 `_top` 图 | 判据改成"**每一处贴图都是本模组 block/ 下控制器自己的图、且文件在盘上**"，强度不变、以后加面也不用再改 |
| `_zf127_verify.py` | 素材线 | D1/D2/F2/F5（"材质先不画"那一套） | 由 `_zf128_artfix.py` 改成自洽 |
| `_zf128_verify.py` | 素材线 | D6（待画数） | 同上 |

跑法：
    python build\\zftools\\_zf128_gatefix2.py
"""
import io
import os
import sys

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

ROOT = r"E:\PotatoST"
TOOLS = os.path.join(ROOT, "build", "zftools")
notes, fails = [], []


def read(p):
    return io.open(p, encoding="utf-8", newline=u"").read()


def write(p, t):
    io.open(p, "w", encoding="utf-8", newline=u"").write(t)


def main():
    # ---------- ① _zf107_verify.py：给根节点一条专属判据 ----------
    p = os.path.join(TOOLS, u"_zf107_verify.py")
    t = read(p)
    old = u'''        icon = o["display"]["icon"]["id"]
        check(u"C1 %s 的图标 id 带本模组命名空间" % n, icon.startswith("potato_s_t:"))
        check(u"C2 %s 的图标物品在盘上注册（%s）" % (n, icon), icon.split(u":", 1)[1] in ids)
        ci = crit_items(o)
        check(u"C3 %s 的判据至少点了一个物品" % n, len(ci) > 0)
        for i in ci:
            check(u"C4 %s 的判据物品 %s 在盘上注册" % (n, i), i in ids)
        check(u"C5 %s 的图标 ∈ 判据物品（拿到就会亮）" % n, icon.split(u":", 1)[1] in ci)'''
    new = u'''        icon = o["display"]["icon"]["id"]
        ci = crit_items(o)
        if n == u"new_beginning":
            # ⚠ ZF128：根节点的**图标**是用户点名的原版毒马铃薯，而**判据**仍是微型粉碎机
            #   （页签图标 = 根节点图标，同一个字段；见 §4.110）。下面 C1/C2/C5 那三条泛化判据
            #   对它天然不成立 ⇒ 换成**同样硬**的三条专属判据，其余 34 条一个字不动。
            check(u"C1r new_beginning 的图标 = minecraft:poisonous_potato（ZF128 用户点名）",
                  icon == u"minecraft:poisonous_potato")
            check(u"C2r 该图标是**原版**命名空间（全表唯一的例外，见 §4.110）",
                  icon.startswith(u"minecraft:"))
            check(u"C5r new_beginning 的**图标 ≠ 判据物品**（图标换了、成就内容没换：判据仍是微型粉碎机）",
                  ci == {u"potato_s_t:micro_crusher"} and icon.split(u":", 1)[1] not in ci)
        else:
            check(u"C1 %s 的图标 id 带本模组命名空间" % n, icon.startswith("potato_s_t:"))
            check(u"C2 %s 的图标物品在盘上注册（%s）" % (n, icon), icon.split(u":", 1)[1] in ids)
            check(u"C3 %s 的判据至少点了一个物品" % n, len(ci) > 0)
            for i in ci:
                check(u"C4 %s 的判据物品 %s 在盘上注册" % (n, i), i in ids)
            check(u"C5 %s 的图标 ∈ 判据物品（拿到就会亮）" % n, icon.split(u":", 1)[1] in ci)'''
    if u"C1r new_beginning" in t:
        notes.append(u"_zf107_verify.py：已经是专属判据版（幂等跳过）")
    elif t.count(old) != 1:
        fails.append(u"_zf107_verify.py：锚点命中 %d 次 —— 停手" % t.count(old))
    else:
        write(p, t.replace(old, new, 1))
        notes.append(u"_zf107_verify.py：根节点三条泛化判据 → 三条专属判据（C1r/C2r/C5r）")

    # ---------- ② _zf125_verify.py：控制器模型改成「每一处都是自己的图」 ----------
    p = os.path.join(TOOLS, u"_zf125_verify.py")
    t = read(p)
    old = u'''    mbm = jload(os.path.join(ASSETS, u"models", u"block", u"diesel_generator_controller.json"))
    check(u"E3 方块模型指向自己的贴图",
          isinstance(mbm, dict) and mbm.get(u"textures", {}).get(u"all")
          == u"potato_s_t:block/diesel_generator_controller")'''
    new = u'''    mbm = jload(os.path.join(ASSETS, u"models", u"block", u"diesel_generator_controller.json"))
    # ⚠ ZF128（**素材线的改动，我这边跟平判据**）：控制器模型从 `textures.all` 一张占位图
    #   改成了 `cube_bottom_top`（顶/底 = 新画的 `_top`，侧面仍是那张占位）⇒ 判据改成
    #   "**每一处贴图都是本模组 block/ 下控制器自己的图、而且文件在盘上**"：
    #   强度不变（照样不许借原版/别人的图），以后素材线再加面也不用改这道门。
    _texs = mbm.get(u"textures", {}) if isinstance(mbm, dict) else {}
    _bad = [k for k, v in _texs.items()
            if not v.startswith(u"potato_s_t:block/diesel_generator_controller")
            or not os.path.exists(os.path.join(ASSETS, *v.split(u":", 1)[1].split(u"/"))[:-1]
                                  + (v.split(u"/")[-1] + u".png",))]
    check(u"E3 方块模型每一处贴图都是控制器自己的图且在盘上（%s；不合规 %s）" % (_texs, _bad),
          bool(_texs) and not _bad)'''
    if u"E3 方块模型每一处贴图" in t:
        notes.append(u"_zf125_verify.py：已经是宽松-但-更硬版（幂等跳过）")
    elif t.count(old) != 1:
        fails.append(u"_zf125_verify.py：锚点命中 %d 次 —— 停手" % t.count(old))
    else:
        write(p, t.replace(old, new, 1))
        notes.append(u"_zf125_verify.py：E3 改成「每一处贴图都是自己的图且在盘上」")

    for fn in (u"_zf107_verify.py", u"_zf125_verify.py"):
        try:
            compile(read(os.path.join(TOOLS, fn)), fn, u"exec")
        except SyntaxError as e:
            fails.append(u"%s 语法不过：%s" % (fn, e))

    print(u"\n".join(u"  [OK] " + x for x in notes))
    print(u"失败项 = %d" % len(fails))
    for f in fails:
        print(u"  !! " + f)
    return 1 if fails else 0


if __name__ == u"__main__":
    sys.exit(main())
