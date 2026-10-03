# -*- coding: utf-8 -*-
r"""_zf99_verify.py —— ZF99 常驻校验：空气分离器工作时的白色烟雾粒子

用户原话（本轮全部规格，一条）：

  「空气分离器工作时加一点白色的烟雾粒子」

骨架（规格 → 实现）：

  A 用的是**白色烟雾**：原版 `ParticleTypes.CLOUD`
  B **在服务端发**：`ServerLevel#sendParticles`（不是 `Level#addParticle` —— 那在服务端是空操作）
  C **只在工作时冒**：调用点在 serverTick 的"真正干活"那一支里 —— 所有失败岔路（红石/罐满/缺电）
    都在它**之前** return 了，所以停机时不会冒
  D 参数与"量"是常量（间隔 / 每次粒数 / 铺开半径 / 初速），要调不用翻代码
  E 不需要客户端渲染器（粒子由原版画）
  F 文档 + 成品 jar
"""
import hashlib
import io
import os
import re
import sys
import zipfile

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

ROOT = r"E:\PotatoST"
JAVA = os.path.join(ROOT, r"src\main\java\com\potatost\mod")
DOCS = os.path.join(ROOT, "docs")
JAR = os.path.join(ROOT, "release", "PotatoST-0.11.jar")

passed = 0
failed = 0
fails = []


def check(label, cond):
    global passed, failed
    if cond:
        passed += 1
        print(u"  [OK]   " + label)
    else:
        failed += 1
        fails.append(label)
        print(u"  [FAIL] " + label)


def eq(label, want, got):
    check(u"%s（期望 %r，实际 %r）" % (label, want, got), want == got)


def read(p):
    return io.open(p, encoding="utf-8").read() if os.path.exists(p) else None


def sha1f(p):
    return hashlib.sha1(open(p, "rb").read()).hexdigest()


def body(java, signature):
    if not java:
        return None
    at = java.find(signature)
    if at < 0 or java.find(signature, at + 1) >= 0:
        return None
    i = java.find(u"{", at + len(signature) - 1)
    depth = 0
    for j in range(i, len(java)):
        if java[j] == u"{":
            depth += 1
        elif java[j] == u"}":
            depth -= 1
            if depth == 0:
                return java[i:j + 1]
    return None


def int_consts(java):
    raw = {}
    for m in re.finditer(r"\bint\s+([A-Z][A-Z0-9_]*)\s*=\s*([^;{}]+);", java or u""):
        expr = re.sub(r"//.*$", u"", m.group(2)).strip()
        if re.fullmatch(r"[0-9A-Za-z_ ()*+\-]+", expr):
            raw[m.group(1)] = expr
    done = {}

    def resolve(name, depth=0):
        if name in done:
            return done[name]
        if depth > 8 or name not in raw:
            return None
        expr = raw[name]

        def sub(mm):
            ident = mm.group(0)
            if ident.isdigit():
                return ident
            v = resolve(ident, depth + 1)
            return str(v) if v is not None else ident

        filled = re.sub(r"[A-Za-z_][A-Za-z0-9_]*|\d+", sub, expr)
        try:
            done[name] = int(eval(filled, {"__builtins__": {}}, {}))
        except Exception:
            return None
        return done[name]

    for k in list(raw):
        resolve(k)
    return done


