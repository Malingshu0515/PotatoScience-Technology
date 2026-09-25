# -*- coding: utf-8 -*-
r"""_zf118_docs2.py —— 交接文档的"活体段落"：§3 全门快照（数字从快照读）+ §5.1 + §6

§3 的绿/红数字**直接读** `build\zftools\_zf118_gatesnap.txt`，不手写（手写就会漂）。
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
SNAP = ROOT + r"\build\zftools\_zf118_gatesnap.txt"

fails, notes = [], []


def read(p):
    return io.open(p, encoding="utf-8").read()


def write(p, t):
    io.open(p, "w", encoding="utf-8", newline=u"").write(t)


def replace_span(path, start_prefix, end_prefix, block, label):
    raw = read(path)
    lines = raw.split(u"\n")
    a = [i for i, l in enumerate(lines) if l.startswith(start_prefix)]
    b = [i for i, l in enumerate(lines) if l.startswith(end_prefix)]
    if not a or not b or b[0] <= a[0]:
        fails.append(u"%s：定位失败" % label)
        return False
    write(path, u"\n".join(lines[:a[0]] + block.split(u"\n") + lines[b[0]:]))
    if block.split(u"\n")[0] not in read(path):
        fails.append(u"%s：回读失败" % label)
        return False
    notes.append(label)
    return True


def sub_once(path, old, new, label):
    raw = read(path)
    if new in raw and old not in raw:
        notes.append(label + u"（已经是新写法，跳过）")
        return True
    if raw.count(old) != 1:
        fails.append(u"%s：锚点出现 %d 次" % (label, raw.count(old)))
        return False
    write(path, raw.replace(old, new, 1))
    if new.split(u"\n")[0] not in read(path):
        fails.append(u"%s：回读失败" % label)
        return False
    notes.append(label)
    return True


def main():
    snap = read(SNAP) if os.path.exists(SNAP) else u""
    m = re.search(u"绿 = (\\d+)\\s+红 = (\\d+)", snap)
    if not m:
        fails.append(u"读不出快照的绿/红数（先跑 _zf118_gatesnap.py）")
        green_n, red_n = u"?", u"?"
    else:
        green_n, red_n = m.group(1), m.group(2)
    greens = re.findall(u"^  OK (_zf\\S+?\\.py)", snap, re.M)

    def bullet(names):
        return u"\n".join(u"- `%s`" % n for n in names) if names else u"- （无）"

    s3 = u"""## 3. 全门快照：**%s 绿 / %s 红**（ZF118 轮末；红的**不是**都有罪，逐条看原因）

跑法：`python build\\zftools\\_zf118_gatesnap.py`（只读，不改盘；输出也在 `build\\zftools\\_zf118_gatesnap.txt`，**39 道门**）。
口径（四条分开看）：

1. **本轮的账（ZF118）**：
   - 新门 **`_zf118_verify.py`（60 项）**：图纸**按位置**逐格核 + 生成器表**整表 31 条**逐条与盘上 JSON 比
     + 59 份旧配方逐字节未变 + 没有第二条产出星轨坠的配方；
   - **`_zf114_verify.py` 的 F5 被我拆成两条**（用户 ZF118 给了配方 ⇒ 「星轨坠不该有配方」一半失效，
     「粗振金仍然没有」保留）—— 这是**用户指令**带来的必要改动，不是放宽；
   - 活体数字：配方 **59 → 60 份**、`crafting_shaped` **53 → 54**、生成器表 **30 → 31 条**；四语言**仍 448 键**。
2. **润色线正在改"进度文案的值"** ⇒ 打到 **`_zf111_verify.py` / `_zf112_verify.py`**（各 4 条：
   「除了新加的键，别的键与改前件逐字相同」）。那些值**归润色线**（§5.1），
   它们按 `_zf117_verify.py` 那套（`DESC_TOUCHED[locale]` 钉名单）收口即可；
   ⚠ **`_zf117_verify.py` 已经这么钉过了**（润色线自己改的），所以它是绿的。
3. **老账照旧**：读成品 jar 的键数（`_zf81 _zf82 _zf93 _zf102` —— 成品还是 ZF114 那版 432 键）、
   陈旧配方名单（`_zf73* _zf95 _zf96 _zf97 _zf100 _zf100_recipe_guard _zf101 _zf102`）、
   润色线的 tooltip 文案（`_zf71 _zf80 _zf98`）、素材线正在换的贴图（`_zf96 _zf97 _zf103`）。
