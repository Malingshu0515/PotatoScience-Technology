# -*- coding: utf-8 -*-
u"""_zf119_docs3.py —— ZF119 修正后的文档补记（用户实测反馈：最后一帧向下弹）

用户原话：「最后一帧会猛地向下弹一下 锭本体保持一致 不要以闪光为基准」

补四处：
  ① 档案 §9 ZF119 小节：加"修正"一节（根因 / 改法 / 新证据 / 新刀 K165）；
  ② 档案 §4.95：加"对齐基准要按**本体**"这条（原来的四步里没写这一条，正是它漏了才出的事）；
  ③ 档案 §5 的 ZF119 行：项数 63 → 65、刀 8 → 9、贴图哈希与构建产物换新；
  ④ 交接文档 §6 第 13 条：补上这次修正。
"""
import io
import sys

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

ROOT = r"E:\PotatoST"
ARCH = ROOT + r"\docs\开发档案.md"
HAND = ROOT + r"\docs\多会话协作交接.md"

fails, notes = [], []


def read(p):
    return io.open(p, encoding="utf-8").read()


def write(p, t):
    io.open(p, "w", encoding="utf-8", newline=u"").write(t)


def sub_once(path, old, new, label):
    raw = read(path)
    if new in raw and old not in raw:
        notes.append(label + u"（已是新写法，跳过）")
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


FIX_SEC = u'''
#### 六、⚠ 修正：你实测抓到「最后一帧往下弹一下」（同一轮内改掉的）

> 用户实测原话：「最后一帧会猛地向下弹一下 锭本体保持一致 **不要以闪光为基准**」

**根因（量出来的，不是猜的）**：第一版我按「**哪一行有不透明像素**」分帧 —— 而闪光会跑到
本体**上方**。第 10 帧就是：闪光在 253..255、本体其实在 **256..279** ⇒ 那一帧的窗口被抬高 3 行，
重排后本体落在 y=**7**..27（其余九帧都是 4..27）⇒ 播放时**最后一帧往下弹 3 像素**。
量帧的两个脚本：`_zf119_align.py`（分本体/闪光包围盒）、`_zf119_bodybands.py`（只按本体分行）。

**改法**：**只按本体分行**（本体 = 低饱和灰白；闪光 = 高饱和黄）⇒ 本体是干净的 **10 段 × 24 行**
（`0..23, 30..53, 58..81, 89..112, 117..140, 145..168, 173..196, 201..224, 229..252, 256..279`）。
重排规则改成：

```
dst 第 y 行  ←  源图第 (本体顶行 − 4 + y) 行       窗口夹在**邻居本体**之间（两帧本体只隔 3 行时会互相咬）
```

⇒ **10 帧的本体全部落在 y=4..27**（与 `titanium_ingot.png` 的摆位一致）**一动不动**；
闪光照旧在动（可以跑进上下那 4 行留白 —— 那本来就是留给它的）。仍然是**零重采样**（整行搬运）。

| | 改前 | 改后 |
|---|---|---|
| 贴图 sha1 | `98aa8894…`（1427 B） | **`e7db8d32…`**（1452 B） |
| 最后一帧本体 | y=**7**..27（弹 3 像素） | y=4..27（与其余九帧一致） |
| 常驻校验 | 63 项 | **65 项**（新增 A9b「10 帧本体包围盒完全一致」、A15b「闪光仍有 ≥3 个位置」） |
| 反证刀 | 8 把 | **9 把**（新增 **K165**：只把最后一帧下移 3 行 ⇒ 必须咬住 A9b —— 直接复现你看到的现象） |
| 探针 | 20 项 ALL OK | **重跑一遍 20 项 ALL OK**（贴图变了，证据要跟着重出） |

'''

PITFALL_ADD = u'''
5. **对齐基准要按「本体」，不能按「有不透明像素的行」**（0.11 ZF119 修正，用户实测抓到的）。
   动画里**闪光会跑到本体上方/下方** ⇒ 拿"有像素"当帧边界，窗口会被闪光抬高/压低，
   重排之后本体就"跳一下"。正确做法：按**本体**（低饱和的那一片）分行 → 本体各 24 行、
   每帧摆到同一位置；闪光允许跑进留白。**常驻检查要直接钉"10 帧本体包围盒完全一致"**
   （`_zf119_verify.py` A9b）—— 这条比"逐像素等于源图"更贴近玩家的观感。
'''

