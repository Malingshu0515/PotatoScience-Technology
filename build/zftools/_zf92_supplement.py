# -*- coding: utf-8 -*-
r"""_zf92_supplement.py —— ZF92 补账：两个"动手后才发现本轮碰过、但快照里没有"的文件

⚠ **本轮我自己漏了两份**（§10 那条"动第一个字节前先抄一份"）：
  ① `build\zftools\_zf66_png.py` —— 我在动手改 OBJ **之前**就给它的 `write_png` 加了元组校验
     （那是 ZF91 留下的工具债：传 3 元组也照写，产出一张自己都读不回来的坏 PNG）。**先改后备份**，违规；
  ② `build\用户素材\_来源凭据.json` —— 处理用户中途丢进来的 `音乐唱片茉莉花.png` 时追加了一条。

按 §4.17 的来源等级，这两份都只能做 **③ 减法重建**（把本轮加的东西去掉、其余原样），
并在这里写清楚重建办法与判据：

  · `_zf66_png.py`：本轮只**插入**了 `write_png` 开头那段校验（7 行，含 2 行注释）。
    重建 = 把那 7 行删掉、恢复成 `def write_png(...)` 紧跟 `raw = bytearray()`。判据：重建后
    文件里不再出现「ZF92 补的护栏」，且能编译、`read_png/stats` 仍可用。
  · `_来源凭据.json`：本轮只**追加**了 `music_disc_jasmine_flower.png` 一条。重建 = 去掉该条后
    按同样的格式参数（`ensure_ascii=False, indent=2` + 结尾换行）重写。**格式与 zf89_pre 快照里的那份
    逐字符同款**（前面 260 字符与结尾 60 字符都比对过：同样的 2 空格缩进、同样的结尾 `}\n`），
    所以重写后的字节与"真·改前件"应当一致；判据：条目数回到 17、不含该键。

用法：
    python _zf92_supplement.py            # 预演：只打印将要做的事
    python _zf92_supplement.py --write    # 真写补账
"""
import hashlib
import io
import json
import os
import shutil
import sys

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

ROOT = r"E:\PotatoST"
BK = r"C:\PotatoST救援\zf92_pre"
TOOLS = os.path.join(ROOT, "build", "zftools")
PNG = os.path.join(TOOLS, "_zf66_png.py")
CRED = os.path.join(ROOT, "build", u"用户素材", u"_来源凭据.json")
NEWKEY = "music_disc_jasmine_flower.png"
ADDED = u"""    # ZF92 补的护栏：以前这里不校验元组长度，传了 3 元组也照写，
    # 结果产出一张自己都读不回来的坏 PNG（ZF91 的 _zf91_overlay.png 就是这么坏的）。
    if len(px) != w * h:
        raise ValueError(u"write_png: 像素数 %d != %d×%d = %d" % (len(px), w, h, w * h))
    for i, p in enumerate(px):
        if len(p) != 4:
            raise ValueError(u"write_png: 第 %d 个像素是 %d 元组（必须 RGBA 4 元组）: %r" % (i, len(p), tuple(p)))
        for c in p:
            if not (0 <= c <= 255):
                raise ValueError(u"write_png: 第 %d 个像素分量越界: %r" % (i, tuple(p)))
"""
fails = []


def sha1(p):
    return hashlib.sha1(open(p, "rb").read()).hexdigest()


