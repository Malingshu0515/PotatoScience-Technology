# -*- coding: utf-8 -*-
u"""_zf78_republish2.py —— 第四次打包（倒油 + 控制器排查显示），并同步文档

本轮同版本打了四次（前三次见 §5 那行）：
  ① `9fd7340f…` 沥青贴图 4 位调色板被 TextureCheck 拦下
  ② `2bf27d2c…` 贴图重编码成 8 位 RGBA
  ③ `bafa7853…` 用户反馈"挡住物品栏字样" ⇒ 整排上提 8 px
  ④ 本版 —— 用户点名要的两件：**右键倒流体** + **右击控制器显示排查信息**

顺便把探针在这一轮抓到的**两个我自己的错**记进 §9（这是本轮最值得留的两条）：
  · 诊断的候选里有个"退化锚点"（塔底落在控制器自己那格）⇒ 距离 0 赢了真塔 ⇒ 加"跳过包含控制器的锚点"；
  · 探针自己"拆"的那一格按图纸本来就是空腔 ⇒ 假 FAIL（老毛病：先怀疑期望）。
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
VOID = "bafa7853364ae22ff8f1e5e2b62aad085ed40dbb"
fails = []


def sha1(p):
    return hashlib.sha1(open(p, "rb").read()).hexdigest()


def read(p):
    return io.open(p, encoding="utf-8").read()


def patch(path, old, new, label):
    t = read(path)
    hits = t.count(old)
    if hits != 1:
        fails.append(u"%s：锚点命中 %d 次（必须 1 次）" % (label, hits))
        return False
    io.open(path, "w", encoding="utf-8", newline=u"\n").write(t.replace(old, new, 1))
    print(u"  [OK]   %s" % label)
    return True


def main():
    old = sha1(DST) if os.path.exists(DST) else u"(缺)"
    if old != VOID:
        print(u"  [FAIL] 当前成品 %s 与预期要作废的 %s 不一致 ⇒ 不动任何文件" % (old, VOID))
        return 1
    if not os.path.exists(SRC):
        print(u"  [FAIL] 没有构建产物")
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
        print(u"  [FAIL] 新旧哈希相同")
        return 1
    shutil.copy2(SRC, DST)
    io.open(SHA, "w", encoding="ascii", newline=u"\n").write(new + u"\n")
    print(u"① 已发布 release\\PotatoST-0.11.jar = %s（%d B / %d 条目）"
          % (new, size, len(names)))

    patch(PUB, u'VOID = "%s"' % VOID, u'VOID = "%s"' % new, u"发布脚本 VOID 跟到最新")

    # §5 那行：三次 → 四次，并补上这两件功能
    patch(DOC,
          u"⚠ **本轮同版本打了三次**（都是我自己撞出来的）：① `9fd7340f…` 沥青贴图还是原版那种 "
          u"**4 位调色板** PNG（TextureCheck 当场拦下）；② `2bf27d2c…` 贴图重编码成 8 位 RGBA 后重打；"
          u"③ 本版 —— 你 09-24 反馈「储罐ui和沥青槽挡住物品栏字样了」⇒ 整排上提 8 px。"
          u"作废链：`27787d5e…`(ZF77) → `9fd7340f…` → `2bf27d2c…`；"
          u"0.10 成品 `84d09345…` 始终原样保留" % VOID,
          u"⚠ **本轮同版本打了四次**：① `9fd7340f…` 沥青贴图还是原版那种 **4 位调色板** PNG"
          u"（TextureCheck 当场拦下）；② `2bf27d2c…` 贴图重编码成 8 位 RGBA 后重打；"
          u"③ `bafa7853…` 你 09-24 反馈「储罐ui和沥青槽挡住物品栏字样了」⇒ 整排上提 8 px；"
          u"④ **本版** —— 你点名的两件：**右键容器倒流体进石油罐**（`pourFrom`，1000 mB/次、"
          u"罐余量不足就倒多少算多少、倒不进/空容器都有提示）与**右击控制器显示排查信息**"
          u"（数到几座 / 最像的一处第几层第几排第几列应该是什么实际是什么）。"
          u"作废链：`27787d5e…`(ZF77) → `9fd7340f…` → `2bf27d2c…` → `bafa7853…`；"
          u"0.10 成品 `84d09345…` 始终原样保留",
          u"§5 行：四次打包 + 两件新功能")

    patch(DOC,
          u"      这一版成品 = `bafa7853364ae22ff8f1e5e2b62aad085ed40dbb`（2,274,791 B / 771 条目；"
          u"同版本重打包 ⇒ 上一版 `2bf27d2c…` 作废）。",
          u"      第三次打包 = `bafa7853…`（上提 8 px），**第四次（当前成品）= `%s`**"
          u"（%d B / %d 条目）—— 就是你点名的两件：" % (new, size, len(names)) + u"""
      ① **右键容器倒流体**：手上拿油桶（或任何流体容器）右键操作器 ⇒ 往**石油罐**倒 1000 mB/次
      （罐里余量不足 1000 就倒多少算多少；罐满 / 流体不对 ⇒ 一滴不倒、容器内容物一点不丢；
      空容器会提示"手里的容器是空的"）。逻辑抽成 `DistillationOperatorBlock.pourFrom`（纯函数），
      探针在没有玩家的服务端上直接验它（§4.43 那课：不碰玩家对象）。
      ② **右击控制器显示排查信息**：数到塔 ⇒ 报「检测到 N 座分馏塔（最多认 4 座）」；
      一座都没数到 ⇒ 报**最像的那一处**的第一处不符：第几层第几排第几列 + 坐标 + 应该是什么 +
      实际是什么 + 112 格里错了几格（`DistillationTowerStructure.diagnose`）。
      **探针在这轮抓到两个我自己的错**：㈠ 诊断的候选里有个「退化锚点」——塔底正好落在**控制器自己那格**
      （1 格不符 + 距离 0）⇒ 把真正只差一格的塔挤掉了；修法是"跳过包围盒里装着控制器的锚点"
      （控制器是实心方块，塔里不可能有它 ⇒ 这条跳过永远安全），并给判分加了第二判据
      "第一处不符越靠后越像"；㈡ 我探针里"拆"的那一格按图纸本来就是**空腔**（第 4 层 `2..2`）
      ⇒ 等于没拆、假 FAIL（老毛病：先怀疑期望）。探针 **125 项全 [OK]**。""",
          u"§9 反馈条目：两件新功能 + 两个自捉 bug")

    print(u"\n失败项 = %d" % len(fails))
    for f in fails:
        print(u"  !! " + f)
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())
