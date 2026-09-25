# -*- coding: utf-8 -*-
u"""_zf119_falsify.py —— ZF119 的反证刀（K157~K164，8 把）

口径同前：先确认基线绿 → 改一处语义 ⇒ 门必须 FAIL 且**咬住指定的那条检查** ⇒ 逐字节还原 ⇒
收尾回到全绿。一把刀 180 秒超时（§4.77）。

刀面覆盖这一轮说出口的每一句话：
  动画（frametime / mcmeta 消失 / 帧数 / 摆位）、物品（创造页那一行）、
  标签（c:ingots/vibranium）、语言（键被删）、**没有配方**（有人偷偷加一条）。
"""
import hashlib
import io
import json
import os
import subprocess
import sys

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

sys.path.insert(0, r"E:\PotatoST\build\zftools")
from PngRecolor import read_png, write_png  # noqa: E402

ROOT = r"E:\PotatoST"
ZT = os.path.join(ROOT, r"build\zftools")
TEXI = os.path.join(ROOT, r"src\main\resources\assets\potato_s_t\textures\item")
LANG = os.path.join(ROOT, r"src\main\resources\assets\potato_s_t\lang")
TAGS = os.path.join(ROOT, r"src\main\resources\data\c\tags\item")
RDIR = os.path.join(ROOT, r"src\main\resources\data\potato_s_t\recipe")
JAVA = os.path.join(ROOT, r"src\main\java\com\potatost\mod")
VERIFY = os.path.join(ZT, u"_zf119_verify.py")

TEX = os.path.join(TEXI, u"vibranium_ingot.png")
MC = TEX + u".mcmeta"


def png_9frames():
    u"""把 10 帧的贴图砍成 9 帧（高度 288）"""
    w, h, buf = read_png(TEX)
    write_png(TEX, w, h - 32, buf[:w * (h - 32) * 4])


def png_shift():
    u"""把每帧内容整体下移 1 行（摆位不再等于基准）"""
    w, h, buf = read_png(TEX)
    out = bytearray(w * h * 4)
    for y in range(h):
        src_y = y - 1
        if src_y < 0 or src_y % 32 == 31:
            continue
        out[y * w * 4:(y + 1) * w * 4] = buf[src_y * w * 4:(src_y + 1) * w * 4]
    write_png(TEX, w, h, out)


def png_lastframe_down():
    u"""**复现用户实测的那个 bug**：只把**最后一帧**整体下移 3 行
    （第一版就是按"有不透明像素的行"分帧 ⇒ 最后一帧的窗口被闪光抬高 3 行 ⇒ 看着向下弹一下）"""
    w, h, buf = read_png(TEX)
    out = bytearray(buf)
    k = h // 32 - 1
    for y in range(31, -1, -1):
        src = (k * 32 + y - 3) * w * 4
        dst = (k * 32 + y) * w * 4
        out[dst:dst + w * 4] = buf[src:src + w * 4] if y >= 3 else bytes(w * 4)
    write_png(TEX, w, h, out)


def add_recipe():
    obj = {
        "type": "minecraft:crafting_shaped",
        "category": "misc",
        "pattern": ["XX", "XX"],
        "key": {"X": {"item": "potato_s_t:raw_vibranium"}},
        "result": {"id": "potato_s_t:vibranium_ingot", "count": 1},
    }
    io.open(os.path.join(RDIR, u"vibranium_ingot.json"), "w", encoding="utf-8",
            newline=u"\n").write(json.dumps(obj, ensure_ascii=False, indent=2) + u"\n")