def main(argv):
    write = "--write" in argv
    if not os.path.isdir(BK):
        print(u"[STOP] 快照目录不在：%s" % BK)
        return 1

    # ① _zf66_png.py
    t = io.open(PNG, encoding="utf-8").read()
    print(u"① %s：当前 %d 字节，sha1 %s…" % (os.path.basename(PNG), len(t.encode("utf-8")), sha1(PNG)[:12]))
    if ADDED not in t:
        print(u"   [SKIP] 找不到本轮插入的那段（可能已经补过账）")
        old_png = None
    else:
        old_png = t.replace(ADDED, u"", 1)
        print(u"   重建（减掉那 7 行）= %d 字节；仍含「ZF92 补的护栏」？%s"
              % (len(old_png.encode("utf-8")), u"ZF92 补的护栏" in old_png))
        if u"ZF92 补的护栏" in old_png:
            fails.append(u"_zf66_png.py 重建后仍含本轮注释")
        try:
            compile(old_png, "_zf66_png.py", "exec")
            print(u"   [OK] 重建件能编译")
        except SyntaxError as e:
            fails.append(u"_zf66_png.py 重建件编译失败：%s" % e)

    # ② _来源凭据.json
    d = json.loads(io.open(CRED, encoding="utf-8").read())
    print(u"\n② %s：当前 %d 条" % (os.path.basename(CRED), len(d)))
    old_cred = None
    if NEWKEY not in d:
        print(u"   [SKIP] 没有本轮追加的那条（可能已经补过账）")
    else:
        d2 = dict(d)
        del d2[NEWKEY]
        old_cred = json.dumps(d2, ensure_ascii=False, indent=2) + u"\n"
        print(u"   重建（去掉 %s）= %d 条 / %d 字节"
              % (NEWKEY, len(d2), len(old_cred.encode("utf-8"))))
        if NEWKEY in old_cred:
            fails.append(u"凭据重建件里仍有该键")

    if fails:
        print(u"\n[STOP] %d 条不过 ⇒ 什么都不写" % len(fails))
        for f in fails:
            print(u"  !! " + f)
        return 1
    if not write:
        print(u"\n预演：没加 --write，什么都不写")
        return 0

    lines = []
    if old_png is not None:
        dst = os.path.join(BK, "build", "zftools", "_zf66_png.py")
        os.makedirs(os.path.dirname(dst), exist_ok=True)
        io.open(dst, "w", encoding="utf-8", newline=u"\n").write(old_png)
        lines.append(u"%s  %10d  %s（③减法重建：减掉本轮插入的 write_png 校验 7 行）"
                     % (sha1(dst), os.path.getsize(dst), u"build\\zftools\\_zf66_png.py"))
        print(u"  [OK] 补账 %s" % dst)
    if old_cred is not None:
        dst = os.path.join(BK, "build", u"用户素材", u"_来源凭据.json")
        os.makedirs(os.path.dirname(dst), exist_ok=True)
        io.open(dst, "w", encoding="utf-8", newline=u"\n").write(old_cred)
        lines.append(u"%s  %10d  %s（③减法重建：去掉本轮追加的一条）"
                     % (sha1(dst), os.path.getsize(dst), u"build\\用户素材\\_来源凭据.json"))
        print(u"  [OK] 补账 %s" % dst)

    note = os.path.join(BK, u"_补说明.txt")
    txt = (u"ZF92 补账（本轮我漏抄的两份，动手后才发现本轮碰过）\n"
           u"================================================\n\n"
           u"来源等级：③ 减法重建（§4.17）—— 这两份**没有**改前原件可抄，只能把本轮加的东西去掉。\n\n"
           u"① build\\zftools\\_zf66_png.py\n"
           u"   本轮做的事：给 write_png 加元组长度/分量范围校验（ZF91 的工具债：传 3 元组也照写，\n"
           u"   产出过一张自己都读不回来的坏 PNG）。\n"
           u"   重建办法：删掉 write_png 里那段以「# ZF92 补的护栏」开头的 7 行，恢复成\n"
           u"   `def write_png(path, w, h, px):` 紧跟 `    raw = bytearray()`。\n"
           u"   判据：重建件里不再出现「ZF92 补的护栏」、且能编译（脚本里都跑过）。\n\n"
           u"② build\\用户素材\\_来源凭据.json\n"
           u"   本轮做的事：追加 music_disc_jasmine_flower.png 一条（用户 2026-09-25 00:07 丢进\n"
           u"   textures/item 的 `音乐唱片茉莉花.png`，3170 字节，sha1 0b1bf5f444a2cd4f320831652c6067c097a0d54d）。\n"
           u"   重建办法：去掉该键后按同样格式参数（ensure_ascii=False, indent=2 + 结尾换行）重写。\n"
           u"   判据：条目数回到 17；格式与 zf89_pre 快照那份逐字符同款（前 260 / 末 60 字符都比对过）。\n\n"
           u"⚠ 这两份**不影响成品**：前者是工具脚本（不进 jar），后者是 build/ 下的留档凭据（不进 jar）。\n")
    io.open(note, "w", encoding="utf-8", newline=u"\n").write(txt)
    print(u"  [OK] 补说明 → %s" % note)
    io.open(os.path.join(BK, u"_sha1.txt"), "a", encoding="utf-8", newline=u"\n").write(
        u"\n# ---- ZF92 补账（③减法重建，见 _补说明.txt）----\n" + u"\n".join(lines) + u"\n")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
