# -*- coding: utf-8 -*-
r"""_zf157_gates.py —— ZF157 门阵：跑一遍，只打印每门的结论行 + 退出码"""
import io, os, re, subprocess, sys
sys.stdout.reconfigure(encoding='utf-8', errors='replace')
ROOT = r'E:\PotatoST'
TOOLS = os.path.join(ROOT, 'build', 'zftools')
env = dict(os.environ, PYTHONIOENCODING='utf-8')

GATES = ['TextureCheck.py', 'ModelCheck.py', 'JsonCheck.py', 'SoundCheck.py',
         '_zf90_verify.py', '_zf71_verify.py', '_zf127_verify.py', '_zf128_verify.py']

PAT = re.compile(u'(失败项|失败 =|非法|结论|检查项|通过 =|待画 =|警告 =|ALL OK|OK\\b)')
rows = []
for g in GATES:
    p = os.path.join(TOOLS, g)
    if not os.path.exists(p):
        rows.append((g, u'缺脚本', u''))
        continue
    try:
        r = subprocess.run([sys.executable, p], cwd=ROOT, env=env,
                           stdout=subprocess.PIPE, stderr=subprocess.STDOUT, timeout=900)
        out = r.stdout.decode('utf-8', 'replace')
        tail = [l.strip() for l in out.strip().splitlines() if PAT.search(l)]
        keep = tail[-3:] if tail else out.strip().splitlines()[-2:]
        rows.append((g, u'rc=%d' % r.returncode, u' | '.join(keep)))
    except Exception as e:
        rows.append((g, u'崩了', str(e)[:120]))
    print(u'%-22s %-7s %s' % rows[-1])

print()
bad = [r for r in rows if not r[1].startswith('rc=0')]
print(u'跑完 %d 门；非零退出的：%d' % (len(rows), len(bad)))
for r in bad:
    print(u'  !! %s %s' % (r[0], r[1]))
