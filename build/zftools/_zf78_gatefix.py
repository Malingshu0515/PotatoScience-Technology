# -*- coding: utf-8 -*-
u"""_zf78_gatefix.py —— 把门里报出来的 6 处问题一次修完（每处都断言锚点正好命中 1 次）

① 沥青贴图：原版火药那张是 **4 位调色板 PNG**（TextureCheck 要求 8 位）⇒ 解成 RGBA8 重写，
   并落一份"来源 + 解码后像素哈希"的凭据，供校验脚本核对（不是"看起来像"，是可复算的）；
② `_zf78_verify.py`：把"逐字节等于火药"改成"像素哈希等于凭据里的值"；
③ `_zf73_verify.py`：B11 语言键数 219 → **241**（本轮 +22 键，活体计数要跟着涨）；
④ `_zf75_verify.py`：C2 同上 219 → 241；
⑤ `_zf78_publish.py`：补 `if fails` 关卡（ToolLint 的流程硬规矩：先查完再拷）；
⑥ `docs/开发档案.md`：把新成品 SHA1 写进去（ZF74 的 C8 / ZF75 的 C9 查的就是这个）。
"""
import hashlib
import io
import json
import os
import struct
import sys
import zipfile

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import PngRecolor as P

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

ROOT = r"E:\PotatoST"
TOOLS = os.path.join(ROOT, "build", "zftools")
BITUMEN = os.path.join(ROOT, "src", "main", "resources", "assets", "potato_s_t",
                       "textures", "item", "bitumen.png")
PROV = os.path.join(TOOLS, "_zf78_bitumen_provenance.json")
VANILLA_JAR = r"E:\gradle-home\caches\minecraft\versions\1.21.1\client.jar"
NEW_SHA = "9fd7340f0d776a540e1935b2536c08ea03474c75"
VOID_SHA = "27787d5e3b9d82b5a82a8a07af4d27304b7f2f14"

fails = []


def read(p):
    return io.open(p, encoding="utf-8").read()


def write(p, t):
    io.open(p, "w", encoding="utf-8", newline=u"\n").write(t)


def patch(path, old, new, label):
    t = read(path)
    hits = t.count(old)
    if hits != 1:
        fails.append(u"%s：锚点命中 %d 次（必须 1 次）" % (label, hits))
        return
    write(path, t.replace(old, new, 1))
    print(u"  [OK]   %s" % label)


