# -*- coding: utf-8 -*-
# _zf131_chain.py —— 柴油发电机循环音：**整条链路的端到端自查**
#
# §6.5 那张"给机器加一个音效（4 处联动）"的表，逐条对着盘上验：
#   ① assets/potato_s_t/sounds/<名>.ogg      —— 文件在、规格对（单声道/44100/Vorbis）
#   ② assets/potato_s_t/sounds.json          —— 有那条事件
#   ③ sound/ModSounds.java                   —— 有注册
#   ④ 触发处（方块实体）                      —— running 字段 + clientTick + sync + save/load + 双端 ticker
#
# 任何一条断了，症状都是"游戏里没声音"，但根因完全不同（§4.52 那一课的同类）。
import io
import json
import os
import re
import sys

import soundfile as sf

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

ROOT = r"E:\PotatoST"
ASSETS = os.path.join(ROOT, r"src\main\resources\assets\potato_s_t")
JAVA = os.path.join(ROOT, r"src\main\java\com\potatost\mod")
NAME = "diesel_generator_running"
fails, oks = [], []


def ok(msg):
    oks.append(msg)
    print(u"  [OK] " + msg)


def bad(msg):
    fails.append(msg)
    print(u"  [!!] " + msg)


def read(p):
    return io.open(p, encoding="utf-8").read()


print(u"== ① 音频文件规格 ==")
ogg = os.path.join(ASSETS, "sounds", NAME + ".ogg")
if not os.path.exists(ogg):
    bad(u"缺 %s" % ogg)
else:
    b, sr = sf.read(ogg, dtype="float32")
    info = sf.info(ogg)
    ch = 1 if b.ndim == 1 else b.shape[1]
    dur = len(b) / sr
    if info.format == "OGG" and info.subtype == "VORBIS":
        ok(u"格式 OGG/VORBIS")
    else:
        bad(u"格式 %s/%s（要 OGG/VORBIS）" % (info.format, info.subtype))
    if ch == 1:
        ok(u"单声道（立体声在 MC 里不吃距离衰减）")
    else:
        bad(u"%d 声道 —— 必须单声道" % ch)
    if sr == 44100:
        ok(u"采样率 44100 Hz")
    else:
        bad(u"采样率 %d（不是 44100 会变速变调）" % sr)
    ok(u"时长 %.2f s，%d 字节" % (dur, os.path.getsize(ogg)))

print(u"\n== ② sounds.json ==")
sj = os.path.join(ASSETS, "sounds.json")
d = json.loads(read(sj))
if NAME not in d:
    bad(u"sounds.json 里没有 %s" % NAME)
else:
    entry = d[NAME]
    ok(u"有 %s 条目：%s" % (NAME, json.dumps(entry, ensure_ascii=False)))
    if "stream" in json.dumps(entry):
        bad(u"短音效不该带 stream:true（那是长音乐用的）")
    else:
        ok(u"没有 stream:true（正确 —— 只有唱片那种长音频才加）")

print(u"\n== ③ ModSounds.java 注册 ==")
ms = read(os.path.join(JAVA, "sound", "ModSounds.java"))
if u'SOUND_EVENTS.register("%s"' % NAME in ms:
    ok(u"SOUND_EVENTS.register(\"%s\") 在" % NAME)
else:
    bad(u"ModSounds 里没有注册 %s" % NAME)
if u"DIESEL_GENERATOR_RUNNING" in ms:
    ok(u"常量 DIESEL_GENERATOR_RUNNING 在")
else:
    bad(u"缺常量 DIESEL_GENERATOR_RUNNING")

