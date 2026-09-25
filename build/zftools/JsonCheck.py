# -*- coding: utf-8 -*-
"""JsonCheck.py —— 严格 JSON 语法校验（0.10 新增，作为 JsonCheck.java 的离线替代）

为什么要它：`JsonCheck.java` 依赖 Gson，而 Gson 只存在于 Gradle 的依赖缓存里；
本机离线构建时不一定能凑出 classpath（2026-09-18 实测 `gson*.jar` 已不在缓存中）。
Python 标准库的 `json` 同样是**真解析器**（不是 PowerShell 的 ConvertFrom-Json，
后者会把错误位置报得离谱，见档案 §4.5），且本机 python 常驻可用。

用法：
    python JsonCheck.py <文件或目录> [更多...]
目录会递归收集所有 *.json。发现非法 JSON 时以退出码 1 结束。
"""
import io
import json
import os
import sys


def iter_json(paths):
    for path in paths:
        if os.path.isdir(path):
            for root, _dirs, names in os.walk(path):
                for name in sorted(names):
                    if name.endswith(".json"):
                        yield os.path.join(root, name)
        else:
            yield path


def main(argv):
    total = 0
    bad = 0
    for path in iter_json(argv):
        total += 1
        try:
            with io.open(path, "r", encoding="utf-8") as handle:
                json.loads(handle.read())
        except Exception as exc:  # noqa: BLE001 - 就是要连位置一起报出来
            bad += 1
            print("  [FAIL] {0}\n         -> {1}".format(path, exc))
    print("检查 {0} 个 JSON 文件，非法 {1} 个".format(total, bad))
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
