# ZF166 收尾清单（下一轮照着做，一步都不用想）

> 目标轮次：**ZF166**（0.13，流体转化器）。机器本体、语言、配方、探针、门、反证刀、文档**都已完成**，
> 只剩「重打成品 + 哈希三处联动 + 提交推送」这一步 —— 而它被**另一条线的在途探针**挡住了。

## 已经完成的（都有证据）

| 项 | 状态 | 证据 |
|---|---|---|
| 机器（方块/方块实体/菜单/界面/blockstate+2 model） | ✅ | `_zf166_verify.py` A/B 段全绿 |
| 四行注册 + `PotatoST.java` 两个能力 | ✅ | 门 B9（能量 + 流体各一次） |
| 12 个语言键（593→605 / 595→607）+ GUI 文案改短 | ✅ | 门 C5/C6 |
| 配方（生成器表 + 盘上 94 份，重出只多一份） | ✅ | 门 C1–C4、C7 |
| 真开服探针（IE + 沉浸原油）**20/0** | ✅ | `build/zftools/_zf166_probe_utf8.txt` |
| 反证刀 **6/6** | ✅ | `build/zftools/_zf166_falsify.log` |
| 常驻门 `_zf166_verify.py` **31/0** | ✅ | 刚才实测 |
| 文档脚本（§4.172 / §5 / §9 / 交接 37 / 公告） | ✅ 已落盘 | `_zf166_docs.log`：失败 0 |

## 挡着的是什么（两个，都是别人的或环境的）

1. **另一条线（ZF165）的临时探针还在源码树里**：`src/main/java/com/potatost/mod/Zf165Check.java`
   ⇒ `gradlew build` 打出来的 jar 里带着 `com/potatost/mod/Zf165Check.class`
   （`_zf162_pkg.py` 审计当场抓到：`!! jar 里有探针 class`）。
   **探针打进发布 jar = 玩家开服就会跑别人的测试代码**，所以这一份**不能发布、也不能提交**。
   → 等他们把探针摘掉（他们每轮收尾都会摘）再重打。
2. **gradle 锁争用**：盘上同时有 6 个 java 进程（另一条线在跑构建/服务端），
   `gradlew compileJava` 卡了两分钟以上（我把自己那个挂着的作业停了，免得互抢锁）。

## 下一轮的最小步骤（照抄即可）

```powershell
cd E:\PotatoST
# ① 等 Zf165Check.java 消失（多看几眼）；它没了再往下
Test-Path src\main\java\com\potatost\mod\Zf165Check.java
# ② 重打 + 审计（脚本已跟平：配方 94 / 键 605×4+607 / 不许有探针 class）
.\gradlew build --offline --console=plain
python build\zftools\_zf162_pkg.py --write
# ③ 文档 + 哈希三处联动（脚本会自己读新 jar 的 sha1/体积/class 数）
python build\zftools\_zf166_docs.py --write
# ④ 门：自己的 + 三条 jar 门 + 全门快照
python build\zftools\_zf166_verify.py
python build\zftools\_zf149_verify.py; python build\zftools\_zf149_jar.py
python build\zftools\_zf156_jarcheck.py; python build\zftools\_zf155_jarcheck.py
Copy-Item build\zftools\_zf164_gatesnap.py build\zftools\_zf166_gatesnap.py   # 再把 _zf166_verify.py 加进 NAMES
python build\zftools\_zf166_gatesnap.py --out build\zftools\_zf166_gatesnap.txt
# ⑤ 确认「新增的红 = 0」，然后提交（只 add 我自己的路径；成品那两行在脚本里已备好、记得取消注释）
python build\zftools\_zf166_commit.py --write --commit
git push origin main
```

## 提交前必须确认的三件事

1. `_zf166_commit.py` 里 `release\PotatoST-0.13.jar` 与 `.sha1` **那两行要取消注释**（它们现在被注释掉了，
   因为当前那份 jar 带着别人的探针，我故意没提交）。
2. `_zf166_docs.py` 跑完后再核对一次：`_zf149_verify.py` 的 `WANT_SHA` / `WANT_SIZE` / 「N classes, 43
   advancements, 94 recipes」那句、公告的 Download 段、交接 §1 的成品行 —— 三处必须是**同一个** sha1。
3. `run/server/mods` 里我留下的 `curios-neoforge-9.5.1+1.21.1.jar` **别删**：
   本模组现在（另一条线 ZF165 改的 `neoforge.mods.toml`）**硬依赖 Curios**，删了 `runServer` 直接起不来。

## 已知的、要如实告诉用户的

- 这台机器**还没有自己的贴图**：block model 复用 `potato_s_t:block/fluid_exchanger`（占位），
  用户给画之前都长这样。
- 用户若要"输入罐也能手倒"之外的手势/更细的样板规则，都是一处改（`FluidConverterBlock.useItemOn`）。
