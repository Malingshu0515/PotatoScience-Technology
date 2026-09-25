# -*- coding: utf-8 -*-
"""ModelCheck.py —— 模型 / 贴图引用是否都能解析（0.10 ZF15 新增）

**为什么需要它**：这类错误**编译不报、加载不报、启动日志也不报** ——
游戏里只是那个物品变成紫黑格或者干脆透明。跟 §4.14 的"吞产物"同一性质：
**没有任何机制会替你发现**，只能机械查。已经踩过的同类：配方标签打错一个字母（§6.6.2）。

查四件事：
  ① 每个**注册过的物品 id** 都要有 `models/item/<id>.json`（漏了 = 物品隐形）
  ② 每个模型（沿 `parent` 链一直到原版）声明的贴图都要有对应 `.png`
     （本项目 → `src/main/resources/assets/...`；原版 → `client.jar`）
  ③ 每个 `blockstates/*.json` 引用的模型要存在
  ④ 反向：**没有任何模型引用的孤儿贴图**（只报 WARN，可能是有意留的）

跑法：
    python build/zftools/ModelCheck.py
    python build/zftools/ModelCheck.py --quiet     # 只打印问题

退出码：有 FAIL 项 → 1
"""
import io
import json
import os
import re
import sys
import zipfile

PROJ = "E:\\PotatoST"
ASSETS = os.path.join(PROJ, "src", "main", "resources", "assets", "potato_s_t")
JAVA_DIR = os.path.join(PROJ, "src", "main", "java", "com", "potatost", "mod")
VANILLA_JAR = r"E:\gradle-home\caches\minecraft\versions\1.21.1\client.jar"
MODID = "potato_s_t"


def read_json(path):
    with io.open(path, "r", encoding="utf-8") as fh:
        return json.load(fh)


class Vanilla:
    """原版 client.jar 里的模型与贴图（只读，懒加载）。"""

    def __init__(self, path):
        self.zip = zipfile.ZipFile(path) if os.path.isfile(path) else None
        self.names = set(self.zip.namelist()) if self.zip else set()

    def model(self, rel):
        """rel 形如 'item/generated'；返回解析后的 dict 或 None。"""
        entry = "assets/minecraft/models/{0}.json".format(rel)
        if entry not in self.names:
            return None
        return json.loads(self.zip.read(entry).decode("utf-8"))

    def has_texture(self, rel):
        return "assets/minecraft/textures/{0}.png".format(rel) in self.names


def java_files():
    """递归列出所有 Java 源文件（含 client/ sound/ menu/ 等子包）。"""
    for root, _d, files in os.walk(JAVA_DIR):
        for f in files:
            if f.endswith(".java"):
                yield os.path.join(root, f)


def collect_item_ids():
    """从 Java 源码里抠出注册的物品 id。

    覆盖三种写法：`ITEMS.register("x"` / `ORE_ITEMS.register("x"` / `raw("x")` / `ore("x",`。
    这是**文本抠取**，不是解析 Java —— 只用它做"模型文件在不在"的交叉核对，宁可多报几个也不漏。
    """
    ids = set()
    patterns = [
        re.compile(r'\bITEMS\.register\(\s*"([a-z0-9_]+)"'),
        re.compile(r'\bORE_ITEMS\.register\(\s*"([a-z0-9_]+)"'),
        re.compile(r'\braw\(\s*"([a-z0-9_]+)"'),
        re.compile(r'\bore\(\s*"([a-z0-9_]+)"'),
    ]
    for path in java_files():
        text = io.open(path, "r", encoding="utf-8").read()
        for pat in patterns:
            for m in pat.finditer(text):
                ids.add(m.group(1))
    return ids


# 有些贴图**模型里根本没有**，是 Java 直接引用的：流体（still/flow）走 ModFluids，
# 发电机的实体渲染走 GeneratorRenderer / GeneratorItemRenderer。
# 不把这类算进来，孤儿贴图检查就会误报（本工具第一版就报了 8 个假阳性）。
JAVA_TEXTURE_PATTERNS = [
    re.compile(r'"textures/((?:block|item|fluid)/[a-z0-9_/]+)\.png"'),
    re.compile(r'"((?:block|item|fluid)/[a-z0-9_/]+)"'),
]

