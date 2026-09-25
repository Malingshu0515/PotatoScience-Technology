# -*- coding: utf-8 -*-
u"""_zf107_falsify.py —— 【反证刀】证明 `_zf107_verify.py` 真的会失败（0.11 ZF107）

§4.17 的口径：**"能失败的检查"才算检查**。本轮全是数据 + 四语言，
所以每把刀只动**一个语义**，改完直接跑校验器（不用重新编译），
要求它报 FAIL；**逐字还原**之后再跑一遍，要求它回到全绿。

开跑前先跑一次基线：**基线不是绿的就不许挥刀**（"基线本来就红"时，
任何 FAIL 都可能是旧账，这把刀就成了摆设）。
"""
import hashlib
import io
import json
import os
import shutil
import subprocess
import sys

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

PROJ = r"E:\PotatoST"
ZT = os.path.join(PROJ, "build", "zftools")
ADIR = os.path.join(PROJ, r"src\main\resources\data\potato_s_t\advancement")
LANG = os.path.join(PROJ, r"src\main\resources\assets\potato_s_t\lang")
BAK = os.path.join(ZT, "_zf107_falsify_bak_%d" % os.getpid())
VERIFY = os.path.join(ZT, "_zf107_verify.py")

fails = []


def sha(p):
    return hashlib.sha256(open(p, "rb").read()).hexdigest()


def read(p):
    return io.open(p, encoding="utf-8").read()


def write(p, t):
    io.open(p, "w", encoding="utf-8", newline=u"").write(t)


def run_gate():
    u"""跑校验器。

    ⚠ 带超时：K82 那把刀造出环之后，校验器第一版会在算树深时**卡死**（不是报错）——
    卡死和"抓到"在退出码上都是"非 0"，但含义完全不同。所以超时一律按**没抓到**处理，
    并且在输出里明说"挂死"（§4.77）。
    """
    try:
        p = subprocess.run([sys.executable, VERIFY], stdout=subprocess.PIPE,
                           stderr=subprocess.STDOUT, timeout=180)
    except subprocess.TimeoutExpired:
        return -9, u"**校验器挂死（180 秒超时）** —— 坏数据下必须报错，不许卡死"
    return p.returncode, p.stdout.decode("utf-8", "replace")


def adv(p):
    return os.path.join(ADIR, p + u".json")


def lang(l):
    return os.path.join(LANG, l + u".json")


def json_sub(path, fn):
    u"""按 JSON 语义改一处（保持两空格缩进写法）"""
    obj = json.loads(read(path))
    fn(obj)
    write(path, json.dumps(obj, ensure_ascii=False, indent=2) + u"\n")
    return True


def text_sub(path, old, new, count=1):
    t = read(path)
    if t.count(old) != count:
        return False
    write(path, t.replace(old, new, count))
    return True


# ------------------------------- 刀 -------------------------------
def knife_k80():
    u"""把一个成就文件改名藏起来（校验器的文件名集合与条数都该当场报错）"""
    os.rename(adv("steel"), adv("steel") + u".hidden")
    return True


KNIVES = [
    (u"K80 删掉一个成就文件（steel.json 改名藏起来）", knife_k80),
    (u"K81 把 crushing 的父指针改成不存在的 potato_s_t:nope",
     lambda: json_sub(adv("crushing"), lambda o: o.__setitem__("parent", "potato_s_t:nope"))),
    # ⚠ 这把刀第一版**写错了**：原来把 `first_power` 的父改成 `crushing` —— 那两个是**兄弟**
    #   （都是 `new_beginning` 的孩子），改完只是换了个父，**根本没有环**，校验器保持全绿是**对的**。
    #   照 §4.30「FAIL 先怀疑期望/刀，再怀疑被测物」⇒ 改成真环：`capacitor` 的父指向它的**后代** `acid`
    #   （acid → combustion → fuel → distillation → oil → steel → blast_furnace → capacitor）。
    #   这样根还是只有一个（B1 仍然绿），只有 B3（环）与 B4（可达）该红。
    (u"K82 制造真父子环：把 capacitor 的父指向它的后代 acid",
     lambda: json_sub(adv("capacitor"), lambda o: o.__setitem__("parent", "potato_s_t:acid"))),
    (u"K83 把 titanium 的图标换成没注册的 titanium_gem",
     lambda: json_sub(adv("titanium"), lambda o: o["display"]["icon"].__setitem__(
         "id", "potato_s_t:titanium_gem"))),
    (u"K84 把 stable_block 的图标换成原版金块（不在本模组注册名单里）",
     lambda: json_sub(adv("stable_block"), lambda o: o["display"]["icon"].__setitem__(
         "id", "minecraft:gold_block"))),
    (u"K85 把 pressing 的图标换成硫（注册了，但不在这条的判据里）",
     lambda: json_sub(adv("pressing"), lambda o: o["display"]["icon"].__setitem__(
         "id", "potato_s_t:sulfur"))),
    (u"K86 删掉 zh_cn 里的一条成就标题键",
     lambda: text_sub(lang("zh_cn"),
                      u'    "advancements.potato_s_t.acid.title":  "酸性反应室",\n', u"")),
    (u"K87 把石油判据里的原油换成柴油（空桶策略不变，只换流体）",
     lambda: text_sub(adv("oil"), u'"id": "potato_s_t:crude_oil"', u'"id": "potato_s_t:diesel"')),
    (u"K88 给 crushing 摘掉父指针（凭空多出第二个根 = 第二个标签页）",
     lambda: json_sub(adv("crushing"), lambda o: o.pop("parent"))),
    (u"K89 把一张隐藏彩蛋的 hidden 改成 false",
     lambda: json_sub(adv("music_disc_jasmine"),
                      lambda o: o["display"].__setitem__("hidden", False))),
    (u"K90 往一条中文说明里塞 ASCII 双引号（本项目的中文串一律用「」）",
     lambda: text_sub(lang("zh_cn"), u'"advancements.potato_s_t.sulfur.description":  "沥青 + 氢气进加氢脱硫反应仓',
                      u'"advancements.potato_s_t.sulfur.description":  "沥青 + 氢气进"加氢脱硫反应仓')),
    (u"K91 把气体的存取两条 requirement 合成一条（真「和」退化成「或」）",
     lambda: json_sub(adv("gas_handling"),
                      lambda o: o.__setitem__("requirements", [["c0", "c1"]]))),
]

