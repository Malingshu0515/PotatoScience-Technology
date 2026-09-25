# -*- coding: utf-8 -*-
u"""_zf83_docs.py —— ZF83 文档：档案 §4.56 + §5 ZF83 行 + §9 验收 + 贴图清单更新

`__NEWSHA__` / `__NEWSIZE__` / `__NEWENTRIES__` 由 `_zf83_publish.py` 填真值。
插入点都断言"恰好命中 1 次"（ToolLint 硬规矩）。
"""
import io
import os
import sys

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

DOCS = r"E:\PotatoST\docs"
fails = []


def read(p):
    if not os.path.exists(p):
        fails.append(u"缺文件：%s" % p)
        return u""
    return io.open(p, encoding="utf-8").read()


def write(p, t):
    io.open(p, "w", encoding="utf-8", newline=u"\n").write(t)


def insert_after(text, anchor, block, label):
    if text.count(anchor) != 1:
        fails.append(u"%s：锚点命中 %d 次（必须 1 次）" % (label, text.count(anchor)))
        return text
    at = text.find(anchor)
    eol = text.find(u"\n", at)
    return text[:eol + 1] + block + text[eol + 1:]


TRAP = u"""
### 4.56 【贴图雷】白底素材做透明**不能一刀切"白色全透明"**——要从四边泛洪，还只留最大连通域（0.11 ZF83）

用户给的板子素材是**白底**（钢/铁）与**深底**（铜）、16×16 JPEG。要把背景做透明时：

| 做法 | 后果 |
|---|---|
| 把"接近白色的像素"一律设成透明 | **板面内部也是白的** ⇒ 板子被掏空，只剩一圈描边 |
| 从**四边泛洪**、只把与背景同色的连通区设透明 | ✅ 板面保住（内部被描边围住，泛洪到不了） |
| 泛洪 + **只保留最大连通域** | ✅ 连 JPEG 噪点留下的"板外飘一个像素"也清掉 |

⚠ **泛洪后做连通域清理时，遍历必须跳过"已属某个域"的像素**：第一版没跳，
同一个域被反复泛洪出**内容相同但对象不同**的多个集合，`max(...)` 选中的那个成了唯一保留项、
其余（同样是整块板）全被清零 ⇒ 三张图**全空**。教训与 §4.30「先怀疑期望」同源：
**清理逻辑写完先渲染一张 alpha 图看一眼**，比事后在游戏里找"贴图不见了"便宜得多。

**另记一笔（流程）**：本轮我**先动手后抄**（贴图转档 + 改模型之后才建 `zf83_pre`），
这是第二次（ZF78 那次也是）。补救用了和 ZF78 同一套**可验证重建**：
把改前那 6 份（3 张贴图 + 3 个模型）从 **ZF82 已发布的成品 jar** 里逐字节取回并核 SHA1
—— 那是用户手上那个包，也就是"改动前游戏里真实生效的样子"。
"""

ROW = (u"| ZF83 | **补建 `zf83_pre`**（10 份；⚠ **先动手后抄**：贴图与模型这 6 份是从 **ZF82 成品 jar** "
       u"里逐字节取回并核过 SHA1 的「可验证重建」，不是当时磁盘上的原件；文档与旧成品那 4 份是动手前拷的。"
       u"详见 `zf83_pre\\_说明.txt`） | 0.11：**三张板子贴图换新**（用户原话：「钢板和铁（银 铝...）板 "
       u"铜板贴图放item文件夹了 **换一下** 然后**删除原来的贴图**」）。"
       u"① 把用户留在 `textures/item` 的三张 16×16 原图（钢/铁=白底描边板、铜=深底亮板）转成"
       u"**16×16 / 8 位 / RGBA** 贴上：`steel_plate.png` / `iron_plate.png`（新建）/ `copper_plate.png`；"
       u"背景处理用**从四边泛洪 + 只留最大连通域**（一刀切「白色全透明」会把板面掏空，见 §4.56）。"
       u"② **铁板**原来借的是通用 `plate.png`，这次连同钢/铜一起指向自己的贴图；三个 json 一并重写。"
       u"③ 通用 `plate.png` **没删**：银/铝/镍/钴四件还在用它（删了那四件会变紫黑块）—— "
       u"已在汇报里点给用户：要它们也各来一张（或我来生成）说一声。"
       u"④ 原图按 §4.24 继续留在 `build/用户素材/`（ASCII 名 + `_来源凭据.json` 记哈希）。"
       u"⑤ 校验 `_zf83_verify.py` 加了三条**全量扫描**：item 模型引用的贴图必须都存在（防紫黑块）、"
       u"每张 `textures/item/*.png` 至少被引用一次（防孤儿）、三张新图必须**与 ZF82 成品里那张不同**"
       u"（证明真的换了、而不是「改了但没生效」）。 |\n")

