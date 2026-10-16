# -*- coding: utf-8 -*-
r"""_zf179_128b.py —— 把 ZF179「改上 128」的补记写进三份文档（上一跑在"找不到后面的 ---"上崩了）

崩因：ZF179 那一节是 `贴图清单.md` 的**最后一节**，它后面没有 `\n---\n` ⇒ 我的插入点找不着。
这回改稳妥：清单**追加到文末**、档案**在这一行的最后一个 `|` 之前插**。
"""
import io, os, sys
sys.stdout.reconfigure(encoding='utf-8', errors='replace')
ROOT = r'E:\PotatoST\PotatoSTneoforge1.21.1'
DOCS = os.path.join(ROOT, 'docs')
LIST = os.path.join(DOCS, u'贴图清单.md')
ARCH = os.path.join(DOCS, u'开发档案.md')
ANN = os.path.join(DOCS, 'UpdateAnnouncement_EN.md')
fails = []
def check(ok, msg):
    print((u'  [OK]   ' if ok else u'  [FAIL] ') + msg)
    if not ok:
        fails.append(msg)
def read(p):
    return io.open(p, encoding='utf-8').read()
def write(p, t):
    io.open(p, 'w', encoding='utf-8', newline='\n').write(t)

print(u'===== ① 贴图清单：ZF179 节（它在文末）追加补记 =====')
NOTE = (u"\n- **ZF179 补记（用户拍板）**：「行直接上128」⇒ 引力装置**改用 128x128 原字节复制**"
        u"（不重采样、不二值化，sha1 `8c283a8272b7` 与素材逐位相同）。上文那张四种定尺的对比表**只作留档**："
        u"16 / 32 / 64 三版都在 `build/zftools/`（`_zf179_reject16.png` / `_zf179_keep32.png` / "
        u"`zf179_pre/gravity_device.64x64.png`）。"
        u"⚠ 代价如实记：物品贴图固定画在 16 逻辑像素的四边形上 ⇒ **低界面缩放下靠 mipmap 平滑**，观感偏"
        u"「照片感」而不是像素画（预览 `_zf179_preview128.png` 第三格就是低缩放模拟）；缩放 8 才 1:1。\n")
t = read(LIST)
if u'ZF179 补记（用户拍板）' in t:
    print(u'  [幂等] 已记过')
else:
    check(u'## ZF179（0.13）' in t, u'清单里有 ZF179 节')
    if not t.endswith(u'\n'):
        t += u'\n'
    write(LIST, t + NOTE)
    check(u'ZF179 补记（用户拍板）' in read(LIST), u'贴图清单已补记（%d -> %d 字节）'
          % (len(t.encode()), len(read(LIST).encode())))

print()
print(u'===== ② 档案：钉在 ZF179 那一行的最后一个 | 之前 =====')
ADD = (u"　**ZF179 补记**：用户拍板「行直接上128」⇒ 引力装置改用 **128x128 原字节复制**"
       u"（sha1 `8c283a8272b7` 与素材逐位相同；16/32/64 三版留档在 `build/zftools/`）。")
t = read(ARCH)
if u'行直接上128' in t:
    print(u'  [幂等] 已记过')
else:
    lines = t.split(u'\n')
    idx = [k for k, l in enumerate(lines) if l.startswith(u'| ZF179 |')]
    check(len(idx) == 1, u'ZF179 行唯一（实测 %d 行）' % len(idx))
    if len(idx) == 1:
        k = idx[0]
        ln = lines[k]
        p = ln.rfind(u'|')
        check(p > 0, u'这一行有收尾的 |')
        lines[k] = ln[:p] + ADD + u' ' + ln[p:]
        write(ARCH, u'\n'.join(lines))
        check(u'行直接上128' in read(ARCH), u'档案变更行已补记')

print()
print(u'===== ③ 英文公告 =====')
EN = (u"\n**ZF179 follow-up:** the Gravity Device texture is now the **original 128x128**, copied in\n"
      u"byte-for-byte rather than rescaled. Note the trade-off for the record: an item texture is always\n"
      u"drawn on a 16-pixel quad, so at low GUI scales the extra detail is smoothed by mipmapping (it reads\n"
      u"more like a tiny illustration than pixel art); it is 1:1 only at GUI scale 8. The 16/32/64 variants\n"
      u"are kept in the tools folder.\n")
t = read(ANN)
if u'ZF179 follow-up' in t:
    print(u'  [幂等] 已记过')
else:
    if not t.endswith(u'\n'):
        t += u'\n'
    write(ANN, t + EN)
    check(u'ZF179 follow-up' in read(ANN), u'英文公告已补记')

print()
print(u'===== ④ 终检 =====')
for label, cond in ((u'清单 补记', u'ZF179 补记（用户拍板）' in read(LIST)),
                    (u'清单 待画 = 9', u'## 待画（9 个' in read(LIST)),
                    (u'档案 补记', u'行直接上128' in read(ARCH)),
                    (u'档案 ZF179 行仍在', u'| ZF179 |' in read(ARCH)),
                    (u'公告 补记', u'ZF179 follow-up' in read(ANN))):
    check(cond, label)
print()
print(u'失败项 = %d' % len(fails))
sys.exit(1 if fails else 0)