4. **诚实说明**：本轮开工后**没有**重跑过"改前"快照，所以上面的绿/红**不是**与上一轮同口径的对比；
   能逐条对比的是第 1、2 条里点名的那些门。

### 3.1 因为"**还没打包**"而红（打包那一步会自动消掉，别去改脚本）

| 门 | 症状 |
|---|---|
| `_zf81` `_zf82` `_zf93` `_zf102` | 「成品里 zh_cn 键数 **448**（实际 432）」—— 成品是 ZF114 打的（432 键） |
| `_zf73_repro` `_zf73_verify` `_zf74` `_zf75` | 「成品 == 构建产物（逐字节）」 |

### 3.2 因为"**名单/文案陈旧**"而红（谁加的东西谁改）

| 门 | 要改什么 | 归谁 |
|---|---|---|
| `_zf73_repro` `_zf73_verify` `_zf95` `_zf96` `_zf97` `_zf100` `_zf100_recipe_guard` `_zf101` `_zf102` | 「定形配方总数 51 / 名单」：盘上现在 **60 份 / 54 条**（+ZF109 采油机、+ZF112 锂电池构造间、+**ZF118 星轨坠**） | 主项目线（打包轮） |
| `_zf100_verify.py` | `lithium_battery.json` 的字母→材料表（ZF112 改过；ZF118 已把**生成器表**也对上了，§4.93） | 主项目线（打包轮） |
| `_zf80` `_zf71` `_zf98` | tooltip 文案（Shift 诊断 / 流体措辞 / ru 泵提示） | 润色线 |
| `_zf111` `_zf112` | **进度文案的值**被润色线改了（各 4 条）—— 按 `_zf117_verify.py` 的 `DESC_TOUCHED` 那套钉名单，或者改成"别人的改值只打印" | 润色线 |
| `_zf96` `_zf97` `_zf103` | 「改前那 N 张贴图一张都没动」——素材线 ZF110/ZF116 正在换 | 素材线 |

### 3.3 绿的（%s）

%s

---

""" % (green_n, red_n, green_n, bullet(greens))
    replace_span(HAND, u"## 3. 全门快照", u"## 4. 共用的硬规矩", s3, u"交接 §3 全门快照")

    # ---------- §5.1：给润色线补一条 ----------
    sub_once(HAND,
             u"   ⚠ **ZF117 新钉的一处**：`gui.potato_s_t.lithium_battery_plant.status.no_acid`",
             u"   ⚠ **ZF118 补**：你改**进度文案的值**会打到 **`_zf111_verify.py` / `_zf112_verify.py`**"
             u"（各 4 条「除了新加的键，别的键与改前件逐字相同」，现在红着）；\n"
             u"   `_zf117_verify.py` 你自己已经用 `DESC_TOUCHED[locale]` 钉过名单了 —— 那两门照同一套收口即可。\n"
             u"   ⚠ **ZF117 新钉的一处**：`gui.potato_s_t.lithium_battery_plant.status.no_acid`",
             u"交接 §5.1 补「值改动打到哪几门」")

    # ---------- §6：追加 ZF118 ----------
    raw = read(HAND)
    if u"12. **ZF118 的账**" in raw:
        notes.append(u"交接 §6 已有 ZF118 条目（跳过）")
    else:
        anchor = u"11. **ZF118 的账**"
        i = raw.find(anchor)
        if i < 0:
            fails.append(u"交接 §6：找不到 §11 那条")
        else:
            j = raw.find(u"\n", raw.find(u"\n", i) + 1) + 1   # §11 是两行
            add = (u"12. **ZF118 的账（本轮真欠的）**：① 配方耦合的 9 道门名单要跟到 **60 份 / 54 条**（打包轮）；\n"
                   u"    ② 生成器表现在**有常驻对账**了（`_zf118_verify.py` B8 整表 31 条）——"
                   u"以后改配方**只改表再 `--write`**，别手改 JSON（§4.93）；\n"
                   u"    ③ 星轨坠有配方之后，ZF117 给它做的**隐藏彩蛋位**是否挪进主线（挂 `star_steel`、"
                   u"去掉 `hidden`）—— 用户一句话就改。\n")
            write(HAND, raw[:j] + add + raw[j:])
            notes.append(u"交接 §6 追加 ZF118 第 12 条")

    print(u"\n".join(u"  [OK] " + n for n in notes))
    print(u"\n失败项 = %d" % len(fails))
    for f in fails:
        print(u"  !! " + f)
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())
