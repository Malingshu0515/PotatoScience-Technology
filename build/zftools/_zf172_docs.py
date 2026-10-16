# -*- coding: utf-8 -*-
r"""_zf172_docs.py —— ZF172 文档：更正 ZF170/ZF171 的误放 + 新开一节 + 立坑 + 卸掉重跑风险"""
import io, os, re, sys
sys.stdout.reconfigure(encoding='utf-8', errors='replace')
ROOT = r'E:\PotatoST\PotatoSTneoforge1.21.1'
TOOLS = os.path.join(ROOT, 'build', 'zftools')
DOCS = os.path.join(ROOT, 'docs')
LIST = os.path.join(DOCS, u'贴图清单.md')
ARCH = os.path.join(DOCS, u'开发档案.md')
ANN = os.path.join(DOCS, 'UpdateAnnouncement_EN.md')
FIX = os.path.join(TOOLS, '_zf172_fix.py')
fails = []
def check(ok, msg):
    print((u'  [OK]   ' if ok else u'  [FAIL] ') + msg)
    if not ok:
        fails.append(msg)
def read(p):
    return io.open(p, encoding='utf-8').read()
def write(p, t):
    io.open(p, 'w', encoding='utf-8', newline='\n').write(t)

print(u'===== ① 卸掉重跑风险 + 修我自己算错的那个数 =====')
s = read(FIX)
if u'**不要重跑**' in s:
    print(u'  [幂等] 已加过「不要重跑」警告')
else:
    a = u'"""\nimport io, os, sys, json, shutil, hashlib, subprocess'
    b = (u'"""\n'
         u'# \u26a0\u26a0 **\u4e0d\u8981\u91cd\u8dd1**\uff1a\u7b2c\u4e00\u6b65\u4f1a\u628a**\u73b0\u503c**\u5f53\u6210\u6539\u524d\u4ef6\u6284\u8fdb `zf172_pre`\uff0c\n'
         u'#   \u800c\u73b0\u503c\u5df2\u7ecf\u662f\u65b0\u8d34\u56fe\u4e86 \u21d2 \u91cd\u8dd1\u4f1a\u628a\u771f\u6b63\u7684\u6539\u524d\u4ef6\u8986\u76d6\u6389\u3002\n'
         u'#   \uff08\u8fd9\u4e00\u8f6e\u5df2\u7ecf\u6267\u884c\u5b8c\u6bd5\uff1b\u8981\u91cd\u505a\u8bf7\u5148\u4ece `zf172_pre` \u628a\u6539\u524d\u4ef6\u62a4\u4f4f\u3002\uff09\n'
         u'import io, os, sys, json, shutil, hashlib, subprocess')
    check(s.count(a) == 1, u'文件头锚点命中 1 次（实测 %d）' % s.count(a))
    if s.count(a) == 1:
        s = s.replace(a, b)
    c = u"check(len(back) == 58, u'凭据条数 = 58（实测 %d）' % len(back))"
    d = u"check(len(back) == 59, u'凭据条数 = 59（55 原有 + ZF170 三条 + ZF172 新增的 bottom 一条；实测 %d）' % len(back))"
    check(s.count(c) == 1, u'条数断言锚点命中 1 次（实测 %d）' % s.count(c))
    if s.count(c) == 1:
        s = s.replace(c, d)
    write(FIX, s)
    import ast
    ast.parse(read(FIX))
    check(True, u'_zf172_fix.py 改后能过 ast.parse（并已标「不要重跑」）')

print()
print(u'===== ② 贴图清单：给 ZF170/ZF171 那两处加更正指针 + 新开 ZF172 节 =====')
t = read(LIST)
BANNER = (u"\n> ⚠ **这一节放错了机器**（更正见文末 **ZF172**）：素材是**饮料罐装机** `beverage_canning_machine` 的，\n"
          u"> 不是灌装机 `filling_machine` 的。灌装机那三张与模型**已于 ZF172 逐字节退回原样**；以下内容留档不改字。\n")
a = u"## ZF170（0.13）饮料灌装机三面新材质（侧面 / 顶部 / 底部）"
if u'这一节放错了机器' in t:
    print(u'  [幂等] ZF170 节已有更正横幅')
