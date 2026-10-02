# -*- coding: utf-8 -*-
r"""_zf163_gatefix.py —— 修 v2 门里 `sample()` 的入参类型（base 误传成"行列表"）

病根：`sample(fr, x, p)` 是按**扁平缓冲**索引的（`fr[(i%16)*64 + x*4]`），
而判据 (4) 传进去的是 `rows_of(...)` 的**行列表** ⇒ `bytes * float` 当场 TypeError。
修法：判据 (4) 的第 0 帧底图传**扁平 bytes**。模板文件与盘上的门一起改，免得下次重装又带回来。
"""
import io, os, sys, ast, subprocess
sys.stdout.reconfigure(encoding='utf-8')
ROOT = r'E:\PotatoST'
TOOLS = os.path.join(ROOT, 'build', 'zftools')
GATE = os.path.join(TOOLS, '_zf135_fluidcheck.py')
TPL = os.path.join(TOOLS, '_zf163_gate_v2.py')
OLD = u"        base = rows_of(rgba, 0)\n        for t in range(h // 16):"
NEW = u"        base = bytes(rgba[0:1024])          # 判据 (4) 用的是**扁平**底图（sample() 按扁平索引）\n        for t in range(h // 16):"
fails = []
for p, label in ((GATE, u'盘上的门'), (TPL, u'模板')):
    t = io.open(p, encoding='utf-8').read()
    n = t.count(OLD)
    ok = (n == 1)
    print(u'  %s %s 锚点命中 %d 次' % (u'[OK]' if ok else u'[FAIL]', label, n))
    if not ok:
        fails.append(label)
        continue
    io.open(p, 'w', encoding='utf-8', newline='\n').write(t.replace(OLD, NEW))
    ast.parse(io.open(p, encoding='utf-8').read())
    print(u'  [OK] %s 已修且能过 ast.parse' % label)

print()
print(u'===== 跑门 =====')
r = subprocess.run([sys.executable, GATE], cwd=ROOT, env=dict(os.environ, PYTHONIOENCODING='utf-8'),
                   stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
out = r.stdout.decode('utf-8', 'replace')
io.open(os.path.join(TOOLS, '_zf163_gate.txt'), 'w', encoding='utf-8', newline='\n').write(out)
for l in out.splitlines():
    if l.startswith(u'  [OK]') or l.startswith(u'  !!') or u'失败项' in l or u'最大比值' in l or u'结论' in l:
        print(l)
print(u'rc = %d' % r.returncode)
print(u'失败项 = %d' % (len(fails) + (1 if r.returncode else 0)))
sys.exit(1 if (fails or r.returncode) else 0)
