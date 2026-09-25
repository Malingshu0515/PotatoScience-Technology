# -*- coding: utf-8 -*-
u"""_zf119_docs.py —— ZF119 文档：档案 §5/§9/§4 + 交接文档活体数字 + 英文公告"""
import io
import sys

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

ROOT = r"E:\PotatoST"
ARCH = ROOT + r"\docs\开发档案.md"
HAND = ROOT + r"\docs\多会话协作交接.md"
ANN = ROOT + r"\docs\UpdateAnnouncement_EN.md"

fails, notes = [], []


def read(p):
    return io.open(p, encoding="utf-8").read()


def write(p, t):
    io.open(p, "w", encoding="utf-8", newline=u"").write(t)


def insert_after_prefix(path, prefix, block, label):
    raw = read(path)
    probe = [l for l in block.split(u"\n") if l.strip()][0]
    if probe in raw:
        notes.append(label + u"（已经在盘上，跳过）")
        return True
    lines = raw.split(u"\n")
    hits = [i for i, l in enumerate(lines) if l.startswith(prefix)]
    if not hits:
        fails.append(u"%s：找不到行首前缀 %r" % (label, prefix[:40]))
        return False
    lines[hits[0] + 1:hits[0] + 1] = block.split(u"\n")
    write(path, u"\n".join(lines))
    if probe not in read(path):
        fails.append(u"%s：回读失败" % label)
        return False
    notes.append(label)
    return True


def insert_before_exact(path, exact, block, label):
    raw = read(path)
    probe = [l for l in block.split(u"\n") if l.strip()][0]
    if probe in raw:
        notes.append(label + u"（已经在盘上，跳过）")
        return True
    if raw.count(exact) != 1:
        fails.append(u"%s：锚点出现 %d 次" % (label, raw.count(exact)))
        return False
    write(path, raw.replace(exact, block + exact, 1))
    if probe not in read(path):
        fails.append(u"%s：回读失败" % label)
        return False
    notes.append(label)
    return True


def sub_once(path, old, new, label):
    raw = read(path)
    if new in raw and old not in raw:
        notes.append(label + u"（已经是新值，跳过）")
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


ROW = (
    u"| ZF119 | **新建 `zf119_pre`**（136 份改前件：`ModItems.java` + 四份 lang + `c:ingots` 父标签 + "
    u"全部常驻校验脚本 + 3 份文档 + 旧成品 jar 与 `.sha1` + 盘上现有 `.mcmeta`；逐份核哈希、失败 0。"
    u"⚠ **2 份事后补账**：① `ModItems.java`（**建备份之前就动了盘** —— 本轮的顺序失误，见 §9 第五节）；"
    u"② `PotatoST.java`（探针挂载点，**ZF117 之后第二次**漏进清单）—— 两份都用「① git blob + "
    u"③ 减法重建」双路逐字节证明，见 `zf119_pre\\_补说明.txt`） "
    u"| 0.11：**振金锭（新物品 + 10 帧动画贴图，没有配方）**。用户原话：「加个振金锭（目前没配方）"
    u"这是振金锭贴图 做成动态贴图 3t播放一帧」。① **素材体检**：真 PNG / 32×280 / 8 位 RGBA / "
    u"零半透明 / 57 色；内容是 **10 个 32×24 的锭** 竖着堆（间距 6,4,7,4,4,4,4,4，最后两个挨着）—— "
    u"⚠ **32×280 不能直接当动画用**：MC 要求「宽 × (宽 × 帧数)」，280/32 = 8.75 ⇒ 游戏按 **8 帧**截断"
    u"（整数除法），白丢 2 帧；② **重排成 32×320（10 帧）**，帧尺寸与摆位**照盘上 `titanium_ingot.png`**"
    u"（ZF60 用户自己画的：32×32、内容 32×24、上下各留 4 行 —— 与本图内容尺寸一模一样），"
    u"全程只做整行搬运（**零重采样**），回读断言逐像素等于源；③ `.mcmeta` = "
    u"`{\"animation\": {\"frametime\": 3}}` ⇒ 3 tick 一帧、10 帧 = 30 tick = **1.5 秒一轮**；"
    u"④ 物品：`ModItems` 注册 + 创造页（§4.82）+ 模型 + 三个 `c:` 标签（`c:ingots/vibranium` / "
    u"`c:vibranium_ingots` / 父 `c:ingots`）+ 四语言 1 键（**448 → 449**，23 份往轮校验一起重定目标）；"
    u"⑤ **没有配方**（用户明说「目前没配方」）⇒ 常驻检查扫全表：任何配方产物都不许是它；"
    u"⑥ 证据：真服务端探针 `Zf119Check`（**20 项 ALL OK**：注册 / 名字 en_us 念得出 / 三个标签 / "
    u"1350 条配方里没有一条产出它 / **从 classpath 读资源**解 IHDR 得 32×320、读 mcmeta 得 frametime 3、"
    u"读模型得 layer0）、`_zf119_verify.py`（**62 项**）、反证 8 把刀 | 见 §9 |"
)

