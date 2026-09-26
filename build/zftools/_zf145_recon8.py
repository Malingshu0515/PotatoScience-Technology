# -*- coding: utf-8 -*-
u"""ZF145 侦察 8：现有 35 条成就的四语言标题/说明（照腔调）+ 相关物品名。只读。"""
import io, json, os, sys

ROOT = r'E:\PotatoST'
LANG = os.path.join(ROOT, 'src', 'main', 'resources', 'assets', 'potato_s_t', 'lang')
OUT  = os.path.join(ROOT, 'build', 'zftools', '_zf145_recon8.txt')
lines = []
def w(s=u''):
    lines.append(s)

T = {}
for loc in ('zh_cn', 'en_us', 'ja_jp', 'ru_ru'):
    T[loc] = json.load(io.open(os.path.join(LANG, loc + '.json'), encoding='utf-8'))

IDS = ['new_beginning', 'crushing', 'pressing', 'wiring', 'first_power', 'stronger_power',
       'steel', 'titanium', 'titanium_tools', 'light_alloy', 'hard_alloy', 'star_steel',
       'star_steel_armor', 'starfall', 'salt', 'fluid_logistics', 'fuel', 'combustion',
       'distillation', 'oil', 'oil_pump', 'lithium_battery_plant', 'lithium_battery',
       'music_disc_anvil', 'music_disc_jasmine']
w(u'===== ZF145 侦察 8：腔调样板 =====')
for i in IDS:
    w(u'[' + i + u']')
    for loc in ('zh_cn', 'en_us', 'ja_jp', 'ru_ru'):
        w(u'  %-6s T: %s' % (loc, T[loc].get(u'advancements.potato_s_t.%s.title' % i, u'(缺)')))
        w(u'         D: %s' % T[loc].get(u'advancements.potato_s_t.%s.description' % i, u'(缺)'))
w()
w(u'===== 相关物品名 =====')
for k in ('item.potato_s_t.vibranium_ingot', 'item.potato_s_t.raw_vibranium',
          'item.potato_s_t.hard_titanium_alloy', 'item.potato_s_t.thermal_metal',
          'item.potato_s_t.light_titanium_alloy', 'item.potato_s_t.star_chart_tome',
          'item.potato_s_t.diesel_generator_controller', 'item.potato_s_t.silver_wire',
          'item.potato_s_t.silver_wire_spool', 'item.potato_s_t.empty_spool',
          'item.potato_s_t.silver_ingot', 'item.potato_s_t.star_steel_ingot',
          'block.potato_s_t.diesel_generator_controller', 'block.potato_s_t.wiring_block',
          'block.potato_s_t.terminal', 'item.potato_s_t.vibranium_chestplate',
          'item.potato_s_t.titanium_alloy_chestplate', 'item.potato_s_t.star_steel_pickaxe',
          'item.potato_s_t.star_steel_sword', 'item.potato_s_t.star_steel_axe',
          'item.potato_s_t.star_steel_hoe', 'item.potato_s_t.star_steel_shovel'):
    w(u'  ' + k)
    for loc in ('zh_cn', 'en_us', 'ja_jp', 'ru_ru'):
        w(u'      %-6s %s' % (loc, T[loc].get(k, u'(缺)')))

io.open(OUT, 'w', encoding='utf-8').write(u'\n'.join(lines))
sys.stdout.write(u'OK -> %s\n' % OUT)
