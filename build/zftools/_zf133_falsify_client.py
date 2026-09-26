# -*- coding: utf-8 -*-
"""_zf133_falsify_client.py —— 反证 C13：把"崩溃那次"的写法塞回去，判据必须咬住

注入的就是**用户实机崩溃时的原样**：
```java
if (any) { BufferUploader.drawWithShader(buffer.buildOrThrow()); }
else { buffer.buildOrThrow(); }
```
以及另一种走法：把 `Tesselator.begin` 留着但删掉收尾（"漏了"）。
两条都必须被 C13/C13b 咬住，否则这条门是摆设。

跑法：python build\\zftools\\_zf133_falsify_client.py
"""
import hashlib
import io
import os
import subprocess
import sys

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
ROOT = r"E:\PotatoST"
REND = os.path.join(ROOT, r"src\main\java\com\potatost\mod\client\ShockwaveRenderer.java")
VERIFY = os.path.join(ROOT, r"build\zftools\_zf133_verify.py")


def sha(p):
    return hashlib.sha1(open(p, "rb").read()).hexdigest()


def run_verify():
    env = dict(os.environ, PYTHONIOENCODING="utf-8")
    r = subprocess.run([sys.executable, VERIFY], capture_output=True, env=env)
    out = r.stdout.decode("utf-8", "replace")
    return [l.strip() for l in out.split("\n") if "[FAIL]" in l]


# 用例：(编号, 说明, 注入后的完整 drawWall 末尾, 期望红的编号)
CRASH_TAIL = """        if (coreAlpha <= 2) {
            return;   // 整道波都淡到看不见了：**不开始** builder
        }
        BufferBuilder buffer = Tesselator.getInstance()
                .begin(VertexFormat.Mode.QUADS, DefaultVertexFormat.POSITION_COLOR);
        QUADS_HERE
        if (any) {
            BufferUploader.drawWithShader(buffer.buildOrThrow());
        } else {
            buffer.buildOrThrow();
        }
    }"""


def main():
    orig = io.open(REND, encoding="utf-8").read()
    base = sha(REND)
    print("基线失败条数 =", len(run_verify()))

    cases = [
        ("K-CLIENT-1",
         "把崩溃那次的原样塞回去（else 里单独一句 buildOrThrow）",
         "        // 到这里一定至少有一个四边形（门槛已在函数开头判过）\n"
         "        BufferUploader.drawWithShader(buffer.buildOrThrow());",
         "        BufferUploader.drawWithShader(buffer.buildOrThrow());\n"
         "        buffer.buildOrThrow();",
         "C13b"),
        ("K-CLIENT-2",
         "开了 builder 却不收尾（漏掉 drawWithShader）",
         "        // 到这里一定至少有一个四边形（门槛已在函数开头判过）\n"
         "        BufferUploader.drawWithShader(buffer.buildOrThrow());",
         "        // 故意不收尾",
         "C13"),
    ]

    results = []
    for kid, desc, old, new, expect in cases:
        s = orig
        n = s.count(old)
        if n != 1:
            print("[SKIP] %s 锚点 %d 次" % (kid, n))
            results.append((kid, desc, "ANCHOR", False))
            continue
        io.open(REND, "w", encoding="utf-8", newline="\n").write(s.replace(old, new, 1))
        fails = run_verify()
        hit = any(expect in f for f in fails)
        results.append((kid, desc, "红 %d 条，含 %s = %s" % (len(fails), expect, hit), hit))
        print("[%s] %s —— 红 %d 条，%s %s" % ("咬住" if hit else "**没咬住**", kid,
                                              len(fails), expect, "命中" if hit else "没命中"))
        for f in fails[:4]:
            print("        " + f[:150])
        io.open(REND, "w", encoding="utf-8", newline="\n").write(orig)
        assert sha(REND) == base, "还原不干净"

    io.open(REND, "w", encoding="utf-8", newline="\n").write(orig)
    print("还原后失败 =", len(run_verify()))
    caught = sum(1 for r in results if r[3])
    print("反证结果：%d / %d" % (caught, len(results)))
    return 0 if caught == len(results) else 1


sys.exit(main())
