
## ZF154（0.12）：采油机加**顶/底渲染**

用户原话：「采油机的放素材了」—— 素材 `采油机顶部和底部_001.png`
（3059 B / sha1 `64fcb674c2ff` / 16×16 / 8 位 RGBA / **整张不透明** / 12 色），
文件名点明是**顶面与底面**。

### 一、改了什么

`models/block/oil_pump.json`：**`cube_all` → `cube_bottom_top`**
（与 ZF130 处理「锂电池构造器 / 柴油发电机控制器」**同一套做法**，
工程里 `lithium_battery` 也是这个父级）：

| 位置 | 用哪张 |
|---|---|
| 顶 / 底 | `block/oil_pump_top.png` = **用户新给的素材**（原字节复制，3059 B） |
| 四个侧面 | `block/oil_pump.png` = ZF109 那张程序生成占位（151 B），**一个字节没动** |

顶与底**用同一张**（`top`/`bottom` 两个槽指同一个文件），与那两台机器写法一致。
物品模型不动（它父级到方块模型；`cube_bottom_top` 的物品图标取**顶面**）。

**新图长什么样**：深灰底板 + **四周橙色 L 形角**（油井井架的框架感）
+ 中间**黄色的抽油机构**（横梁贯穿 + 两侧斜撑 + 底部黑色泵体）。
现有那张侧面是"橙面板 + 四角铆钉 + 朝下吸油管"的侧视 —— 两张各司其职，不冲突。

### 二、⚠ 连带：`_zf109_verify.py` 的两条判据跟到新事实

那轮的钉子原来是：

```python
eq(u"方块模型父级 = cube_all", "minecraft:block/cube_all", bm.get("parent"))
eq(u"方块模型贴图", "potato_s_t:block/oil_pump", bm.get("textures", {}).get("all"))
```

**判据不删、按新事实收紧（不是放宽）**：父级改成 `cube_bottom_top`；
贴图从"一个 `all` 槽"改成"**三个槽各自点名**"——
这比原来**更严**：原来只查一个槽，现在 top / bottom / side 三个都查，
而且顶/底必须是新贴图、侧面必须仍是原贴图 ⇒「有没有偷懒把六面都换成新的」也被钉住了。

### 三、验收

| 项 | 结果 |
|---|---|
| `_zf154_apply.py` | 0 失败（前置断言 → 备份校验 → 素材体检 → 原字节上线 → 模型改写回读 → 物品模型 → 凭据登记） |
| 产物 | `build/resources/.../block/oil_pump_top.png` = 3059 B / sha1 `64fcb674c2ff`，与源**逐字节一致** |
| `compileJava` / `processResources` | **BUILD SUCCESSFUL** |
| `TextureCheck` / `ModelCheck` / `SoundCheck` / `JsonCheck` | 全 **0 失败** |
| `_zf109_verify.py` | 采油机那两条已绿（其余红项是别的线的旧账：四语言键序不一致等） |
| 凭据 | 48 条（新贴图登记 `原名`） |
| 备份 | `zf154_pre/`（被改的模型 + 凭据） |

> 📄 对照图 `_zf154_preview.png`：上=现状（六面同一张）／下=提议（顶底换新、四面不动）。
