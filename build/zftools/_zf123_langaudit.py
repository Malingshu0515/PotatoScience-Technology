# -*- coding: utf-8 -*-
u"""_zf123_langaudit.py —— 「某个物品名为什么显示英文？」的一站式体检（只读）

用户 ZF123 报的第二件事：「星璨钢貌似还只有英文名称了」。
这个脚本把"名字为什么不是中文"的**四种可能**逐条查一遍：

  ① **键在不在**：四份 lang 的键集合必须完全一致（少一份就是"切语言后看到原始 key"）；
  ② **值是不是英文**：zh_cn 的值与 en_us **完全相同** = 没翻译（白名单只有 `itemGroup.*` 这种商标名）；
  ③ **有没有重复键**：JSON 允许同名键，**后一个赢** ⇒ 手改/脚本插重复会静默把中文顶成英文；
  ④ **注册 id 有没有语言键**：把 `ITEMS.register("x")` / `BLOCKS.register("x")` 全部抓出来，
     逐个查 `item.potato_s_t.x` / `block.potato_s_t.x` —— 查不到就是"游戏里显示原始 key"。

跑法：
    python build\\zftools\\_zf123_langaudit.py            # 全量体检
    python build\\zftools\\_zf123_langaudit.py 星璨钢      # 只关心名字里含这个串的键
"""
import collections
import io
import json
import os
import re
import sys

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

ROOT = r"E:\PotatoST"
LANG = os.path.join(ROOT, r"src\main\resources\assets\potato_s_t\lang")
JAVA = os.path.join(ROOT, r"src\main\java\com\potatost\mod")
LOCALES = [u"zh_cn", u"en_us", u"ja_jp", u"ru_ru"]
# 允许"中文与英文一样"的键（商标 / 缩写）
SAME_OK = (u"itemGroup.potato_s_t",)

fails = []


def read(p):
    return io.open(p, encoding="utf-8").read()


def main(argv):
    want = argv[0] if argv else None
    data, texts = {}, {}
    for f in LOCALES:
        texts[f] = read(os.path.join(LANG, f + u".json"))
        data[f] = json.loads(texts[f])

    print(u"== 键数 ==")
    for f in LOCALES:
        print(u"  %-6s %d" % (f, len(data[f])))
    base = set(data[u"zh_cn"])
    for f in LOCALES:
        d = set(data[f]) ^ base
        if d:
            fails.append(u"%s 与 zh_cn 的键集合不同：%s" % (f, sorted(d)[:8]))
    print(u"  四份键集合：%s" % (u"完全一致" if not fails else u"**不一致**"))

    print(u"\n== ② 值是不是被写成英文（zh_cn == en_us）==")
    same = [k for k in data[u"zh_cn"] if data[u"zh_cn"][k] == data[u"en_us"][k]
            and not k.startswith(SAME_OK)]
    if same:
        for k in same:
            print(u"  !! %-52s %r" % (k, data[u"zh_cn"][k][:60]))
        fails.append(u"%d 个键的中文值等于英文值" % len(same))
    else:
        print(u"  没有（白名单里的商标键不算）")

    print(u"\n== ③ 重复键 ==")
    for f in LOCALES:
        keys = re.findall(r'^\s*"([^"]+)"\s*:', texts[f], re.M)
        dup = [k for k, n in collections.Counter(keys).items() if n > 1]
        if dup:
            print(u"  !! %s 有重复键：%s" % (f, dup[:6]))
            fails.append(u"%s 有重复键" % f)
        else:
            print(u"  %s：没有重复键（%d 行 == %d 键）" % (f, len(keys), len(data[f])))

    print(u"\n== ④ 注册 id 有没有语言键 ==")
    ids = set()
    for d, _s, fs in os.walk(JAVA):
        for fn in fs:
            if not fn.endswith(u".java"):
                continue
            t = read(os.path.join(d, fn))
            for m in re.finditer(r'(?:ITEMS|BLOCKS)\.register\(\s*"([a-z0-9_]+)"', t):
                ids.add(m.group(1))
    miss = [i for i in sorted(ids)
            if (u"item.potato_s_t." + i) not in base and (u"block.potato_s_t." + i) not in base]
    if miss:
        for i in miss:
            print(u"  !! %s（游戏里会显示原始 key）" % i)
        fails.append(u"%d 个注册 id 没有语言键" % len(miss))
    else:
        print(u"  注册 id %d 个，全部有语言键" % len(ids))

    if want:
        print(u"\n== 关键词「%s」相关的键 ==" % want)
        for k in sorted(base):
            v = data[u"zh_cn"][k]
            if want in v or want in k:
                print(u"  %-52s zh=%s" % (k, v[:60]))
                for f in LOCALES[1:]:
                    print(u"       %-6s %s" % (f, data[f][k][:60]))

    print(u"")
    print(u"通过 = %d   失败 = %d" % (len(LOCALES) * 3 + 1 - len(fails), len(fails)))
    for f in fails:
        print(u"  !! " + f)
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