KNIVES = [
    dict(id="K157", why=u"动画帧时长从 3 tick 改成 1 tick", path=MC,
         old=u'"frametime": 3', new=u'"frametime": 1',
         expect=u"A16 mcmeta：animation.frametime = 3"),
    dict(id="K158", why=u"mcmeta 整个删掉（贴图不变 ⇒ 游戏当静态图）", path=MC, mode="delete",
         expect=u"A2 mcmeta 在"),
    dict(id="K159", why=u"贴图被砍成 9 帧（320 → 288）", path=TEX, mode="png", fn="nine",
         expect=u"A7 贴图尺寸 32×320"),
    dict(id="K160", why=u"每帧内容整体下移一行（摆位不再等于基准）", path=TEX, mode="png", fn="shift",
         expect=u"A8 每帧**本体**都落在 y=4..27"),
    dict(id="K165", why=u"**复现用户实测的那个弹跳**：只把最后一帧下移 3 行（闪光抬高过窗口的老 bug）",
         path=TEX, mode="png", fn="last3", expect=u"A9b 10 帧的**本体包围盒完全一致**"),
    dict(id="K161", why=u"四语言里删掉振金锭那个键", path=os.path.join(LANG, u"zh_cn.json"),
         mode="line", old=u'"item.potato_s_t.vibranium_ingot":',
         expect=u"C1 四语言各 449 键"),
    dict(id="K162", why=u"创造页那一行被删掉（§4.82 的老毛病）",
         path=os.path.join(JAVA, u"ModItems.java"), mode="line",
         old=u"output.accept(VIBRANIUM_INGOT.get())",
         expect=u"B2 创造页里 accept 了它"),
    dict(id="K163", why=u"c:ingots/vibranium 标签文件被删",
         path=os.path.join(TAGS, u"ingots", u"vibranium.json"), mode="delete",
         expect=u"B4 c:ingots/vibranium 收下它"),
    dict(id="K164", why=u"有人偷偷给它加了一条配方（用户明说目前没配方）",
         path=os.path.join(RDIR, u"vibranium_ingot.json"), mode="create", fn="recipe",
         expect=u"B6 **没有任何配方**产出它"),
]

fails, notes = [], []


def run():
    try:
        r = subprocess.run([sys.executable, VERIFY], stdout=subprocess.PIPE,
                           stderr=subprocess.STDOUT, timeout=300)
        return r.returncode, r.stdout.decode("utf-8", "replace")
    except subprocess.TimeoutExpired:
        return 99, u"**超时**"


def summary(out):
    line = [l for l in out.split(u"\n") if u"通过" in l and u"失败" in l]
    return line[-1].strip() if line else u"?"


def main():
    rc, out = run()
    print(u"基线：%s（退出码 %d）" % (summary(out), rc))
    if rc != 0:
        print(u"  [STOP] 基线不绿，先修")
        for l in out.split(u"\n"):
            if l.strip().startswith(u"!!"):
                print(u"    " + l.strip())
        return 1
    n_ok = 0
    for k in KNIVES:
        path = k["path"]
        orig = open(path, "rb").read() if os.path.exists(path) else None
        before = hashlib.sha1(orig).hexdigest() if orig is not None else u"(不存在)"
        mode = k.get("mode", "replace")
        try:
            if mode == "delete":
                os.remove(path)
            elif mode == "create":
                add_recipe()
            elif mode == "png":
                {"nine": png_9frames, "shift": png_shift,
                 "last3": png_lastframe_down}[k["fn"]]()
            elif mode == "line":
                text = orig.decode("utf-8")
                lines = [l for l in text.split(u"\n") if not l.strip().startswith(k["old"])]
                if len(lines) == len(text.split(u"\n")):
                    fails.append(u"%s：要删的行没找到" % k["id"])
                    continue
                open(path, "wb").write(u"\n".join(lines).encode("utf-8"))
            else:
                text = orig.decode("utf-8")
                if text.count(k["old"]) != 1:
                    fails.append(u"%s：锚点命中 %d 次" % (k["id"], text.count(k["old"])))
                    continue
                open(path, "wb").write(text.replace(k["old"], k["new"], 1).encode("utf-8"))
            rc, out = run()
        finally:
            if orig is None:
                if os.path.exists(path):
                    os.remove(path)
            else:
                open(path, "wb").write(orig)
        after = hashlib.sha1(open(path, "rb").read()).hexdigest() if os.path.exists(path) else u"(不存在)"
        if after != before:
            fails.append(u"%s：还原失败" % k["id"])
            break
        if rc != 0 and k["expect"] in out:
            n_ok += 1
            print(u"  [OK]   %s %s ⇒ 咬住「%s」" % (k["id"], k["why"], k["expect"]))
        else:
            print(u"  [BAD]  %s %s（退出码 %d）" % (k["id"], k["why"], rc))
            fails.append(u"%s %s ⇒ %s" % (k["id"], k["why"],
                                          u"门还是绿的" if rc == 0 else u"咬错了检查"))
    rc, out = run()
    print(u"收尾：%s（退出码 %d）" % (summary(out), rc))
    if rc != 0:
        fails.append(u"收尾不是全绿")
    print(u"刀 = %d，咬住 = %d，失败项 = %d" % (len(KNIVES), n_ok, len(fails)))
    for f in fails:
        print(u"  !! " + f)
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())
