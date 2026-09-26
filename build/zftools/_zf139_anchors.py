# -*- coding: utf-8 -*-
u"""_zf139_anchors.py —— 把要用的插入锚点原样导出来看（只读）。"""
import io

OUT = []
doc = io.open(r"E:\PotatoST\docs\开发档案.md", encoding="utf-8").read().split(u"\n")
OUT.append(u"===== 开发档案.md：共 %d 行 =====" % len(doc))
for a, b, t in ((2148, 2162, u"§5 表尾"), (4196, 4216, u"§4.112 块附近"),
                (len(doc) - 12, len(doc), u"文件末尾")):
    OUT.append(u"---- %s（%d-%d）----" % (t, a + 1, b))
    for i in range(a, min(b, len(doc))):
        OUT.append(u"%5d | %s" % (i + 1, doc[i]))

hand = io.open(r"E:\PotatoST\docs\多会话协作交接.md", encoding="utf-8").read().split(u"\n")
OUT.append(u"")
OUT.append(u"===== 多会话协作交接.md：共 %d 行 =====" % len(hand))
for i in range(0, 30):
    OUT.append(u"%4d | %s" % (i + 1, hand[i]))
OUT.append(u"---- §6 尾部 ----")
for i in range(len(hand) - 30, len(hand)):
    OUT.append(u"%4d | %s" % (i + 1, hand[i]))

ann = io.open(r"E:\PotatoST\docs\UpdateAnnouncement_EN.md", encoding="utf-8").read().split(u"\n")
OUT.append(u"")
OUT.append(u"===== UpdateAnnouncement_EN.md：共 %d 行 =====" % len(ann))
for i in range(max(0, len(ann) - 24), len(ann)):
    OUT.append(u"%4d | %s" % (i + 1, ann[i]))

io.open(r"E:\PotatoST\build\zftools\_zf139_anchors.txt", u"w", encoding="utf-8",
        newline=u"\n").write(u"\n".join(OUT) + u"\n")
print(u"ok")
