# -*- coding: utf-8 -*-
"""_zf136_apply.py —— ZF136：星璨钢**锭**换新材质

用户原话：「星璨钢换个材质 放素材里了」——素材 `build/用户素材/星璨钢重置.png`
（3093 B / sha1 `d5c18e82…` / 16×16 / 真 PNG）。

## 凭什么断定这是**锭**（不是盔甲/斧头）

| 判据 | 实测 |
|---|---|
| 尺寸 | 16×16 单张 ⇒ 不是盔甲层贴图（那是 64×32） |
| 形状 IoU vs `star_steel_ingot` | **0.985**（vs 其余五件只有 0.37~0.62） |
| alpha 掩码差异 | 与旧锭**只差 2 个像素** ⇒ 就是同一件东西重画 |
| 颜色 | 135 个共有像素**全部换过**，平均色差 **B −118.9** ⇒ 亮紫 → 暗紫灰 |
| 体量 | 137 不透明像素，旧锭 135 ⇒ 对得上 |

⇒ 判定为 `textures/item/star_steel_ingot.png`。**模型一个字不用改**
（`models/item/star_steel_ingot.json` 的 `layer0` 已经指向它）。
"""
import hashlib
import io
import json
import os
import shutil
import sys

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
sys.path.insert(0, r"E:\PotatoST\build\zftools")
from PngRecolor import read_png  # noqa: E402

ROOT = r"E:\PotatoST"
SRC = os.path.join(ROOT, "build", u"用户素材", u"星璨钢重置.png")
DST = os.path.join(ROOT, r"src\main\resources\assets\potato_s_t\textures\item",
                   "star_steel_ingot.png")
ARCH = os.path.join(ROOT, "build", u"用户素材", "star_steel_ingot.png")
PROV = os.path.join(ROOT, "build", u"用户素材", "_来源凭据.json")
PRE = os.path.join(ROOT, r"build\zftools\zf136_pre")

EXPECT_OLD_SHA = "9e29de461afb"      # ZF104 那张的 sha1 前 12（档案里记着）
fails = []


def sha1(p):
    return hashlib.sha1(open(p, "rb").read()).hexdigest()