else:
    check(t.count(a) == 1, u'ZF170 标题锚点命中 1 次（实测 %d）' % t.count(a))
    if t.count(a) == 1:
        t = t.replace(a, a + BANNER)
b = u"旧正面留在 `zf171_pre/`，用户哪天画了专属正面就换回来。"
if u'该正面改动同样在 ZF172 里被退回' in t:
    print(u'  [幂等] ZF171 补记已有更正')
else:
    check(t.count(b) == 1, u'ZF171 补记锚点命中 1 次（实测 %d）' % t.count(b))
    if t.count(b) == 1:
        t = t.replace(b, b + u"（⚠ **该正面改动同样在 ZF172 里被退回** —— 那台机器本来就不该动。）")
SEC = u"""
---

## ZF172（0.13）**更正**：三张素材是**饮料罐装机**的，不是灌装机的

**用户原话**：「不不不宝 是饮料罐装机改贴图 不是灌装机」

本工程有**两台**名字只差一个字的机器：

| 注册名 | 中文名 | 是什么 |
|---|---|---|
| `filling_machine` | **灌装机** | 内部五个 5000 mB 罐，把罐里的流体灌进容器（5 mB/t、每罐 60 FE/t） |
| `beverage_canning_machine` | **饮料罐装机** | 三只罐（碳酸 100 / 水 1000 / 乙醇 100 mB）+ 糖 / 可可豆 / 空铝罐 → 可乐，600 FE/t、5 秒一罐 |

**ZF170/ZF171 我按素材文件名里的「饮料灌装机」认成了灌装机 ⇒ 放错了机器。** 这一轮：

1. **灌装机逐字节退回**（三张贴图 + 模型）：
   - `filling_machine_side.png` → `719c785060ce`（ZF170 改前值）
   - `filling_machine_top.png` → `8bedfc2b861d`
   - `filling_machine_front.png` → `3430395ef96d`（ZF171 那次「正面统一」同样退回）
   - `models/block/filling_machine.json` → 与 ZF170 改前件**逐字节相同**（`bottom` 槽撤掉、`down` 面退回 `#top`）
   - 误建的 `filling_machine_bottom.png` **挪出工程**（留在 `zf172_pre/`）
2. **落到罐装机**（原字节复制）：

| 素材 | sha1 | 落位 | 用在 |
|---|---|---|---|
| `饮料灌装机侧面_001.png` | `1cb30de97346` | `beverage_canning_machine_side.png` | 四个侧面 |
| `饮料灌装机顶部_001.png` | `e0852840e843` | `beverage_canning_machine_top.png` | 顶面 |
| `饮料灌装机底部_001.png` | `9db3ca07bdc5` | `beverage_canning_machine_bottom.png` | 底面（**新开的槽**） |

3. **罐装机的模型**：原来只有 `top` / `side` 两个槽、`up` **和** `down` **都用顶面那张** ⇒ 新开 `bottom` 槽、
   `down` 面改指 `#bottom`（与 ZF154 采油机同一套做法）。它**没有正面**（blockstate 只有空字符串那一个变体、
   四面全用 `#side`）⇒ 不存在「正对着的那面看不到新图」那回事。
4. 凭据那三条**误记的键名**改成罐装机（`filling_machine_side/top.png` → `beverage_canning_machine_side/top.png`），
   新加底部一条 ⇒ 58 → **59** 条。
"""
if u'## ZF172（0.13）**更正**' in t:
    print(u'  [幂等] 清单已有 ZF172 节')
else:
    if not t.endswith(u'\n'):
        t += u'\n'
    t = t + SEC
    check(u'## ZF172（0.13）**更正**' in t, u'贴图清单已加 ZF172 节')
write(LIST, t)

print()
print(u'===== ③ 开发档案：更正 ZF170 行 + 插 ZF172 行 + 立坑 =====')
t = read(ARCH)
ADD170 = (u"　**⚠ ZF172 更正**：这一轮的素材**放错了机器** —— 用户给的是**饮料罐装机** `beverage_canning_machine` 的，"
          u"我却落到**灌装机** `filling_machine` 上（两台机器中文名只差一个字）⇒ 已于 ZF172 **逐字节退回**，素材改落罐装机。")
