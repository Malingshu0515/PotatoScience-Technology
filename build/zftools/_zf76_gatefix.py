# -*- coding: utf-8 -*-
u"""_zf76_gatefix.py —— 把 ZF75 的「3 倍」实现从"重复注入同一个特征"改成"再挂一份更密的放置特征"

⚠ 这是一次**真事故的修复**：用户新建世界卡在 0%。服务端复现 = 崩在区块生成：
    `java.lang.IllegalStateException: Feature order cycle found`
根因：同一个 placed feature 被注入到同一个 step **两次以上** ⇒ 原版 `FeatureSorter` 的顺序校验
建出自环、直接判定成环。⇒ 改成：基础 `mini_oilfield_placed`（chance 200，全主世界）
+ `mini_oilfield_placed_dense`（chance 100，只挂沙漠/恶地）⇒ 沙漠恶地合计 3/200 = **3 倍**，
且**没有任何重复特征**。本脚本把校验与文档对齐到这个方案，并加一条"禁止重复注入"的回归断言。
"""
import io
import sys

Z = r"E:\PotatoST\build\zftools"
VERIFY = Z + r"\_zf75_verify.py"
ARCH = r"E:\PotatoST\docs\开发档案.md"

OLD_A6 = u"""    for tag in (u"a", u"b"):
        extra = load(os.path.join(DATA, u"neoforge", u"biome_modifier",
                                  u"mini_oilfield_desert_%s.json" % tag))
        check(u"A6%s 沙漠/恶地额外注入器 %s（tag 形式，单值）" % (tag, tag),
              extra.get(u"biomes") == u"#potato_s_t:oilfield_dense"
              and extra.get(u"step") == u"lakes")"""
NEW_A6 = u"""    # ⚠ ZF76 修复：原来这里是"两份注入器重复注入同一个 placed feature" ⇒
    #   原版 FeatureSorter 报 `Feature order cycle found`，**新建世界直接崩**（用户报的卡 0%）。
    #   现在改成"再挂一份更密的放置特征"：基础 chance 200 + dense chance 100 ⇒ 沙漠恶地 3 倍，
    #   而且没有任何特征被重复注入。
    extra = load(os.path.join(DATA, u"neoforge", u"biome_modifier",
                              u"mini_oilfield_desert_a.json"))
    check(u"A6 沙漠/恶地追加注入器挂的是 dense 版本（tag 形式，单值）",
          extra.get(u"biomes") == u"#potato_s_t:oilfield_dense"
          and extra.get(u"step") == u"lakes"
          and extra.get(u"features") == [u"potato_s_t:mini_oilfield_placed_dense"])
    dense_pl = load(os.path.join(DATA, u"worldgen", u"placed_feature",
                                 u"mini_oilfield_placed_dense.json"))
    check(u"A6b dense 版放置参数与基础一致，只有 rarity 是 100（200 的一半 ⇒ 合计 3 倍）",
          dense_pl.get(u"feature") == u"potato_s_t:mini_oilfield"
          and dense_pl[u"placement"][0].get(u"chance") == 100
          and [m.get(u"type") for m in dense_pl.get(u"placement", [])]
          == [m.get(u"type") for m in pl.get(u"placement", [])])
    # 回归断言：我们注入的 placed feature 不许重复（重复 = Feature order cycle = 新建世界崩）
    injected = []
    for f in os.listdir(os.path.join(DATA, u"neoforge", u"biome_modifier")):
        if f.startswith(u"mini_oilfield"):
            injected.extend(load(os.path.join(DATA, u"neoforge", u"biome_modifier", f))
                            .get(u"features", []))
    check(u"A6c 注入特征没有重复（Feature order cycle 的根因）",
          len(injected) == len(set(injected)), u", ".join(injected))"""
NEW_A6 = NEW_A6.replace(u"\\n", u"\n")

OLD_DOC = u"另两份挂自定义标签 `#potato_s_t:oilfield_dense` ⇒ 探针实测**平原 1 份 / 沙漠 3 份 / 恶地 3 份**；"
NEW_DOC = (u"另一份挂自定义标签 `#potato_s_t:oilfield_dense`（= `#minecraft:is_badlands` + `minecraft:desert`）"
           u"并注入一份**更密的放置特征** `mini_oilfield_placed_dense`（rarity **100**）⇒ 沙漠/恶地合计 "
           u"3/200 = **3 倍**（⚠ 见 §9 的 ZF76 修复：**不能**靠「重复注入同一个特征」来做倍数）；")

OLD_S9_TAIL = u"      嫌多/嫌少改 `_zf75` 之后那个默认值或世界预设里的 `\"oil_chance\"`（三个预设都在）。"
NEW_S9_TAIL = OLD_S9_TAIL + u"""
- [x] **ZF76（事故修复）：新建世界卡在 0% —— 已修**。你反馈后我在服务端复现：新建 normal 世界崩在区块生成，
      报 `java.lang.IllegalStateException: Feature order cycle found`。
      **根因**：ZF75 我用"**把同一个 placed feature 注入两次**"来做沙漠/恶地 3 倍 ——
      原版 `FeatureSorter` 要按特征顺序做全局一致性校验，同一特征在一个 step 里出现两次会建出自环
      ⇒ 判定成"特征顺序成环"⇒ 区块生成直接抛异常（客户端表现就是**卡在 0%**）。
      **修法**：基础 `mini_oilfield_placed`（rarity 200，全主世界）+ `mini_oilfield_placed_dense`
      （rarity **100**，只挂沙漠/恶地）⇒ 合计 3/200 = 3 倍，**且没有任何重复注入**；
      校验里加了一条回归断言（`A6c`：注入特征不许重复）。
      **验证**：清了端口残留后端起新世界，`Preparing spawn area` 正常推到 51%+ 并继续（修复前直接在生成阶段崩）。"""


def main():
    fails = []
    t = io.open(VERIFY, "r", encoding="utf-8").read()
    if t.count(OLD_A6) != 1:
        fails.append(u"verify A6 锚点命中 %d 次" % t.count(OLD_A6))
    else:
        io.open(VERIFY, "w", encoding="utf-8", newline=u"\n").write(t.replace(OLD_A6, NEW_A6, 1))
        print(u"  [OK] _zf75_verify.py 改成 dense 方案 + 加禁止重复注入断言")
    a = io.open(ARCH, "r", encoding="utf-8").read()
    if a.count(OLD_DOC) != 1:
        fails.append(u"档案 §5 片段命中 %d 次" % a.count(OLD_DOC))
    else:
        a = a.replace(OLD_DOC, NEW_DOC, 1)
        print(u"  [OK] 档案 §5 行改成 dense 方案")
    if a.count(OLD_S9_TAIL) != 1:
        fails.append(u"档案 §9 尾锚点命中 %d 次" % a.count(OLD_S9_TAIL))
    else:
        a = a.replace(OLD_S9_TAIL, NEW_S9_TAIL, 1)
        print(u"  [OK] 档案 §9 记录 ZF76 事故修复")
        io.open(ARCH, "w", encoding="utf-8", newline=u"\n").write(a)
    print(u"失败项 = %d" % len(fails))
    for f in fails:
        print(u"  !! " + f)
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())
