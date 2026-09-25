# -*- coding: utf-8 -*-
r"""_zf95_supplement.py —— ZF95 补账：两份"动手后才发现本轮碰过、但快照里没有"的脚本

⚠ **本轮我又漏了两份**（§10 那条"动第一个字节之前先抄一份"）：
  ① `build\zftools\_zf73_repro.py`  ② `build\zftools\_zf73_verify.py`
  —— 它们各自的"新增配方名单"里没有 ZF95 的 5 条 ⇒ 门当场报错（这正是"陈旧断言该挂"），
  我改完才发现这两份没进快照。按 §4.17 只能做 **③ 减法重建**（把我加的东西去掉）。

重建办法（都在本文里写死，便于复核）：
  ① `_zf73_repro.py`：把 `NEW_OK = {...}` 从 7 项集合换回 2 项集合（`oil_bucket.json`、
     `fluid_exchanger.json`），注释同理换回原文。
  ② `_zf73_verify.py`：把 D2 那条 check 换回原来那两行（期望值只有 fluid_exchanger + oil_bucket，
     标题里没有 ZF95 那半句）。
判据：重建件里不再出现 ZF95 的痕迹、且能编译。

用法：
    python _zf95_supplement.py            # 预演
    python _zf95_supplement.py --write    # 真写补账
"""
import hashlib
import io
import os
import sys

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

TOOLS = r"E:\PotatoST\build\zftools"
BK = r"C:\PotatoST救援\zf95_pre"

REPRO = os.path.join(TOOLS, "_zf73_repro.py")
REPRO_OLD = (u"# ⚠ ZF82 又加了 fluid_exchanger.json（容器换流器的合成台配方）——\n"
             u"#   「其余 34 份逐字节未变」才是这条的真正内容，新增名单随轮次增长。\n"
             u"NEW_OK = {u\"oil_bucket.json\", u\"fluid_exchanger.json\"}")
REPRO_NEW_HEAD = u"# ⚠ ZF82 又加了 fluid_exchanger.json（容器换流器的合成台配方）；ZF95 又加了用户口述的 5 条"

VER = os.path.join(TOOLS, "_zf73_verify.py")
VER_OLD = (u"        check(u\"D2 只新增了预期的那些（ZF82 起含 fluid_exchanger.json）\",\n"
           u"      sorted(cur - pre) == [u\"fluid_exchanger.json\", u\"oil_bucket.json\"],\n"
           u"              u\", \".join(sorted(cur - pre)))")
VER_NEW_HEAD = u"        # ⚠ 这条的**内容**是"

fails = []


def sha1(p):
    return hashlib.sha1(open(p, "rb").read()).hexdigest()


def rebuild(path, marker, old_text):
    t = io.open(path, encoding="utf-8").read()
    if marker not in t:
        print(u"  [SKIP] %s：找不到本轮加的那段（可能已经补过账）" % os.path.basename(path))
        return None
    # 把"本轮那段"整块换成原文：本轮那段从 marker 开始、到下一个空行为止
    start = t.index(marker)
    end = t.index(u"\n\n", start) if u"\n\n" in t[start:] else len(t)
    out = t[:start] + old_text + t[end:]
    if marker in out:
        fails.append(u"%s 重建后仍含本轮标记" % os.path.basename(path))
    try:
        compile(out, os.path.basename(path), "exec")
    except SyntaxError as e:
        fails.append(u"%s 重建件编译失败：%s" % (os.path.basename(path), e))
    return out


def main(argv):
    write = "--write" in argv
    if not os.path.isdir(BK):
        print(u"[STOP] 快照目录不在：%s" % BK)
        return 1
    print(u"① %s：当前 %d 字节 sha1 %s…" % (os.path.basename(REPRO),
                                          os.path.getsize(REPRO), sha1(REPRO)[:12]))
    r_new = rebuild(REPRO, REPRO_NEW_HEAD, REPRO_OLD)
    print(u"② %s：当前 %d 字节 sha1 %s…" % (os.path.basename(VER),
                                          os.path.getsize(VER), sha1(VER)[:12]))
    v_new = rebuild(VER, VER_NEW_HEAD, VER_OLD)
    if fails:
        print(u"\n[STOP] %d 条不过 ⇒ 什么都不写" % len(fails))
        for f in fails:
            print(u"  !! " + f)
        return 1
    if not write:
        print(u"\n预演：没加 --write，什么都不写")
        return 0
    lines = []
    for path, text, rel in ((REPRO, r_new, r"build\zftools\_zf73_repro.py"),
                            (VER, v_new, r"build\zftools\_zf73_verify.py")):
        if text is None:
            continue
        dst = os.path.join(BK, rel)
        os.makedirs(os.path.dirname(dst), exist_ok=True)
        io.open(dst, "w", encoding="utf-8", newline=u"\n").write(text)
        lines.append(u"%s  %10d  %s（③减法重建：换回本轮之前的「新增配方名单」）"
                     % (sha1(dst), os.path.getsize(dst), rel))
        print(u"  [OK] 补账 %s" % dst)
    note = os.path.join(BK, u"_补说明.txt")
    io.open(note, "w", encoding="utf-8", newline=u"\n").write(
        u"ZF95 补账（本轮我漏抄的两份，门当场报错才发现的）\n"
        u"================================================\n\n"
        u"来源等级：③ 减法重建（§4.17）—— 这两份没有改前原件可抄，只能把本轮改的那段换回去。\n\n"
        u"① build\\zftools\\_zf73_repro.py\n"
        u"   本轮做的事：`NEW_OK` 从 2 项（oil_bucket / fluid_exchanger）扩到 7 项（+ZF95 的 5 条）。\n"
        u"   重建：换回那两行注释 + 2 项集合。\n"
        u"② build\\zftools\\_zf73_verify.py\n"
        u"   本轮做的事：D2 那条 check 的期望值扩到 7 份、标题补了「ZF95 起含 5 条口述配方」。\n"
        u"   重建：换回原来那两行（期望只有 fluid_exchanger + oil_bucket，标题无 ZF95 字样）。\n\n"
        u"判据：重建件里不再出现 ZF95 的痕迹（脚本跑过）、且能编译（脚本跑过）。\n"
        u"⚠ 这两份是**校验脚本**，不进 jar。\n")
    print(u"  [OK] 补说明 → %s" % note)
    io.open(os.path.join(BK, u"_sha1.txt"), "a", encoding="utf-8", newline=u"\n").write(
        u"\n# ---- ZF95 补账（③减法重建，见 _补说明.txt）----\n" + u"\n".join(lines) + u"\n")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