print(u"\n== ④ 触发处：DieselGeneratorBlockEntity ==")
be = read(os.path.join(JAVA, "DieselGeneratorBlockEntity.java"))
checks = [
    (u"import MachineRunningSound", u"import com.potatost.mod.client.sound.MachineRunningSound;"),
    (u"import ModSounds", u"import com.potatost.mod.sound.ModSounds;"),
    (u"running 字段", u"private boolean running = false;"),
    (u"isRunning() 读数", u"public boolean isRunning()"),
    (u"clientTick 驱动循环音",
     u"MachineRunningSound.update(this, this.running, ModSounds.DIESEL_GENERATOR_RUNNING.get());"),
    (u"tick 双端分支", u"if (level.isClientSide) {\n            machine.clientTick();"),
    (u"只用 syncedRunning 比（**不是**本 tick 头尾比）", u"if (this.syncedRunning != this.running) {"),
    (u"syncedRunning 字段", u"private boolean syncedRunning = false;"),
    (u"sync 前先记下已同步的值", u"this.syncedRunning = this.running;"),
    (u"getUpdateTag 覆写", u"public CompoundTag getUpdateTag(HolderLookup.Provider registries)"),
    (u"getUpdatePacket 覆写", u"public Packet<ClientGamePacketListener> getUpdatePacket()"),
    (u"sendBlockUpdated(..., UPDATE_CLIENTS)", u"Block.UPDATE_CLIENTS"),
    (u"running 写进 saveAdditional", u'tag.putBoolean("running", this.running);'),
    (u"running 从 loadAdditional 读回", u'this.running = tag.getBoolean("running");'),
    (u"每 tick 先清零", u"this.running = false;"),
    (u"真烧油才置真", u"this.running = true;"),
]
for label, needle in checks:
    n = be.count(needle)
    if n >= 1:
        ok(u"%s（%d 处）" % (label, n))
    else:
        bad(u"%s —— 找不到：%r" % (label, needle[:60]))

# ⚠ 这条断言我前后写错两次，记下来免得第三次：
#   第一次跟"serverTickBody 里第一个 return"比 —— 那是早退 `if (level == null) return;`，是**误报**；
#   第二次数"四条停机分支都在第一个 return 之后" —— 还是拿早退当基准，仍然误报。
#   这条要断言的**实质顺序**是：**清零 → 四个停机门 → 各自的 return**。
#   所以直接按出现位置排一遍，看顺序对不对（不再拿任何 return 当基准）。
body_start = be.find("private void serverTickBody()")
wrapper_start = be.find("private void serverTick()")
if wrapper_start > 0 and body_start > wrapper_start:
    reset_at = be.index("this.running = false;", wrapper_start)
    gate_pos = [(name, be.find(u"this.status = " + name + ";", body_start))
                for name in ("STATUS_DISABLED", "STATUS_NO_STRUCTURE",
                             "STATUS_OUTPUT_FULL", "STATUS_EMPTY")]
    ok_order = reset_at < min(p for _, p in gate_pos if p > 0)
    # 每个门后面紧跟一个 return
    rets = []
    for name, p in gate_pos:
        nxt = be.find("return;", p)
        rets.append(0 < nxt < p + 400)
    if ok_order and all(rets):
        ok(u"顺序正确：清零 → 四个停机门（红石/没成型/缓冲满/没油）→ 各自 return")
    else:
        bad(u"顺序不对（清零在四个门之前=%s；每个门后面都紧跟 return=%s）" % (ok_order, rets))
    # 反向：真烧油那一步必须在四个门**之后**
    run_at = be.find("this.running = true;", body_start)
    if run_at > max(p for _, p in gate_pos):
        ok(u"置真在四个门之后（只有真扣了油才算运行）")
    else:
        bad(u"置真的位置比某个停机门还靠前 —— 停机时可能仍被判成运行")

print(u"\n== ⑤ 方块侧 ticker 必须双端（§4.26）==")
blk = read(os.path.join(JAVA, "DieselGeneratorBlock.java"))
seg = blk[blk.find("getTicker"):blk.find("getTicker") + 500] if "getTicker" in blk else ""
if u"createTickerHelper" in seg and u"isClientSide) return null" not in seg.replace(" ", ""):
    ok(u"getTicker 用 createTickerHelper 且没有单端 early-return")
else:
    bad(u"getTicker 可能只给服务端 —— 客户端收不到 tick 就永远没声音")

print(u"\n== ⑥ SoundCheck.py（本项目第 9 道门）==")
import subprocess
r = subprocess.run([sys.executable, os.path.join(ROOT, "build", "zftools", "SoundCheck.py")],
                   capture_output=True, cwd=os.path.join(ROOT, "build", "zftools"))
out = r.stdout.decode("utf-8", "replace")
for ln in out.splitlines():
    if any(k in ln for k in (u"失败项", u"结论", NAME)):
        print(u"  " + ln.strip())

print(u"\n" + u"=" * 60)
print(u"通过 %d 项，失败 %d 项" % (len(oks), len(fails)))
for f in fails:
    print(u"  !! " + f)
sys.exit(1 if fails else 0)
