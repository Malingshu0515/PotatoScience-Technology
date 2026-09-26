# -*- coding: utf-8 -*-
u"""ZF145 侦察 5：从 sources.jar 抠三件事的权威格式。
  ① DamageTypePredicate 的 codec 字段名（killing_blow 怎么写）
  ② KilledTrigger.TriggerInstance 的字段名（player_killed_entity 的条件）
  ③ 伤害类型标签的目录名与 TagKey 注册（Registries.DAMAGE_TYPE 的 tag 路径）
只读 jar，不写盘。
"""
import io, os, re, sys, zipfile, glob

ROOT = r'E:\PotatoST'
OUT  = os.path.join(ROOT, 'build', 'zftools', '_zf145_recon5.txt')
JARS = glob.glob(os.path.join(ROOT, 'build', 'neoForm', '*', 'sources.jar'))
lines = []
def w(s=u''):
    lines.append(s)

w(u'===== ZF145 侦察 5：jar 取证 =====')
w(u'sources.jar: %s' % JARS)
if not JARS:
    io.open(OUT, 'w', encoding='utf-8').write(u'\n'.join(lines)); sys.exit(1)

zf = zipfile.ZipFile(JARS[0])
names = zf.namelist()
w(u'条目数 %d' % len(names))

def dump(pat, keep=80, ctx=None):
    hit = [n for n in names if re.search(pat, n)]
    w(u'--- /%s/ → %d 个文件 ---' % (pat, len(hit)))
    for n in hit[:6]:
        w(u'  ' + n)
    if not hit:
        return
    src = zf.read(hit[0]).decode('utf-8', 'replace').splitlines()
    for i, l in enumerate(src[:keep]):
        w(u'  %4d| %s' % (i + 1, l))
    w()

w(u'##### ① DamageTypePredicate #####')
dump(r'damagesource/DamageTypePredicate\.java$', 60)

w(u'##### ② KilledTrigger #####')
dump(r'advancements/critereon/KilledTrigger\.java$', 90)

w(u'##### ③ 伤害类型标签：Tags / TagKey 用法 #####')
hit = [n for n in names if re.search(r'world/damagesource/DamageTypes\.java$', n)]
w(u'  DamageTypes.java: %s' % hit)
if hit:
    src = zf.read(hit[0]).decode('utf-8', 'replace').splitlines()
    for i, l in enumerate(src[:40]):
        w(u'  %4d| %s' % (i + 1, l))
w()
hit = [n for n in names if re.search(r'tags/DamageTypeTags\.java$', n)]
w(u'  DamageTypeTags.java: %s' % hit)
if hit:
    src = zf.read(hit[0]).decode('utf-8', 'replace').splitlines()
    for i, l in enumerate(src[:30]):
        w(u'  %4d| %s' % (i + 1, l))
w()

w(u'##### ④ 现有原版伤害类型标签文件（jar 内 data/minecraft/tags/damage_type/）#####')
hit = [n for n in names if 'tags/damage_type' in n]
for n in hit[:25]:
    w(u'  ' + n)
w(u'  合计 %d' % len(hit))
w()

w(u'##### ⑤ 原版成就里用 killing_blow 的先例 #####')
hit = [n for n in names if re.search(r'advancements/critereon/.*Trigger\.java$', n)]
w(u'  触发器类共 %d 个' % len(hit))
for n in hit:
    s = zf.read(n).decode('utf-8', 'replace')
    if 'killing_blow' in s or 'killingBlow' in s:
        w(u'  [命中] ' + n)

io.open(OUT, 'w', encoding='utf-8').write(u'\n'.join(lines))
sys.stdout.write(u'OK -> %s\n' % OUT)