if u'⚠ ZF172 更正' in t:
    print(u'  [幂等] ZF170 行已有更正')
else:
    key = u"| 见 §4.165 / §9 |"
    check(t.count(key) == 1, u'ZF170 行尾锚点命中 1 次（实测 %d）' % t.count(key))
    if t.count(key) == 1:
        t = t.replace(key, ADD170 + u" | 见 §4.165 / §9 |")
        write(ARCH, t)
        check(u'⚠ ZF172 更正' in read(ARCH), u'ZF170 行已更正')
ADD171 = u"　**⚠ ZF172 更正**：这一手的「正面统一」是**打在错误的机器上**的，已随灌装机一起退回。"
if u'打在错误的机器上' in read(ARCH):
    print(u'  [幂等] ZF171 补记已有更正')
else:
    k2 = u"（详见 §9）。"
    t = read(ARCH)
    n = t.count(k2)
    check(n == 1, u'ZF171 补记锚点命中 1 次（实测 %d）' % n)
    if n == 1:
        write(ARCH, t.replace(k2, u"（详见 §9）。" + ADD171))
        check(u'打在错误的机器上' in read(ARCH), u'ZF171 补记已更正')

ROW = (u"| ZF172 | **新建 `zf172_pre`**（3 份改前件：罐装机的两张贴图 + 它的模型）；"
       u"⚠ **本轮是「撤 + 改落」**：灌装机那三张贴图与模型用 ZF170/ZF171 的备份**逐字节退回**"
       u"（`719c785060ce` / `8bedfc2b861d` / `3430395ef96d`；模型与 ZF170 改前件逐字节相同），"
       u"误建的 `filling_machine_bottom.png` 挪出工程 | "
       u"0.13：**更正 —— 三张素材属于「饮料罐装机」不是「灌装机」**（用户原话「不不不宝 是饮料罐装机改贴图 不是灌装机」）。"
       u"① 本工程有**两台名字只差一个字**的机器：`filling_machine` = **灌装机**（五个 5000 mB 罐，把罐里的流体灌进容器）、"
       u"`beverage_canning_machine` = **饮料罐装机**（碳酸/水/乙醇三罐 + 糖/可可豆/空铝罐 → 可乐），"
       u"ZF170 我按素材文件名里的「饮料灌装机」认成了灌装机 ⇒ **放错机器**；"
       u"② **退回**：三张贴图逐字节回原值、模型回 `down → #top` 且撤掉 `bottom` 槽、误建的 bottom 贴图挪出工程；"
       u"③ **改落罐装机**：侧面→`side`、顶部→`top`、底部→**新开的 `bottom` 槽**（原来 `up` 与 `down` 共用顶面那张），"
       u"与 ZF154/ZF170 同一套做法；罐装机**没有正面**（blockstate 只有空字符串那一个变体、四面全用 `#side`）"
       u"⇒ 不存在「正对着的那面看不到新图」那回事；"
       u"④ 凭据两条**误记的键名**改成罐装机、新增底部一条 ⇒ 58 → **59** 条；"
       u"⑤ 立 **§4.172**：素材文件名会骗人 + 我自己的两个操作失误（按平名字去编码备份里找、把凭据条数算错） | 见 §4.172 / §9 |\n")
t = read(ARCH)
if u'| ZF172 |' in t:
    print(u'  [幂等] 档案已有 ZF172 行')
else:
    lines = t.split(u'\n')
    idx = max(i for i, l in enumerate(lines) if l.startswith(u'| ZF'))
    lines.insert(idx + 1, ROW.rstrip(u'\n'))
    write(ARCH, u'\n'.join(lines))
    check(u'| ZF172 |' in read(ARCH), u'档案变更表插入 ZF172 行（追在 %s 之后）' % lines[idx][:10])