def main():
    print(u"=========== ZF99 校验：空气分离器工作时的白色烟雾粒子 ===========")
    be = read(os.path.join(JAVA, "AirSeparatorBlockEntity.java")) or u""
    check(u"方块实体源码在", be != u"")

    print(u"\n== A 用的是白色烟雾 ==")
    check(u"用了原版 ParticleTypes.CLOUD（白色烟团）", u"ParticleTypes.CLOUD" in be)
    check(u"导入的是 net.minecraft.core.particles.ParticleTypes",
          u"import net.minecraft.core.particles.ParticleTypes;" in be)
    check(u"没有改用别的颜色/种类的烟（SMOKE / LARGE_SMOKE / CAMPFIRE_* 都不出现）",
          not any(k in be for k in (u"ParticleTypes.SMOKE", u"ParticleTypes.LARGE_SMOKE",
                                    u"ParticleTypes.CAMPFIRE")))

    print(u"\n== B 在服务端发 ==")
    spawn = body(be, u"private void spawnWorkParticles()") or u""
    check(u"spawnWorkParticles() 抠得出来", spawn != u"")
    check(u"用 ServerLevel#sendParticles（服务端广播）", u"server.sendParticles(" in spawn)
    check(u"**没有**用 Level#addParticle（那在服务端是空操作）",
          u"addParticle(" not in be)
    check(u"有 `this.level instanceof ServerLevel` 的双保险",
          u"this.level instanceof ServerLevel server" in spawn)
    check(u"导入 net.minecraft.server.level.ServerLevel",
          u"import net.minecraft.server.level.ServerLevel;" in be)

    print(u"\n== C 只在工作时冒 ==")
    tick = body(be, u"private void serverTick()") or u""
    call = tick.find(u"spawnWorkParticles();")
    check(u"serverTick 里调用了 spawnWorkParticles()", call > 0)
    work = tick.find(u"this.energy -= ENERGY_PER_TICK;")
    check(u"调用点在「扣电开工」之后（%d > %d）" % (call, work), work >= 0 and call > work)
    returns = [m.start() for m in re.finditer(r"\breturn;", tick)]
    check(u"三条失败岔路（红石 / 罐满 / 缺电）的 return 全在它**之前** ⇒ 停机时不冒烟"
          u"（最晚一个 return 在 %d，调用点在 %d）" % (max(returns) if returns else -1, call),
          bool(returns) and max(returns) < call)
    check(u"状态标记为 STATUS_RUNNING 也在它之前",
          u"this.status = STATUS_RUNNING;" in tick
          and tick.find(u"this.status = STATUS_RUNNING;") < call)
    check(u"红石停机那条岔路照旧提前返回（老行为没被粒子改动）",
          u"if (this.level.hasNeighborSignal(this.worldPosition))" in tick)

    print(u"\n== D 量是可调常量 ==")
    c = int_consts(be)
    eq(u"冒烟间隔 = 5 tick（每秒 4 次）", 5, c.get("PARTICLE_INTERVAL"))
    eq(u"每次 3 粒", 3, c.get("PARTICLES_PER_EMIT"))
    check(u"铺开半径与初速也是常量（PARTICLE_SPREAD / PARTICLE_SPEED）",
          u"PARTICLE_SPREAD = 0.3;" in be and u"PARTICLE_SPEED = 0.01;" in be)
    check(u"sendParticles 的实参用的是这些常量（不是写死的字面量）",
          u"server.sendParticles(ParticleTypes.CLOUD, x, y, z, PARTICLES_PER_EMIT," in spawn
          and u"PARTICLE_SPREAD, 0.02, PARTICLE_SPREAD, PARTICLE_SPEED);" in spawn)
    check(u"粒子从**顶面**冒出来（y + 1.05，x/z 取方块中心 +0.5）",
          u"this.worldPosition.getY() + 1.05" in spawn
          and u"this.worldPosition.getX() + 0.5" in spawn
          and u"this.worldPosition.getZ() + 0.5" in spawn)

    print(u"\n== E 不需要客户端渲染器 ==")
    scr = read(os.path.join(JAVA, r"client\AirSeparatorScreen.java")) or u""
    check(u"界面文件里没有粒子代码（粒子是世界里画的，不是 GUI 里）",
          u"Particle" not in scr)
    check(u"没有为粒子新增方块实体渲染器（PotatoSTClient 里仍只有原来的 4 个）",
          (read(os.path.join(JAVA, "PotatoSTClient.java")) or u"").count(
              u"registerBlockEntityRenderer(") == 4)

    print(u"\n== F 文档与成品 ==")
    arch = read(os.path.join(DOCS, u"开发档案.md")) or u""
    ann = read(os.path.join(DOCS, "UpdateAnnouncement_EN.md")) or u""
    check(u"档案里有 ZF99 那一行", u"| ZF99 |" in arch)
    check(u"档案 §4 有本轮那条规矩（粒子要在服务端发）", u"### 4.67 " in arch)
    check(u"档案 §9 有 ZF99 那一节", u"### ZF99（0.11）" in arch)
    check(u"公告里写了工作时的白烟", u"white smoke" in ann.lower())
    if not os.path.exists(JAR):
        check(u"成品 jar 在", False)
    else:
        sha = sha1f(JAR)
        check(u".sha1 与 jar 一致（%s…）" % sha[:8], (read(JAR + u".sha1") or u"").strip() == sha)
        with zipfile.ZipFile(JAR) as zf:
            names = zf.namelist()
            check(u"成品里有空气分离器的 class",
                  u"com/potatost/mod/AirSeparatorBlockEntity.class" in names)
            check(u"成品里没有探针 class",
                  not [n for n in names if u"Check" in n.split(u"/")[-1] and n.endswith(u".class")])

    print(u"\n通过 = %d   失败 = %d" % (passed, failed))
    for f in fails:
        print(u"  !! " + f)
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
