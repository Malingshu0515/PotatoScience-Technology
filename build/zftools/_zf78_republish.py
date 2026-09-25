# -*- coding: utf-8 -*-
u"""_zf78_republish.py —— 版式微调后第三次打包（并把这轮的"三次重打包"如实写进文档）

本轮同版本打了三次：
  ① `9fd7340f…` 第一次（沥青贴图还是 4 位调色板 ⇒ 被 TextureCheck 拦下）
  ② `2bf27d2c…` 第二次（贴图重编码成 8 位 RGBA 后重打）
  ③ `?`          第三次（用户反馈"罐挡住物品栏字样" ⇒ 整排上提 8 px）

作废链：`27787d5e…`(ZF77) → `9fd7340f…` → `2bf27d2c…`；0.10 成品 `84d09345…` 始终原样保留。
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
VOID = "2bf27d2cf68a51e2721901af8805c6a8cf1273ed"
fails = []


def sha1(p):
    return hashlib.sha1(open(p, "rb").read()).hexdigest()


def patch(path, old, new, label):
    t = io.open(path, encoding="utf-8").read()
    hits = t.count(old)
    if hits != 1:
        fails.append(u"%s：锚点命中 %d 次" % (label, hits))
        return
    io.open(path, "w", encoding="utf-8", newline=u"\n").write(t.replace(old, new, 1))
    print(u"  [OK]   %s" % label)


def main():
    old = sha1(DST) if os.path.exists(DST) else u"(缺)"
    if old != VOID:
        print(u"  [FAIL] 当前成品是 %s，与预期要作废的 %s 不一致 ⇒ 不动任何文件" % (old, VOID))
        return 1
    if not os.path.exists(SRC):
        print(u"  [FAIL] 没有构建产物 %s" % SRC)
        return 1
    with zipfile.ZipFile(SRC) as zf:
        names = zf.namelist()
        bad = [n for n in names if "Check" in n.split("/")[-1] and n.endswith(".class")]
    if bad:
        print(u"  [FAIL] 成品里带探针：%s" % bad)
        return 1
    new = sha1(SRC)
    size = os.path.getsize(SRC)
    if new == old:
        print(u"  [FAIL] 新旧哈希相同 ⇒ 源码没变？")
        return 1

    shutil.copy2(SRC, DST)
    io.open(SHA, "w", encoding="ascii", newline=u"\n").write(new + u"\n")
    print(u"① 已发布 release\\PotatoST-0.11.jar = %s（%d B / %d 条目）"
          % (new, size, len(names)))
    print(u"   作废 %s（本轮第二次）" % VOID[:8])

    patch(PUB, u'VOID = "%s"' % VOID, u'VOID = "%s"' % new,
          u"发布脚本的 VOID 跟到最新（下次重打包作废这一版）")

    # 文档：三次打包的完整记录（§5 那行 + §9 那条）
    patch(DOC,
          u"发布：成品 `release\\PotatoST-0.11.jar` = **`%s`**（2,274,796 B / 771 条目）。"
          u"⚠ **本轮同版本打了两次**：第一次 `9fd7340f…` 的沥青贴图还是原版那种 **4 位调色板** PNG"
          u"（TextureCheck 第 6 道门当场拦下）⇒ 解成 8 位 RGBA 重写后**重打一次**；"
          u"两次都作废：`27787d5e…`（ZF77）与 `9fd7340f…`（本轮第一次）。"
          u"0.10 成品 `84d09345…` 仍原样保留" % VOID,
          u"发布：成品 `release\\PotatoST-0.11.jar` = **`%s`**（%d B / %d 条目）。"
          u"⚠ **本轮同版本打了三次**（都是我自己撞出来的）：① `9fd7340f…` 沥青贴图还是原版那种 "
          u"**4 位调色板** PNG（TextureCheck 当场拦下）；② `2bf27d2c…` 贴图重编码成 8 位 RGBA 后重打；"
          u"③ 本版 —— 你 09-24 反馈「储罐ui和沥青槽挡住物品栏字样了」⇒ 整排上提 8 px。"
          u"作废链：`27787d5e…`(ZF77) → `9fd7340f…` → `2bf27d2c…`；"
          u"0.10 成品 `84d09345…` 始终原样保留" % (new, size, len(names)),
          u"§5 行：三次打包完整记录")

    patch(DOC,
          u"      这一版成品 = `__NEWSHA__`（同版本重打包 ⇒ 上一版 `2bf27d2c…` 作废）。",
          u"      这一版成品 = `%s`（%d B / %d 条目；同版本重打包 ⇒ 上一版 `2bf27d2c…` 作废）。"
          % (new, size, len(names)),
          u"§9 反馈记录填上真实哈希")

    print(u"\n失败项 = %d" % len(fails))
    for f in fails:
        print(u"  !! " + f)
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())
