# -*- coding: utf-8 -*-
u"""_zf188_docs.py —— ZF188 文档落笔（§4.188 + §5 行 + §9 段 + 交接第 46 条 + 英文公告 +
中英双语公告）+ 哈希三处联动。

主题：装了「配置界面」(Configured) 就让位给它（没装则回落 NeoForge 自带界面）。
跑法：python build\\zftools\\_zf188_docs.py [--write]
"""
import hashlib
import io
import json
import os
import re
import sys
import zipfile

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding=u"utf-8", errors="replace")

ROOT = r"E:\PotatoST"
DOC = os.path.join(ROOT, "docs", u"开发档案.md")
HAND = os.path.join(ROOT, "docs", u"多会话协作交接.md")
ANN = os.path.join(ROOT, "docs", "UpdateAnnouncement_EN.md")
BIL = os.path.join(ROOT, "docs", u"0.13_0.14更新公告与介绍_中英.md")
V149 = os.path.join(ROOT, "build", "zftools", u"_zf149_verify.py")
JAR = os.path.join(ROOT, "release", u"PotatoST-0.14.jar")

S4 = u"""### 4.188 【接入雷】「联动配置界面」要**让位**，而且要把"让不让位"抽成**可验的纯函数**（0.14 ZF188）

用户拍板（原话追问「不需要[配置界面]这个mod吗」之后二选一）：「**让「配置界面」(Configured) 接管；
没装就用 NeoForge 自带的**」。

**① 先搞清楚对方怎么判，再决定我们做什么。** Configured 2.6.3（本机
`run\\client\\mods\\[配置界面] configured-neoforge-1.21.1-2.6.3.jar`）的
`com.mrcrayfish.configured.client.ClientConfigured.generateConfigFactories` 给**每个模组**跑一段 lambda，
反编译出来是：

```java
if (container.getCustomExtension(IConfigScreenFactory.class).isPresent()
        && !Config.isForceConfiguredMenu()) return;          // 模组自带界面 ⇒ 它让位
Map<ConfigType, ?> map = ClientHandler.createConfigMap(new ModContext(modId));
if (map.isEmpty()) return;                                    // 没有任何配置的模组它也不管
LOG.info("Registering config factory for mod {}. Found {} config(s)", modId, count);
container.registerExtensionPoint(IConfigScreenFactory.class, ...);   // ← 接管模组列表那个「配置」按钮
```

⇒ **结论**：ZF186 注册了自带的 `ConfigurationScreen`，恰恰**挡住了** Configured（它一看你有界面就不接管）。
「联动」的正确做法**不是**"再注册一个更好看的界面"，而是 **它装了就別注册**。
（反证：`getCustomExtension` / `registerExtensionPoint` 这两个符号在它 jar 里**只出现在
`ClientConfigured` 一个类**里 —— 常量池搜过 ⇒ 没有第二条路径绕开这个让位判据。）

**② 把策略抽成纯函数，否则这条根本没法验。** 这台机器上跑不了真客户端 GUI（没有可用图形会话），
但策略的**真值表**可以在真服务端验 ⇒
`PotatoSTConfig.shouldRegisterOwnConfigScreen(boolean configuredModPresent)`（就是 `return !configuredModPresent;`），
客户端只负责把 `ModList.get().isLoaded("configured")` 传进来。
探针 `Zf188Check` 三条：没装 ⇒ 自己注册 / 装了 ⇒ 让位 / **现场事实**（本服务器 mods 里确实没有 configured）
⇒ 走"自己注册"那一支 —— 策略与真实查询接得上。

**③ ⚠ 代价写在代码注释和 §9 里，不藏。** 装了 Configured 之后，**NeoForge 自带那个界面就点不到了**
（那个按钮归它）。要回来自带界面：在 Configured 配置里关掉强制接管，或卸掉它。

**④ 不许把"可选"变成"必需"。** `configured` 这个 modid 只作为**字符串**出现在客户端类里
（`CONFIGURED_MODID`），`neoforge.mods.toml` 与改前**逐字节相同** —— 门 A3 两条都钉着
（反证刀 K4「漏进公共类」/ K5「加一条必需依赖」各砍一刀）。

**⑤ 诚实边界。** 客户端那一半（Configured 打完 `Registering config factory for mod potato_s_t. Found 1 config(s)`）
在没图形会话的机器上**验不了** ⇒ 探针报告里明写"由用户实测、探针没验 GUI"，门 B3 钉住**这句声明必须在**
（不许把"策略验过了"说成"界面验过了"）。要你实测时看的就是 `logs/latest.log` 里那一行。

**⑥ 顺带一个小观察（不是问题，是判据写法的功劳）**：回归再跑 `Zf186Check` 时，`run\\server` 里还留着
上一轮探针 `saveInto` 存下的黑洞存档，服务器一起来 `loadFrom` 就把它读回来了 ⇒ D1 那一行的数字是
**1→2** 而不是 **0→1**。判据写的是**相对值**（`activeCount() == before + 1`）所以照样绿 ——
要是当初写成"等号右边必须是 1"，这一跑就会假红。

"""

