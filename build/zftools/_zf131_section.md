
## ZF131（0.11）：大型柴油发电机的工作循环音（**用户给的音频**）

用户原话：「柴油发电工作时加个音效 放素材了」—— 素材 `build/用户素材/柴油发电机工作.mp3`
（346070 B，13:13 放进来的）。

### 一、素材规格（本来就是对的）

| 项 | 实测 | 结论 |
|---|---|---|
| 格式 | MP3 / MPEG_LAYER_III | 要转 OGG Vorbis |
| 采样率 | **44100 Hz** | ✅ 正好（不是 44100 会变速变调） |
| 声道 | **单声道** | ✅ 正好（立体声在 MC 里不吃距离衰减） |
| 时长 | 10.81 s | — |
| RMS / 峰值 | 0.1464 / 0.733 | 要降响度（工程口径 0.10） |
| 首尾静音 | 0.086 s / 0.025 s | 很短 |

⇒ 不需要降混、不需要重采样，只要掐头尾 + 循环 + 对齐响度。

### 二、⚠ 这一条**不能照抄** ZF64 那次的参数（本轮的主要工作）

按工程惯例先转了一版：`--start 0.09 --end 10.79 --crossfade 400`（与合金炉 ZF64 同一套），
工具回读的**接缝首尾差 = 0.1061** —— 比合金炉那次的 0.0008 **差两个数量级**，
每绕一圈都会"咔"一声。

根因：**合金炉那次素材首尾本来就淡到接近 0，默认切法够用；这段柴油机声不是。**
`MakeSfx.py --loop` 的接缝质量取决于素材自身首尾是否连续，`--crossfade 400` 只是
当时的取值，**不是规律**。

于是把 `(start, end, crossfade)` 当参数搜了一遍。判据**两条**，都在**真编码出来的 OGG**
上量（不是算中间态 —— 中间态差 1 个样本就能让结论差一个数量级，见 §4.112）：

| 判据 | 含义 | 阈值 |
|---|---|---|
| **接缝样本差** | `\|last − first\|` | ≤ 0.010 |
| **末→首电平差** | `\|RMS(末 0.5s) − RMS(首 0.5s)\| / 全段 RMS` | ≤ 3.5% |

**第二条是搜的过程中补上的**：只看接缝样本差会挑出
「样本差 0.0003、但末块 0.100 → 首块 0.081（差 **19.4%**）」的解 ——
绕回开头时音量先塌一下，**人耳对电平台阶比单个样本的"咔"敏感得多**。

**最终配方**：`--start 0.086 --end 10.550 --crossfade 300 --target-rms 0.10`

| 成品指标 | 值 |
|---|---|
| 规格 | **单声道 44100 Hz Ogg Vorbis，10.16 s** |
| RMS / 峰值 | 0.0981 / 0.493（与其它机器循环一致） |
| 接缝样本差 | **0.0136** |
| 末→首电平差 | **3.13%**（实测 1.98%；素材本身的块间抖动就是 4.49% ⇒ 落在噪声里） |
| 落盘 | `sounds/diesel_generator_running.ogg`（90109 B） |

### 三、接线（§6.5 那张「4 处联动」表逐条落实）

| # | 位置 | 做了什么 |
|---|---|---|
| 1 | `sounds/diesel_generator_running.ogg` | 上面那份成品 |
| 2 | `assets/potato_s_t/sounds.json` | 加 `diesel_generator_running` 条目（**不带** `stream` —— 那是唱片那种长音频才要的） |
| 3 | `sound/ModSounds.java` | `SOUND_EVENTS.register("diesel_generator_running", …)` |
| 4 | `DieselGeneratorBlockEntity` | `running` 字段 + `clientTick()` 调 `MachineRunningSound.update(...)` + `getUpdateTag`/`getUpdatePacket` + `syncedRunning` 翻转才发包 + `running` 写进 `saveAdditional` 也读回 |

方块侧的 `getTicker` **本来就是双端 ticker**（ZF125 建这台机器时就按 §4.26 写对了），
所以这次一行都没动方块。

### 四、⚠ 本轮自己抓出来的一个真 bug（差点交出去）

第一版照合金炉的写法：
```java
boolean before = this.running;
serverTickBody();          // 里面：this.running = false; … 真烧油才 this.running = true;
if (before != this.running) sync();
```
**稳态运行时 `before` 与 `after` 都是 true**（tick 开头清零、真烧油又置真），
⇒ 条件永不成立 ⇒ **一次都不发包** ⇒ 客户端永远收不到"在运行" ⇒ **声音一次都不响**。

改成拿**上次真正同步出去的值**比：
```java
this.running = false;                    // 每 tick 先清零（世界卸载那一 tick 也不留 stale true）
if (this.level != null) serverTickBody(); // 只有四个门全过、真扣了油才置真
if (this.syncedRunning != this.running) { // ★ 与"上次发出去的值"比
    this.syncedRunning = this.running;
    sync();
}
```
`_zf131_chain.py` 专门有一条断言钉这个（"只用 syncedRunning 比，**不是**本 tick 头尾比"）。

### 五、验收

`_zf131_chain.py`（**常驻**，端到端 4 处联动 + 音频规格 + 双端 ticker + 清零/置真顺序）**27 项全绿**；
`SoundCheck.py` 0 失败（9 个音效事件）；`TextureCheck` / `ModelCheck` / `JsonCheck` 均 0 失败；
`gradlew compileJava` → BUILD SUCCESSFUL。

> 运行时"真的响了"的免费信号（§3）：日志里**没有** `Missing sound for event: potato_s_t:diesel_generator_running`
> ⇒ 文件链路已被证明。
