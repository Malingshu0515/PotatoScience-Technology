# -*- coding: utf-8 -*-
r"""_zf119_docs2.py —— 交接文档的"活体段落"：§3 全门快照（数字从快照读）

§3 的绿/红数字**直接读** `build\zftools\_zf119_gatesnap.txt`，不手写（手写就会漂）。
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
SNAP = ROOT + r"\build\zftools\_zf119_gatesnap.txt"

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


def main():
    snap = read(SNAP) if os.path.exists(SNAP) else u""
    m = re.search(u"绿 = (\\d+)\\s+红 = (\\d+)", snap)
    if not m:
        fails.append(u"读不出快照的绿/红数（先跑 _zf119_gatesnap.py）")
        green_n, red_n = u"?", u"?"
    else:
        green_n, red_n = m.group(1), m.group(2)
    greens = re.findall(u"^  OK (_zf\\S+?\\.py)", snap, re.M)
    bullet = u"\n".join(u"- `%s`" % n for n in greens) if greens else u"- （无）"

    s3 = u"""## 3. 全门快照：**%s 绿 / %s 红**（ZF119 轮末；红的**不是**都有罪，逐条看原因）

跑法：`python build\\zftools\\_zf119_gatesnap.py`（只读，不改盘；输出也在 `build\\zftools\\_zf119_gatesnap.txt`，**40 道门**）。
口径（四条分开看）：

1. **本轮的账（ZF119）**：新门 **`_zf119_verify.py`（63 项）** 绿 —— 独立再数一遍动画帧、
   逐帧逐像素与源图比、mcmeta 的 frametime、物品/模型/三个 `c:` 标签/**没有配方**、
   键数 449、23 份往轮校验无残留 448；**没有一道原本绿的门因为本轮变红**
   （键数 448 → 449 的重定目标把 23 份一起改了，改完逐份 `compile()` 过）。
2. **润色线正在改"进度文案的值"** ⇒ 打到 **`_zf111_verify.py` / `_zf112_verify.py`**（各 4 条）。
   那些值**归润色线**（§5.1），按 `_zf117_verify.py` 那套（`DESC_TOUCHED[locale]` 钉名单）收口即可。
3. **老账照旧**：读成品 jar 的键数（`_zf81 _zf82 _zf93 _zf102` —— 成品还是 ZF114 那版 432 键）、
   陈旧配方名单（`_zf73* _zf95 _zf96 _zf97 _zf100 _zf100_recipe_guard _zf101 _zf102`）、
   润色线的 tooltip 文案（`_zf71 _zf80 _zf98`）、素材线正在换的贴图（`_zf96 _zf97 _zf103`）。
4. **诚实说明**：本轮开工后**没有**重跑过"改前"快照，所以绿/红**不是**与上一轮同口径的对比；
   能逐条对比的是第 1、2 条里点名的那些门。

### 3.1 因为"**还没打包**"而红（打包那一步会自动消掉，别去改脚本）

| 门 | 症状 |
|---|---|
| `_zf81` `_zf82` `_zf93` `_zf102` | 「成品里 zh_cn 键数 **449**（实际 432）」—— 成品是 ZF114 打的 |
| `_zf73_repro` `_zf73_verify` `_zf74` `_zf75` | 「成品 == 构建产物（逐字节）」 |

### 3.2 因为"**名单/文案陈旧**"而红（谁加的东西谁改）

| 门 | 要改什么 | 归谁 |
|---|---|---|
| `_zf73_repro` `_zf73_verify` `_zf95` `_zf96` `_zf97` `_zf100` `_zf100_recipe_guard` `_zf101` `_zf102` | 「定形配方总数 51 / 名单」：盘上现在 **60 份 / 54 条** | 主项目线（打包轮） |
| `_zf100_verify.py` | `lithium_battery.json` 的字母→材料表（ZF112 改过；生成器表已对上，§4.93） | 主项目线（打包轮） |
| `_zf80` `_zf71` `_zf98` | tooltip 文案 | 润色线 |
| `_zf111` `_zf112` | **进度文案的值**（各 4 条）—— 照 `_zf117_verify.py` 的 `DESC_TOUCHED` 收口 | 润色线 |
| `_zf96` `_zf97` `_zf103` | 「改前那 N 张贴图一张都没动」——素材线 ZF110/ZF116 正在换 | 素材线 |

### 3.3 绿的（%s）

%s

---

""" % (green_n, red_n, green_n, bullet)
    replace_span(HAND, u"## 3. 全门快照", u"## 4. 共用的硬规矩", s3, u"交接 §3 全门快照")

    print(u"\n".join(u"  [OK] " + n for n in notes))
    print(u"\n失败项 = %d" % len(fails))
    for f in fails:
        print(u"  !! " + f)
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())
