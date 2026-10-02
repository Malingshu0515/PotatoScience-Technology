# -*- coding: utf-8 -*-
u"""_zf178_falsify.py —— ZF178 的**反证刀**：砍一刀，`_zf178_verify.py` 必须当场变红。

跑法：python build\\zftools\\_zf178_falsify.py
"""
import hashlib
import io
import os
import shutil
import subprocess
import sys

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding=u"utf-8", errors="replace")

ROOT = r"E:\PotatoST"
ZT = os.path.join(ROOT, "build", "zftools")
JAVA = os.path.join(ROOT, r"src\main\java\com\potatost\mod")
ASSETS = os.path.join(ROOT, r"src\main\resources\assets\potato_s_t")
DATA = os.path.join(ROOT, r"src\main\resources\data")
GATE = os.path.join(ZT, u"_zf178_verify.py")
TMP = os.path.join(ZT, u"_zf178_falsify_bak")

KNIVES = [
    dict(id=u"K1", why=u"删掉粗钴块的注册（A3 要抓到）",
         path=os.path.join(JAVA, u"PotatoSTOres.java"),
         old=u'    public static final DeferredBlock<Block> RAW_COBALT_BLOCK = rawBlock("raw_cobalt_block");',
         new=u"", want=u"A3"),
    dict(id=u"K2", why=u"把 1→9 的数量改成 1（B1 要抓到）",
         path=os.path.join(DATA, u"potato_s_t", u"recipe", u"raw_silver_from_raw_silver_block.json"),
         old=u'"count": 9', new=u'"count": 1', want=u"B1"),
    dict(id=u"K3", why=u"把 9→1 的产物 id 改错（B1 要抓到）",
         path=os.path.join(DATA, u"potato_s_t", u"recipe", u"raw_nickel_block.json"),
         old=u'"id": "potato_s_t:raw_nickel_block"', new=u'"id": "potato_s_t:raw_nickel"', want=u"B1"),
    dict(id=u"K4", why=u"把磁铁块贴图改名（C1 要抓到）",
         path=os.path.join(ASSETS, "textures", "block", u"magnet_block.png"),
         rename=True, want=u"C1"),
    dict(id=u"K5", why=u"从 needs_stone_tool 里删一个 id（C4 要抓到）",
         path=os.path.join(DATA, u"minecraft", u"tags", u"block", u"needs_stone_tool.json"),
         old=u'    "potato_s_t:raw_tungsten_block",\n', new=u"", want=u"C4"),
    dict(id=u"K6", why=u"从 zh_cn 删一个键（D1 要抓到）",
         path=os.path.join(ASSETS, "lang", u"zh_cn.json"),
         old=u'  "block.potato_s_t.raw_tungsten_block": "粗钨块",\n', new=u"", want=u"D1"),
    dict(id=u"K7", why=u"改一份 loot table 的掉落物（C3 要抓到）",
         path=os.path.join(DATA, u"potato_s_t", u"loot_table", "blocks", u"magnet_block.json"),
         old=u'"name": "potato_s_t:magnet_block"', new=u'"name": "potato_s_t:magnet"', want=u"C3"),
]


def sha1(p):
    return hashlib.sha1(open(p, "rb").read()).hexdigest()


def run_gate():
    r = subprocess.run([sys.executable, GATE], stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                       timeout=300)
    return r.returncode, r.stdout.decode("utf-8", "replace")


def main():
    if os.path.isdir(TMP):
        shutil.rmtree(TMP)
    os.makedirs(TMP)
    ok, bad = 0, []
    for k in KNIVES:
        path = k[u"path"]
        if not os.path.isfile(path):
            bad.append(k[u"id"] + u"(文件不在)")
            print(u"  !! %s 文件不在：%s" % (k[u"id"], path))
            continue
        bak = os.path.join(TMP, k[u"id"] + u"__" + os.path.basename(path))
        shutil.copy2(path, bak)
        before = sha1(path)
        cut = True
        try:
            if k.get(u"rename"):
                os.rename(path, path + u".bak")
            else:
                text = io.open(path, encoding="utf-8", newline=u"").read()
                if k[u"old"] not in text:
                    cut = False
                    bad.append(k[u"id"] + u"(锚点找不到)")
                    print(u"  [FAIL] %s 刀砍不下去：找不到锚点 —— %s" % (k[u"id"], k[u"why"]))
                else:
                    io.open(path, "w", encoding="utf-8", newline=u"").write(
                        text.replace(k[u"old"], k[u"new"], 1))
            if cut:
                rc, out = run_gate()
                caught = [l.strip() for l in out.split(u"\n")
                          if l.strip().startswith(u"[FAIL]") and k[u"want"] in l]
                if rc != 0 and caught:
                    ok += 1
                    print(u"  [OK]   %s 门红了，抓到：%s" % (k[u"id"], caught[0][:70]))
                else:
                    bad.append(k[u"id"])
                    print(u"  [FAIL] %s 门没抓到（rc=%d，想看到 %s）—— %s"
                          % (k[u"id"], rc, k[u"want"], k[u"why"]))
        finally:
            if k.get(u"rename"):
                if os.path.isfile(path + u".bak"):
                    os.rename(path + u".bak", path)
            elif cut:
                shutil.copy2(bak, path)
            if not os.path.isfile(path) or sha1(path) != before:
                bad.append(k[u"id"] + u"(还原不一致)")
                print(u"  !! %s 还原后与砍之前不一致" % k[u"id"])
    print(u"\n反证刀：%d/%d 抓到（漏网 %s）" % (ok, len(KNIVES), u" / ".join(bad) if bad else u"无"))
    return 1 if bad else 0


if __name__ == u"__main__":
    sys.exit(main())
