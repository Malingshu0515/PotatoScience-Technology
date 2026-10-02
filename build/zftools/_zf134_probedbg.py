# -*- coding: utf-8 -*-
"""_zf134_probedbg.py —— (j) 为什么还是"耐久 0/0"？把手上那件东西与静态 axe 都打出来

`耐久 0/0` 说明 `getMaxDamage() == 0` —— 那是**空气**的特征（不是"耐久扣光了"）。
所以要么 `axe` 这个静态栈本身空了，要么玩家手上被换成了别的。打印出来看。
同时把 `[DIRECT]` 的反射异常也打全（上一跑只报"直接结算那一刀"失败，没看到异常）。
"""
import io
import sys

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
CHK = r"E:\PotatoST\src\main\java\com\potatost\mod\Zf133Check.java"

ANCHOR = "        useAxe(player);\n    }\n\n    /** 斜角场景的检查"

INSERT = """        say(TAG + "      [J] 手上=" + player.getMainHandItem() + " 空? " + player.getMainHandItem().isEmpty()
                + " 耐久=" + player.getMainHandItem().getDamageValue() + "/" + player.getMainHandItem().getMaxDamage());
        say(TAG + "      [J] 静态 axe 空? " + axe.isEmpty()
                + " 耐久=" + axe.getDamageValue() + "/" + axe.getMaxDamage()
                + " 同一实例? " + (player.getMainHandItem() == axe));
        useAxe(player);
    }

    /** 斜角场景的检查"""

s = io.open(CHK, encoding="utf-8").read()
n = s.count(ANCHOR)
assert n == 1, "锚点 %d 次" % n
s = s.replace(ANCHOR, INSERT, 1)

# [DIRECT] 的异常要打全（第一版只打一句 t，没有堆栈？其实有 printStackTrace，但被截断了 —— 改成打 message + 首行）
s = s.replace('            say(TAG + "      [DIRECT] 反射调用失败：" + t);',
              '            say(TAG + "      [DIRECT] 反射调用失败：" + t.getClass().getName() + ": " + t.getMessage());', 1)

io.open(CHK, "w", encoding="utf-8", newline="\n").write(s)
print("[OK] 已加 (j) 诊断 + DIRECT 异常摘要")
