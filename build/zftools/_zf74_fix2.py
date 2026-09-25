# -*- coding: utf-8 -*-
u"""_zf74_fix2.py —— 两件事：① 把 B2 断言改成"真的调用了标签判定"；② §5 的 ZF74 行补上反证结果

为什么改 B2：反证第 3 刀把 `return fluid.defaultFluidState().is(Tags.Fluids.GASEOUS);`
换成 `return false;`，校验**没挂** —— 因为断言查的是子串 `Tags.Fluids.GASEOUS`，
而那段代码的**注释里**也写着这个词。这跟 ZF73 的 A14 是同一类错（子串断言 ≠ 代码断言），
一轮里犯两次，值得记档。
"""
import io
import sys

VERIFY = r"E:\PotatoST\build\zftools\_zf74_verify.py"
ARCH = r"E:\PotatoST\docs\开发档案.md"

V_OLD = u'''    check(u"B2 isGas 还认 #c:gaseous（别人挂的气体也算气体）",
          u"Tags.Fluids.GASEOUS" in body)'''
V_NEW = u'''    # ⚠ 第一版这里查的是子串 `Tags.Fluids.GASEOUS` —— 反证第 3 刀把**代码**换成 `return false;`
    # 时校验没挂，因为上面那段注释里也写着这个词。改成断言**真的调用**（与 ZF73 的 A14 同一个教训）。
    check(u"B2 isGas 真的调用 #c:gaseous 判定（不是只在注释里提到）",
          u"fluid.defaultFluidState().is(Tags.Fluids.GASEOUS)" in body)'''

A_OLD = u"| 见 §6.19 / §9 |"
A_NEW = (u"⑥ **反证 4 刀**：gaseous 少挂一个氧（A 挂）、crude_oil 改 `replace:true`（A 挂）、"
         u"档案删掉作废声明（C7 挂）、isGas 不再认标签（B2 挂）；每刀逐字节还原、复跑全绿。"
         u"⚠ **第 3 刀第一次没抓住**：B2 原来查的是子串 `Tags.Fluids.GASEOUS`，而那段注释里也有这个词 —— "
         u"与 ZF73 的 A14 同属「子串断言 ≠ 代码断言」，一轮里犯两次，改成断言真的调用后才挂 | 见 §6.19 / §9 |")


def main():
    t = io.open(VERIFY, "r", encoding="utf-8").read()
    if t.count(V_OLD) != 1:
        print(u"B2 锚点命中 %d 次 ⇒ 不写" % t.count(V_OLD))
        return 1
    io.open(VERIFY, "w", encoding="utf-8", newline=u"\n").write(t.replace(V_OLD, V_NEW, 1))
    print(u"  [OK] B2 断言改成「真的调用」")

    a = io.open(ARCH, "r", encoding="utf-8").read()
    if a.count(A_OLD) != 1:
        print(u"§5 行尾锚点命中 %d 次 ⇒ 不写" % a.count(A_OLD))
        return 1
    io.open(ARCH, "w", encoding="utf-8", newline=u"\n").write(a.replace(A_OLD, A_NEW, 1))
    print(u"  [OK] §5 ZF74 行补上反证结果与教训")
    return 0


if __name__ == "__main__":
    sys.exit(main())