VERIFY = u"""
### ZF83（0.11）三张板子贴图换新 —— 待你实测

- [ ] 进游戏看**铁板 / 钢板 / 铜板**三件的物品贴图：应当是你画的那三张（板形、白/深底已去掉）
- [ ] ⚠ **银板 / 铝板 / 镍板 / 钴板仍然是通用那张**（`plate.png` 还在给它们用）
      —— 你要是也给这四张，我就一起换掉并删掉 `plate.png`；要我先**按金属色生成**四张占位也行，说一声
- [ ] 原图仍在 `build/用户素材/{steel,iron,copper}_plate.jpg`（不进 jar）；要连原图一起删就说一声
- [ ] 上一轮那两条还没在启动器实例里复核：**柴油桶/汽油桶**（放/舀）、**容器换流器**（3 秒换桶 + 泵抽）

**成品**：`release\\PotatoST-0.11.jar` = `__NEWSHA__`（__NEWSIZE__ B / __NEWENTRIES__ 条目），
**作废上一版 `8ba61f5d957fd0d809f1d0c2b811b739b733e7be`**（ZF82）；0.10 成品 `84d09345…` 原样保留。
"""

TEX_SECTION = u"""
## ZF83（0.11）：三张板子贴图换新

| 文件 | 状态 | 来源 / 说明 |
|---|---|---|
| `textures/item/steel_plate.png` | ✅ **换新** | 用户原图 `钢板.jpg`（白底描边板）转档：四边泛洪去背景 |
| `textures/item/iron_plate.png` | ✅ **新建** | 用户原图 `铁板.jpg` 同上（**铁板原先借通用 `plate.png`**，本轮换掉） |
| `textures/item/copper_plate.png` | ✅ **换新** | 用户原图 `铜板.jpg`（深底亮板）同上 |
| `textures/item/plate.png` | 保留 | 银/铝/镍/钴四件仍在用；**删了那四件会变紫黑块**，等它们各自的图 |
| `build/用户素材/{steel,iron,copper}_plate.jpg` | 留档 | §4.24 原名件（不进 jar），哈希在 `_来源凭据.json` |

⚠ 转档规则（§4.56）：**白底素材不能一刀切"白色全透明"** ⇒ 从四边泛洪 + 只保留最大连通域。
"""


def main():
    arch_p = os.path.join(DOCS, u"开发档案.md")
    arch = read(arch_p)
    if u"### 4.56" not in arch:
        anchor = u"\n\n| 版本 | 内容 |"
        if arch.count(anchor) != 1:
            fails.append(u"§4.56 插入点命中 %d 次" % arch.count(anchor))
        else:
            arch = arch.replace(anchor, u"\n" + TRAP + anchor, 1)
    if u"| ZF83 |" not in arch:
        arch = insert_after(arch, u"| ZF82 | **新建 `zf82_pre`**", ROW, u"档案 §5：ZF83 行")
    if u"### ZF83（0.11）三张板子贴图换新" not in arch:
        if arch.count(u"\n## 10. 备份策略") != 1:
            fails.append(u"档案 §9：锚点命中 %d 次" % arch.count(u"\n## 10. 备份策略"))
        else:
            arch = arch.replace(u"\n## 10. 备份策略", u"\n" + VERIFY + u"\n## 10. 备份策略", 1)
    write(arch_p, arch)

    tex_p = os.path.join(DOCS, u"贴图清单.md")
    tex = read(tex_p)
    if u"## ZF83（0.11）" not in tex:
        write(tex_p, tex.rstrip(u"\n") + u"\n" + TEX_SECTION)
        print(u"贴图清单：追加 ZF83 一节")

    print(u"文档改完，失败项 = %d" % len(fails))
    for f in fails:
        print(u"  !! " + f)
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())
