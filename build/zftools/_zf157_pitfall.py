# -*- coding: utf-8 -*-
r"""_zf157_pitfall.py —— ZF157：补 §4.165（备份基目录写错 + 永远为真的断言），并把变更行里的引用改对"""
import io, os, sys
sys.stdout.reconfigure(encoding='utf-8', errors='replace')
ROOT = r'E:\PotatoST'
ARCH = os.path.join(ROOT, 'docs', '开发档案.md')
fails = []
def check(ok, msg):
    print(('  [OK]   ' if ok else '  [FAIL] ') + msg)
    if not ok:
        fails.append(msg)

BLOCK = u"""
### 4.165 【流程雷】备份循环的**基目录**写错 ⇒ 五份改前件静默没抄；而那条"备份 N 份"的断言**永远为真**（0.13 ZF157）

**两件事，一起犯的**：

1. **基目录**：`_zf157_apply.py` 的备份循环里写的是 `a = os.path.join(ROOT, rel)`，
   可 `rel` 有两套口径 —— `docs/…`、`build/…` 是**仓库相对**的，而
   `textures/item/thermal_metal.png`、`models/item/…json` 是**相对 `ASSET`**（资源根）的。
   ⇒ 后五份一律被判"不存在"，脚本打了 `[MISS]`、**一份都没抄**，
   而被顶掉的那张 160×160 占位图**当场就被覆盖了**（没有第二次机会）。
   **补法必须是可验证的**：从 **git HEAD** 取回，并且取回那份的 sha1（`e827c8325d64…` / 728 B）
   **与改前实测逐位一致** —— 拿不到这个等式，就只是"看起来像"。
2. **永远为真的断言**：紧接着那行是 `check(True, u"备份 %d 份" % len(BAK))` ——
   它数的是**我自己写的那张清单的长度**、不是**真抄到的份数**，
   于是"一份都没抄"照样打 `[OK]`（§4.17 又一次：判据必须能红）。

**规矩**：备份循环里**每一份**都要回答两个问题 ——
（a）源路径按**哪把尺子**解析（仓库相对 / 资源相对）；
（b）**抄完回读**，且"抄到几份"这个数**必须来自磁盘**（`os.path.exists(备份路径)` 现数），
不许来自我手写的那张清单。
"""


def main():
    t = io.open(ARCH, encoding='utf-8').read()
    if u'### 4.165 ' in t:
        print(u'  [幂等] 已有 §4.165')
    else:
        lines = t.split(u'\n')
        i = None
        for k, ln in enumerate(lines):
            if ln.startswith(u'### 4.164 '):
                i = k
                break
        check(i is not None, u'找到 §4.164 的标题行')
        if i is None:
            return 1
        j = None
        for k in range(i + 1, len(lines)):
            if lines[k].startswith(u'## '):
                j = k
                break
        check(j is not None, u'找到 §4.164 之后的下一个二级标题（插入点）')
        if j is None:
            return 1
        check(u'### 4.165' not in t, u'§4.165 这个号没被占（现最大是 4.164）')
        t = u'\n'.join(lines[:j]) + BLOCK + u'\n' + u'\n'.join(lines[j:])
        io.open(ARCH, 'w', encoding='utf-8', newline='\n').write(t)
        print(u'  [OK] §4.165 已插在 §4.164 那一节之后（第 %d 行前：%s）' % (j + 1, lines[j][:24]))

    # 变更行里我原先写的是 §4.166（号写错了）⇒ 改成 4.165
    t = io.open(ARCH, encoding='utf-8').read()
    old, new = u'立 **§4.166**', u'立 **§4.165**'
    if new in t and old not in t:
        print(u'  [幂等] 变更行里的引用已是 §4.165')
    else:
        n = t.count(old)
        check(n == 1, u'变更行里 `%s` 命中 1 次（实测 %d）' % (old, n))
        if n == 1:
            io.open(ARCH, 'w', encoding='utf-8', newline='\n').write(t.replace(old, new))
            print(u'  [OK] 变更行引用 §4.166 -> §4.165')

    t = io.open(ARCH, encoding='utf-8').read()
    check(u'### 4.165 ' in t and u'立 **§4.165**' in t, u'回读：小节与变更行引用都在')
    check(set(t.split(u'### 4.165 ')) and t.count(u'### 4.165 ') == 1, u'§4.165 只出现一次（标题）')
    print(u'  文档现在 %d 字节' % len(t.encode()))
    print(u'失败项 = %d' % len(fails))
    return 1 if fails else 0


if __name__ == '__main__':
    sys.exit(main())
