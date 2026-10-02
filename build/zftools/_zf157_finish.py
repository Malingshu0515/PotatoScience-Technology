# -*- coding: utf-8 -*-
r"""_zf157_finish.py —— ZF157 收尾三件事

① **补账**：`_zf157_apply.py` 的备份循环把"资源相对路径"当成"仓库相对路径"，
   于是 `textures/item/thermal_metal.png` 与四个物品模型**没抄进 `zf157_pre`**
   （脚本自己打了 `[MISS]`，没吞掉）。被顶掉的那张 160x160 占位图按老规矩
   **从 git HEAD 取回**，并用"取回来的 sha1 必须等于改前实测的 `e827c8325d64`"证明取对了。
② 把 `_zf157_apply.py` 那个 bug 与那条**永远为真**的断言（§4.17）修掉。
③ `_zf90_verify.py` 里"贴图清单待画表头 = 13"这条判据跟到 **9**（判据不删、不放宽）。
"""
import sys, os, io, json, hashlib, subprocess, shutil
sys.stdout.reconfigure(encoding='utf-8')

ROOT = r'E:\PotatoST'
TOOLS = os.path.join(ROOT, 'build', 'zftools')
PRE = os.path.join(TOOLS, 'zf157_pre')
ASSET_REL = 'src/main/resources/assets/potato_s_t'
OLD_THERMAL_SHA1 = 'e827c8325d64f3cc3b4ac06ce27e9ff7bfd5a2a2'  # 改前实测（只知前 12 位，下面按前缀核）
OLD_THERMAL_12 = 'e827c8325d64'
OLD_THERMAL_BYTES = 728

fails = []
def check(ok, msg):
    print(('  [OK]   ' if ok else '  [FAIL] ') + msg)
    if not ok:
        fails.append(msg)

def sha1(b):
    return hashlib.sha1(b).hexdigest()

