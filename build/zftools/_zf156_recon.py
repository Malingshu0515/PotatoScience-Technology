# -*- coding: utf-8 -*-
"""_zf156_recon.py —— ZF156 侦察（只读）：三个问题的根因取证。

① 端子连线「有时候会消失」：区块卸载会走 setRemoved，而我们在 setRemoved 里断了对端。
② 手册「每回进游戏都给一本」：玩家持久化数据在**克隆**（换维度 / 死后重生）里被丢掉
   —— ServerPlayer.restoreFrom 只搬 PERSISTED_NBT_TAG 那一把；附件（attachment）才会被搬。
③ 金属板配方只认自家板：配方原料写的是**物品**而不是标签，而板子的跨 mod 约定是
   `c:plates/*`（IE / Create 都自己挂了）。

⚠ NBT 一律用 `_zf156_nbtdump.Reader`（那份已经对过 42 键/43 键的真实存档）。
   本轮我在这份脚本里手写过一版迷你解析器，**连踩两个坑**（根 compound 少认一个类型字节、
   TAG_List 的元素多认一个类型字节），当场删掉改成复用 —— 解析器不要写第二份。

跑法：python build\\zftools\\_zf156_recon.py [--write]
"""
import io
import json
import os
import re
import sys
import zipfile

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _zf156_nbtdump import Reader  # noqa: E402

if __name__ == u"__main__":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding=u"utf-8", errors=u"replace")

ROOT = r"E:\PotatoST"
SRC = os.path.join(ROOT, r"build\neoForm\neoFormJoined1.21.1-20240808.144430\steps\transformSource\transformed")
OUT = os.path.join(ROOT, r"build\zftools\_zf156_recon.txt")
PACK = u"E:\\game\\pcl快照\\.minecraft\\versions\\科技mod乱炖\\mods"
DEV_PACK = os.path.join(ROOT, r"run\client\mods")
SAVES = u"E:\\game\\pcl快照\\.minecraft\\versions\\科技mod乱炖\\saves"
DEV_SAVE = os.path.join(ROOT, r"run\client\saves\新的世界\playerdata")

LINES = []


def say(s):
    LINES.append(s)
    print(s)


def read(path):
    return io.open(path, encoding=u"utf-8", errors=u"replace").read()


def grep(path, pat, limit=6):
    out = []
    for i, line in enumerate(read(path).splitlines(), 1):
        if re.search(pat, line):
            out.append(u"%s:%d: %s" % (os.path.basename(path), i, line.strip()))
            if len(out) >= limit:
                break
    return out


def nbt_root(path):
    import gzip
    with gzip.open(path, "rb") as fh:
        raw = fh.read()
    r = Reader(raw)
    t = r.u1()
    if t != 10:
        raise ValueError(u"根不是 compound（type=%d）" % t)
    r.s()
    return r.payload(10)


def jar_plate_tags(jar):
    """返回 {标签文件: [条目]} 与 modid（只看 plates）。"""
    tags, modid = {}, None
    with zipfile.ZipFile(jar) as zf:
        for n in zf.namelist():
            if "/tags/" in n and "/plates" in n and n.endswith(".json"):
                try:
                    data = json.loads(zf.read(n).decode("utf-8"))
                except Exception:
                    continue
                vals = []
                for v in data.get("values", []):
                    vals.append(v if isinstance(v, str) else v.get("id"))
                tags[n] = vals
            if modid is None and (n.endswith("neoforge.mods.toml") or n.endswith("mods.toml")):
                m = re.search(r'modId\s*=\s*"([^"]+)"', zf.read(n).decode("utf-8", "replace"))
                modid = m.group(1) if m else None
    return tags, modid


