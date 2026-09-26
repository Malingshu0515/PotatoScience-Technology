# -*- coding: utf-8 -*-
u"""ZF145：核对待写 JSON 的格式（缩进 / 尾换行），只读。"""
import io, os, json, glob, sys
ROOT = r'E:\PotatoST'
ADV = os.path.join(ROOT, 'src', 'main', 'resources', 'data', 'potato_s_t', 'advancement')
for n in ('star_steel.json', 'new_beginning.json', 'star_steel_armor.json'):
    b = io.open(os.path.join(ADV, n), 'rb').read()
    txt = b.decode('utf-8')
    print(n)
    print(u'  末尾 20 字节 = %r' % b[-20:])
    print(u'  有 CRLF = %s' % (b'\r\n' in b))
    print(u'  顶层键序 = %s' % list(json.loads(txt).keys()))
    print(u'  display 键序 = %s' % list(json.loads(txt).get('display', {}).keys()))
    print(u'  icon 键序 = %s' % list(json.loads(txt).get('display', {}).get('icon', {}).keys()))
    # 缩进宽度
    for line in txt.split('\n'):
        if line.startswith(' ') and line.strip():
            print(u'  首层缩进 = %d 空格' % (len(line) - len(line.lstrip(' '))))
            break
# 现有 criteria 的写法样例
d = json.loads(io.open(os.path.join(ADV, 'titanium_tools.json'), encoding='utf-8').read())
print(u'titanium_tools criteria = %s' % json.dumps(d['criteria'], ensure_ascii=False))
print(u'titanium_tools requirements = %s' % json.dumps(d['requirements'], ensure_ascii=False))
d = json.loads(io.open(os.path.join(ADV, 'pressing.json'), encoding='utf-8').read())
print(u'pressing criteria keys = %s' % list(d['criteria'].keys()))
print(u'pressing items[0] = %s' % json.dumps(d['criteria'][list(d['criteria'])[0]], ensure_ascii=False)[:300])
print(u'pressing requirements = %s' % json.dumps(d['requirements'], ensure_ascii=False))
