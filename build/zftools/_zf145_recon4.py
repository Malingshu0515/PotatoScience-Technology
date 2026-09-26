# -*- coding: utf-8 -*-
u"""ZF145 侦察 4：振金合金配方输入 / 套装效果 / 银线速率 / 锹剑常数。只读。"""
import io, os, re, sys, glob, json

ROOT = r'E:\PotatoST'
J    = os.path.join(ROOT, 'src', 'main', 'java', 'com', 'potatost', 'mod')
OUT  = os.path.join(ROOT, 'build', 'zftools', '_zf145_recon4.txt')
lines = []
def w(s=u''):
    lines.append(s)

def grab(fn, pat, ctx=0, limit=40):
    fp = os.path.join(J, fn)
    if not os.path.exists(fp):
        w(u'  [无文件] ' + fn); return
    src = io.open(fp, encoding='utf-8').read().splitlines()
    n = 0
    for i, l in enumerate(src):
        if re.search(pat, l):
            for k in range(max(0, i - ctx), min(len(src), i + ctx + 1)):
                w(u'  %s:%d  %s' % (fn, k + 1, src[k].strip()[:160]))
            n += 1
            if n >= limit:
                break
    if n == 0:
        w(u'  %s : 未命中 /%s/' % (fn, pat))

w(u'===== ZF145 侦察 4 =====')
w()
w(u'--- 振金合金配方（AlloySmelterRecipes）---')
grab('AlloySmelterRecipes.java', r'VIBRANIUM|vibranium', 3, 40)
w()
w(u'--- 振金套效果（ModVibraniumSet）---')
grab('ModVibraniumSet.java', r'.', 0, 200)
w()
w(u'--- 银线速率常数 ---')
grab('ModItems.java', r'SILVER|silver_wire|RATE|rate', 0, 40)
w()
w(u'--- 星辉斩常数（StarSteelSwordItem）---')
grab('StarSteelSwordItem.java', r'static final|SLASH_', 0, 30)
w()
w(u'--- 锹 / 档位常数 ---')
grab('ModTiers.java', r'STAR_STEEL|static final', 0, 30)
w()
w(u'--- 大型柴油发电机常数 ---')
grab('DieselGeneratorBlockEntity.java', r'static final|MAX_|_PER_TICK', 0, 20)
w()
w(u'--- ModArmorItems 注册名 ---')
grab('ModArmorItems.java', r'register|VIBRANIUM_|STAR_STEEL_|TITANIUM_', 0, 40)
w()
io.open(OUT, 'w', encoding='utf-8').write(u'\n'.join(lines))
sys.stdout.write(u'OK -> %s\n' % OUT)