def git_show(relpath):
    r = subprocess.run(['git', '-C', ROOT, 'show', 'HEAD:' + relpath],
                       stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    return r.stdout if r.returncode == 0 else None

print(u'===== ① 补账：从 git HEAD 取回五份改前件 =====')
WANT = [('textures/item/thermal_metal.png', True),
        ('models/item/titanium_alloy_helmet.json', False),
        ('models/item/titanium_alloy_chestplate.json', False),
        ('models/item/titanium_alloy_leggings.json', False),
        ('models/item/titanium_alloy_boots.json', False)]
for rel, is_tex in WANT:
    blob = git_show(ASSET_REL + '/' + rel)
    if blob is None:
        check(False, u'git HEAD 里取不到 %s' % rel)
        continue
    h = sha1(blob)
    if is_tex:
        check(h.startswith(OLD_THERMAL_12) and len(blob) == OLD_THERMAL_BYTES,
              u'取回的 %s 就是改前那张（sha1 %s… / %d 字节，与改前实测一致）'
              % (rel, h[:12], len(blob)))
    else:
        check(b'minecraft:item/iron_' in blob,
              u'取回的 %s 里仍是 `minecraft:item/iron_*`（%s…）' % (rel, h[:12]))
    dst = os.path.join(PRE, (ASSET_REL + '/' + rel).replace('/', '__'))
    with open(dst, 'wb') as f:
        f.write(blob)
    with open(dst, 'rb') as f:
        check(sha1(f.read()) == h, u'%s 写入 zf157_pre 后回读一致' % os.path.basename(rel))

# 真实清单（含四个新建件"改前不存在"这件事）
lines = []
for rel in ['src/main/resources/assets/potato_s_t/textures/item/thermal_metal.png',
            'src/main/resources/assets/potato_s_t/models/item/titanium_alloy_helmet.json',
            'src/main/resources/assets/potato_s_t/models/item/titanium_alloy_chestplate.json',
            'src/main/resources/assets/potato_s_t/models/item/titanium_alloy_leggings.json',
            'src/main/resources/assets/potato_s_s_t/models/item/titanium_alloy_boots.json'.replace('_s_t_s_t', '_s_t'),
            'docs/贴图清单.md', 'docs/开发档案.md', 'docs/UpdateAnnouncement_EN.md',
            'build/zftools/_zf90_verify.py', 'build/用户素材/_来源凭据.json']:
    p = os.path.join(ROOT, rel.replace('/', os.sep))
    b = os.path.join(PRE, rel.replace('/', '__'))
    if os.path.exists(b):
        lines.append(u'%s\t%s\t%d\t(备份)' % (rel, sha1(open(b, 'rb').read()), os.path.getsize(b)))
    elif os.path.exists(p):
        lines.append(u'%s\t%s\t%d' % (rel, sha1(open(p, 'rb').read()), os.path.getsize(p)))
    else:
        lines.append(u'%s\tMISSING' % rel)
for rel in ['src/main/resources/assets/potato_s_t/textures/item/titanium_alloy_helmet.png',
            'src/main/resources/assets/potato_s_t/textures/item/titanium_alloy_chestplate.png',
            'src/main/resources/assets/potato_s_t/textures/item/titanium_alloy_leggings.png',
            'src/main/resources/assets/potato_s_t/textures/item/titanium_alloy_boots.png']:
    lines.append(u'%s\t改前不存在（本轮的**新建件**）' % rel)
io.open(os.path.join(PRE, '_sha1.txt'), 'w', encoding='utf-8', newline='\n').write(u'\n'.join(lines) + u'\n')
check(len(lines) == 14, u'zf157_pre/_sha1.txt 重写成 %d 行（14 = 10 份改前件 + 4 份"改前不存在"）' % len(lines))

print()
print(u'===== ② 修 `_zf157_apply.py` 的两个毛病 =====')
AP = os.path.join(TOOLS, '_zf157_apply.py')
ap = io.open(AP, encoding='utf-8').read()
old_loop = u"for rel in BAK:\n    a = os.path.join(ROOT, rel.replace('/', os.sep))"
new_loop = (u"# \u26a0 ZF157 \u8865\u8d26\uff1a\u8fd9\u91cc\u539f\u6765\u5199\u7684\u662f `os.path.join(ROOT, rel)` \u2014\u2014 \u4f46\u8d44\u6e90\u7c7b\u7684 rel\n"
            u"#   \u662f**\u76f8\u5bf9 ASSET** \u7684\uff0c\u4e8e\u662f\u4e94\u4efd\u6539\u524d\u4ef6\u5f53\u573a\u88ab\u5224\u6210 MISSING\u3001\u4e00\u4efd\u90fd\u6ca1\u6284\uff08\u5f53\u65f6\u6253\u4e86 [MISS]\uff09\u3002\n"
            u"#   \u771f\u6b63\u7684\u6539\u524d\u4ef6\u5df2\u7ecf\u7528 `_zf157_finish.py` \u4ece git HEAD \u53d6\u56de\u3002\n"
            u"ASSET_REL_BAK = 'src/main/resources/assets/potato_s_t/'\n"
            u"for rel in BAK:\n"
            u"    base = ROOT if rel.startswith(('docs/', 'build/')) else os.path.join(ROOT, ASSET_REL_BAK.replace('/', os.sep))\n"
            u"    a = os.path.join(base, rel.replace('/', os.sep))")
check(ap.count(old_loop) == 1, u'备份循环的基目录那一处锚点命中 1 次')
ap = ap.replace(old_loop, new_loop)
old_assert = u"check(True, u'\u5907\u4efd %d \u4efd\uff08\u6e05\u5355\u89c1 zf157_pre/_sha1.txt\uff09' % len(BAK))"
new_assert = (u"n_copied = sum(1 for rel in BAK if os.path.exists(os.path.join(PRE, rel.replace('/', '__'))))\n"
              u"check(n_copied == len(BAK), u'\u5907\u4efd %d/%d \u4efd\uff08\u6e05\u5355\u89c1 zf157_pre/_sha1.txt\uff09' % (n_copied, len(BAK)))")
check(ap.count(old_assert) == 1, u'那条"永远为真"的断言（§4.17）锚点命中 1 次')
ap = ap.replace(old_assert, new_assert)
io.open(AP, 'w', encoding='utf-8', newline='\n').write(ap)
import ast
ast.parse(io.open(AP, encoding='utf-8').read())
check(True, u'_zf157_apply.py 改后能过 ast.parse')

print()
print(u'===== ③ `_zf90_verify.py` 待画判据 13 -> 9 =====')
Z90 = os.path.join(TOOLS, '_zf90_verify.py')
z = io.open(Z90, encoding='utf-8').read()
o1 = u'贴图清单的待画表头已变 13 个'
o2 = u'## 待画（13 个'
for o in (o1, o2):
    check(z.count(o) == 1, u'锚点 `%s` 命中 1 次（实测 %d）' % (o, z.count(o)))
z = z.replace(o1, u'贴图清单的待画表头已变 9 个').replace(o2, u'## 待画（9 个')
io.open(Z90, 'w', encoding='utf-8', newline='\n').write(z)
zz = io.open(Z90, encoding='utf-8').read()
check(u'## 待画（9 个' in zz and u'待画表头已变 9 个' in zz, u'两处都已是 9')
check(u'## 待画（13 个' not in zz and u'已变 13 个' not in zz, u'旧值 13 一处都不剩')
ast.parse(zz)
check(True, u'_zf90_verify.py 改后能过 ast.parse')

print()
print(u'------------------------------')
print(u'失败项 = %d' % len(fails))
for f in fails:
    print(u'  !! ' + f)
sys.exit(1 if fails else 0)