def main():
    os.makedirs(PRE, exist_ok=True)

    print(u"① 前置断言")
    if not os.path.exists(SRC):
        print(u"  !! 找不到 %s" % SRC)
        return 1
    # ⚠ 锭这一件**没有 ASCII 留档**：ZF104（那是另一条线做的）只把它上线了，
    #   没做"复制一份留档"（和 ZF116 那三件盔甲同样的疏漏）。
    #   它的原图 build/用户素材/star_steel.png（3975 B）还在，但**凭据里没有它**。
    #   ⇒ **不去伪造留档**（把 160×160 原图重新缩一遍 ≠ 原字节，不能冒充"原件"）；
    #     被顶掉的那份由 zf136_pre/ 保底（逐字节可回退），并在凭据里如实写明。
    if not os.path.exists(DST):
        fails.append(u"缺在用锭贴图")
        print(u"  !! 缺在用锭贴图（%s）" % DST)
        return 1
    old_sha = sha1(DST)
    print(u"  在用 star_steel_ingot.png  sha1 %s（%d B）" % (old_sha[:12], os.path.getsize(DST)))
    if old_sha[:12] != EXPECT_OLD_SHA:
        fails.append(u"在用锭贴图不是预期的 %s（实际 %s）—— 盘被人动过，停手"
                     % (EXPECT_OLD_SHA, old_sha[:12]))
    if fails:
        print(u"\n前置断言未过，停手：")
        for f in fails:
            print(u"  !! " + f)
        return 1
    print(u"  [OK] 与档案记录一致（ZF104 那张 %s）" % EXPECT_OLD_SHA)

    print(u"\n② 备份被替换的那张")
    shutil.copyfile(DST, os.path.join(PRE, "star_steel_ingot.png"))
    if sha1(os.path.join(PRE, "star_steel_ingot.png")) != old_sha:
        print(u"  !! 备份校验失败，停手")
        return 1
    print(u"  [OK] zf136_pre/star_steel_ingot.png（sha1 %s）" % old_sha[:12])

    print(u"\n③ 新图体检 + 原字节上线")
    raw = open(SRC, "rb").read()
    if raw[:8] != b"\x89PNG\r\n\x1a\n":
        fails.append(u"新图不是真 PNG")
        return 1
    w, h, rgba = read_png(SRC)
    op = sum(1 for i in range(w * h) if rgba[i * 4 + 3] == 255)
    semi = sum(1 for i in range(w * h) if 0 < rgba[i * 4 + 3] < 255)
    print(u"  %dx%d 位深%d 类型%d 不透明 %d 半透明 %d  %d B"
          % (w, h, raw[24], raw[25], op, semi, len(raw)))
    if (w, h, raw[24], raw[25]) != (16, 16, 8, 6):
        fails.append(u"规格不是 16x16/8/RGBA")
    if semi:
        fails.append(u"有 %d 个半透明像素" % semi)
    if fails:
        print(u"  停手")
        for f in fails:
            print(u"  !! " + f)
        return 1

    io.open(DST, "wb").write(raw)
    if open(DST, "rb").read() != raw:
        fails.append(u"写出后逐字节不一致")
        return 1
    print(u"  [OK] textures/item/star_steel_ingot.png 逐字节写出 sha1 %s" % sha1(DST)[:12])

    # ⚠ 不往 build/用户素材 里造第二份：锭从来就没有 ASCII 留档（见 ① 的注释），
    #   被顶掉的那份已在 zf136_pre/ 里逐字节保住 ⇒ 回退路径是完整的。
    print(u"  [OK] 被顶掉的那份在 zf136_pre/star_steel_ingot.png（sha1 %s）" % old_sha[:12])

    print(u"\n④ 凭据登记")
    prov = json.loads(io.open(PROV, encoding="utf-8").read())
    key = "star_steel_ingot.png"
    note = (u"用户 ZF136 给的星璨钢锭新材质（素材原名 `星璨钢重置.png`，3093 B，16x16）"
            u"⇒ 原字节复制上线，顶掉 ZF104 那张（sha1 9e29de461afb… / 214 B）。"
            u"形状与旧锭只差 2 个像素、颜色 135 个像素全部重上（亮紫 → 暗紫灰，平均色差 B -118.9）。"
            u"⚠ 锭**没有 ASCII 留档**（ZF104 只上线没留档，和 ZF116 三件盔甲同样的疏漏）；"
            u"被顶掉那份由 build/zftools/zf136_pre/star_steel_ingot.png 保底；"
            u"更早的 ZF104 原图是 build/用户素材/star_steel.png（3975 B，160x160），它此前不在凭据里")
    if key in prov:
        prov[key][u"原名"] = u"星璨钢重置.png"
        prov[key]["sha1"] = hashlib.sha1(raw).hexdigest()
        prov[key]["bytes"] = len(raw)
        prov[key][u"说明"] = note
    else:
        prov[key] = {u"原名": u"星璨钢重置.png", "sha1": hashlib.sha1(raw).hexdigest(),
                     "bytes": len(raw), u"说明": note}
    # 顺手把 ZF104 那张原图也登进来（此前漏了）
    if "star_steel.png" not in prov and os.path.exists(os.path.join(ROOT, "build", u"用户素材", "star_steel.png")):
        sp = os.path.join(ROOT, "build", u"用户素材", "star_steel.png")
        sb = open(sp, "rb").read()
        prov["star_steel.png"] = {
            u"原名": u"star_steel.png（ZF104 时期放进来的，文件名本来就是 ASCII）",
            "sha1": hashlib.sha1(sb).hexdigest(), "bytes": len(sb),
            u"说明": u"星璨钢的原始素材图（160x160）⇒ ZF104 缩到 16x16 成 textures/item/star_steel_ingot.png；"
                    u"ZF136 补登（此前凭据里漏了它）",
        }
        print(u"  [补登] star_steel.png（ZF104 原图，此前凭据里没有）")
    io.open(PROV, "w", encoding="utf-8", newline="\n").write(
        json.dumps(prov, indent=2, ensure_ascii=False) + "\n")
    back = json.loads(io.open(PROV, encoding="utf-8").read())
    print(u"  [OK] 凭据条目 %d 条，%s 已更新" % (len(back), key))

    print(u"\n⑤ 模型指向（应指向自己，不用改）")
    mp = os.path.join(ROOT, r"src\main\resources\assets\potato_s_t\models\item\star_steel_ingot.json")
    l0 = json.loads(io.open(mp, encoding="utf-8").read())["textures"]["layer0"]
    print(u"  layer0 = %s  %s" % (l0, u"[OK]" if l0 == "potato_s_t:item/star_steel_ingot" else u"[!!]"))
    if l0 != "potato_s_t:item/star_steel_ingot":
        fails.append(u"模型没指向自己")

    print(u"\n失败项 = %d" % len(fails))
    for f in fails:
        print(u"  !! " + f)
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())