ROW = u"""| ZF188 | **新建 `zf188_pre`**（**118 份**改前件：2 份将改源码 + `neoforge.mods.toml` + 4 份文档 + 6 份本轮要动的脚本 + 上一轮探针 + 旧成品与 `.sha1` + **全部常驻门 102 份**；逐份核 sha1 + 回读，失败 0。⚠ 轮号 `_zf188_*` 查过没人占（§4.147）） | **0.14：配置界面归属 —— 装了「配置界面」(Configured) 就让位给它**（用户拍板见 §9）。① 反编译 Configured 2.6.3 拿到判据：**模组自己注册过 `IConfigScreenFactory` 它就让位**（且没有任何配置的模组它也不接管）⇒ 我们**只在它不在场时**注册 NeoForge 自带界面。② 策略抽成纯函数 `PotatoSTConfig.shouldRegisterOwnConfigScreen(boolean)`（`!configuredModPresent`），客户端只传 `ModList.get().isLoaded("configured")` —— 这样它能在真服务端探针里被验。③ `configured` 只作为字符串出现在客户端类；`neoforge.mods.toml` **一字未动**（门 A3 + 反证刀 K4/K5）。④ **探针 `Zf188Check` 4/0** + **上一轮探针 `Zf186Check` 回归再跑 20/0**（重构没碰坏配置行为）；报告里明写"GUI 那一半由用户实测"（门 B3）。⑤ 门 `_zf188_verify.py` **11/0**、反证刀 **7/7**。⑥ **重打**：`release\\PotatoST-0.14.jar` = **{size} 字节 / sha1 `{sha}`**（class {cls}；§4.159 三处联动）。 | 见 §9 ｜ 见 §4.188 |
"""

S9 = u"""### ZF188（0.14）「配置界面」(Configured) 接管那个按钮 —— **要你实测一行日志**

按你选的口径改的（选项 A）：

- **装了「配置界面」(Configured)** ⇒ 模组列表里的「配置」按钮**归它**（它的界面更好看、分组更清楚）；
- **没装** ⇒ 自动回落到 NeoForge 自带界面（就是上一轮那个）。
- **一个依赖都没加**：`neoforge.mods.toml` 与上一版**逐字节相同**（门 A3 + 反证刀 K4/K5 钉着）；
  `configured` 这个名字只作为字符串出现在客户端类里。

**你怎么确认它真的接管了**（我这边没有图形会话，验不了 GUI，只能给你判据）：
启动客户端后看 `logs/latest.log`，应当出现 **Configured** 打的那一行
`Registering config factory for mod potato_s_t. Found 1 config(s)`；
同时聊天框/控制台还会有我们自己的 `[PotatoST] 检测到「配置界面」(Configured)：配置界面交给它接管`。

⚠ **副作用（先说清）**：装了 Configured 之后，**NeoForge 自带那个界面就点不到了**（按钮归它）。
想回来自带界面：在 Configured 的配置里关掉强制接管，或者把 Configured 卸掉。

**真服务端验到的**（`Zf188Check` 4/0 + 上一轮 `Zf186Check` 回归 20/0）：没装 → 自己注册；
装了 → 让位；本服务器确实没装 → 走"自己注册"这一支；11 项配置的出厂值一字未变。
"""