def main(argv):
    say(u"=========== ZF156 侦察 ===========")

    # ---------- ① 端子 ----------
    say(u"\n① 端子连线消失：区块卸载会走 setRemoved")
    for f, pat in ((r"server\level\ServerLevel.java", r"clearAllBlockEntities"),
                   (r"world\level\chunk\LevelChunk.java", r"clearAllBlockEntities\(\) \{|BlockEntity::onChunkUnloaded|BlockEntity::setRemoved"),
                   (r"world\level\block\entity\BlockEntity.java", r"public void setRemoved\(\)")):
        for l in grep(os.path.join(SRC, "net", "minecraft", f), pat):
            say(u"   " + l)
    tb = read(os.path.join(ROOT, r"src\main\java\com\potatost\mod\TerminalBlockEntity.java"))
    say(u"   本模组现状：setRemoved 里断开对端 %d 处；有没有 onChunkUnloaded 覆写：%s"
        % (tb.count(u"removeConnection(this.getBlockPos())") + tb.count(u"removePowerConnection(this.getBlockPos())"),
           u"有" if u"onChunkUnloaded" in tb else u"没有"))

    # ---------- ② 手册 ----------
    say(u"\n② 手册每回都发：克隆（换维度 / 死后重生）只搬 PERSISTED_NBT_TAG")
    for l in grep(os.path.join(SRC, r"net\minecraft\server\level\ServerPlayer.java"),
                  r"public void restoreFrom\(|PERSISTED_NBT_TAG|onPlayerClone\("):
        say(u"   " + l)
    for l in grep(os.path.join(SRC, r"net\minecraft\server\network\ServerGamePacketListenerImpl.java"),
                  r"getPlayerList\(\)\.respawn\("):
        say(u"   " + l)
    for l in grep(os.path.join(SRC, r"net\neoforged\neoforge\attachment\AttachmentInternals.java"),
                  r"copyAttachments\(from|onPlayerClone"):
        say(u"   " + l)
    for l in grep(os.path.join(SRC, r"net\neoforged\neoforge\attachment\AttachmentType.java"),
                  r"boolean copyOnDeath|this.copyOnDeath = builder.copyOnDeath|copyOnDeath requires"):
        say(u"   " + l)
    say(u"   真实存档取证（玩家持久化数据里有没有 potato_s_t_guide_given）：")
    for base in (SAVES, DEV_SAVE):
        if not os.path.isdir(base):
            continue
        for dirpath, _dirnames, filenames in os.walk(base):
            if os.path.basename(dirpath) != "playerdata":
                continue      # 只认玩家数据（存档里别的 .dat 不是玩家）
            for fn in sorted(filenames):
                if not fn.endswith(".dat"):
                    continue
                p = os.path.join(dirpath, fn)
                try:
                    root = nbt_root(p)
                except Exception as exc:
                    say(u"     !! %s : %s" % (fn[:8], exc))
                    continue
                nf = root.get("NeoForgeData") or {}
                say(u"     %-10s guide=%-4s PlayerPersisted=%-4s 死亡记录=%-4s 维度落点=%-4s %d 键 %s"
                    % (fn[:8],
                       u"有" if nf.get("potato_s_t_guide_given") else u"没有",
                       u"有" if "PlayerPersisted" in nf else u"没有",
                       u"有" if "LastDeathLocation" in root else u"没有",
                       u"有" if "SpawnDimension" in root else u"没有",
                       len(root), os.path.relpath(p, base)[:44]))

    # ---------- ③ 金属板 ----------
    say(u"\n③ 金属板：别的 mod 自己就挂在 c:plates/* 上")
    for d in (PACK, DEV_PACK):
        if not os.path.isdir(d):
            continue
        say(u"   --- " + d)
        for name in sorted(os.listdir(d)):
            if not name.lower().endswith(".jar"):
                continue
            try:
                tags, modid = jar_plate_tags(os.path.join(d, name))
            except Exception:
                continue
            if tags:
                say(u"     %s (%s)" % (modid, name[:46]))
                for k in sorted(tags):
                    if k.count("/") >= 6:
                        say(u"        %s = %s" % (k.split("tags/")[-1],
                                                  json.dumps(tags[k], ensure_ascii=False)))
    our = os.path.join(ROOT, r"src\main\resources\data\c\tags\item\plates")
    say(u"   本模组已挂：%s" % u", ".join(sorted(os.listdir(our))))
    recipes = os.path.join(ROOT, r"src\main\resources\data\potato_s_t\recipe")
    hits, taghits = [], 0
    for dirpath, _d, filenames in os.walk(recipes):
        for fn in filenames:
            if not fn.endswith(".json"):
                continue
            t = read(os.path.join(dirpath, fn))
            n = len(re.findall(r"potato_s_t:(?:aluminum|cobalt|copper|iron|nickel|silver|steel)_plate", t))
            if n:
                hits.append((fn, n))
            taghits += len(re.findall(r"#c:plates/", t))
    say(u"   本模组配方里写死自家板的地方：%d 份 / %d 处；已经用 #c:plates/ 的：%d 处"
        % (len(hits), sum(n for _f, n in hits), taghits))
    say(u"     " + u", ".join(u"%s×%d" % h for h in sorted(hits)))

    say(u"\n=========== 侦察完 ===========")
    if u"--write" in argv:
        io.open(OUT, "w", encoding="utf-8", newline=u"\n").write(u"\n".join(LINES) + u"\n")
        print(u"（已写 %s）" % OUT)
    return 0


if __name__ == u"__main__":
    sys.exit(main(sys.argv[1:]))
