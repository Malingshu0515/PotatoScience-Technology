# -*- coding: utf-8 -*-
r"""_zf171_front.py —— 灌装机**正面**也换成新侧面那张（四面统一），并记账

背景：用户报「重启游戏还是不显示」。查清了：
  · 盘上**没有任何 PotatoS/T 的 jar** 装在启动器实例里（`.minecraft` / `.hmcl` / `PCL` /
    `ModrinthApp` / `CurseForge` / `curseforge` / `run\mods` 全搜过）⇒ 他跑的是**开发客户端**；
  · `build/resources/main` 里那四张贴图**已经是最新的**（ZF170 收尾时验过）；
  · 模型里 `up/south/east/west` 是新图，**`north`（正面）仍是旧占位** —— 而放置机器时正面正对玩家。

所以这一手：把 **`filling_machine_front.png` 换成新的侧面那张**（原字节复制，**模型一个字不动** ——
这样不产生孤儿贴图，`ModelCheck` 的提示数不会动）。旧正面那张留在 `zf171_pre/` 里，
你哪天画了专属正面，说一声就换回来（一行）。
"""
import io, os, sys, json, shutil, hashlib, struct, subprocess
sys.stdout.reconfigure(encoding='utf-8')
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from PngRecolor import read_png

ROOT = r'E:\PotatoST\PotatoSTneoforge1.21.1'
TOOLS = os.path.join(ROOT, 'build', 'zftools')
SRCJA = os.path.join(ROOT, 'src', 'main', 'java', 'com', 'potatost', 'mod')
TEXB = os.path.join(ROOT, 'src', 'main', 'resources', 'assets', 'potato_s_t', 'textures', 'block')
BTEXB = os.path.join(ROOT, 'build', 'resources', 'main', 'assets', 'potato_s_t', 'textures', 'block')
PRE = os.path.join(TOOLS, 'zf171_pre')
DOCS = os.path.join(ROOT, 'docs')
fails = []
def check(ok, msg):
    print((u'  [OK]   ' if ok else u'  [FAIL] ') + msg)
    if not ok:
        fails.append(msg)

def sha1(p):
    return hashlib.sha1(open(p, 'rb').read()).hexdigest()

print(u'===== ① 放置时正面朝哪边（读源码，不猜）=====')
for fn in os.listdir(SRCJA):
    if 'FillingMachine' in fn and fn.endswith('.java'):
        p = os.path.join(SRCJA, fn)
        for i, l in enumerate(io.open(p, encoding='utf-8').read().splitlines(), 1):
            if any(k in l for k in ('HORIZONTAL_FACING', 'getStateForPlacement', 'getHorizontalDirection', 'FACING =')):
                print(u'  %s:%d  %s' % (fn, i, l.strip()[:120]))

print()
print(u'===== ② 备份 + 换正面 =====')
os.makedirs(PRE, exist_ok=True)
fp = os.path.join(TEXB, 'filling_machine_front.png')
sp = os.path.join(TEXB, 'filling_machine_side.png')
h_old, h_side = sha1(fp), sha1(sp)
shutil.copy2(fp, os.path.join(PRE, 'filling_machine_front.png'))
check(sha1(os.path.join(PRE, 'filling_machine_front.png')) == h_old, u'旧正面已备份（%s…）' % h_old[:12])
print(u'  旧正面 = %s…  新侧面 = %s…' % (h_old[:12], h_side[:12]))
data = open(sp, 'rb').read()
open(fp, 'wb').write(data)
check(sha1(fp) == h_side, u'正面已换成新侧面那张（逐字节，%s…）' % sha1(fp)[:12])
w, h, px = read_png(fp)
check((w, h) == (16, 16), u'换完仍是 16x16（实测 %dx%d）' % (w, h))

print()
print(u'===== ③ 模型一个字没动（免得产生孤儿贴图）=====')
mp = os.path.join(ROOT, 'src', 'main', 'resources', 'assets', 'potato_s_t', 'models', 'block', 'filling_machine.json')
m = json.loads(io.open(mp, encoding='utf-8').read())
check(m['textures'].get('front') == 'potato_s_t:block/filling_machine_front', u'front 槽仍指向 filling_machine_front')
check(m['elements'][0]['faces']['north']['texture'] == '#front', u'north 面仍用 #front')
check(m['textures'].get('bottom') == 'potato_s_t:block/filling_machine_bottom', u'bottom 槽还在（ZF170 那手没丢）')

