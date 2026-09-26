# -*- coding: utf-8 -*-
u"""ZF145 侦察 3：候选成就节点所需的配方 / 常数事实核对。只读。"""
import io, json, os, re, sys, glob

ROOT = r'E:\PotatoST'
RES  = os.path.join(ROOT, 'src', 'main', 'resources', 'data', 'potato_s_t', 'recipe')
OUT  = os.path.join(ROOT, 'build', 'zftools', '_zf145_recon3.txt')

lines = []
def w(s=u''):
    lines.append(s)

def show(name):
    fp = os.path.join(RES, name + '.json')
    if not os.path.exists(fp):
        w(u'  [无此配方] ' + name)
        return
    d = json.load(io.open(fp, encoding='utf-8'))
    t = d.get('type', '?')
    w(u'  %s  type=%s' % (name, t))
    if t == 'minecraft:crafting_shaped':
        w(u'     pattern=%s' % json.dumps(d.get('pattern'), ensure_ascii=False))
        w(u'     key=%s' % json.dumps(d.get('key'), ensure_ascii=False))
        w(u'     result=%s' % json.dumps(d.get('result'), ensure_ascii=False))
    elif t == 'minecraft:smithing_transform':
        w(u'     template=%s' % json.dumps(d.get('template'), ensure_ascii=False))
        w(u'     base=%s' % json.dumps(d.get('base'), ensure_ascii=False))
        w(u'     addition=%s' % json.dumps(d.get('addition'), ensure_ascii=False))
        w(u'     result=%s' % json.dumps(d.get('result'), ensure_ascii=False))
    else:
        w(u'     %s' % json.dumps(d, ensure_ascii=False)[:600])

w(u'===== ZF145 侦察 3：配方事实 =====')
for n in ('vibranium_ingot', 'vibranium_helmet', 'vibranium_chestplate', 'vibranium_leggings',
          'vibranium_boots', 'star_chart_tome', 'silver_wire', 'silver_wire_spool',
          'titanium_alloy_helmet', 'titanium_alloy_chestplate', 'titanium_alloy_leggings',
          'titanium_alloy_boots', 'star_steel_sword', 'star_steel_pickaxe', 'star_steel_hoe',
          'star_steel_shovel', 'star_steel_axe', 'diesel_generator_controller',
          'star_steel_helmet', 'star_steel_chestplate', 'star_steel_leggings', 'star_steel_boots'):
    w(u'[' + n + u']')
    show(n)
w()

# 合金冶炼炉里振金那条（机器配方，可能在 Java 或 alloy_smelter 数据里）
w(u'--- 抓 vibranium 相关常量（Java）---')
javadir = os.path.join(ROOT, 'src', 'main', 'java', 'com', 'potatost', 'mod')
for fp in glob.glob(os.path.join(javadir, '*.java')):
    src = io.open(fp, encoding='utf-8').read()
    if 'vibranium' in src.lower() or 'VIBRANIUM' in src:
        hits = [l.strip() for l in src.splitlines()
                if re.search(r'VIBRANIUM|vibranium', l) and re.search(r'=\s*[0-9]|new ItemStack|FE|TICK', l)]
        if hits:
            w(u'[' + os.path.basename(fp) + u']')
            for h in hits[:14]:
                w(u'    ' + h[:150])
w()

w(u'--- 星璨钢工具配方耗材（键里的锭数）---')
for n in ('star_steel_sword', 'star_steel_pickaxe', 'star_steel_hoe', 'star_steel_shovel',
          'star_steel_axe', 'star_steel_helmet', 'star_steel_chestplate'):
    fp = os.path.join(RES, n + '.json')
    if os.path.exists(fp):
        d = json.load(io.open(fp, encoding='utf-8'))
        pat = d.get('pattern', [])
        if isinstance(pat, list):
            cnt = sum(row.count('X') for row in pat)
            w(u'  %-24s X=%d' % (n, cnt))
w()

# 银线 / 星仪图之章 的配方是否在生成器表里
w(u'--- 生成器表 _zf45_recipes.py 命中 ---')
gen = io.open(os.path.join(ROOT, 'build', 'zftools', '_zf45_recipes.py'), encoding='utf-8').read()
for n in ('vibranium_ingot', 'vibranium_helmet', 'star_chart_tome', 'silver_wire',
          'titanium_alloy_helmet', 'star_steel_sword', 'star_steel_axe', 'diesel_generator_controller'):
    w(u'  %-30s %s' % (n, u'在表里' if n in gen else u'—— 不在表里'))
w()
w(u'生成器表里的配方名总数（近似）：%d' % len(re.findall(r'^\s*RECIPES?\s*=|^\s*\(\s*"', gen, re.M)))

io.open(OUT, 'w', encoding='utf-8').write(u'\n'.join(lines))
sys.stdout.write(u'OK -> %s\n' % OUT)
