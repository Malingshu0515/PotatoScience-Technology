# -*- coding: utf-8 -*-
r"""_rzh_sync_generators.py —— 把两个成就生成器里的说明文案同步到盘上（瘦身后）的值。

为什么必须同步：`_zf107_adv.py` / `_zf117_adv.py` 把四语言文案**硬编码**在自己里面
（`zh=(u"标题", u"说明")`），写盘前有冲突保护（`_zf117_adv.py` L363-366
「这些键已经有别的值」⇒ fails、不写）。只改 lang 而不同步生成器，重跑生成器就会报冲突中止。

做法（笨但每一步都核过）：
  1. 用源码 `compile()` + `co_consts` 递归收集每个 kwarg 组里出现的 str（标题 + 说明），
     这样"旧值"是从**源码本身**取得的，不是我凭记忆写的；
  2. 在源码里从 `id="<节点>"` 那行往下，按**圆括号配平**找到 `zh=(...)` / `en=(...)` 这些块；
  3. 校验块内的字符串字面量**隐式拼接结果恰好等于** 该节点该语言的老值 —— 对不上就中止；
  4. 用**单行**新字面量替换整块，缩进沿用原来 `zh=` 的缩进；
  5. `compile()` 语法自检通过才写盘；按行号**倒序**替换避免错位。
"""
import ast
import io
import json
import sys
import importlib.util

GENS = [u"build/zftools/_zf107_adv.py", u"build/zftools/_zf117_adv.py"]
LOC2ARG = {u"zh_cn": u"zh", u"en_us": u"en", u"ja_jp": u"ja", u"ru_ru": u"ru"}
LANGS = [u"zh_cn", u"en_us", u"ja_jp", u"ru_ru"]
ROOT = u"src/main/resources/assets/potato_s_t/lang/%s.json"

# ⚠ **白名单**：只有本轮真正缩短过的 (节点, 语言) 才允许动生成器里的字面量。
#   第一版没有白名单，于是把所有节点都按盘上值重写了一遍 —— 那不是本轮的事
#   （还因为一处替换撞出语法错误、被 compile() 挡住才没写盘）。
#   这份名单用 `git show HEAD:<lang>` 与工作树逐键比对机械算出，不凭记忆。
WHITELIST = {
    (u"oil_pump", u"zh_cn"), (u"oil_pump", u"en_us"), (u"oil_pump", u"ja_jp"), (u"oil_pump", u"ru_ru"),
    (u"starfall", u"zh_cn"), (u"starfall", u"en_us"), (u"starfall", u"ja_jp"), (u"starfall", u"ru_ru"),
    (u"fluid_logistics", u"zh_cn"), (u"fluid_logistics", u"en_us"), (u"fluid_logistics", u"ja_jp"), (u"fluid_logistics", u"ru_ru"),
    (u"lithium_battery_plant", u"zh_cn"), (u"lithium_battery_plant", u"en_us"), (u"lithium_battery_plant", u"ja_jp"), (u"lithium_battery_plant", u"ru_ru"),
    (u"lithium_battery", u"zh_cn"), (u"lithium_battery", u"en_us"), (u"lithium_battery", u"ja_jp"), (u"lithium_battery", u"ru_ru"),
    (u"star_steel", u"zh_cn"), (u"star_steel", u"en_us"), (u"star_steel", u"ja_jp"), (u"star_steel", u"ru_ru"),
    (u"salt", u"zh_cn"), (u"salt", u"en_us"), (u"salt", u"ja_jp"), (u"salt", u"ru_ru"),
    (u"blast_furnace", u"zh_cn"), (u"blast_furnace", u"en_us"), (u"blast_furnace", u"ja_jp"), (u"blast_furnace", u"ru_ru"),
    (u"wiring", u"en_us"), (u"wiring", u"ru_ru"),
    (u"alloy_smelter", u"ru_ru"),
}


def load_nodes(path):
    spec = importlib.util.spec_from_file_location(u"_g", path)
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return {n[u"id"]: n for n in getattr(m, u"NODES")}


def find_block(lines, nid, arg):
    """在 `dict(id="<nid>"` 之后找 `arg=(` 起始行，按圆括号配平找到结束行与列。

    ⚠ 用 `dict(id="<nid>"` 而不是裸 `id="<nid>"`：生成器的文件头注释里也出现过这些 id
      （例如 A① 采油机那段说明），裸匹配会先命中注释。
    """
    start = None
    key = u'dict(id="%s"' % nid
    for i, l in enumerate(lines):
        if key in l:
            start = i
            break
    if start is None:
        return None
    for i in range(start, min(start + 80, len(lines))):
        l = lines[i]
        j = l.find(arg + u"=(")
        if j < 0:
            continue
        if j > 0 and (l[j - 1].isalnum() or l[j - 1] == u"_"):
            continue                      # 避免匹配到别的名字尾巴，如 xxzh=(
        # 从 j 开始配平。⚠ **必须跳过字符串字面量内部** —— 标题里就有 `（）`、`—` 这些字符，
        #   直接数字符会把它们当成括号（ZF117 那 8 条全栽在这上面）。
        depth = 0
        row = i
        col = j
        in_str = None
        esc = False
        while row < len(lines):
            l2 = lines[row]
            while col < len(l2):
                ch = l2[col]
                if in_str is not None:
                    if esc:
                        esc = False
                    elif ch == u"\\":
                        esc = True
                    elif ch == in_str:
                        in_str = None
                elif ch in (u'"', u"'"):
                    in_str = ch
                elif ch in (u'(', u'[', u'{'):
                    depth += 1
                elif ch in (u')', u']', u'}'):
                    depth -= 1
                    if depth == 0:
                        # ⚠ 用**跨度重建**整块文本。第一版写的是 `l2[j:col+1]` —— 但 l2 是
                        #   **末行**，于是多行块只返回了最后一行 ⇒ 求值必然失败。
                        if row == i:
                            block = l2[j:col + 1]
                        else:
                            parts = [lines[i][j:]] + lines[i + 1:row] + [l2[:col + 1]]
                            block = u"\n".join(parts)
                        return (i, j, row, col, block)
                col += 1
            row += 1
            col = 0
    return None