print()
print(u'===== ④ 重新 processResources 并核对产物 =====')
r = subprocess.run([os.path.join(ROOT, 'gradlew.bat'), 'processResources', '--console=plain'],
                   cwd=ROOT, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
out = r.stdout.decode('utf-8', 'replace')
check(u'BUILD SUCCESSFUL' in out, u'gradle processResources BUILD SUCCESSFUL')
sys.stdout.write(u''.join(l + u'\n' for l in out.splitlines() if 'error' in l.lower() or 'FAILED' in l))
for k in ('side', 'top', 'bottom', 'front'):
    a = os.path.join(TEXB, 'filling_machine_%s.png' % k)
    b = os.path.join(BTEXB, 'filling_machine_%s.png' % k)
    hb = sha1(b) if os.path.exists(b) else 'MISSING'
    check(sha1(a) == hb, u'产物 %-6s 源=%s… 产物=%s…' % (k, sha1(a)[:12], hb[:12]))

print()
print(u'===== ⑤ 三门 =====')
for g in ['TextureCheck.py', 'ModelCheck.py', 'JsonCheck.py']:
    rr = subprocess.run([sys.executable, os.path.join(TOOLS, g)], cwd=ROOT,
                        env=dict(os.environ, PYTHONIOENCODING='utf-8'),
                        stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    o = rr.stdout.decode('utf-8', 'replace')
    tail = [l.strip() for l in o.splitlines() if (u'失败' in l or u'结论' in l or u'非法' in l or u'提示' in l)]
    print(u'  %-20s rc=%d  %s' % (g, rr.returncode, u' | '.join(tail[-2:])))
    check(rr.returncode == 0, u'%s rc=0' % g)

print()
print(u'===== ⑥ 记账（ZF171：一句补记，不另开小节）=====')
LIST = os.path.join(DOCS, u'贴图清单.md')
ARCH = os.path.join(DOCS, u'开发档案.md')
ANN = os.path.join(DOCS, 'UpdateAnnouncement_EN.md')
NOTE = (u"\n- **ZF171 补记（正面）**：用户报「重启游戏还是不显示」⇒ 查清原因：他跑的是**开发客户端**"
        u"（盘上任何启动器实例里都没有我们的 jar），资源是最新的，**问题是「正面」那一面** —— "
        u"`north` 面用的是 `filling_machine_front`（旧占位），而放置时正面正对玩家。"
        u"这一手把 **`filling_machine_front.png` 换成新的侧面那张**（原字节复制、**模型一个字没动** ⇒ 不产生孤儿贴图）；"
        u"旧正面留在 `zf171_pre/`，用户哪天画了专属正面就换回来。\n")
t = io.open(LIST, encoding='utf-8').read()
if u'ZF171 补记（正面）' in t:
    print(u'  [幂等] 清单已记过')
else:
    check(u'## ZF170' in t, u'清单里有 ZF170 小节可挂')
    i = t.index(u'\n---\n', t.index(u'## ZF170')) if u'\n---\n' in t[t.index(u'## ZF170'):] else len(t)
    io.open(LIST, 'w', encoding='utf-8', newline='\n').write(t[:i] + NOTE + t[i:])
    check(u'ZF171 补记（正面）' in io.open(LIST, encoding='utf-8').read(), u'贴图清单已补记')
t = io.open(ARCH, encoding='utf-8').read()
ADD = u"　**ZF171 补记**：正面（`north`）也换成新侧面那张 —— 用户报「重启游戏还是不显示」，查清是**跑的是开发客户端 + 旧正面正对玩家**（详见 §9）。"
if u'ZF171 补记' in t:
    print(u'  [幂等] 档案已记过')
else:
    key = u"④ 凭据 55 → 58 条（三条纯追加，先证明「读进来再原样写回」与盘上逐字节相同才动笔） | 见 §4.165 / §9 |"
    n = t.count(key)
    check(n == 1, u'ZF170 变更行锚点命中 1 次（实测 %d）' % n)
    if n == 1:
        io.open(ARCH, 'w', encoding='utf-8', newline='\n').write(t.replace(key, key.rstrip(u' |') + u" |" + ADD))
        check(u'ZF171 补记' in io.open(ARCH, encoding='utf-8').read(), u'档案变更行已补记')
t = io.open(ANN, encoding='utf-8').read()
EN = (u"\n**ZF171 follow-up:** the **front** face now uses the new side texture as well. The report was"
      u" \"restarted the game and it still does not show\" - the cause was that the tester runs the **dev"
      u" client** (no PotatoS/T jar exists in any launcher instance) with up-to-date resources, and the"
      u" face they were looking at was the **front**, which this round had deliberately left untouched."
      u" The old front art is kept in the round's backup.\n")
if u'ZF171 follow-up' in t:
    print(u'  [幂等] 公告已记过')
else:
    if not t.endswith(u'\n'):
        t += u'\n'
    io.open(ANN, 'w', encoding='utf-8', newline='\n').write(t + EN)
    check(u'ZF171 follow-up' in io.open(ANN, encoding='utf-8').read(), u'英文公告已补记')

print()
print(u'失败项 = %d' % len(fails))
sys.exit(1 if fails else 0)