SEC9 = u'''
### ZF119（0.11）振金锭：新物品 + 10 帧动画贴图（**没有配方**）—— **未打包**

用户原话：「加个振金锭（目前没配方）这是振金锭贴图 做成动态贴图 3t播放一帧」

#### 一、素材体检（`_zf119_intake.py`，只读）

| 项 | 实测 |
|---|---|
| 真格式 | **PNG**（25 字节头 `89 50 4e 47` —— 本工程被"名字叫 .png 实际是 webp/jpg"坑过 3 次，每次都先验头） |
| 尺寸 / 位深 | **32 × 280**，8 位，颜色类型 6（RGBA） |
| alpha | 全透明 39.6%、**半透明 0 像素**、不透明 5411 |
| 用色 | 57 种 |
| 内容 | **10 个锭，每个 32×24**，竖着堆（间距 6,4,7,4,4,4,4,4 —— 最后两个挨着，没有分隔行） |

⚠ **32×280 不能直接当动画贴图用**：MC 的动画贴图必须满足「宽 × (宽 × 帧数)」；
`280 / 32 = 8.75` ⇒ 游戏按整数除法取 **8 帧**，后两帧直接被丢掉。所以必须重排。

#### 二、重排成 32×320（10 帧 × 32）—— 零重采样

帧尺寸与**内容摆位**不靠感觉：量了盘上全部物品贴图，**`titanium_ingot.png`（ZF60 用户自己画的那张）
= 32×32、内容 32×24、上下各留 4 行** —— 与本图的内容尺寸**一模一样** ⇒ 照它摆：

```
每帧 32×32：  y=0..3 透明 / y=4..27 = 源图里那个锭的 24 行 / y=28..31 透明
```

全程**只做整行搬运**（不缩放、不插值）。回读断言：10 帧 × 32×24 **逐像素等于源图**、留白全透明。

`.mcmeta`：`{"animation": {"frametime": 3}}` ⇒ **3 tick 一帧**（用户原话），10 帧 = **30 tick = 1.5 秒**一轮。

#### 三、物品本身

| 项 | 落点 |
|---|---|
| 注册 | `ModItems.VIBRANIUM_INGOT` → `potato_s_t:vibranium_ingot` |
| 创造页 | `output.accept(VIBRANIUM_INGOT.get())`（§4.82：漏了就是"物品栏看不见、JEI 搜不到"） |
| 模型 | `models/item/vibranium_ingot.json`，`layer0 = potato_s_t:item/vibranium_ingot` |
| 标签 | `c:ingots/vibranium` + `c:vibranium_ingots` + 父 `c:ingots`（照 star_steel 先例；矿物/锭一律走 `c:`） |
| 语言 | 四语言各 **1** 键（振金锭 / Vibranium Ingot / ヴィブラニウムインゴット / Слиток вибраниума）⇒ 键数 **448 → 449** |
| 配方 | **没有**（用户明说「目前没配方」）—— 常驻检查扫全表：任何配方产物都不许是它 |
| 下游 | 也没有（粗振金 → 振金锭 → ？留到以后；与"硫"当初同一条口径：用户没说的不发明） |

#### 四、证据

| 项 | 值 |
|---|---|
| 探针 | `Zf119Check.java`（真 `runServer`）**20 项 ALL OK**：注册 / 名字（en_us 键生效）/ 三个 `c:` 标签 / **1350 条配方里没有一条产出它** / **从 classpath 读资源**：解 PNG 的 IHDR 得 **32×320**、读 `.mcmeta` 得 **frametime 3**、读模型得 layer0 指向自己 |
| 探针存档 | `build\\zftools\\check\\Zf119Check.java`（12335 B，sha1 `9f02ab7c…`，**先抄后删**） |
| 常驻校验 | `_zf119_verify.py`（**62 项**）：**独立再数一遍帧**（不 import 出图那个脚本）、逐帧逐像素与源图比、留白/半透明、帧真的在动、mcmeta、物品/模型/标签/无配方、键数 449、23 份往轮校验无残留 448 |
| 反证刀 | **K157~K164（8 把）**：frametime 改 1 / 删 mcmeta / 贴图高度改 288（9 帧）/ 内容摆位挪一行 / 删语言键 / 删创造页那行 / 删 `c:` 标签那一行 / 给它加一条配方 —— 每把都必须咬住指定的检查 |
| 活体数字 | 语言键 **448 → 449**（23 份往轮校验 + 英文公告一起重定目标）；物品 +1；贴图 +1（动画）|
| ⚠ 客户端行为 | **动画长什么样只能肉眼验**：无头服务端验得到"文件几何 + mcmeta 数值 + 模型指向"，验不到"游戏里真的在闪" |

#### 五、⚠ 我这一轮的**顺序失误**（如实记，别学）

1. **建 `zf119_pre` 之前就动了盘**：`ModItems.java` 的两处插入是先做的（贴图 / `.mcmeta` 是**新建**文件，
   不算改盘，但也一并记在案）。补救：`ModItems.java` 走**事后补账** ——
   ① `git cat-file blob HEAD:…`（本轮开工前它是干净的：三个 diff 都空）；
   ② 减法重建（把本轮插进去的两段删掉）⇒ 两条路**逐字节相同**（sha1 `972450d25a333c7c…`）。
2. **`PotatoST.java` 又漏进改前件清单了**（ZF117 之后**第二次**，那次我还写过"下不为例"）。
   补救：同样双路补账 + **新立一条常驻检查**（`_zf119_verify.py` 的 F3：只要本轮挂了探针，
   改前件清单里就必须有 `PotatoST.java`，漏了当场红）。
3. **本轮起的新口径**：脚本第一句就是建备份；**先建备份，再动第一个字节**。
   这两笔失误都记在 `zf119_pre\\_补说明.txt` 与 §4.94。

**要你实测的**（进游戏）：

1. 创造页最后应当有**振金锭**（图标本身就在动：3 tick 一帧、10 帧一轮 = 1.5 秒）；
2. JEI 里搜「振金锭」**搜得到物品、搜不到配方**（这是对的：目前没配方）；
3. 名字四语言：振金锭 / Vibranium Ingot / ヴィブラニウムインゴット / Слиток вибраниума。

**成品**：**本轮没有新成品** —— `release\\PotatoST-0.11.jar` 仍是 ZF114 打的 **`303c5d468b96826ef6836b0a4e54ccb8a539557c`**（432 键）。
本轮构建产物 `build\\libs\\potato_s_t-0.11.jar` = **`ded5b30292b53547f04922f290e4ce0b6aca76af`**（4,308,290 B）。

'''

