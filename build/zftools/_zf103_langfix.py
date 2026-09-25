# -*- coding: utf-8 -*-
u"""_zf103_langfix.py —— 把用户润色时被覆盖掉的 3 个键补回 `zh_cn.json`（只加这 3 个，别的一字不动）

来历：用户润色后的那份是基于 **ZF102 之前**的 zh_cn（332 键）⇒ 把 ZF102 新加的三个键覆盖掉了：
  · `gui.potato_s_t.acidic_reaction_chamber.recipe.name.3`（第 4 个按钮的名字）
  · `gui.potato_s_t.acidic_reaction_chamber.recipe.info.3`（第 4 个按钮的悬停说明）
  · `fluid_type.potato_s_t.hydrochloric_acid`（盐酸的流体名）

这三个键**原文就是 ZF102 里我写的那三句**（用户的 10 处润色一处都没碰它们 —— 它们在他的底稿里根本不存在）
⇒ 补回去 = 恢复事实，不是替用户改文案。

自证：① 补之前先断言"正好缺这三个"；② 补之后逐键比对，**除这三个之外**必须与用户那份**完全一致**。
"""
import io
import json
import sys

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

P = r"E:\PotatoST\src\main\resources\assets\potato_s_t\lang\zh_cn.json"
BACKUP = r"E:\PotatoST\build\zftools\_zf103_zh_cn_user.json"

ADD = {
    u"gui.potato_s_t.acidic_reaction_chamber.recipe.name.3": u"盐酸",
    u"gui.potato_s_t.acidic_reaction_chamber.recipe.info.3":
        u"盐酸：每 tick 10 mB 氢气 + 10 mB 氯气 + 5 mB 水 → 5 mB 盐酸",
    u"fluid_type.potato_s_t.hydrochloric_acid": u"盐酸",
}

fails = []


def main():
    raw = io.open(P, encoding="utf-8").read()
    user = json.loads(raw)
    io.open(BACKUP, "w", encoding="utf-8", newline=u"\n").write(raw)   # 先把用户那份原样留一份
    print(u"用户那份（%d 键）已留档：%s" % (len(user), BACKUP))
    missing = [k for k in ADD if k not in user]
    # ⚠ 第一次写成 `missing != sorted(ADD)`：`missing` 是**字典序**、`sorted(ADD)` 是**字母序**
    #   ⇒ 两个列表内容一样却判不等，白报一条 FAIL（§4.30「先怀疑期望」第 N 次）。
    if set(missing) != set(ADD):
        fails.append(u"缺的键不是预期的这三个：%s" % missing)
        print(u"  [FAIL] " + fails[-1])
        return 1
    print(u"  [OK]   正好缺这三个（ZF102 新加的）")

    # 行级插入：与 `_zf102_lang.py` 同一套写法（每行自带逗号，最后一行不带）
    lines = raw.split(u"\n")
    last = max(i for i, l in enumerate(lines) if l.strip().startswith(u'"'))
    if not lines[last].rstrip().endswith(u","):
        lines[last] = lines[last].rstrip() + u","
    block = [u'    %s:  %s,' % (json.dumps(k, ensure_ascii=False), json.dumps(v, ensure_ascii=False))
             for k, v in ADD.items()]
    block[-1] = block[-1][:-1]
    lines[last + 1:last + 1] = block
    text = u"\n".join(lines)
    back = json.loads(text)
    if len(back) != len(user) + 3:
        fails.append(u"回读键数 %d ≠ %d" % (len(back), len(user) + 3))
    # ⚠ 除这三个之外，别的键必须**逐字**与用户那份一致
    diff = [k for k in user if back.get(k) != user[k]]
    if diff:
        fails.append(u"补键碰坏了别的键：%s" % diff)
    if fails:
        print(u"  [FAIL] 一个字节都不写：%s" % fails)
        return 1
    io.open(P, "w", encoding="utf-8", newline=u"").write(text)
    print(u"  [OK]   补回三个键：%d → %d 键，其余 %d 键逐字未动" % (len(user), len(back), len(user)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
