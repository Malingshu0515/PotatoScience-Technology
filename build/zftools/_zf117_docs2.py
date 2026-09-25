# -*- coding: utf-8 -*-
r"""_zf117_docs2.py —— 交接文档的"活体段落"：§2 最近动作 / §3 全门快照 / §5.1 / §5.2 / §6 欠账

§3 的数字**直接读** `build\zftools\_zf117_gatesnap.txt`（跑完快照再跑本脚本），
不手写 —— 手写就会和盘上漂移（这正是这份文件存在的意义）。
"""
import io
import os
import re
import sys

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

ROOT = r"E:\PotatoST"
HAND = ROOT + r"\docs\多会话协作交接.md"
SNAP = ROOT + r"\build\zftools\_zf117_gatesnap.txt"

fails, notes = [], []


def read(p):
    return io.open(p, encoding="utf-8").read()


def write(p, t):
    io.open(p, "w", encoding="utf-8", newline=u"").write(t)


def sub_once(path, old, new, label):
    raw = read(path)
    if raw.count(old) != 1:
        fails.append(u"%s：锚点出现 %d 次" % (label, raw.count(old)))
        return False
    write(path, raw.replace(old, new, 1))
    if new.split(u"\n")[0] not in read(path):
        fails.append(u"%s：回读失败" % label)
        return False
    notes.append(label)
    return True


def replace_span(path, start_prefix, end_prefix, block, label):
    raw = read(path)
    lines = raw.split(u"\n")
    a = [i for i, l in enumerate(lines) if l.startswith(start_prefix)]
    b = [i for i, l in enumerate(lines) if l.startswith(end_prefix)]
    if not a or not b or b[0] <= a[0]:
        fails.append(u"%s：定位失败（%s / %s）" % (label, start_prefix[:20], end_prefix[:20]))
        return False
    new = lines[:a[0]] + block.split(u"\n") + lines[b[0]:]
    write(path, u"\n".join(new))
    if block.split(u"\n")[0] not in read(path):
        fails.append(u"%s：回读失败" % label)
        return False
    notes.append(label)
    return True


S2_OLD = u'''- **最近动作**：ZF100~ZF109（燃烧反应室 / 酸性反应室 / 碳酸硝酸硫酸盐酸 / 27 条进度 /
  合金炉贴图 / **采油机 + 运行时改群系**）。
  本轮的进度树、四语言 48 键、`§4.74~4.77` 四条新雷、以及 `_zf107_*` 那套脚本都**已经提交**
  （`b64a054` / `53f89ee`）；ZF108 两次提交（`06abb5c` / `1fd3df8`）；
  **ZF109 的四语言 10 键（398 → 408）把 17 份往轮校验器的活体数字一起改了**
  （`_zf109_retarget.py`，含 `_zf107_verify.py` 自己 —— 它上一轮漏在名单外）。'''
S2_NEW = u'''- **最近动作**：**ZF117 进度树补线**（8 条新节点：采油机 / 锂电池构造间 / 三元锂 /
  星璨钢 / 星璨钢套装 / 星轨坠 + 海盐 / 液体物流），四语言 **432 → 448 键**，
  `_zf107_verify.py` 的总数 27 → **35**；顺手修了 ZF115 漏的**四句状态文案**（1 mB / 600 mB）
  与 ZF114 打包留下的 **`.sha1` 格式**（§4.90~4.92 三条新雷）。
  更早：ZF100~ZF115（燃烧反应室 / 酸性反应室 / 四种酸 / 27 条进度 / 合金炉贴图 /
  **采油机 + 运行时改群系** / 星璨钢合金配方 / 锂电池构造间 …）都已提交。'''