PITFALLS = u'''
### 4.94 【流程雷】"先建备份再动盘"这条，我自己连栽两次（0.11 ZF117 / ZF119）

- **ZF117**：探针要往 `PotatoST.java` 挂一行，我**挂完才建备份** ⇒ 改前件里没有它，只能事后补证明，
  当场写下「下不为例：要挂探针的轮次，`PotatoST.java` 必须进改前件清单」。
- **ZF119**：**同一个坑又踩了一次** —— `PotatoST.java` 再次漏进清单；而且这轮更糟：
  **建 `zf119_pre` 之前就已经改了盘**（`ModItems.java` 的两处插入先做了）。

**补救（两条路互证，不是"看着差不多"）**：

1. `git cat-file blob HEAD:<path>` 取开工前那份（前提：本轮开工前该路径是干净的 ——
   用 `git diff` / `git diff --cached` / `git status` 三条都空来证明）；
2. **减法重建**：把本轮插进去的文本从盘上文件里删掉 ⇒ 必须与 ① **逐字节相同**。
   两份都以等级 ①+③ 记进 `_补说明.txt` 与 `_sha1.txt`。

**规矩**：

1. **脚本第一句就是建备份**；备份没落地之前，一个字节都不许改（新建文件也一样记在 `_newfiles.txt`）。
2. **要挂探针的轮次，改前件清单里必须有 `PotatoST.java`** —— 现在这条**常驻**了：
   `_zf119_verify.py` 的 F3 检查「改前件清单里有 PotatoST.java」，漏了当场红。
3. 别指望"我记得"：**这条已经失败过两次**，靠门比靠记忆便宜。

### 4.95 【素材雷】用户给的"动画长条"不能直接塞进资源树：MC 要求「宽 × (宽 × 帧数)」（0.11 ZF119）

用户给的 `振金锭.png` 是 **32 × 280**：10 个 32×24 的锭竖着堆。直觉是"这就是 10 帧，直接放进去"——
但 MC 的动画贴图尺寸必须是 **宽 × (宽 × 帧数)**：

```java
// net.minecraft.client.renderer.texture.atlas.SpriteContents / AnimationMetadataSection
frameCount = frames.isEmpty() ? height / width : frames.size();   // ← 整数除法
```

`280 / 32 = 8`（**8.75 被截断**）⇒ 游戏只播 **8 帧**，最后两帧**静默消失**，
而且因为每帧按 32 行切，第 8 帧还会把"第 9 个锭的上半截"当帧内容 —— 看起来像"动画卡住/串帧"。

**规矩（做动画贴图四步）**：

1. **先数帧**：扫"哪一行没有不透明像素"得到分隔行 ⇒ 段数 = 帧数（本例：10）。
   注意**最后两段可能挨着**（没有分隔行），要按"轮廓骤降"补一刀，别少数一帧。
2. **再定帧格**：拿盘上**同类**贴图当基准 —— 本例量到 `titanium_ingot.png`（用户自己画的 32×32 锭）
   是「内容 32×24 + 上下各留 4 行」，而新素材的内容尺寸**一模一样** ⇒ 照它摆，不用猜。
3. **重排只做整行搬运**（零重采样），写完**回读**：逐帧逐像素与源图比、留白必须全透明。
4. **`.mcmeta`**：`{"animation": {"frametime": N}}`；帧数 × frametime = 一轮 tick 数（本例 10×3 = 30 tick = 1.5 秒）。
   ⚠ 动画**只能肉眼验**：无头服务端验得到文件几何与 mcmeta，验不到"游戏里真的在动"。

'''

