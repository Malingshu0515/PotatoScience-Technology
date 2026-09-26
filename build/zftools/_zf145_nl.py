# -*- coding: utf-8 -*-
u"""ZF145：看两份参考件的换行（tags 参考件 vs 语言文件）。只读。"""
import io, os
ROOT = r'E:\PotatoST'
for rel in (r'src\main\resources\data\potato_s_t\tags\item\potato_s_t.json',
            r'src\main\resources\data\potato_s_t\tags\item\copper_blocks.json',
            r'src\main\resources\data\potato_s_t\damage_type\star_steel_slash.json',
            r'src\main\resources\assets\potato_s_t\lang\zh_cn.json',
            r'src\main\resources\data\potato_s_t\advancement\star_steel.json'):
    b = io.open(os.path.join(ROOT, rel), 'rb').read()
    print(u'%-70s CRLF=%s CR=%d LF=%d 尾=%r' % (
        rel.replace('\\', '/'), b'\r\n' in b, b.count(b'\r'), b.count(b'\n'), b[-12:]))