HAND_ADD = (u"    ⑤ **补充（用户实测抓到并当场修掉）**：第一版按「有不透明像素的行」分帧 ⇒ "
            u"闪光跑到本体上方的那一帧窗口被抬高 3 行 ⇒ **最后一帧往下弹**；改成**只按本体对齐**后，"
            u"10 帧本体都落在 y=4..27（贴图 sha1 `98aa8894…` → `e7db8d32…`，校验 63 → 65 项，"
            u"新刀 K165 专门复现这个弹跳）。\n")


def main():
    # ① §9：在 ZF119 小节末尾（"**成品**"那段之前）插入修正一节
    anchor = u"**成品**：**本轮没有新成品** —— `release\\PotatoST-0.11.jar` 仍是 ZF114 打的"
    raw = read(ARCH)
    if u"#### 六、⚠ 修正：你实测抓到" in raw:
        notes.append(u"档案 §9 修正节已在（跳过）")
    else:
        i = raw.find(anchor)
        if i < 0:
            fails.append(u"§9：找不到成品段锚点")
        else:
            write(ARCH, raw[:i] + FIX_SEC.lstrip(u"\n") + u"\n" + raw[i:])
            notes.append(u"档案 §9 加「修正」一节")

    # ② §4.95 补第 5 条
    sub_once(ARCH,
             u"4. **`.mcmeta`**：`{\"animation\": {\"frametime\": N}}`；帧数 × frametime = 一轮 tick 数"
             u"（本例 10×3 = 30 tick = 1.5 秒）。",
             u"4. **`.mcmeta`**：`{\"animation\": {\"frametime\": N}}`；帧数 × frametime = 一轮 tick 数"
             u"（本例 10×3 = 30 tick = 1.5 秒）。" + PITFALL_ADD,
             u"档案 §4.95 补第 5 条（按本体对齐）")

    # ③ §5 行与 §9 里的数字/哈希
    for old, new, label in (
        (u"`_zf119_verify.py`（**63 项**）、反证 8 把刀 | 见 §9 |",
         u"`_zf119_verify.py`（**65 项**）、反证 **9 把刀**（含 K165：复现「最后一帧下弹」）| 见 §9 |",
         u"§5 行：63 → 65 / 刀 8 → 9"),
        (u"| 常驻校验 | `_zf119_verify.py`（**63 项**）：",
         u"| 常驻校验 | `_zf119_verify.py`（**65 项**，修正后）：",
         u"§9 表：63 → 65"),
        (u"| 反证刀 | **K157~K164（8 把）**：",
         u"| 反证刀 | **K157~K165（9 把）**：",
         u"§9 表：刀 8 → 9"),
        (u"本轮构建产物 `build\\libs\\potato_s_t-0.11.jar` = **`ded5b30292b53547f04922f290e4ce0b6aca76af`**"
         u"（4,308,290 B）。",
         u"本轮构建产物 `build\\libs\\potato_s_t-0.11.jar` = **`f0a984b0f92e0cb6e94e26783a926c845fbbba64`**"
         u"（4,308,293 B，修正后的贴图）。",
         u"§9：构建产物换新"),
    ):
        sub_once(ARCH, old, new, label)

    # ④ 交接 §6 第 13 条补一句
    sub_once(HAND,
             u"    ④ 本轮**顺序失误**（先动盘后建备份）已记进 §4.94 与 `zf119_pre\\_补说明.txt`；",
             HAND_ADD + u"    ④ 本轮**顺序失误**（先动盘后建备份）已记进 §4.94 与 `zf119_pre\\_补说明.txt`；",
             u"交接 §6：补修正一条")

    print(u"\n".join(u"  [OK] " + n for n in notes))
    print(u"\n失败项 = %d" % len(fails))
    for f in fails:
        print(u"  !! " + f)
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())