ANN_ENTRY = u'''
- **Vibranium Ingot (0.11 ZF119)** - a new item with an **animated icon**: 10 frames, 3 ticks per frame (a 1.5 second loop). It has **no recipe yet** (by request) and nothing consumes it yet, so for now it is a creative-only ingot that drops nothing and crafts nothing. Its item id is `potato_s_t:vibranium_ingot`, and it is tagged `c:ingots/vibranium`, `c:vibranium_ingots` and `c:ingots` like every other ingot in this mod.
'''


def main():
    insert_after_prefix(ARCH, u"| ZF118 |", ROW, u"档案 §5 加 ZF119 行")
    insert_before_exact(ARCH, u"## 10. 备份策略", SEC9, u"档案 §9 加 ZF119 小节")
    insert_before_exact(ARCH, u"## 7. 权威情报来源（怎么查原版行为，别靠记忆）",
                        PITFALLS, u"档案 §4 加 4.94/4.95")
    sub_once(HAND,
             u"| 语言键数 | **448 键 × 4**（zh_cn / en_us / ja_jp / ru_ru，四份键集合必须完全一致） | "
             u"翻译润色线正在重写**值**；键数的活体数字：… → 408（ZF109）→ 432（ZF114）→ **448**（ZF117） |",
             u"| 语言键数 | **449 键 × 4**（zh_cn / en_us / ja_jp / ru_ru，四份键集合必须完全一致） | "
             u"翻译润色线正在重写**值**；键数的活体数字：… → 432（ZF114）→ 448（ZF117）→ **449**（ZF119 振金锭） |",
             u"交接 §1 语言键数")
    sub_once(HAND,
             u"| 未发布的构建 | `build\\libs\\potato_s_t-0.11.jar` = `7f0a325002a415a9ee1f0b0a58ce3bc543b389cc`"
             u"（4,307,139 B，ZF117 打的：448 键 + 35 条进度）",
             u"| 未发布的构建 | `build\\libs\\potato_s_t-0.11.jar` = `ded5b30292b53547f04922f290e4ce0b6aca76af`"
             u"（4,308,290 B，ZF119 打的：449 键 + 35 条进度 + 振金锭动画贴图）",
             u"交接 §1 未发布的构建")
    raw = read(HAND)
    if u"13. **ZF119 的账**" in raw:
        notes.append(u"交接 §6 已有 ZF119 条目（跳过）")
    else:
        anchor = u"12. **ZF118 的账（本轮真欠的）**"
        i = raw.find(anchor)
        if i < 0:
            fails.append(u"交接 §6：找不到 §12 那条")
        else:
            j = raw.find(u"\n", raw.find(u"\n", raw.find(u"\n", i) + 1) + 1) + 1
            add = (u"13. **ZF119 的账**：① 振金锭**没有配方**（用户明说「目前没配方」）—— "
                   u"常驻检查会一直盯着「任何配方产物都不许是它」，等哪天给配方，把那条改成正向断言；\n"
                   u"    ② 它**没有下游**（粗振金 → 振金锭 → ？）—— 与「硫」当初同一条口径：用户没说的不发明；\n"
                   u"    ③ 动画贴图是**客户端行为**，无头服务端验不到 ⇒ 要用户肉眼确认（3 tick 一帧、10 帧一轮 = 1.5 秒）；\n"
                   u"    ④ 本轮**顺序失误**（先动盘后建备份）已记进 §4.94 与 `zf119_pre\\_补说明.txt`；"
                   u"`PotatoST.java` 第二次漏账 ⇒ 现在有常驻检查（`_zf119_verify.py` F3）。\n")
            write(HAND, raw[:j] + add + raw[j:])
            notes.append(u"交接 §6 追加 ZF119 第 13 条")
    raw = read(ANN)
    if u"Vibranium Ingot (0.11 ZF119)" in raw:
        notes.append(u"公告已有 ZF119 条目（跳过）")
    else:
        if not raw.endswith(u"\n"):
            raw += u"\n"
        write(ANN, raw + ANN_ENTRY)
        if u"Vibranium Ingot (0.11 ZF119)" in read(ANN):
            notes.append(u"公告追加 ZF119 变更条目")
        else:
            fails.append(u"公告：追加条目回读失败")

    print(u"\n".join(u"  [OK] " + n for n in notes))
    print(u"\n失败项 = %d" % len(fails))
    for f in fails:
        print(u"  !! " + f)
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())
