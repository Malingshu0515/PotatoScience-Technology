import io
p = 'docs/开发档案.md'
lines = io.open(p, encoding='utf-8').read().split('\n')
print('total', len(lines))
for i, l in enumerate(lines):
    if l.startswith('## ') or l.startswith('### '):
        print(i+1, l[:110])
