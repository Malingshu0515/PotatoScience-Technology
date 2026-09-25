# -*- coding: utf-8 -*-
u"""_zf122_fixdocs.py —— ZF122 补丁建档：§4.91 新雷区 + §9 那节里的成品号与修复说明

用户实测抓到的真 bug：「这个天空和会随着视角转动啊 不行的啦 需要定住的 要不然会很晕 而且怪怪的」。
根因：`AFTER_SKY` 那一刻的 pose stack **只有位置、没有摄像机朝向** ⇒ 球幕画在摄像空间里 ⇒ 贴在屏幕上。
修法：`pose.mulPose(event.getModelViewMatrix())`（原版 renderSky 用的同一句）。

跑法：python build\\zftools\\_zf122_fixdocs.py [--write]
"""
import io
import sys

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

DOC = r"E:\PotatoST\docs\开发档案.md"
OLD_SHA = u"f8bd11c415fe976da65760a467a47609b0ff4027"
NEW_SHA = u"2c7382386e860398dc88df9074e84e1686510cf4"

S4 = u"""
### 4.91 【渲染雷】`AFTER_SKY` 的 pose stack **没有摄像机朝向** —— 天空会"贴在屏幕上"跟着视线转（0.11 ZF122）

星仪图之章第一版交付后用户实测：「**这个天空和会随着视角转动啊 不行的啦 需要定住的 要不然会很晕 而且怪怪的**」。

**根因**：我在 `RenderLevelStageEvent.Stage.AFTER_SKY` 里直接拿 `event.getPoseStack()` 的矩阵画球幕。
那一拍 pose stack 里**只有摄像机位置（平移），没有摄像机朝向（旋转）** ⇒ 顶点是在**摄像空间**里画出来的
⇒ 球幕相对屏幕不动、相对世界在转，表现为"天跟着我转"。

**修法**（一行，和原版 `LevelRenderer.renderSky` 用的是同一句）：

```java
pose.pushPose();
pose.mulPose(event.getModelViewMatrix());   // 纯旋转矩阵，补上摄像机朝向
Matrix4f matrix = pose.last().pose();
...
pose.popPose();
```

`RenderLevelStageEvent` 一共给了三个矩阵，**分工要分清**（javap 出来的真签名）：

| 取法 | 是什么 | 什么时候要它 |
|---|---|---|
| `getPoseStack()` | 当前位置栈（摄像机处、**未含朝向**） | 画"跟着屏幕走"的东西（HUD、进度条） |
| `getModelViewMatrix()` | **纯旋转**的视图矩阵（`camera.rotation().conjugate()`） | 画**钉在世界里**的东西 —— 天空、星空、远处的背景板 |
| `getProjectionMatrix()` | 投影矩阵 | 自己做裁剪/自绘管线时 |

**规矩**：凡是"世界里的背景"（天空盒、星图、行星、极光），都要 `mulPose(getModelViewMatrix())`
并用 push/pop 包住；凡是"贴在屏幕上的"（HUD、调试叠加）才用原始 pose stack。
**判断哪一种是哪个，只要问一句：这个东西该跟着我转，还是该留在原地？**
—— 这一条本可以在我写第一版时就问自己（当时只想着"把球幕画出来"，
没想过"画在哪个空间里"），代价是用户先看到了一版会转的天。
"""

S9ADD = u"""
- [x] **用户实测反馈 #1（已修）：天空会跟着视线转** —— `AFTER_SKY` 的 pose stack 不含摄像机朝向，
      球幕被画在摄像空间里。修法 `pose.mulPose(event.getModelViewMatrix())`（原版 renderSky 同一句），
      见 §4.91；`_zf122_verify.py` 加了 **E12/E13** 两条断言钉住它。⚠ **旧成品 `%s` 作废**，
      新成品 `%s`。
""" % (OLD_SHA, NEW_SHA)


def main(argv):
    write = "--write" in argv
    text = io.open(DOC, encoding="utf-8").read()
    lines = text.split(u"\n")
    s4_idx = None
    for i, l in enumerate(lines):
        if l.startswith(u"### 4.90 "):
            s4_idx = i
            break
    if s4_idx is None:
        print(u"[FAIL] 找不到 §4.90 锚点")
        return 1
    anchor9 = u"### ZF122（0.11）星仪图之章 —— **待你实测**"
    if text.count(anchor9) != 1:
        print(u"[FAIL] §9 锚点命中 %d 次" % text.count(anchor9))
        return 1
    # §9 节末尾：插在那节最后一个空行之前 —— 用"下一个 ### "或"## 10"当边界
    start = text.index(anchor9)
    nxt = text.find(u"\n## ", start)
    sec = text[start:nxt]
    sec_new = sec.rstrip(u"\n") + u"\n" + S9ADD
    print(u"   锚点：§4.90 @%d；§9 节长度 %d 字符" % (s4_idx + 1, len(sec)))
    if not write:
        print(u"（体检模式，未写盘）")
        return 0
    lines.insert(s4_idx, S4.strip(u"\n"))
    out = u"\n".join(lines).replace(sec, sec_new)
    io.open(DOC, "w", encoding="utf-8", newline=u"").write(out)
    chk = io.open(DOC, encoding="utf-8").read()
    bad = 0
    for label, needle, want in ((u"§4.91", u"### 4.91 【渲染雷】", 1),
                                (u"新 SHA1", NEW_SHA, 2),
                                (u"§9 补记", u"用户实测反馈 #1（已修）", 1)):
        n = chk.count(needle)
        ok = (n == want)
        print(u"   %-8s 出现 %d 次（期望 %d）%s" % (label, n, want, u"✓" if ok else u"✗"))
        bad += 0 if ok else 1
    print(u"复核失败 = %d" % bad)
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
