# 0.14 版本抬升：一次性执行清单（等用户/另一条线一句话）

> 用户在这次 bug 报告里写的是「**（0.14版本）**」，但仓库 `gradle.properties` 此刻仍是 `mod_version=0.13`。
> 抬版本要动的是**全工程共享**的东西（产物文件名、几十份门的活体数字），所以按 ZF147 的先例走一遍，
> 确认后照本清单一次做完。**在此之前不发 0.14 的包**（现在发的是 0.13，内容已经是 0.14 那批修复）。

## 一、为什么不能只改一行

1. `gradle.properties` 的 `mod_version` 是**全工程唯一一处**版本号（`neoforge.mods.toml` 引 `${mod_version}`）；
2. 改完构建产物变成 `build/libs/potato_s_t-0.14.jar`，发布件要改成 `release\PotatoST-0.14.jar`；
3. **多份门把自己的靶子钉在 0.13 上**（活体数字 + 文件名），必须一起跟平，否则"看起来发了新包、门却对不上"。

## 二、要改的文件（按优先级）

| 类别 | 文件 | 改什么 |
|---|---|---|
| 版本号 | `gradle.properties` | `mod_version=0.13` → `0.14` |
| 三份**断言 mod_version** 的老门（ZF147 先例点名的就是这三份） | `_zf73_verify.py` / `_zf78_verify.py` / `_zf79_verify.py` | "仍是 0.13 / 本轮没有 0.14 任务"这类断言跟到 0.14（**判据不放宽**，仍是逐字比那个常量） |
| 成品名/哈希的活体持有者 | `_zf149_verify.py`（WANT_SHA/WANT_SIZE + jar 名）、`_zf149_jar.py`、`_zf155_jarcheck.py`、`_zf156_jarcheck.py` | `PotatoST-0.13.jar` → `PotatoST-0.14.jar`；哈希/体积/class/配方/键数取自新产物 |
| 我的打包/文档脚本 | `_zf162_pkg.py`、`_zf166_repack.py`、`_zf180_docs.py`（及后续 `_zfNNN_*`） | 同上（jar 名 + 内嵌的旧版本号） |
| 文档 | `docs\多会话协作交接.md` §1 成品行、`docs\UpdateAnnouncement_EN.md` 本轮那段、`docs\开发档案.md` §5 本轮行 | 成品名/哈希/体积/class/配方/键数一起跟平（§4.159 三处联动） |

⚠ **不要动**：历史轮次的 `_zfNNN_*.py`（它们记的是当年的活体数字，改了就是篡改历史）、
以及档案/公告里**过去那些轮**的 `PotatoST-0.13.jar` 字样。

## 三、执行顺序（一次跑完）

```powershell
cd E:\PotatoST
# ① 改 gradle.properties（0.13 → 0.14）
python build\zftools\_zf181_bump.py --write      # 待写：见第四节
# ② 重打（产物名会变成 potato_s_t-0.14.jar）
.\gradlew build --offline --console=plain
Copy-Item build\libs\potato_s_t-0.14.jar release\PotatoST-0.14.jar -Force
# ③ 写 release\PotatoST-0.14.jar.sha1（纯哈希一行 + 换行）
# ④ 文档跟平（本轮那个 _zfNNN_docs.py 把 JAR 常量指到 0.14 再跑 --write）
# ⑤ 门：先跑三份版本门 + 四份成品门，再走一遍全门快照看"新增的红 = 0"
```

## 四、`_zf181_bump.py` 要干什么（还没写）

1. 改 `gradle.properties` 一行（并断言只剩一处 `mod_version`）；
2. 对**白名单**内的活体文件做替换：`PotatoST-0.13.jar`→`0.14`、`potato_s_t-0.13.jar`→`0.14`、
   `mod_version` 断言里的 `0.13`→`0.14`；
3. 打印"改了哪些文件、各几处"，并**拒绝**改历史脚本（白名单外一律不碰）。

## 五、当前状态

- 内容侧**已经就是 0.14 那批**：附魔修复（9 个装备类型标签）+ 磁铁块/6 个粗矿块 + 流体转化器三处修复等，
  已推送到 `90e6007`（远端同步）；
- 发布件仍是 `release\PotatoST-0.13.jar`（sha1 `c2edae6821e8c52ac7f2d9b3d1efdc3d8e02f06a`）；
- **等一句话**：抬到 0.14 就照上面做（含把 0.13 那份留在 `release\` 里当历史）。
