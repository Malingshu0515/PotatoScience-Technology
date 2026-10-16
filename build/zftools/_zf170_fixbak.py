# -*- coding: utf-8 -*-
r"""_zf170_fixbak.py —— 补账：4 份改前件没抄进 zf170_pre（**同一个坑第二次踩**）

`_zf170_apply.py` 的备份循环又写成 `os.path.join(ROOT, rel)`，而 `textures/…` 与 `models/…`
是**相对 ASSET** 的 ⇒ 4 份改前件一份都没抄，其中三张贴图**当场被覆盖**。
（§4.165 就是 ZF157 为这个坑立的 —— 这轮我又写了一遍，必须记上"第 2 次"。）

补法（与 ZF157 同一套，可验证）：
  · 从 **git HEAD** 取回，且**必须**取回那份的 sha1 等于**改前实测值**
    （side `719c785060ce` / top `8bedfc2b861d` / front `3430395ef96d`，来自 dry 那一跑的实测）；
  · 交叉印证：`build/resources/main/...` 里若还有旧副本，sha1 也必须相同。
"""
import io, os, sys, json, hashlib, subprocess, shutil
sys.stdout.reconfigure(encoding='utf-8')
ROOT = r'E:\PotatoST\PotatoSTneoforge1.21.1'
TOOLS = os.path.join(ROOT, 'build', 'zftools')
PRE = os.path.join(TOOLS, 'zf170_pre')
ASSET_REL = 'src/main/resources/assets/potato_s_t'
BUILD_ASSET = os.path.join(ROOT, 'build', 'resources', 'main', 'assets', 'potato_s_t')
fails = []
def check(ok, msg):
    print(('  [OK]   ' if ok else u'  [FAIL] ') + msg)
    if not ok:
        fails.append(msg)

def sha1b(b):
    return hashlib.sha1(b).hexdigest()

def git_show(rel):
    r = subprocess.run(['git', '-C', ROOT, 'show', 'HEAD:' + rel], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    return r.stdout if r.returncode == 0 else None

WANT = [('textures/block/filling_machine_side.png', '719c785060ce', 173),
        ('textures/block/filling_machine_top.png', '8bedfc2b861d', 175),
        ('textures/block/filling_machine_front.png', '3430395ef96d', 180),
        ('models/block/filling_machine.json', None, None)]

print(u'===== ① 从 git HEAD 取回 4 份改前件 =====')
for rel, pre12, size in WANT:
    blob = git_show(ASSET_REL + '/' + rel)
    if blob is None:
        check(False, u'git HEAD 里取不到 %s' % rel)
        continue
    h = sha1b(blob)
    if pre12:
        check(h.startswith(pre12) and len(blob) == size,
              u'%s 就是改前那份（sha1 %s… / %d B，与 dry 实测一致）' % (rel, h[:12], len(blob)))
        bp = os.path.join(BUILD_ASSET, rel.replace('/', os.sep))
        if os.path.exists(bp):
            hb = sha1b(open(bp, 'rb').read())
            check(hb == h, u'  交叉印证：build 产物里那份也是 %s…' % hb[:12])
        else:
            print(u'  （build 产物里已没有旧副本，跳过交叉印证）')
    else:
        check(b'"texture": "#top"' in blob and b'"bottom"' not in blob,
              u'%s 是改前那份（down 面仍指 #top、还没有 bottom 槽；%s…）' % (rel, h[:12]))
    dst = os.path.join(PRE, (ASSET_REL + '/' + rel).replace('/', '__'))
    open(dst, 'wb').write(blob)
    check(sha1b(open(dst, 'rb').read()) == h, u'  写入 zf170_pre 后回读一致：%s' % os.path.basename(rel))

print()
print(u'===== ② 重写 zf170_pre/_sha1.txt（真实清单）=====')
lines = []
for rel in ['textures/block/filling_machine_side.png', 'textures/block/filling_machine_top.png',
            'textures/block/filling_machine_front.png', 'models/block/filling_machine.json']:
    b = os.path.join(PRE, (ASSET_REL + '/' + rel).replace('/', '__'))
    lines.append(u'%s\t%s\t%d\t(git HEAD 取回)' % (rel, sha1b(open(b, 'rb').read()), os.path.getsize(b)))
lines.append(u'textures/block/filling_machine_bottom.png\t改前不存在（本轮**新建件**）')
for rel in ['build/用户素材/_来源凭据.json', 'docs/贴图清单.md', 'docs/开发档案.md', 'docs/UpdateAnnouncement_EN.md']:
    b = os.path.join(PRE, rel.replace('/', '__'))
    p = os.path.join(ROOT, rel.replace('/', os.sep))
    src = b if os.path.exists(b) else p
    if os.path.exists(src):
        lines.append(u'%s\t%s\t%d\t(备份)' % (rel, sha1b(open(src, 'rb').read()), os.path.getsize(src)))
io.open(os.path.join(PRE, '_sha1.txt'), 'w', encoding='utf-8', newline='\n').write(u'\n'.join(lines) + u'\n')
check(len(lines) == 9, u'_sha1.txt 重写成 %d 行（4 份改前件 + 1 份"改前不存在" + 4 份备份）' % len(lines))

print()
print(u'===== ③ 修 `_zf170_apply.py` 的基目录（免得下次重跑又漏）=====')
AP = os.path.join(TOOLS, '_zf170_apply.py')
s = io.open(AP, encoding='utf-8').read()
OLD = u"for rel in BAK:\n    a = os.path.join(ROOT, rel.replace('/', os.sep))"
NEW = (u"# \u26a0 ZF170 \u8865\u8d26\uff1a\u8fd9\u91cc\u539f\u6765\u53ea\u62fc ROOT \u2014\u2014 \u800c `textures/`\u3001`models/` \u662f**\u76f8\u5bf9 ASSET** \u7684\uff0c\n"
       u"#   \u56db\u4efd\u6539\u524d\u4ef6\u5f53\u573a\u88ab\u5224 MISSING\u3001\u4e00\u4efd\u90fd\u6ca1\u6284\uff08\u5176\u4e2d\u4e09\u5f20\u8d34\u56fe\u8fd8\u88ab\u8986\u76d6\u4e86\uff09\u3002\n"
       u"#   \u771f\u6b63\u7684\u6539\u524d\u4ef6\u5df2\u7528 `_zf170_fixbak.py` \u4ece git HEAD \u53d6\u56de\uff08\u89c1 \u00a74.165 \u7b2c 2 \u6b21\uff09\u3002\n"
       u"for rel in BAK:\n"
       u"    base = ROOT if rel.startswith(('docs/', 'build/')) else os.path.join(ROOT, 'src', 'main', 'resources', 'assets', 'potato_s_t')\n"
       u"    a = os.path.join(base, rel.replace('/', os.sep))")
check(s.count(OLD) == 1, u'锚点命中 1 次（实测 %d）' % s.count(OLD))
if s.count(OLD) == 1:
    io.open(AP, 'w', encoding='utf-8', newline='\n').write(s.replace(OLD, NEW))
    import ast
    ast.parse(io.open(AP, encoding='utf-8').read())
    check(True, u'_zf170_apply.py 改后能过 ast.parse')

print()
print(u'失败项 = %d' % len(fails))
sys.exit(1 if fails else 0)
