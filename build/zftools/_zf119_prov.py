# -*- coding: utf-8 -*-
r"""_zf119_prov.py —— 把本轮素材登进 `build\用户素材\_来源凭据.json`（原字节可追的账本）

⚠ 这份账本是**多会话共用**的（ZF116 素材线刚往里加了三件盔甲）。并发环境 ⇒
「读 → 加键 → 立刻回读断言 → 只动自己的键」，绝不整份覆盖。
"""
import hashlib
import io
import json
import os
import sys

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

USERART = r"E:\PotatoST\build\用户素材"
PROV = os.path.join(USERART, u"_来源凭据.json")
SRC = os.path.join(USERART, u"振金锭.png")
KEY = u"振金锭.png"
TEX = r"E:\PotatoST\src\main\resources\assets\potato_s_t\textures\item\vibranium_ingot.png"

fails = []


def main():
    raw = io.open(PROV, encoding="utf-8").read()
    prov = json.loads(raw)
    before = len(prov)
    sha = hashlib.sha1(open(SRC, "rb").read()).hexdigest()
    entry = {
        u"原名": u"振金锭.png",
        u"sha1": sha,
        u"bytes": os.path.getsize(SRC),
        u"说明": (u"用户 ZF119 从会话附件给的素材（32×280 / 8 位 RGBA / 零半透明）——"
                u"它是**动画长条**：10 个 32×24 的锭竖着堆。MC 的动画贴图要求「宽 × (宽 × 帧数)」，"
                u"280/32 = 8.75 ⇒ 不能直接当动画用。重排脚本 `build\\zftools\\_zf119_texture.py` "
                u"只做整行搬运（零重采样），产出 textures/item/vibranium_ingot.png（32×320，10 帧）"
                u"+ 同名 .mcmeta（frametime = 3，3 tick 一帧、一轮 30 tick = 1.5 秒）；"
                u"摆位照盘上 titanium_ingot.png（同样 32×24 内容、上下各留 4 行）。"
                u"产出贴图 sha1 = " + hashlib.sha1(open(TEX, "rb").read()).hexdigest()),
    }
    if prov.get(KEY) == entry:
        print(u"  [--]   账本里已经有这一条（同值），跳过")
        return 0
    if KEY in prov:
        fails.append(u"账本里已有 %s 但内容不同 —— 先看清再改：%s"
                     % (KEY, json.dumps(prov[KEY], ensure_ascii=False)[:200]))
    else:
        prov[KEY] = entry
        text = json.dumps(prov, ensure_ascii=False, indent=2) + u"\n"
        io.open(PROV, "w", encoding="utf-8", newline=u"").write(text)
        back = json.loads(io.open(PROV, encoding="utf-8").read())
        if len(back) != before + 1 or back.get(KEY) != entry:
            fails.append(u"回读失败：%d → %d" % (before, len(back)))
        else:
            print(u"  [OK]   账本 %d → %d 条（新增 %s，sha1 %s…）"
                  % (before, len(back), KEY, sha[:12]))
        # 只动自己那个键
        changed = [k for k in prov if k != KEY and k in json.loads(raw)]
        if changed:
            pass
    print(u"失败项 = %d" % len(fails))
    for f in fails:
        print(u"  !! " + f)
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())
