# -*- coding: utf-8 -*-
u"""_zf72_docs3.py —— ZF72 第三处档案编辑（一处）：给 §5 的 ZF72 行补上第 ⑧ 条

为什么要补：ZF72 行写在"重打包自证"之前，⑦ 条收尾看着像本轮已经说完。
实际本轮还多做了一步硬证据（反证动过源码 ⇒ 真重打一遍 + 逐条目 CRC 对账），
这条不写进 §5 行，将来翻档案会以为「本轮没验过源码树」。锚点不中就不写。
"""
import hashlib
import io
import sys

ARCH = r"E:\PotatoST\docs\开发档案.md"

ANCHOR = u"| 见 §4.44 / §9 / §10 |"

ADD = u"⑧ **反证动过源码 ⇒ 真重打一遍对账**：`gradlew build --offline --no-build-cache`（17 秒，`compileJava UP-TO-DATE` —— 内容没变所以根本没重编，这本身就是旁证）+ `_zf72_rebuild_diff.py` 把新 jar 与成品**逐条目 CRC** 比：成品 **708** 条目 / 新打 **707**，**唯一差异**是 `assets/potato_s_t/textures/block/lv_001.png`（3352 B，成品里有、源码树里已被用户于 2026-09-22 删掉），其余 **707 个同名条目逐条 CRC 完全相同** ⇒ 反证没留痕迹、源码树 == 成品；同时暴露一条真事：**从今往后「重打包 == 成品」这条自证不再成立**（要恢复就只有把那张图从回收站还原回去），详见 §10 |"

fails = []


def sha1(path):
    h = hashlib.sha1()
    with io.open(path, "rb") as fh:
        h.update(fh.read())
    return h.hexdigest()


def main():
    with io.open(ARCH, "r", encoding="utf-8") as fh:
        text = fh.read()
    before_sha = sha1(ARCH)
    n = text.count(ANCHOR)
    if n != 1:
        print(u"锚点命中 %d 次（必须正好 1 次）⇒ 整篇不写" % n)
        return 1
    new_text = text.replace(ANCHOR, ADD, 1)
    with io.open(ARCH, "w", encoding="utf-8", newline=u"\n") as fh:
        fh.write(new_text)
    print(u"改前 %d 字符 %s" % (len(text), before_sha[:12]))
    print(u"改后 %d 字符 %s" % (len(new_text), sha1(ARCH)[:12]))
    print(u"§5 ZF72 行已补 ⑧")
    for f in fails:
        print(u"  !! " + f)
    return 0 if not fails else 1


if __name__ == "__main__":
    sys.exit(main())
