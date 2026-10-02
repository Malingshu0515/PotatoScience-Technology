
## ZF143（0.11）：四种锭（银 / 镍 / 铝 / 钴）换上手绘新图

用户原话：「把四种锭的图优化一下 我放用户素材里了」

素材（都在 `build/用户素材/`，23:37 一次放的，各约 3 KB）：

| 素材 | 落到哪 | 大小 | sha1(前12) |
|---|---|---|---|
| `银锭.png` | `textures/item/silver_ingot.png` | 3067 B | `d117b9fdc72a` |
| `镍锭.png` | `textures/item/nickel_ingot.png` | 3047 B | `d34b5bca78b8` |
| `铝锭.png` | `textures/item/aluminum_ingot.png` | 3085 B | `bb47d148f325` |
| `钴锭.png` | `textures/item/cobalt_ingot.png` | 3104 B | `0581cfa56669` |

### 一、「优化」指的是什么（有对照图为证）

被换掉的四张现有图是 **160×160 的程序生成占位色块**（每张只有 8~10 色）。
游戏按 16×16 渲染 ⇒ 它们在包里**几乎是一坨白/灰，四种金属分不出来**
（📄 `_zf143_preview.png` 左列 = 按 16×16 采样后的"游戏所见"）。

新图是 **16×16 / 8 位 RGBA / 零半透明 / 17~18 色**，四种金属颜色明确分开：

| 金属 | 平均色 | 观感 |
|---|---|---|
| 银 | `#acacac` | 中性冷白灰，高光最亮 |
| 镍 | `#9c928b` | 偏暖的米灰（镍本来就是暖调金属） |
| 铝 | `#8c8c8c` | 干净的中性灰 |
| 钴 | `#7e7b9b` | 紫蓝（与星璨钢一族，但更沉） |

**凭什么断定这是"四种锭"**：四张的形状**完全相同**（不透明都恰好 135 像素），
只有颜色不同 ⇒ 一套同模的四种金属锭；且文件名与物品一一对应。

### 二、改了什么

| 文件 | 变化 |
|---|---|
| `textures/item/{silver,nickel,aluminum,cobalt}_ingot.png` | **160×160 占位 → 16×16 手绘**（原字节复制，一个像素没重编码） |
| `models/item/*_ingot.json` | **一个都没改** —— `layer0` 本来就指向自己 |
| `build/zftools/zf143_pre/*.png` | 四张旧占位的逐字节备份（可回退） |
| `build/用户素材/{silver,nickel,aluminum,cobalt}_ingot.png` | ASCII 留档（原件仍留在原处） |

### 三、验收

| 项 | 结果 |
|---|---|
| `_zf143_apply.py` | 0 失败（体检 → 备份校验 → 原字节上线 → 模型指向 → 凭据登记，五段全绿） |
| 产物 | `build/resources/.../item/` 里四张都是 16×16、sha1 与源**逐字节一致** |
| `TextureCheck` | **警告 27 → 24**（那四张 160×160 的尺寸警告随占位一起消失），失败 0 / 待画 13 |
| `ModelCheck` / `SoundCheck` / `JsonCheck` | 全 0 失败 |
| `compileJava` / `processResources` | **BUILD SUCCESSFUL** |
| 凭据 | 41 条（四件登记 `原名`，原件保留） |

> 📄 对照图 `_zf143_final.png`：**左=旧（游戏所见）｜中=新上线｜右=留档**，三份逐像素一致。