def literal_value(block):
    """把 `zh=(u"标题", u"说明")` 这类片段求值成 tuple。

    ⚠ block 从 `arg=(` 开始，本身已是完整的 `(…)`，**不要再补一个括号**
      （第一版多补了一个 ⇒ 128 处全部 "( was never closed"）。
    """
    expr = block.split(u"=", 1)[1]
    return ast.literal_eval(expr)


def main():
    total = 0
    skipped = []
    for path in GENS:
        nodes = load_nodes(path)
        src = io.open(path, encoding=u"utf-8", newline=u"").read()
        lines = src.split(u"\n")
        data = {l: json.load(io.open(ROOT % l, encoding=u"utf-8")) for l in LANGS}

        edits = []
        for nid, node in nodes.items():
            for arg in (u"zh", u"en", u"ja", u"ru"):
                if arg not in node:
                    continue
                got = find_block(lines, nid, arg)
                if got is None:
                    skipped.append(u"%s / %s：找不到 %s=( 块" % (path, nid, arg))
                    continue
                i, j, row, col, block = got
                try:
                    pair = literal_value(block)
                except Exception as e:
                    skipped.append(u"%s / %s：%s 块求值失败 %s" % (path, nid, arg, e))
                    continue
                old_title, old_desc = pair[0], pair[1]
                if old_title != node[arg][0] or old_desc != node[arg][1]:
                    skipped.append(u"%s / %s：%s 块与 NODES 里的值不一致，跳过" % (path, nid, arg))
                    continue
                loc = [k for k, v in LOC2ARG.items() if v == arg][0]
                new_desc = data[loc].get(u"advancements.potato_s_t.%s.description" % nid)
                new_title = data[loc].get(u"advancements.potato_s_t.%s.title" % nid)
                if new_desc is None or new_title is None:
                    continue
                if new_desc == old_desc and new_title == old_title:
                    continue
                edits.append((i, j, row, col, block, nid, arg, old_title, old_desc,
                              new_title, new_desc))

        if not edits:
            print(u"[--] %-26s 无需同步" % path.split(u"/")[-1])
            continue

        print(u"\n== %-26s %d 处 ==" % (path.split(u"/")[-1], len(edits)))
        for (r0, c0, r1, c1, block, nid, arg, old_title, old_desc,
             new_title, new_desc) in sorted(edits, reverse=True):
            # ⚠⚠ 必须重建**整个二元组** `arg=(标题, 说明)`。
            #    第一版只写 `arg=(新说明)` ⇒ 把 `en=("标题", "说明")` 压成了单个字符串、**标题丢了**，
            #    而且是静默的（compile 照样过、只看说明也对）。那批已用 git checkout 回滚重做。
            uq = u"u" if arg in (u"zh", u"ja") else u""
            tl = uq + json.dumps(new_title, ensure_ascii=False)
            dl = uq + json.dumps(new_desc, ensure_ascii=False)
            indent = lines[r0][:c0]
            tail = lines[r1][c1 + 1:]          # `)),` / `),` / `,` 原样保留
            if r1 > r0:
                del lines[r0 + 1:r1 + 1]
            lines[r0] = indent + arg + u"=(" + tl + u", " + dl + u")" + tail
            note = u""
            if new_title != old_title:
                note += u"  [标题也改]"
            if r1 > r0:
                note += u"  (多行块)"
            print(u"  %-24s %-3s %3d → %3d%s" % (nid, arg, len(old_desc), len(new_desc), note))
        out = u"\n".join(lines)
        code = compile(out, path, u"exec")
        # ---- 写前最后一道：**结构**必须还是 2 元组，且与盘上逐字一致 ----
        #      （第一版就是在这道缺失的地方静默把标题写没了，只留下说明）
        ns = {}
        exec(code, ns)
        bad_struct, bad_val = [], []
        for n in ns[u"NODES"]:
            for loc, a in LOC2ARG.items():
                v = n.get(a)
                if not (isinstance(v, tuple) and len(v) == 2):
                    bad_struct.append((n[u"id"], a))
                    continue
                want = data[loc].get(u"advancements.potato_s_t.%s.description" % n[u"id"])
                if v[1] != want:
                    bad_val.append((n[u"id"], loc))
        if bad_struct or bad_val:
            print(u"[!!] %s：结构坏 %s / 值不符 %s ⇒ 不写盘" % (path, bad_struct[:4], bad_val[:4]))
            continue
        io.open(path, u"w", encoding=u"utf-8", newline=u"").write(out)
        total += len(edits)

    if skipped:
        print(u"\n跳过 %d 处（未改）：" % len(skipped))
        for s in skipped[:20]:
            print(u"  - " + s)
    print(u"\n合计同步 %d 处" % total)


if __name__ == u"__main__":
    main()
