# -*- coding: utf-8 -*-
u"""_zf122_docs.py —— ZF122 建档：§5 一行 + §9 一节 + §4.90 一条

只加行（§4.7）；三处插入各自要求锚点恰好命中 1 次；写完复核"插进去的东西各出现 1 次"。
跑法：python build\\zftools\\_zf122_docs.py [--write]
"""
import io
import sys

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

DOC = r"E:\PotatoST\docs\开发档案.md"

ROW = (u"| ZF122 | **新建 `zf122_pre`**（⚠ **事后补的**：本轮动手前忘了建快照，第三次犯 §10 那条；"
       u"补法是**可验证的减法重建** —— 三个 Java + 配方生成器逐条反向替换、每处断言锚点恰好命中 1 次，"
       u"四份 lang 的改前件取自 **git HEAD**（等级①）；见 `zf122_pre\\_说明.txt`） | "
       u"0.11：**星仪图之章**（用户原话：「星仪图之章 右键顺次切换主世界的天空盒 你看看怎么好做 图我给你了 "
       u"你想怎么编辑都可以 我感觉这个图真的很好看！」）。① **本工程第一次改天空**：原版没有自定义天空盒接口，"
       u"做法是在 NeoForge 的 `RenderLevelStageEvent.Stage.AFTER_SKY`（原版天空画完、地形还没画）这一拍，"
       u"朝摄像机画一个**不透明球幕**盖住太阳/月亮/星星，地形随后画在上层 ⇒ 地平线自然被遮；"
       u"三个必须写对的地方：`depthMask(false)`（否则 100 格外的地形会被背景板挡掉）、`disableCull()`（从球内看）、"
       u"关雾（雾按地形距离算，不关会糊成白）；② **只有自己看得见**（用户拍板）：编号存在书自己的 "
       u"`sky_index` 数据组件里（1.21 的 DataComponent，`networkSynchronized` 自动同步）⇒ **一个自定义包都不用发**；"
       u"③ 四张图按**等距圆柱**（裁成 2:1 再缩到 1024×512）贴到球幕上，顶点用球坐标、UV 直接取经纬度 ⇒ 不变形；"
       u"④ 体积实测：调色板+抖动 **1.2 MB** vs 直存 RGBA **5.4 MB**（量化误差 4.6~7.9/255，已出图肉眼验过）；"
       u"⑤ 配方：四角纸 ×4 + 四边紫水晶碎片 ×4 + 中间荧石 → 1（用户说「你看着办」）；"
       u"⑥ `_zf122_verify.py` **全过**，八道门全绿；四语言 454 → **464** 键 | 见 §9 |\n")

S4 = u"""
### 4.90 【工具雷】从**源码文本**里抠一个 Python 字面量的"值" —— 少一个反斜杠就永远匹配不上（0.11 ZF122）

补 `zf122_pre` 快照时（本轮动手前忘了备份，见 §10），我要把三个 Java 里"本轮插进去的那一段"
**反向删掉**来重建改前件。做法是读 `_zf122_java.py` 的源码、数引号把那一段抠出来 —— 结果锚点**永远 0 命中**，
而文件里那段明明在（`star_chart_tome` grep 得到 1 次）。

**根因**：抠出来的是**源码里的转义写法**，不是 Python 求值后的**字符串值**：

| 位置 | 内容 |
|---|---|
| 脚本源码里写的 | `别手改 recipe\\\\*.json`（两个反斜杠） |
| Python 插进 Java 的**值** | `别手改 recipe\\*.json`（一个反斜杠） |

一个字符的差别 ⇒ `str.count()` 恒 0。**正确做法：`import` 那个模块直接取常量**（模块顶层无副作用、
`main()` 有 `__main__` 守卫），别做文本解析。

**同轮第二条**（同族的另一种）：反向锚点里我顺手把注释**凭记忆重写**了一遍
（"今年轮我自己定的图纸" vs 实际插入的"这一轮的图纸我自己定的"）⇒ 又是 0 命中。
⇒ **凡是要"反向删掉一段"的，锚点优先用结构标记**（起止行号、唯一短串），
**别拿长注释原文当锚点** —— 记忆和源码不可能一字不差。这两条合起来就是 §4.22 那句
"改过的源码没有权威副本"的另一面：**连我自己刚写下的东西都不该凭记忆去匹配**。

> 附带一句流程：本轮**第三次**犯了"先动手后备份"（前两次 ZF78/ZF83）。
> 三次的补法都是减法重建 + 断言，但代价明显 —— 本轮为了补快照多花了四轮往返。
> **规矩照旧：阶段第一件事是建 `zfNNN_pre`，没建之前不落任何一笔编辑。**
"""

