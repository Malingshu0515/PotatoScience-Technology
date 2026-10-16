# -*- coding: utf-8 -*-
r"""_zf171_probe.py —— "重启游戏还是不显示"：先查**游戏到底加载的是哪份资源**

三件事：
  ① 方块状态文件指向哪个模型（模型没被 blockstate 用到的话，改模型等于没改）；
  ② 盘上有哪些 PotatoS/T 的 jar、各自什么时候打的；
  ③ 每个 jar **里面**那几张贴图是什么（sha1 与源目录现值的比对）—— 这是判"是不是装的旧包"的硬证据。
"""
import glob, hashlib, io, json, os, sys, zipfile
sys.stdout.reconfigure(encoding='utf-8')
ROOT = r'E:\PotatoST\PotatoSTneoforge1.21.1'
ASSET = os.path.join(ROOT, 'src', 'main', 'resources', 'assets', 'potato_s_t')

print(u'===== ① 方块状态 -> 模型 =====')
for bs in ['filling_machine']:
    p = os.path.join(ASSET, 'blockstates', bs + '.json')
    if os.path.exists(p):
        raw = io.open(p, encoding='utf-8').read()
        print(u'  blockstates/%s.json: %s' % (bs, raw.strip().replace('\n', ' ')[:400]))
        try:
            d = json.loads(raw)
            models = set()
            for v in d.get('variants', {}).values():
                if isinstance(v, dict):
                    models.add(v.get('model'))
                elif isinstance(v, list):
                    for e in v:
                        models.add(e.get('model'))
            if 'multipart' in d:
                for e in d['multipart']:
                    ap = e.get('apply')
                    if isinstance(ap, dict):
                        models.add(ap.get('model'))
            print(u'  ⇒ 用到的模型：%s' % sorted(m for m in models if m))
        except Exception as e:
            print(u'  !! blockstate 解析失败：%s' % e)
    else:
        print(u'  !! 没有 blockstates/%s.json' % bs)

print()
print(u'===== ② 盘上的 jar =====')
CAND = [os.path.join(ROOT, 'release'), os.path.join(ROOT, 'build', 'libs'),
        os.path.join(ROOT, 'run', 'mods'), os.path.join(ROOT, 'run', 'client', 'mods'),
        os.path.join(os.environ.get('APPDATA', ''), '.minecraft', 'mods'),
        os.path.join(os.environ.get('APPDATA', ''), 'com.modrinth.theseus', 'profiles')]
jars = []
for d in CAND:
    if not os.path.isdir(d):
        continue
    for f in sorted(glob.glob(os.path.join(d, '*.jar'))):
        if 'otato' in os.path.basename(f) or 'potato' in os.path.basename(f).lower():
            jars.append(f)
for f in sorted(glob.glob(os.path.join(ROOT, 'run', '**', '*.jar'), recursive=True)):
    if 'otato' in os.path.basename(f):
        jars.append(f)
if not jars:
    print(u'  没找到 PotatoS/T 的 jar')
for f in sorted(set(jars)):
    st = os.stat(f)
    print(u'  %-70s %9d B  %s  sha1 %s' % (f, st.st_size,
          __import__('datetime').datetime.fromtimestamp(st.st_mtime).strftime('%Y-%m-%d %H:%M'),
          hashlib.sha1(open(f, 'rb').read()).hexdigest()[:12]))

print()
print(u'===== ③ jar 里的贴图 vs 源目录现值 =====')
WATCH = ['assets/potato_s_t/textures/block/filling_machine_side.png',
         'assets/potato_s_t/textures/block/filling_machine_top.png',
         'assets/potato_s_t/textures/block/filling_machine_bottom.png',
         'assets/potato_s_t/textures/item/titanium_alloy_helmet.png',
         'assets/potato_s_t/textures/block/crude_oil_still.png']
now = {}
for w in WATCH:
    rel = w.replace('assets/potato_s_t/', '')
    p = os.path.join(ASSET, rel.replace('/', os.sep))
    now[w] = hashlib.sha1(open(p, 'rb').read()).hexdigest()[:12] if os.path.exists(p) else 'MISSING'
print(u'  源目录现值：')
for w in WATCH:
    print(u'    %-58s %s' % (w.split('/')[-1], now[w]))
for f in sorted(set(jars)):
    print(u'  --- %s ---' % f)
    try:
        z = zipfile.ZipFile(f)
    except Exception as e:
        print(u'    !! 打不开：%s' % e)
        continue
    names = set(z.namelist())
    for w in WATCH:
        if w not in names:
            print(u'    %-58s **不在包里**' % w.split('/')[-1])
            continue
        h = hashlib.sha1(z.read(w)).hexdigest()[:12]
        print(u'    %-58s %s %s' % (w.split('/')[-1], h,
              u'== 源（新）' if h == now[w] else u'**旧包**'))
    mb = 'assets/potato_s_t/models/block/filling_machine.json'
    if mb in names:
        t = z.read(mb).decode('utf-8')
        print(u'    模型里的 bottom 槽：%s' % (u'有' if u'"bottom"' in t else u'**没有（旧包）**'))