HAND46 = u"""46. **ZF188 的账（0.14：配置界面归属 —— 装了 Configured 就让位）**：① 用户拍板见档案 §9；判据来源与三条设计决定见 §4.188
    —— **先反编译对方**（`ClientConfigured.generateConfigFactories`：模组自带 `IConfigScreenFactory` 它就让位，
    且没配置的模组它也不接管）⇒ 我们**只在它不在场时**注册自带界面；
    **策略抽成纯函数** `PotatoSTConfig.shouldRegisterOwnConfigScreen(boolean)` 才能在没有图形会话的机器上验真值表。
    ② 探针 `Zf188Check` **4/0** + 上一轮 `Zf186Check` **回归再跑 20/0**；门 `_zf188_verify.py` **11/0**、反证刀 **7/7**。
    ③ ⚠ **诚实边界**：客户端 GUI 那一半验不了 ⇒ 报告里必须留着"由用户实测"那句（门 B3 钉着），
    要用户看的是 `logs/latest.log` 里的 `Registering config factory for mod potato_s_t`。
    ④ ⚠ **副作用**：装了 Configured 后 NeoForge 自带界面点不到（写进类注释与 §9）。
    ⑤ `configured` 只许作为字符串出现在客户端类；`neoforge.mods.toml` 逐字节未动（反证刀 K4/K5）。
"""

BIL_ZH = u"""
- **0.14 追加（ZF188）配置界面归属**：装了「配置界面」(Configured) 就**让它接管**模组列表里的「配置」按钮
  （它的界面更好看）；**没装**则自动回落到 NeoForge 自带界面。依赖清单仍然**一字未动**。
  ⚠ 装了它之后，NeoForge 自带那个界面就点不到了 —— 想回去就在 Configured 里关掉强制接管或卸掉它。
"""

BIL_EN = u"""
- **0.14 follow-up (ZF188) - who owns the Config button:** if you have **Configured** installed it takes
  over the Config button in the mod list (its GUI is nicer); if you do not, the mod falls back to
  NeoForge's built-in configuration screen. The dependency list is still byte-identical.
  Note: with Configured installed, NeoForge's own screen is no longer reachable - turn off Configured's
  forced menu or remove it if you want it back.
"""


def sha(p):
    h = hashlib.sha1()
    with open(p, "rb") as fh:
        for c in iter(lambda: fh.read(1 << 16), b""):
            h.update(c)
    return h.hexdigest()


def read(p):
    return io.open(p, encoding="utf-8", newline=u"").read()


