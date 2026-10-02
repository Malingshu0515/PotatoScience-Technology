# -*- coding: utf-8 -*-
u"""_zf116_docs2.py —— 追补：档案 §4.85 + 贴图清单 ZF116 小节里那句

§4.85 记本轮第二课：常驻校验里的"子串过滤"会被**新名字**误伤
（`chestplate` 含 `plate` ⇒ 一条老门当场红）。
"""
import io
import sys

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
ARCH = r"E:\PotatoST\docs\开发档案.md"

PITFALL = u"""### 4.85 【校验雷】常驻门里的**子串过滤**会被"新名字"误伤（0.11 ZF116）

`_zf90_verify.py` 里有一条从 ZF90 立到现在的断言：

```python
left = sorted(n for n in os.listdir(TEXI) if u"plate" in n)
eq(u"textures/item 里的板现在正好三张", [cu, iron, steel], left)
```

ZF116 把 **`star_steel_chestplate.png`** 放进同一个目录，这条立刻红：
**"chestplate" 里含 "plate"** ⇒ 它被当成第四张板子。
但胸甲根本不是这张门要保护的东西（它保护的是**通用板 `plate.png` 已被删**这件事），
`chestplate` 还是**原版就有的命名**（`minecraft:item/iron_chestplate`）。

**改法与边界**：收窄成"以 `_plate.png` 结尾 **或** 正好叫 `plate.png`"。
判据一条没少 —— 三张专用板仍在枚举里、`plate.png` 若复活照样被抓
（`check(u"textures/item/plate.png 已不存在")` 那条也在）—— **这不是放宽断言**：
放宽是"把会失败的东西改到不会失败"，这里是把**误伤**的输入排除掉。

**规矩**：

1. 常驻门里凡是"按名字挑文件"的过滤（`in` / `startswith` / 正则），
   **一律写成带边界的模式**（`_plate.png` 这种带分隔符的后缀，或锚定正则），
   **不要用裸子串** —— 目录里随时会冒出别人新加的名字。
2. 门红了先问"**这是不是我的新东西把它撞了**"，再问"是不是真 bug"（§4.30 同一族）。
   本轮的判据是：ZF116 只新增了 4 个 PNG + 改了 3 个模型指向，
   **没有任何一条改动会碰"板"的语义** ⇒ 那就有理由怀疑是门的判据太宽，而不是产物错了。
3. 改门**必须同时把理由写进门的注释里**（本轮两张门都写了），
   否则下一轮有人看到"这里为什么要 `endswith`"会又改回子串。

"""


def main():
    raw = io.open(ARCH, encoding="utf-8").read()
    if u"### 4.85 " in raw:
        print(u"  [幂等] 档案已有 §4.85")
        return 0
    anchor = u"### 4.84 "
    if raw.count(anchor) != 1:
        print(u"  !! §4.84 锚点出现 %d 次，停手" % raw.count(anchor))
        return 1
    idx = raw.index(anchor)
    out = raw[:idx] + PITFALL + raw[idx:]
    io.open(ARCH, "w", encoding="utf-8", newline="\n").write(out)

    back = io.open(ARCH, encoding="utf-8").read()
    ok = (u"### 4.85 " in back and u"### 4.84 " in back and u"### 4.83 " in back
          and u"| ZF116 |" in back)
    print(u"  %s 档案插入 §4.85；回读确认 4.83 / 4.84 / ZF116 行都在"
          % (u"[OK]" if ok else u"[!!]"))
    print(u"  %d -> %d 字节" % (len(raw.encode()), len(back.encode())))
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
