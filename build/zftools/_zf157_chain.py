# -*- coding: utf-8 -*-
r"""_zf157_chain.py —— ZF157：把「借原版贴图的模型数」这条**活体数字链** 13 -> 9 跟平

这条链**四处**（ZF127 立的规矩，见 `_zf90_verify.py:177-184`）：
  ① `docs/UpdateAnnouncement_EN.md` 里那句 `N models still do this`
  ② `_zf71_verify.py` 的 `n_draw`（一处断言 + 一处文案）
  ③ `_zf90_verify.py` 的三条（公告那句 / 黑名单 / `_zf71` 同步）
  ④ `docs/贴图清单.md` 的表头（已由 `TextureCheck.py --plan` 重跑，已是 9）
⚠ 黑名单里**原来就有 9**（历史上的值）—— 现数变成 9 之后，那条「不许再出现 9 models」
  会当场把**正确的**状态判红。所以黑名单要把 9 摘掉、把 13 加进去。
"""
import io, os, sys
sys.stdout.reconfigure(encoding='utf-8', errors='replace')
ROOT = r'E:\PotatoST'
TOOLS = os.path.join(ROOT, 'build', 'zftools')
DOCS = os.path.join(ROOT, 'docs')
fails = []
def check(ok, msg):
    print(('  [OK]   ' if ok else '  [FAIL] ') + msg)
    if not ok:
        fails.append(msg)

def read(p):
    return io.open(p, encoding='utf-8').read()

def write(p, t):
    io.open(p, 'w', encoding='utf-8', newline='\n').write(t)

def patch(path, pairs, label):
    t = read(path)
    for old, new in pairs:
        n = t.count(old)
        check(n == 1, u'%s：锚点命中 1 次（实测 %d）—— %s' % (label, n, old[:46]))
        if n == 1:
            t = t.replace(old, new)
    write(path, t)
    import ast
    if path.endswith('.py'):
        ast.parse(read(path))
        check(True, u'%s 改后能过 ast.parse' % label)

Z90 = os.path.join(TOOLS, '_zf90_verify.py')
Z71 = os.path.join(TOOLS, '_zf71_verify.py')
ANN = os.path.join(DOCS, 'UpdateAnnouncement_EN.md')

print(u'===== ① `_zf90_verify.py`（三处 + 两处注释）=====')
patch(Z90, [
    (u'check(u"英文公告已改成 13 models still do this", u"13 models still do this" in ann)',
     u'check(u"英文公告已改成 9 models still do this", u"9 models still do this" in ann)'),
    (u'check(u"英文公告里不再写 5/6/7/9/12/15 models（13 是当前值，不进黑名单）", not any(u"%d models still do this" % n in ann\n'
     u'                                                     for n in (5, 6, 7, 9, 12, 15)))',
     u'check(u"英文公告里不再写 5/6/7/12/13/15 models（9 是当前值，不进黑名单）", not any(u"%d models still do this" % n in ann\n'
     u'                                                     for n in (5, 6, 7, 12, 13, 15)))'),
    (u'check(u"`_zf71_verify.py` 的期望值同步成 13", u"n_draw == 13" in z71)',
     u'check(u"`_zf71_verify.py` 的期望值同步成 9", u"n_draw == 9" in z71)'),
    (u'    #   公告那句、本脚本两条、`_zf71_verify.py` 的 `n_draw`、`docs/贴图清单.md` 的表头）',
     u'    #   公告那句、本脚本两条、`_zf71_verify.py` 的 `n_draw`、`docs/贴图清单.md` 的表头）\n'
     u'    #   **ZF157** 钛合金套四件拿到自己的背包图标（热力金属那张本来就是自己的）⇒ **13 → 9**\n'
     u'    #   （同样四处一起改；⚠ 黑名单里原来就有 9 ⇒ 要把它摘掉、把 13 加进去，否则会把对的状态判红）'),
    (u'    # ZF110/ZF116/ZF120 重跑过 `TextureCheck.py --plan` ⇒ 表头跟着活体数字走（现在 13 个）',
     u'    # ZF110/ZF116/ZF120/ZF157 重跑过 `TextureCheck.py --plan` ⇒ 表头跟着活体数字走（现在 9 个）'),
], u'_zf90_verify.py')

print(u'===== ② `_zf71_verify.py`（两处 + 注释）=====')
patch(Z71, [
    (u'check(n_draw == 13 and u"13 models still do this" in doc,\n'
     u'          u"还在借原版贴图的模型 = %d 个（公告写 13）" % n_draw)',
     u'check(n_draw == 9 and u"9 models still do this" in doc,\n'
     u'          u"还在借原版贴图的模型 = %d 个（公告写 9）" % n_draw)'),
    (u'    #   （这一次把 `_zf71_verify.py` 也一起跟到 15 —— ZF120 那次漏了它，它就一直红着）',
     u'    #   （这一次把 `_zf71_verify.py` 也一起跟到 15 —— ZF120 那次漏了它，它就一直红着）\n'
     u'    #   **ZF157** 钛合金套四件拿到自己的背包图标 ⇒ **13 → 9**（四处一起改）'),
], u'_zf71_verify.py')

print(u'===== ③ 英文公告那句 =====')
patch(ANN, [(u'(13 models still do this', u'(9 models still do this')], u'UpdateAnnouncement_EN.md')

print(u'===== ④ 回读 =====')
z90 = read(Z90); z71 = read(Z71); ann = read(ANN); lst = read(os.path.join(DOCS, u'贴图清单.md'))
for label, cond in ((u'_zf90：公告那条 = 9', u'9 models still do this" in ann' in z90),
                    (u'_zf90：黑名单已换成 5/6/7/12/13/15', u'for n in (5, 6, 7, 12, 13, 15)' in z90),
                    (u'_zf90：n_draw == 9', u'u"n_draw == 9" in z71' in z90),
                    (u'_zf71：n_draw == 9', u'n_draw == 9' in z71),
                    (u'_zf71：公告写 9', u'（公告写 9）' in z71),
                    (u'公告：9 models still do this', u'9 models still do this' in ann),
                    (u'公告：13 models 已绝迹', u'13 models still do this' not in ann),
                    (u'清单表头 = 9', u'## 待画（9 个' in lst)):
    check(cond, label)
print(u'失败项 = %d' % len(fails))
sys.exit(1 if fails else 0)