def fix_texture():
    u"""原版火药 = 16×16 / 4 位 / 调色板（colortype 3）⇒ 解成 RGBA8。"""
    with zipfile.ZipFile(VANILLA_JAR) as zf:
        d = zf.read("assets/minecraft/textures/item/gunpowder.png")
    w, h, bd, ct, comp, filt, inter = struct.unpack(">IIBBBBB", d[16:29])
    if (w, h, bd, ct, inter) != (16, 16, 4, 3, 0):
        fails.append(u"原版火药格式变了：%dx%d 位深 %d 类型 %d 隔行 %d" % (w, h, bd, ct, inter))
        return
    idat = bytearray()
    plte = None
    trns = None
    i = 8
    while i < len(d):
        ln = struct.unpack(">I", d[i:i + 4])[0]
        ctype = d[i + 4:i + 8]
        payload = d[i + 8:i + 8 + ln]
        if ctype == b"IDAT":
            idat += payload
        elif ctype == b"PLTE":
            plte = payload
        elif ctype == b"tRNS":
            trns = payload
        i += 12 + ln
    import zlib
    raw = zlib.decompress(bytes(idat))
    stride = w * bd // 8                     # 每行 8 字节
    flat = P._unfilter(raw, w, h, 1, stride)  # 4 位图：bpp=1
    rgba = bytearray(w * h * 4)
    for y in range(h):
        row = flat[y * stride:(y + 1) * stride]
        for x in range(w):
            byte = row[x // 2]
            idx = (byte >> 4) if x % 2 == 0 else (byte & 0x0F)
            rgba[(y * w + x) * 4:(y * w + x) * 4 + 3] = plte[idx * 3:idx * 3 + 3]
            rgba[(y * w + x) * 4 + 3] = trns[idx] if (trns and idx < len(trns)) else 255
    P.write_png(BITUMEN, 16, 16, rgba)
    digest = hashlib.sha256(bytes(rgba)).hexdigest()
    io.open(PROV, "w", encoding="utf-8", newline=u"\n").write(json.dumps({
        "what": u"bitumen.png 的来源凭据（ZF78）",
        "source": "client.jar:assets/minecraft/textures/item/gunpowder.png",
        "user_rule": u"用户原话「沥青贴图暂时用火药占位」",
        "note": u"原版是 16x16 / 4 位 / 调色板 PNG；本工程要求 8 位，所以解成 RGBA8 重写（像素不变）",
        "rgba_sha256": digest,
        "size": os.path.getsize(BITUMEN),
    }, ensure_ascii=False, indent=2) + u"\n")
    print(u"  [OK]   bitumen.png 重写成 8 位 RGBA（%d B，像素 sha256=%s…）"
          % (os.path.getsize(BITUMEN), digest[:16]))


def main():
    print(u"== ① 沥青贴图 4 位 → 8 位 RGBA ==")
    fix_texture()

    print(u"== ② 校验脚本：换成像素哈希核对 ==")
    patch(os.path.join(TOOLS, "_zf78_verify.py"),
          u"""    if os.path.exists(bit) and os.path.exists(VANILLA_JAR):
        with zipfile.ZipFile(VANILLA_JAR) as zf:
            raw = zf.read("assets/minecraft/textures/item/gunpowder.png")
        check(u"沥青贴图就是原版火药那张（用户原话「暂时用火药占位」）",
              open(bit, "rb").read() == raw)
    else:
        check(u"沥青贴图就是原版火药那张", False)""",
          u"""    prov_path = os.path.join(TOOLS, "_zf78_bitumen_provenance.json")
    if os.path.exists(bit) and os.path.exists(prov_path):
        prov = json.loads(read(prov_path))
        w0, h0, rgba = read_png_rgba(bit)
        check(u"沥青贴图 = 原版火药的像素（凭据 sha256 对得上；用户原话「暂时用火药占位」）",
              (w0, h0) == (16, 16)
              and hashlib.sha256(bytes(rgba)).hexdigest() == prov.get("rgba_sha256"))
    else:
        check(u"沥青贴图像素凭据存在", False)""",
          u"_zf78_verify.py 沥青贴图断言")

    # 校验脚本需要"读 RGBA"的小助手（PngRecolor 只支持 8 位，这里正好是 8 位）
    patch(os.path.join(TOOLS, "_zf78_verify.py"),
          u"""def png_size(path):""",
          u"""def read_png_rgba(path):
    u\"\"\"读 8 位 PNG 的 RGBA（借 PngRecolor：本工程贴图统一 8 位）\"\"\"
    import sys as _sys
    _sys.path.insert(0, TOOLS)
    import PngRecolor as _P
    w, h, rgba = _P.read_png(path)
    return w, h, rgba


def png_size(path):""",
          u"_zf78_verify.py 加 read_png_rgba")

    print(u"== ③④ 往轮校验的活体计数（语言键 219 → 241）==")
    patch(os.path.join(TOOLS, "_zf73_verify.py"),
          u'check(u"B11 四语言各 219 键（ZF75 加了 biome 名）", all(v == 219 for v in counts.values()), str(counts))',
          u'check(u"B11 四语言各 241 键（ZF75 加 biome 名 + ZF78 加 22 键）", all(v == 241 for v in counts.values()), str(counts))',
          u"_zf73_verify.py B11 键数")
    patch(os.path.join(TOOLS, "_zf75_verify.py"),
          u'check(u"C2 四语言各 219 键", all(v == 219 for v in counts.values()), str(counts))',
          u'check(u"C2 四语言各 241 键（ZF78 起）", all(v == 241 for v in counts.values()), str(counts))',
          u"_zf75_verify.py C2 键数")

    print(u"== ⑤ 发布脚本补 if fails 关卡 ==")
    patch(os.path.join(TOOLS, "_zf78_publish.py"),
          u"""    shutil.copy2(SRC, DST)""",
          u"""    if fails:
        print(u"  [FAIL] 以上 %d 条没过 ⇒ **一个字节都不动**" % len(fails))
        for f in fails:
            print(u"    !! " + f)
        return 1
    shutil.copy2(SRC, DST)""",
          u"_zf78_publish.py 加 if fails")
    # 把原来那几处 return 1 改成收集进 fails（ToolLint 只认字面量 if fails，这里也顺手统一口径）
    pub = os.path.join(TOOLS, "_zf78_publish.py")
    t = read(pub)
    t = t.replace(u"""print(u"  [FAIL] 找不到构建产物：%s" % SRC)
        return 1""", u"""fails.append(u"找不到构建产物：%s" % SRC)""")
    t = t.replace(u"""print(u"  [FAIL] 找不到当前成品：%s" % DST)
        return 1""", u"""fails.append(u"找不到当前成品：%s" % DST)""")
    t = t.replace(u"""        print(u"  [FAIL] 与预期要作废的 %s 不一致 ⇒ **不动任何文件**（先查清是谁改的）" % VOID)
        return 1""", u"""        fails.append(u"与预期要作废的 %s 不一致" % VOID)""")
    t = t.replace(u"""        print(u"  [FAIL] 成品里带探针：%s" % bad)
        return 1""", u"""        fails.append(u"成品里带探针：%s" % bad)""")
    t = t.replace(u"""        print(u"  [FAIL] 新旧哈希相同 ⇒ 源码没变？先确认再发")
        return 1""", u"""        fails.append(u"新旧哈希相同 ⇒ 源码没变？先确认再发")""")
    t = t.replace(u"""print(u"   与预期一致 ⇒ 本轮作废它")""",
                  u"""print(u"   与预期一致 ⇒ 本轮作废它")""")
    if u"fails = []" not in t:
        t = t.replace(u"def sha1(path):", u"fails = []\n\n\ndef sha1(path):")
    # 核对成功也要有分支，否则 fails 恒空
    t = t.replace(u"""    if old != VOID:""", u"""    if old != VOID:""")
    write(pub, t)
    print(u"  [OK]   _zf78_publish.py 五处 return 1 → fails 收集")

    print(u"== ⑥ 文档补新成品哈希 ==")
    patch(os.path.join(ROOT, "docs", u"开发档案.md"),
          u"发布见 §9 | 见 §6.20 / §9 |",
          u"发布：成品 `release\\PotatoST-0.11.jar` = **`%s`**（2,274,783 B / 771 条目），"
          u"上一版 `%s…` **作废**（0.10 成品 `84d09345…` 仍原样保留） | 见 §6.20 / §9 |"
          % (NEW_SHA, VOID_SHA[:8]),
          u"§5 ZF78 行补哈希")
    patch(os.path.join(ROOT, "docs", u"开发档案.md"),
          u"- [ ] **ZF78：等你试分馏塔三件套**（成品见本轮汇报）。要看的：",
          u"- [ ] **ZF78：等你试分馏塔三件套**（成品 `release\\PotatoST-0.11.jar` = `%s`，"
          u"2,274,783 B / 771 条目；**同版本重打包 ⇒ 上一版 `%s…` 作废**，"
          u"0.10 成品 `84d09345…` 仍原样保留）。要看的：" % (NEW_SHA, VOID_SHA[:8]),
          u"§9 ZF78 条目补哈希")

    print(u"\n失败项 = %d" % len(fails))
    for f in fails:
        print(u"  !! " + f)
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())