S9 = u"""
### ZF122（0.11）星仪图之章 —— **待你实测**

用户原话：「星仪图之章 右键顺次切换主世界的天空盒 你看看怎么好做 图我给你了 你想怎么编辑都可以
我感觉这个图真的很好看！」；两条拍板：**只你自己看得见** / **配方我看着办**（已给）。

- [ ] **要你实测的**：创造页最后拿到**星仪图之章**（深蓝封面 + 金边 + 白色星芒那本），
      右键一次 ⇒ 天空换成「碧霄星云」，再右键依次 **星海幽峦 / 赤河星汉 / 蛛巢星云**，第 5 次回到**原版星空**；
      **潜行右键**往回切。动作栏会提示换成了哪片天。
- [ ] **重点看三件事**：① 太阳、月亮、星星是不是被盖住了（球幕是不透明的）；
      ② **远处地形有没有被"吃掉"**（这一条最容易翻车 —— 修法就是 `depthMask(false)`，见类注释）；
      ③ 抬头看天顶、低头看地平线附近**有没有缝或拉伸**（等距圆柱投影的两极会有点聚拢，属正常）。
- [ ] 天空盒**只改你自己的屏幕**：换到别的物品后天空**保持不变**（一本书记住一种天），
      再拿书切回 0 号就回到原版；同服的人不受影响。
- [ ] 四条天分别来自你给的四张图（原图已按项目规矩归档到 `build\\用户素材\\星仪图\\`，
      原名与 sha256 记在 `_来源凭据.json`）：绿星云 / 神秘山 / 银河中心 / 蜘蛛星云，
      贴图是**裁成 2:1 再缩到 1024×512**、调色板 256 色 + Floyd–Steinberg 抖动（1.2 MB 四张）。
      嫌糊就说一声 —— 直存 RGBA 那版是 5.4 MB（脚本 `_zf122_textures.py` 两版都还在 `_zf122_out\\`）。
- [ ] **配方**（我定的）：四角**纸** ×4 + 四边**紫水晶碎片** ×4 + 中间**荧石** ×1 → 1 本。
      不想要就说，改一行表重跑生成器即可。
- [ ] ⚠ 已知边界：**只作用于主世界**（下界/末地不换天，用户原话就是"主世界"）；
      球幕是**静态**的（不随昼夜旋转）；云仍然会飘在球幕前面（原版云在天空之后画，没动它）。
- [ ] **成品**：`release\\PotatoST-0.11.jar` = `f8bd11c415fe976da65760a467a47609b0ff4027`（5,634,633 B；
      比上一版大 1.3 MB，正是四张天空盒贴图的体积），⚠ **上一版 `303c5d468b96826ef6836b0a4e54ccb8a539557c` 作废**
      （同版本原地重打包）。注：这一版同样**带着并行会话 ZF115~ZF121 尚未打包的改动**。

"""


def main(argv):
    write = "--write" in argv
    text = io.open(DOC, encoding="utf-8").read()
    lines = text.split(u"\n")
    row_idx = s4_idx = s9_idx = None
    for i, l in enumerate(lines):
        if l.startswith(u"| ZF121 |"):
            row_idx = i
        if l.startswith(u"### 4.90 "):
            s4_idx = i
        if l.startswith(u"## 10. 备份策略"):
            s9_idx = i
    # §5 行插在表格最后一行（现用最大号）之后
    if row_idx is None:
        cand = [i for i, l in enumerate(lines) if l.startswith(u"| ZF")]
        row_idx = cand[-1] if cand else None
    if s4_idx is None:      # 还没有 4.90 ⇒ 插在最后一條 §4.8x/4.9x 之前
        cand = [i for i, l in enumerate(lines) if l.startswith(u"### 4.9")]
        s4_idx = cand[0] if cand else None
        where = u"（插在 §4.9x 之前）"
    else:
        where = u"（替换位置）"
    if row_idx is None or s9_idx is None:
        print(u"[FAIL] 找不到锚点：row=%s s4=%s s9=%s" % (row_idx, s4_idx, s9_idx))
        return 1
    print(u"   锚点：§5 表格末行 @%d，§4 插入点 @%s %s，## 10 @%d"
          % (row_idx + 1, s4_idx + 1 if s4_idx is not None else u"-", where, s9_idx + 1))
    if not write:
        print(u"（体检模式，未写盘）")
        return 0
    lines.insert(s9_idx, S9.rstrip(u"\n"))
    if s4_idx is not None:
        lines.insert(s4_idx, S4.strip(u"\n"))
    lines.insert(row_idx + 1, ROW.rstrip(u"\n"))
    io.open(DOC, "w", encoding="utf-8", newline=u"").write(u"\n".join(lines))
    chk = io.open(DOC, encoding="utf-8").read()
    bad = 0
    for label, needle in ((u"§5 行", u"| ZF122 |"), (u"§9 节", u"### ZF122（0.11）星仪图之章"),
                          (u"§4.90", u"### 4.90 【工具雷】")):
        n = chk.count(needle)
        print(u"   %-8s 出现 %d 次 %s" % (label, n, u"✓" if n == 1 else u"✗"))
        bad += 0 if n == 1 else 1
    print(u"复核失败 = %d" % bad)
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