t = read(ARCH)
nums = [int(m.group(1)) for m in re.finditer(u'^### 4\\.(\\d+)', t, re.M)]
nxt = max(nums) + 1
print(u'  现行 §4 最大号 = 4.%d ⇒ 本轮立 §4.%d' % (max(nums), nxt))
PIT = (u"\n### 4.%d 【命名雷】素材文件名会骗人：**「灌装机」与「罐装机」只差一个字**，改之前先把注册名与中文名对一遍（0.13 ZF172）\n\n"
       u"用户给的三张素材叫 `饮料灌装机侧面/顶部/底部_001.png`，我照名字认成 `filling_machine`（**灌装机**）—— "
       u"可本工程还有一台 `beverage_canning_machine`（**饮料罐装机**：碳酸/水/乙醇三罐 + 糖/可可豆/空铝罐 → 可乐）。"
       u"用户随后一句「不不不宝 是饮料罐装机改贴图 不是灌装机」把这事点破。**素材放错了机器**，只能整轮退回再改落。\n\n"
       u"**规矩**：\n"
       u"  ① 中文名相近的机器（灌装 / 罐装、低级 / 高级、控制器 / 操作器……）在**同一个 mod 里同时存在**时，"
       u"**不要拿文件名当唯一证据** —— 先查一遍 `zh_cn.json` 里所有 `block.potato_s_t.*` 的中文名，"
       u"把「名字里带这几个字」的**全部**列出来，再决定落哪个；\n"
       u"  ② 两边都说得通时**问一句**（本轮就是没问：文件名写「灌装机」、用户心里想的是「罐装机」）；\n"
       u"  ③ 改之前先看清目标机器的**模型有几个槽**（这台罐装机只有 `top`/`side` 两个，`up` 与 `down` 还共用顶面）"
       u"—— 槽位对不上就说明很可能认错了机器。\n\n"
       u"**同轮的两个操作失误（都记下来，都是「我自己的工具用错」）**：\n"
       u"  · 退回时按**平名字**去 `zf170_pre` 找备份，可它们是 `_zf170_fixbak.py` 写的**带路径编码**的名字"
       u"（`src__main__…__filling_machine_side.png`）⇒ 找不到、脚本中途抛异常；改成**按后缀在备份目录里找**才过。"
       u"**备份目录里的命名约定必须与写入时一致**（§4.165 的姊妹条）；\n"
       u"  · 凭据条数我在断言里写成 58，实际是 **59**（55 + ZF170 三条 + ZF172 新加的 bottom 一条）——"
       u"**判据里的算术要跟着「新增几条」一起算**，别只算改名。\n") % nxt
if u'### 4.%d ' % nxt in t:
    print(u'  [幂等] 已有 §4.%d' % nxt)
else:
    lines = t.split(u'\n')
    i = max(k for k, l in enumerate(lines) if re.match(u'^### 4\\.\\d+ ', l))
    j = None
    for k in range(i + 1, len(lines)):
        if lines[k].startswith(u'## '):
            j = k
            break
    if j is None:
        check(False, u'找不到 §4 的收尾边界')
    else:
        write(ARCH, u'\n'.join(lines[:j]) + PIT + u'\n' + u'\n'.join(lines[j:]))
        check(u'### 4.%d ' % nxt in read(ARCH), u'§4.%d 已插入' % nxt)

print()
print(u'===== ④ 英文公告 =====')
t = read(ANN)
EN = u"""
## New in 0.13 ZF172 - correction: those three textures belong to the Beverage Canning Machine

- The three textures supplied earlier are for the **Beverage Canning Machine**
  (`beverage_canning_machine`), **not** the Filling Machine (`filling_machine`). The two share a
  nearly identical Chinese name (灌装机 vs 饮料罐装机), and the file names said "filling machine", so
  the previous round put them on the wrong block.
- **The Filling Machine has been rolled back byte-for-byte**: its side, top and front textures are
  exactly the pre-change values again, and its model is byte-identical to the earlier one (the added
  `bottom` slot is gone, `down` points back at `#top`). The stray `filling_machine_bottom.png` was
  moved out of the project.
- **The Beverage Canning Machine now has the new art**: side (all four faces), top, and a new
  **bottom** slot - its model previously reused the top texture on the underside. It has no front
  face at all, so there is no "the side you look at is the old one" problem here.
"""
if u'ZF172 - correction' in t:
    print(u'  [幂等] 公告已有 ZF172 条')
else:
    if not t.endswith(u'\n'):
        t += u'\n'
    write(ANN, t + EN)
    check(u'ZF172 - correction' in read(ANN), u'英文公告已加 ZF172 条')

print()
print(u'失败项 = %d' % len(fails))
sys.exit(1 if fails else 0)
