# -*- coding: utf-8 -*-
u"""_zf78_republish3.py —— 第五次（也是最终一次）打包：把「倒不进去」文案改准后的成品发出去

本轮五次打包的完整链条（前四次见档案 §5 那行）：
  ① `9fd7340f…` 沥青贴图 4 位调色板被 TextureCheck 拦下
  ② `2bf27d2c…` 贴图重编码成 8 位 RGBA
  ③ `bafa7853…` 用户反馈"挡住物品栏字样" ⇒ 整排上提 8 px
  ④ `c9a3a492…` 倒流体 + 控制器排查显示
  ⑤ 本版 —— 把「倒不进去」那句话改准（原来漏了"一座塔都没认出来 ⇒ 容量 0"这种情况）

发布脚本里那套"先核对旧哈希、再动文件"的关卡照旧（§5 的 ZF63 教训）。
"""
import hashlib
import io
import os
import shutil
import sys
import zipfile

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

ROOT = r"E:\PotatoST"
SRC = os.path.join(ROOT, "build", "libs", "potato_s_t-0.11.jar")
DST = os.path.join(ROOT, "release", "PotatoST-0.11.jar")
SHA = DST + ".sha1"
PUB = os.path.join(ROOT, "build", "zftools", "_zf78_publish.py")
DOC = os.path.join(ROOT, "docs", u"开发档案.md")
VOID = "c9a3a492285af992bd93a11185a0d724d6d49449"
fails = []


def sha1(p):
    return hashlib.sha1(open(p, "rb").read()).hexdigest()


def patch(path, old, new, label):
    t = io.open(path, encoding="utf-8").read()
    hits = t.count(old)
    if hits != 1:
        fails.append(u"%s：锚点命中 %d 次（必须 1 次）" % (label, hits))
        return
    io.open(path, "w", encoding="utf-8", newline=u"\n").write(t.replace(old, new, 1))
    print(u"  [OK]   %s" % label)


def main():
    old = sha1(DST) if os.path.exists(DST) else u"(缺)"
    if old != VOID:
        fails.append(u"当前成品 %s 与预期要作废的 %s 不一致" % (old, VOID))
    if not os.path.exists(SRC):
        fails.append(u"没有构建产物")
    new = sha1(SRC) if os.path.exists(SRC) else u"(缺)"
    size = os.path.getsize(SRC) if os.path.exists(SRC) else 0
    entries = 0
    bad = []
    if os.path.exists(SRC):
        with zipfile.ZipFile(SRC) as zf:
            names = zf.namelist()
            entries = len(names)
            bad = [n for n in names if "Check" in n.split("/")[-1] and n.endswith(".class")]
    if bad:
        fails.append(u"成品里带探针：%s" % bad)
    if new == old:
        fails.append(u"新旧哈希相同 ⇒ 源码没变？")
    if fails:
        print(u"  [FAIL] 以上 %d 条没过 ⇒ 一个字节都不动" % len(fails))
        for f in fails:
            print(u"    !! " + f)
        return 1

    shutil.copy2(SRC, DST)
    io.open(SHA, "w", encoding="ascii", newline=u"\n").write(new + u"\n")
    print(u"① 已发布 release\\PotatoST-0.11.jar = %s（%d B / %d 条目）" % (new, size, entries))

    patch(PUB, u'VOID = "%s"' % VOID, u'VOID = "%s"' % new, u"发布脚本 VOID 跟到最新")

    patch(DOC,
          u"⚠ **本轮同版本打了四次**：",
          u"⚠ **本轮同版本打了五次**（第 ⑤ 次只改了一句提示文案，见 §9）：", 
          u"§5 行：四次 → 五次")
    patch(DOC,
          u"作废链：`27787d5e…`(ZF77) → `9fd7340f…` → `2bf27d2c…` → `bafa7853…`；"
          u"0.10 成品 `84d09345…` 始终原样保留",
          u"⑤ `%s`（%d B / %d 条目，**最终成品**）—— 把「倒不进去」那句提示改准："
          u"原来只写了「罐满或流体不对」，其实**一座分馏塔都没认出来时石油罐容量是 0**、"
          u"照样倒不进去（一共三种情况，顺手也把句子缩短了，它显示在动作栏上）。"
          u"作废链：`27787d5e…`(ZF77) → `9fd7340f…` → `2bf27d2c…` → `bafa7853…` → `c9a3a492…`；"
          u"0.10 成品 `84d09345…` 始终原样保留" % (new, size, entries),
          u"§5 行：补第五次 + 最终哈希")

    patch(DOC,
          u"**第四次（当前成品）= `c9a3a492285af992bd93a11185a0d724d6d49449`**"
          u"（2282004 B / 773 条目）",
          u"第四次 = `c9a3a492…`；**第五次（当前成品）= `%s`**（%d B / %d 条目）" % (new, size, entries),
          u"§9 条目：当前成品改指第五次")

    print(u"\n失败项 = %d" % len(fails))
    for f in fails:
        print(u"  !! " + f)
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())