# 【0.11 ZF106 补】盔甲层贴图是**第四种**"模型里没有"的贴图：
# 它由 `ArmorMaterial.Layer(ResourceLocation)` 按**命名约定**读，路径是
#   textures/models/armor/<资源名>_layer_1.png（外层，头/胸/靴）
#   textures/models/armor/<资源名>_layer_2.png（内层，护腿）
# 名字在 Java 里以**裸字符串**出现（`fromNamespaceAndPath(MODID, "titanium_alloy")`），
# 所以上面那两条 `(block|item|fluid)/` 的正则一条都匹配不到 ⇒ 4 张全被误报成孤儿。
# ⚠ 这里**不做名字匹配**（那要靠语义猜），只认"这个 Java 文件里出现过 /models/armor"这一件事：
#   本工程只有 `ModArmorMaterials` 会拼这个路径，它一旦出现就说明盔甲层贴图是被代码读的。
ARMOR_LAYER_LAYER = os.path.join("textures", "models", "armor")
ARMOR_LAYER_REL = "models/armor"          # 与孤儿检查那一侧的键形状对齐（它去掉了 textures/ 前缀）


def collect_armor_layer_textures():
    """凡 Java 源码里出现 `models/armor` 的，就把该目录下所有贴图视为"被 Java 引用"。"""
    hits = set()
    marker = "models/armor"
    for path in java_files():
        text = io.open(path, "r", encoding="utf-8").read()
        if marker not in text:
            continue
        d = os.path.join(ASSETS, ARMOR_LAYER_LAYER)
        if not os.path.isdir(d):
            continue
        for f in os.listdir(d):
            if f.endswith(".png"):
                # ⚠ 键的形状必须与孤儿检查那一侧一致：`<modid>:<去 textures/ 前缀、去 .png 的相对路径>`
                #   （踩过两次：第一版多留 `.png`、第二版多留 `textures/`，两次这 4 张都照报孤儿。
                #    与 §4.71 同款教训 —— **判据的形状要对齐**，不是"逻辑写对了"就行。）
                hits.add("{0}:{1}/{2}".format(MODID, ARMOR_LAYER_REL, f[:-4]))
    return hits


def collect_java_textures():
    """Java 源码里直接引用的贴图路径（去掉 textures/ 前缀与 .png）。"""
    found = set()
    for path in java_files():
        text = io.open(path, "r", encoding="utf-8").read()
        for pat in JAVA_TEXTURE_PATTERNS:
            for m in pat.finditer(text):
                found.add("{0}:{1}".format(MODID, m.group(1)))
    return found


# 同样地，**OBJ 模型的贴图也不走模型 JSON**：它写在 `.mtl` 的 `map_Kd` 里。
# 0.10 ZF39 的电力高炉就是这种 —— 不把 `.mtl` 算进来，那张贴图会被误报成孤儿。
MTL_PATTERN = re.compile(r'^\s*map_Kd\s+(\S+)\s*$', re.MULTILINE)


def collect_mtl_textures():
    """扫 assets/<modid>/models 下所有 .mtl，把 map_Kd 指的贴图算成"被引用"。"""
    found = set()
    models_dir = os.path.join(PROJ, "src", "main", "resources", "assets", MODID, "models")
    for root, _d, files in os.walk(models_dir):
        for f in files:
            if not f.endswith(".mtl"):
                continue
            text = io.open(os.path.join(root, f), "r", encoding="utf-8").read()
            for m in MTL_PATTERN.finditer(text):
                found.add(m.group(1))       # 已经是 "potato_s_t:block/xxx" 形式
    return found