TARGETS = [adv(n) for n in ("steel", "crushing", "first_power", "titanium", "stable_block",
                            "pressing", "oil", "music_disc_jasmine", "gas_handling",
                            # ⚠ `capacitor` 是 K82 改刀（真环）之后才轮到它被改的 ——
                            #   第一版漏进 TARGETS，于是那把刀被中断时**盘上留着一个环**、
                            #   而备份里没有它可还原（教训：**改了刀就必须同步改 TARGETS**）。
                            "capacitor")]
TARGETS += [lang(n) for n in ("zh_cn", "en_us", "ja_jp", "ru_ru")]


def main():
    only = sys.argv[1:] or None
    if os.path.isdir(BAK):
        shutil.rmtree(BAK)
    os.makedirs(BAK)
    print(u"================ 基线 ================")
    rc, out = run_gate()
    print(u"  校验器退出码 %s（必须 0）" % rc)
    if rc != 0:
        for l in [l for l in out.split(u"\n") if l.strip().startswith(u"!!")][:6]:
            print(u"    %s" % l.strip()[:120])
        print(u"  [STOP] 基线就不是绿的 —— 不许挥刀（否则抓到的是旧账，不是这把刀）")
        return 1

    manifest = []
    print(u"")
    print(u"================ 备份（逐份核副本自己的哈希）================")
    for t in TARGETS:
        if not os.path.isfile(t):
            fails.append(u"缺文件：%s" % t)
            continue
        dst = os.path.join(BAK, os.path.basename(t) + u"." + hashlib.md5(
            t.encode("utf-8")).hexdigest()[:8])
        shutil.copy2(t, dst)
        ok = sha(t) == sha(dst)
        manifest.append((t, dst, sha(dst)))
        print(u"  [%s] %-28s %s" % (u"OK" if ok else u"FAIL", os.path.basename(dst), sha(dst)[:16]))
        if not ok:
            fails.append(u"备份哈希不符：%s" % t)

    def restore():
        # 被改名的那个先挪回来（免得在 advancement 目录里留下野文件）
        if os.path.exists(adv("steel") + u".hidden"):
            os.replace(adv("steel") + u".hidden", adv("steel"))
        for t, dst, h in manifest:
            if not os.path.isfile(dst):
                fails.append(u"备份副本不见了：%s" % dst)
                continue
            shutil.copy2(dst, t)
            if sha(t) != h:
                fails.append(u"还原后哈希不符：%s" % t)

    print(u"")
    print(u"================ 逐刀 ================")
    for name, mutate in KNIVES:
        if only and not any(o in name for o in only):
            continue
        before = {t: sha(t) for t, _d, _h in manifest}
        try:
            acted = mutate()
        except Exception as e:
            acted = False
            print(u"  [SKIP] %s —— 变更抛异常 %s" % (name, e))
        if not acted:
            print(u"  [SKIP] %s —— 锚点没命中" % name)
            fails.append(u"锚点不唯一：%s" % name)
            restore()
            continue
        rc, out = run_gate()
        caught = rc != 0
        print(u"  [%s] %s" % (u"OK" if caught else u"FAIL", name))
        print(u"         ↳ 校验器退出码 %s（必须非 0）" % rc)
        for l in [l for l in out.split(u"\n") if l.strip().startswith(u"!!")][:3]:
            print(u"         ↳ %s" % l.strip()[:120])
        if not caught:
            fails.append(name)
        restore()
        rc2, _ = run_gate()
        back = all(sha(t) == h for t, h in before.items())
        print(u"         ↳ 还原后哈希一致 %s，校验器回到全绿 %s"
              % (u"✓" if back else u"✗", u"✓" if rc2 == 0 else u"✗"))
        if not (back and rc2 == 0):
            fails.append(u"还原失败：%s" % name)
        print(u"")

    print(u"================ 收尾 ================")
    for t, _dst, h in manifest:
        same = sha(t) == h
        print(u"  [%s] %s 回到备份哈希" % (u"OK" if same else u"FAIL", os.path.basename(t)))
        if not same:
            fails.append(u"收尾哈希不符：%s" % t)
    print(u"")
    print(u"失败项 = %d" % len(fails))
    for f in fails:
        print(u"  !! " + f)
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())