def main(argv):
    write = u"--write" in argv
    size, h = os.path.getsize(JAR), sha(JAR)
    z = zipfile.ZipFile(JAR)
    names = z.namelist()
    cls = len([n for n in names if n.endswith(u".class")])
    recipes = len([n for n in names if n.startswith(u"data/potato_s_t/recipe/") and n.endswith(u".json")])
    adv = len([n for n in names if n.startswith(u"data/potato_s_t/advancement/") and n.endswith(u".json")])
    z.close()
    print(u"成品：%d 字节 / sha1 %s / class %d / 配方 %d / 进度 %d" % (size, h, cls, recipes, adv))

    v149 = read(V149)
    m = re.search(u'WANT_SHA = u?"([0-9a-f]{40})"', v149)
    old_sha = m.group(1) if m else u""
    m = re.search(u"WANT_SIZE = (\\d+)", v149)
    old_size = u"{:,}".format(int(m.group(1))) if m else u""
    fails = []

    def refresh(text):
        if old_sha:
            text = text.replace(old_sha, h)
        if old_size:
            for unit in (u" 字节", u" bytes", u" B"):
                text = text.replace(old_size + unit, u"{:,}{}".format(size, unit))
        text = re.sub(u"\\*\\*\\d+ classes, \\d+ advancements, \\d+ recipes\\*\\*",
                      u"**%d classes, %d advancements, %d recipes**" % (cls, adv, recipes), text)
        return text

    doc = read(DOC)
    if u"### 4.188 " not in doc:
        a = u"| ZF147 |"
        if doc.count(a) != 1:
            fails.append(u"档案 §5 表头锚点 %d 次" % doc.count(a))
        else:
            doc = doc.replace(a, S4 + a, 1)
    if u"| ZF188 |" not in doc:
        a2 = u"（class {cls}；§4.159 三处联动）。 | 见 §9 ｜ 见 §4.186 |\n"
        a2 = a2.replace(u"{cls}", str(cls))
        if doc.count(a2) != 1:
            fails.append(u"档案 ZF186 行尾锚点 %d 次" % doc.count(a2))
        else:
            row = ROW.replace(u"{size}", u"{:,}".format(size)).replace(u"{sha}", h).replace(u"{cls}", str(cls))
            doc = doc.replace(a2, a2 + row + u"\n", 1)
    if u"### ZF188（0.14）" not in doc:
        a3 = u"## 10. 备份策略"
        if doc.count(a3) != 1:
            fails.append(u"档案 §10 锚点 %d 次" % doc.count(a3))
        else:
            doc = doc.replace(a3, S9 + u"\n" + a3, 1)
    doc = refresh(doc)
    if write and not fails:
        io.open(DOC, "w", encoding="utf-8", newline=u"").write(doc)

    hand = read(HAND)
    if u"46. **ZF188 的账" not in hand:
        a4 = u"## 7. ZF146 这一轮的交接"
        if hand.count(a4) != 1:
            fails.append(u"交接 §7 锚点 %d 次" % hand.count(a4))
        else:
            hand = hand.replace(a4, HAND46 + u"\n" + a4, 1)
    hand = refresh(hand)
    if write and not fails:
        io.open(HAND, "w", encoding="utf-8", newline=u"").write(hand)

    vn = re.sub(u'WANT_SHA = u?"[0-9a-f]{40}"', u'WANT_SHA = u"%s"' % h, v149, count=1)
    vn = re.sub(u"WANT_SIZE = \\d+", u"WANT_SIZE = %d" % size, vn, count=1)
    if vn == v149:
        if (u'WANT_SHA = u"%s"' % h) in v149:
            print(u"  （_zf149_verify.py 的靶子已经就是这份成品，跳过）")
        else:
            fails.append(u"_zf149_verify.py：靶子没换到")
    elif write and not fails:
        io.open(V149, "w", encoding="utf-8", newline=u"").write(vn)

    ann = read(ANN)
    if u"## New in 0.14 ZF188" not in ann:
        a5 = u"## New in 0.14 ZF186 - Config support: an in-game config screen with zero new dependencies"
        if ann.count(a5) != 1:
            fails.append(u"公告 ZF186 段锚点 %d 次" % ann.count(a5))
        else:
            block = (u"## New in 0.14 ZF188 - Configured takes over the Config button when it is installed\n\n"
                     u"- If you have **Configured** installed, it now owns the **Config** button in the mod\n"
                     u"  list (its GUI is nicer and groups options more clearly). If you do not, the mod\n"
                     u"  falls back to NeoForge's built-in configuration screen exactly as before.\n"
                     u"- **Still not a required dependency:** the dependency list in `neoforge.mods.toml` is\n"
                     u"  byte-identical to the previous release, and the mod id `configured` only ever\n"
                     u"  appears as a plain string in the client-only class.\n"
                     u"- How to tell it worked: your client log should contain Configured's own line\n"
                     u"  `Registering config factory for mod potato_s_t. Found 1 config(s)`.\n"
                     u"- Known trade-off: with Configured installed, NeoForge's own configuration screen is\n"
                     u"  no longer reachable - turn off Configured's forced menu (or remove it) to get it back.\n"
                     u"- **Download:** `release/PotatoST-0.14.jar` - **{size} bytes**, sha1 **`{sha}`**.\n\n"
                     ).format(size=u"{:,}".format(size), sha=h)
            ann = ann.replace(a5, block + a5, 1)
    ann = refresh(ann)
    if write and not fails:
        io.open(ANN, "w", encoding="utf-8", newline=u"").write(ann)

    bil = read(BIL)
    if u"0.14 追加（ZF188）配置界面归属" not in bil:
        az = u"改完**即时生效**（不用重启）：实测同一块电池 4M→12M 当场变，蓄力 5 秒 = 100 tick。\n"
        ae = u"  5 s charge-up is 100 ticks.\n"
        if bil.count(az) != 1 or bil.count(ae) != 1:
            fails.append(u"双语公告锚点 zh=%d en=%d" % (bil.count(az), bil.count(ae)))
        else:
            bil = bil.replace(az, az + BIL_ZH, 1)
            bil = bil.replace(ae, ae + BIL_EN, 1)
    bil = refresh(bil)
    if write and not fails:
        io.open(BIL, "w", encoding="utf-8", newline=u"").write(bil)

    print(u"模式：%s ｜ 失败 = %d" % (u"落盘" if write else u"干跑", len(fails)))
    for f in fails:
        print(u"  !! " + f)
    return 1 if fails else 0


if __name__ == u"__main__":
    sys.exit(main(sys.argv[1:]))