def main(argv):
    quiet = "--quiet" in argv
    fails, warns = [], []

    # ---------- 装载我们的模型 ----------
    our_models = {}
    models_root = os.path.join(ASSETS, "models")
    for root, _d, files in os.walk(models_root):
        for f in files:
            if not f.endswith(".json"):
                continue
            full = os.path.join(root, f)
            rel = os.path.relpath(full, models_root).replace(os.sep, "/")[:-5]
            our_models[rel] = read_json(full)

    vanilla = Vanilla(VANILLA_JAR)
    if vanilla.zip is None:
        warns.append("找不到原版 client.jar（{0}），原版父模型/贴图无法核对".format(VANILLA_JAR))

    used_textures = set()

    def resolve_textures(rel, seen):
        """沿 parent 链收集贴图（子覆盖父），返回 {槽位: 值}。"""
        if rel in seen:
            return {}
        seen.add(rel)
        out = {}
        model = our_models.get(rel)
        if rel.startswith("minecraft:"):
            model = vanilla.model(rel.split(":", 1)[1])
        if model is None:
            return None
        parent = model.get("parent")
        if parent:
            pres = parent
            if ":" not in pres:
                pres = "minecraft:" + pres
            if pres.startswith("minecraft:"):
                ptext = resolve_textures(pres, seen)
            else:
                ptext = resolve_textures(pres.split(":", 1)[1], seen)
            if ptext:
                out.update(ptext)
        out.update(model.get("textures", {}))
        return out

    # ---------- ② 贴图引用 ----------
    if not quiet:
        print("== ② 模型贴图引用 ==")
    for rel in sorted(our_models):
        full_ref = "{0}:{1}".format(MODID, rel)
        collected = resolve_textures(rel, set())
        if collected is None:
            fails.append("models/{0}.json 的 parent 链断了（找不到某个父模型）".format(rel))
            continue
        for slot, value in collected.items():
            if value.startswith("#"):
                continue                      # 槽位变量引用，不是文件路径
            used_textures.add(value)
            ns, _, path = value.partition(":")
            if not path:
                ns, path = "minecraft", ns
            if ns == MODID:
                if not os.path.isfile(os.path.join(ASSETS, "textures", path + ".png")):
                    fails.append("models/{0}.json 的 {1}=\"{2}\" 找不到贴图文件 textures/{3}.png".format(
                        rel, slot, value, path))
            elif ns == "minecraft":
                if not vanilla.has_texture(path):
                    fails.append("models/{0}.json 的 {1}=\"{2}\" 在原版 client.jar 里没有".format(
                        rel, slot, value))
            else:
                warns.append("models/{0}.json 引用了别的命名空间的贴图 {1}".format(rel, value))

    # ---------- ③ blockstates ----------
    if not quiet:
        print("== ③ blockstates 模型引用 ==")
    bs_root = os.path.join(ASSETS, "blockstates")
    bs_count = 0
    for f in sorted(os.listdir(bs_root)):
        if not f.endswith(".json"):
            continue
        bs_count += 1
        data = read_json(os.path.join(bs_root, f))
        refs = []

        def walk(node):
            if isinstance(node, dict):
                if "model" in node and isinstance(node["model"], str):
                    refs.append(node["model"])
                for v in node.values():
                    walk(v)
            elif isinstance(node, list):
                for v in node:
                    walk(v)

        walk(data)
        if not refs:
            warns.append("blockstates/{0} 里没有任何 model 引用".format(f))
        for r in refs:
            ns, _, path = r.partition(":")
            if not path:
                ns, path = "minecraft", ns
            if ns == MODID:
                if path not in our_models:
                    fails.append("blockstates/{0} 引用的模型 {1} 不存在".format(f, r))
            elif ns == "minecraft":
                if vanilla.model(path) is None:
                    fails.append("blockstates/{0} 引用的原版模型 {1} 不存在".format(f, r))

    # ---------- ① 物品 id -> 模型文件 ----------
    if not quiet:
        print("== ① 注册物品 -> models/item/<id>.json ==")
    ids = collect_item_ids()
    missing_models = []
    for i in sorted(ids):
        if not os.path.isfile(os.path.join(models_root, "item", i + ".json")):
            missing_models.append(i)
    for i in missing_models:
        fails.append("物品 {0} 没有 models/item/{0}.json（游戏里会是隐形/紫黑格）".format(i))

    # ---------- ④ 孤儿贴图 ----------
    if not quiet:
        print("== ④ 孤儿贴图（模型 + Java + .mtl 都没引用，只报 WARN）==")
    java_tex = collect_java_textures()
    used_textures |= java_tex
    if not quiet:
        print("  其中由 Java 直接引用（模型里没有）的贴图 {0} 个".format(len(java_tex)))
    mtl_tex = collect_mtl_textures()
    used_textures |= mtl_tex
    if not quiet:
        print("  其中由 .mtl 的 map_Kd 引用（OBJ 模型）的贴图 {0} 个".format(len(mtl_tex)))
    armor_tex = collect_armor_layer_textures()
    used_textures |= armor_tex
    if not quiet:
        print("  其中由 ArmorMaterial.Layer 按命名约定引用（盔甲层）的贴图 {0} 个".format(len(armor_tex)))
    tex_root = os.path.join(ASSETS, "textures")
    orphans = []
    for root, _d, files in os.walk(tex_root):
        for f in files:
            if not f.endswith(".png"):
                continue
            rel = os.path.relpath(os.path.join(root, f), tex_root).replace(os.sep, "/")[:-4]
            if "{0}:{1}".format(MODID, rel) not in used_textures:
                orphans.append(rel)
    for o in sorted(orphans):
        warns.append("贴图 textures/{0}.png 没有任何模型引用".format(o))

    # ---------- 汇总 ----------
    print("")
    print("---- 汇总 ----")
    print("  模型 {0} 个 / blockstate {1} 个 / 注册物品 {2} 个 / 贴图 {3} 个".format(
        len(our_models), bs_count, len(ids),
        sum(1 for r, _d, fs in os.walk(tex_root) for f in fs if f.endswith(".png"))))
    if not quiet:
        print("  被引用的贴图 {0} 个".format(len(used_textures)))
    for w in warns:
        print("  [WARN] " + w)
    for f_ in fails:
        print("  [FAIL] " + f_)
    print("")
    print("失败项 = {0}   提示项 = {1}".format(len(fails), len(warns)))
    print("结论: " + ("通过" if not fails else "有失败项，必须修"))
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
