# -*- coding: utf-8 -*-
u"""ZF145 侦察 7：最后一个事实包。
  ① 振金四件的锻造台配方（template/base/addition）
  ② 钛合金四件 / 星璨钢四件的材料数
  ③ tags 目录结构（要新建 tags/damage_type/）
  ④ 四语言「最近一条」文案的写法（ja / ru 的腔调）
"""
import io, os, json, sys, glob

ROOT = r'E:\PotatoST'
RES  = os.path.join(ROOT, 'src', 'main', 'resources', 'data', 'potato_s_t')
LANG = os.path.join(ROOT, 'src', 'main', 'resources', 'assets', 'potato_s_t', 'lang')
OUT  = os.path.join(ROOT, 'build', 'zftools', '_zf145_recon7.txt')
lines = []
def w(s=u''):
    lines.append(s)

w(u'===== ZF145 侦察 7 =====')
w()
w(u'--- ① 振金四件锻造台配方 ---')
for n in ('vibranium_helmet_smithing', 'vibranium_chestplate_smithing',
          'vibranium_leggings_smithing', 'vibranium_boots_smithing'):
    fp = os.path.join(RES, 'recipe', n + '.json')
    d = json.load(io.open(fp, encoding='utf-8'))
    w(u'  %s : type=%s' % (n, d.get('type')))
    for k in ('template', 'base', 'addition', 'result'):
        w(u'      %-9s %s' % (k, json.dumps(d.get(k), ensure_ascii=False)))
w()

w(u'--- ② 三套盔甲的材料数（从图纸数 X）---')
for n in ('titanium_alloy_helmet', 'titanium_alloy_chestplate', 'titanium_alloy_leggings',
          'titanium_alloy_boots', 'star_steel_helmet', 'star_steel_chestplate',
          'star_steel_leggings', 'star_steel_boots'):
    d = json.load(io.open(os.path.join(RES, 'recipe', n + '.json'), encoding='utf-8'))
    cnt = sum(r.count('X') for r in d.get('pattern', []))
    w(u'  %-30s X=%d  key=%s' % (n, cnt, json.dumps(d.get('key'), ensure_ascii=False)))
w()

w(u'--- ③ tags 目录现状 ---')
for p in sorted(glob.glob(os.path.join(RES, 'tags', '**'), recursive=True)):
    if os.path.isdir(p):
        w(u'  [目录] ' + os.path.relpath(p, RES))
    elif os.path.basename(os.path.dirname(p)) in ('tags',) or True:
        pass
w(u'  tags 下的文件（前 25）：')
for p in sorted(glob.glob(os.path.join(RES, 'tags', '**', '*.json'), recursive=True))[:25]:
    w(u'    ' + os.path.relpath(p, RES))
w(u'  合计 %d 份' % len(glob.glob(os.path.join(RES, 'tags', '**', '*.json'), recursive=True)))
w()

w(u'--- ④ 四语言样板（ZF144 加的那 5 个键）---')
samples = ('item.potato_s_t.star_steel_shovel', 'tooltip.potato_s_t.star_steel_sword.1',
           'death.attack.potato_s_t.star_steel_slash')
tables = {}
for loc in ('zh_cn', 'en_us', 'ja_jp', 'ru_ru'):
    tables[loc] = json.load(io.open(os.path.join(LANG, loc + '.json'), encoding='utf-8'))
for k in samples:
    w(u'  [' + k + u']')
    for loc in ('zh_cn', 'en_us', 'ja_jp', 'ru_ru'):
        w(u'    %-6s %s' % (loc, tables[loc].get(k, u'(缺)')))
w()

w(u'--- ⑤ 进度文案样板：ZF117 加的 8 条（四语言）---')
for k in ('advancements.potato_s_t.star_steel.title', 'advancements.potato_s_t.star_steel.description',
          'advancements.potato_s_t.star_steel_armor.title', 'advancements.potato_s_t.star_steel_armor.description',
          'advancements.potato_s_t.titanium_tools.description',
          'advancements.potato_s_t.lithium_battery_plant.description'):
    w(u'  [' + k + u']')
    for loc in ('zh_cn', 'en_us', 'ja_jp', 'ru_ru'):
        w(u'    %-6s %s' % (loc, tables[loc].get(k, u'(缺)')))
w()

w(u'--- ⑥ 键序：lang 文件里 advancements.* 的排布（前 8 个键名 + 末尾 8 个键名）---')
ks = [k for k in tables['zh_cn']]
adv = [k for k in ks if k.startswith('advancements.')]
w(u'  总键 %d；advancements 键 %d' % (len(ks), len(adv)))
w(u'  前 6 个：%s' % ks[:6])
w(u'  末 6 个：%s' % ks[-6:])
advpos = [i for i, k in enumerate(ks) if k.startswith('advancements.')]
w(u'  advancements 键在文件里的下标范围：%d ~ %d（连续=%s）'
  % (advpos[0], advpos[-1], advpos == list(range(advpos[0], advpos[-1] + 1))))

io.open(OUT, 'w', encoding='utf-8').write(u'\n'.join(lines))
sys.stdout.write(u'OK -> %s\n' % OUT)