def main():
    # ---------- §2 ----------
    sub_once(HAND, S2_OLD, S2_NEW, u"交接 §2 最近动作")

    # ---------- §3（数字从快照读） ----------
    snap = read(SNAP) if os.path.exists(SNAP) else u""
    m = re.search(u"绿 = (\\d+)\\s+红 = (\\d+)", snap)
    if not m:
        fails.append(u"读不出快照的绿/红数（先跑 _zf117_gatesnap.py）")
        green_n, red_n = u"?", u"?"
    else:
        green_n, red_n = m.group(1), m.group(2)
    reds = re.findall(u"^  !! (_zf\\S+?\\.py)", snap, re.M)
    greens = re.findall(u"^  OK (_zf\\S+?\\.py)", snap, re.M)

    def bullet(names):
        return u"\n".join(u"- `%s`" % n for n in names) if names else u"- （无）"

    s3 = u"""## 3. 全门快照：**%s 绿 / %s 红**（ZF117 轮末；红的**不是**都有罪，逐条看原因）

跑法：`python build\\zftools\\_zf117_gatesnap.py`（只读，不改盘；输出也在 `build\\zftools\\_zf117_gatesnap.txt`，**38 道门**）。
口径（三条分开看）：

1. **红的 100%% 都是"老账"**：读成品 jar 的键数、陈旧配方名单、润色线的文案、素材线正在换的贴图；
2. **本轮的绿 +3**：`_zf107_verify.py`（696 项，ZF117 把总数与 frame/hidden 两张表修好）、
   `_zf117_verify.py`（**211 项**，本轮新门）、以及 `.sha1` 对账后转绿的六道（`_zf78 _zf79 _zf89 _zf94 _zf99 _zf91`）；
3. **没有一道"原本绿的门"因为本轮变红**（`_zf112_verify.py` 加了 6.5 段之后仍是绿的）。

### 3.1 因为"**还没打包**"而红（打包那一步会自动消掉，别去改脚本）

`.sha1` 那一族**已经在 ZF117 对账过了**（§4.92）⇒ 现在红的是**真·还没打包**这四道：

| 门 | 症状 |
|---|---|
| `_zf81` `_zf82` `_zf93` `_zf102` | 「成品里 zh_cn 键数 **448**（实际 432）」—— 成品是 ZF114 打的（432 键），本轮的四语言 16 键还没进去 |
| `_zf73_repro` `_zf73_verify` `_zf74` `_zf75` | 「成品 == 构建产物（逐字节）」—— 同理 |

### 3.2 因为"**名单/文案陈旧**"而红（谁加的东西谁改；主项目线认领配方那几条）

| 门 | 要改什么 | 归谁 |
|---|---|---|
| `_zf73_repro` `_zf73_verify` `_zf95` `_zf96` `_zf97` `_zf100` `_zf100_recipe_guard` `_zf101` `_zf102` | 「定形配方总数 51 / 名单」：盘上现在 **59 份 / 53 条**（+ZF109 采油机、+ZF112 锂电池构造间） | 主项目线（打包轮） |
| `_zf100_verify.py` | `lithium_battery.json` 的字母→材料表（ZF112 把碳酸锂换成锂电池原件、金属板换成纸） | 主项目线（打包轮） |
| `_zf80` `_zf71` `_zf98` | tooltip 文案（Shift 诊断 / 流体措辞 / ru 泵提示） | 润色线 |
| `_zf96` `_zf97` | 「改前那 N 张贴图一张都没动」——素材线 ZF110/ZF116 正在换 | 素材线 |
| `_zf103_verify.py` | 星璨钢四件盔甲贴图（ZF110 ZF116 已上线三件 + 头盔） | 素材线（做完自己收口） |

### 3.3 绿的（%s）

%s

---

""" % (green_n, red_n, green_n, bullet(greens))
    replace_span(HAND, u"## 3. 全门快照", u"## 4. 共用的硬规矩", s3, u"交接 §3 全门快照")
    if reds:
        notes.append(u"§3 里记下了 %d 道红门的名字" % len(reds))

    # ---------- §5.1 润色线 ----------
    sub_once(HAND,
             u"2. 你的文案改动会打到 **`_zf71_verify.py`（6 条）**、`_zf80_verify.py`（5 条）、"
             u"`_zf98_verify.py`（1 条）：",
             u"2. 你的文案改动会打到 **`_zf71_verify.py`**、`_zf80_verify.py`、`_zf98_verify.py`；\n"
             u"   ⚠ **ZF117 新钉的一处**：`gui.potato_s_t.lithium_battery_plant.status.no_acid`"
             u"（四语言）里必须留 **1 mB / 600 mB**，不许出现 10 mB / 6000 mB ——"
             u"`_zf112_verify.py` 的 6.5 段在盯（那句原本是 ZF115 漏改的旧数字）：",
             u"交接 §5.1 补状态文案那条")

    # ---------- §5.2 盔甲线 ----------
    sub_once(HAND,
             u"- 星璨钢锭**目前生存里没有来源**（只能创造拿）⇒ 27 条进度里我**故意没有**给它做节点；\n"
             u"  你定下来源之后跟我说一声，我补一条 challenge（`_zf107_verify.py` 的表要一起加）。",
             u"- **星璨钢的进度节点 ZF117 已经补上了**（ZF111 给了合金炉配方 ⇒ 来源成立）：\n"
             u"  `star_steel`（goal，挂 `hard_alloy`）+ `star_steel_armor`（**明面 challenge**，\n"
             u"  四件「与」）。你 ZF116 把胸甲/护腿/靴子的贴图换完之后，那条挑战的图标（胸甲）\n"
             u"  在成就界面里也就是新贴图了 —— **不用再改 json**。\n"
             u"- ⚠ 仍然**没有配方**的是 **星轨坠 / 粗振金**（ZF114 明说「先不给」）⇒ 它们那条成就\n"
             u"  我做成了**隐藏彩蛋位**（挂根、hidden），生存里点不亮是**如实反映**，不是漏做。",
             u"交接 §5.2 星璨钢进度那条")

    # ---------- §6 欠账 ----------
    s6 = u"""## 6. 我这边欠的账（谁都能催）

1. **打包发布** `ZF116（三张盔甲贴图）` + `ZF117（8 条进度 + 状态文案 + .sha1 对账）` ⇒ 一次打包，
   作废 `303c5d468b96826ef6836b0a4e54ccb8a539557c`（当前成品，432 键 / 4,298,939 B）。
   ⚠ **打包脚本写 `.sha1` 只写哈希那一行**（§4.92），否则十道门会一起红。
2. **配方名单那 9 处**（§3.2 主项目线那几行）—— 打包轮一起改（以盘上 **59 份 / 53 条**为准）。
3. **`_zf100_verify.py` 的锂电池配方表**（ZF112 改过 `lithium_battery.json`）—— 同上，打包轮改。
4. `build\\zftools\\_zf107_adv.py` 与 `_zf117_adv.py` 的**文案表**与盘上不同步（润色线改过值）
   —— 生成器**重跑幂等、且遇到"值冲突"会停手**，所以不用急着同步；要重新生成才需要。
5. 仓库里还留着首个提交带进去的 **156 个刀备份条目**（`_zf*_falsify_bak_*`）；`.gitignore` 已挡新增，
   旧的要不要 `git rm -r --cached` 出仓 —— 等用户/建仓会话拍板（我倾向清掉）。
6. **ZF109 欠的两条**：① 采油机的**储能 32768 FE**、**下探上限 64 格**、**每秒重扫一次结构**
   这三个数是我定的（用户没给），要改都是一行；② 采油机 GUI 里罐子下面那**两行数字**也是我加的。
7. **ZF109 当天补的账（用户实测）**：采油机**漏进创造页** —— 已修 + `_zf109_tabaudit.py` + 反证刀 K122 +
   档案 §4.82。**以后加任何方块物品，先跑一次 `python build\\zftools\\_zf109_tabaudit.py`**。
8. **ZF111 欠的一条**：星璨钢配方时长（用户没给 ⇒ 30 秒 ⇒ 一件 7,200,000 FE），
   另外**消耗槽现在会收东西了**（只收某条配方点名要消耗的）。
9. **ZF117 新欠的六条**（都是我定的、用户没说的，改都是一行；见 §9）：
   ① 采油机挂 `distillation`；② 星璨钢挂 `hard_alloy`；③ 星轨坠挂**根**且**隐藏**（它没有配方）；
   ④ 星璨钢套装用**明面 challenge**；⑤ 海盐挂 `steel`；⑥ 液体物流挂 `stronger_power`。
   另外**星轨坠那条现在生存里拿不到** —— 等配方/来源定了，把它挪进主线 + 取掉 `hidden`。
10. **ZF117 的账目补记**：`PotatoST.java` 不在 `zf117_pre\\_sha1.txt` 里（探针挂载是动手后才发现的），
    按 §10 用「`git cat-file blob HEAD:` == 摘钩子后的盘上文件」两条路证明，见 `zf117_pre\\_补说明.txt`。
    下不为例：**要挂探针的轮次，`PotatoST.java` 必须进改前件清单**。
"""
    replace_span(HAND, u"## 6. 我这边欠的账", u"\U0001F6A9NEVER_MATCH", s6, u"交接 §6 欠账",
                 ) if False else None
    # §6 是最后一节：直接截到文件尾
    raw = read(HAND)
    i = raw.find(u"## 6. 我这边欠的账（谁都能催）")
    if i < 0:
        fails.append(u"交接 §6：找不到标题")
    else:
        write(HAND, raw[:i] + s6)
        if u"ZF117 新欠的六条" in read(HAND):
            notes.append(u"交接 §6 欠账（整节重写）")
        else:
            fails.append(u"交接 §6：回读失败")

    print(u"\n".join(u"  [OK] " + n for n in notes))
    print(u"\n失败项 = %d" % len(fails))
    for f in fails:
        print(u"  !! " + f)
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())
