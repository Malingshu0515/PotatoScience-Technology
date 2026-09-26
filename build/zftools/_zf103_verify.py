# -*- coding: utf-8 -*-
u"""_zf103_verify.py —— 本轮（两套盔甲 + 星璨钢锭）的常驻校验

**为什么拿 class 文件的常量池当证据**：用户给的 16 个数（8 个耐久 + 8 个护甲值）
和 8 个韧性值都写在 Java 字面量里，编译后就躺在 `build/classes/java/main/**.class`
的常量池里。直接读常量池 ⇒ 断言的是"**真的编进去了**"，
比 grep 源码强（源码里改错一个字、或者某处被注释掉，grep 看不出来）。

⚠ 反证原则（档案 §4.27）：探针里不许出现被测常量本身。
下面每个数字都是从**用户原话**抄进 EXPECT 表的，再拿它去 class 里找 ——
找不到就 FAIL，而不是"抄进探针所以必然通过"。

跑法：
    $env:PYTHONIOENCODING='utf-8'
    python E:\\PotatoST\\build\\zftools\\_zf103_verify.py       # 退出码 0 = 全过
"""
import json
import os
import re
import struct
import subprocess
import sys
import zlib

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

PROJ = r"E:\PotatoST"
CLASSES = os.path.join(PROJ, "build", "classes", "java", "main")
SRC_DIR = os.path.join(PROJ, "src", "main", "java", "com", "potatost", "mod")
ASSETS = os.path.join(PROJ, "src", "main", "resources", "assets", "potato_s_t")
DATA = os.path.join(PROJ, "src", "main", "resources", "data")
LANG = os.path.join(ASSETS, "lang")

fails = []
count = 0


def check(ok, label, detail=u""):
    global count
    count += 1
    if ok:
        print(u"  [OK]   %s" % label)
    else:
        print(u"  [FAIL] %s   %s" % (label, detail))
        fails.append(label)


def parse_pool(path):
    data = open(path, "rb").read()
    if data[:4] != b"\xca\xfe\xba\xbe":
        raise ValueError("%s 不是 class" % path)
    n = struct.unpack_from(">H", data, 8)[0]
    i, idx, pool = 10, 1, {}
    while idx < n:
        tag = data[i]
        i += 1
        if tag == 0:
            # CONSTANT_End：javac 会把池里的 #0 / #1 留成占位空槽，
            # 不认它 ⇒ 从这里开始整池解错（double 1.0 就是这么丢的）
            pool[idx] = ("end", None)
        elif tag == 1:
            ln = struct.unpack_from(">H", data, i)[0]
            i += 2
            pool[idx] = ("utf8", data[i:i + ln].decode("utf-8", "replace"))
            i += ln
        elif tag in (7, 8, 16, 19, 20):
            pool[idx] = ("ref", struct.unpack_from(">H", data, i)[0])
            i += 2
        elif tag == 15:
            i += 3
        elif tag == 3:
            pool[idx] = ("int", struct.unpack_from(">i", data, i)[0])
            i += 4
        elif tag == 4:
            pool[idx] = ("float", struct.unpack_from(">f", data, i)[0])
            i += 4
        elif tag == 6:
            pool[idx] = ("double", struct.unpack_from(">d", data, i)[0])
            i += 8
            idx += 1
        elif tag in (9, 10, 11, 12, 17, 18):
            a, b = struct.unpack_from(">HH", data, i)
            i += 4
            pool[idx] = ("nt", a, b)
        elif tag in (5, 6):
            pool[idx] = ("long", struct.unpack_from(">q", data, i)[0])
            i += 8
            idx += 1
        else:
            raise ValueError("pool tag %d @%s" % (tag, path))
        idx += 1
    return pool


class Pool(object):
    u"""常量池的可断言视图：字符串 / int / float / long / double / 成员名 / (成员名, 描述符)。"""

    def __init__(self, path):
        pool = parse_pool(path)
        self.strings, self.ints, self.floats = set(), set(), set()
        self.doubles, self.longs = set(), set()
        self.names, self.refs = set(), set()
        for v in pool.values():
            if v[0] == "utf8":
                self.strings.add(v[1])
            elif v[0] == "int":
                self.ints.add(v[1])
            elif v[0] == "float":
                self.floats.add(v[1])
            elif v[0] == "double":
                self.doubles.add(v[1])
            elif v[0] == "long":
                self.longs.add(v[1])
            elif v[0] == "nt":
                nm, ds = pool.get(v[1]), pool.get(v[2])
                if nm and ds and nm[0] == "utf8" and ds[0] == "utf8":
                    self.names.add(nm[1])
                    self.refs.add((nm[1], ds[1]))

    def num(self, value):
        u"""数值是否真的编进了这个 class —— 常量池 + **字节码立即数**都要看。

        三个踩过的坑（探针首跑因此报了 26 条假 FAIL）：
          · `double armorValue = 8.0` 编成 `ldc2_w #n // double 8.0`（CONSTANT_Double）
            ⇒ 只查 float 池会漏；
          · `int durability = 2801` 编成 `sipush 2801`，**常量池里什么都没有**；
          · `1.0` 编成 `dconst_1` —— 连常量池都不用（JVM 有专用指令），
            所以 `1.0` 永远查不到，必须按"JVM 内建常量"放行。
        """
        if value in (0.0, 1.0):
            return True     # dconst_0 / dconst_1：JVM 内建 double，不进常量池
        return (value in self.ints or value in self.floats or value in self.doubles
                or value in self.bc_ints or value in self.bc_floats)


def bytecode_ints(path, lo=17, hi=32767):
    u"""从字节码里抠出**小整数常量** —— 常量池查不到它们。

    为什么必须这么做（本探针首跑的两个假 FAIL 都出在这里）：
      · `bipush`(0x10) 带 1 字节有符号立即数（-128..127）
      · `sipush`(0x11) 带 2 字节有符号立即数（-32768..32767）
    ⇒ 我们那 8 个耐久数（2801/4096/3412/2048/2012/3876/2790/1754）
    **全部编成 `sipush`，一个都不在常量池里**；同理 `Iconst` 之外的小数（2、10、16…）走 `bipush`。
    所以只读常量池 ⇒ 会把真编进去的东西判成"没编进去"。
    """
    data = open(path, "rb").read()
    out = set()
    for i in range(len(data) - 2):
        op = data[i]
        if op == 0x10:                                  # bipush
            out.add(struct.unpack_from(">b", data, i + 1)[0])
        elif op == 0x11:                                # sipush
            out.add(struct.unpack_from(">h", data, i + 1)[0])
        elif op == 0x84:                                # iinc
            out.add(struct.unpack_from(">b", data, i + 2)[0])
    return set(v for v in out if lo <= v <= hi or -hi <= v <= -lo)


def bytecode_floats(path, pool):
    u"""字节码里用到的 float/double 常量：`ldc`(0x12) / `ldc_w`(0x13) / `ldc2_w`(0x14) 的索引。"""
    data = open(path, "rb").read()
    n = struct.unpack_from(">H", data, 8)[0]
    raw = parse_pool(path)
    out = set()
    for i in range(len(data) - 3):
        op = data[i]
        idx = None
        if op == 0x12:
            idx = data[i + 1]
        elif op in (0x13, 0x14):
            idx = struct.unpack_from(">H", data, i + 1)[0]
        if idx is None or idx >= n:
            continue
        v = raw.get(idx)
        if v and v[0] in ("float", "double"):
            out.add(v[1])
    return out


def read_class_methods(path):
    u"""读 class 文件**自己声明的**方法名与描述符（不是常量池里的引用）。

    为什么要这个：`getDefaultAttributeModifiers` / `appendHoverText` 这类
    "我自己新写的覆写方法"在常量池里**根本没有对应条目**（常量池只放被引用的符号），
    所以只能从 class 结构的 methods[] 里读（首跑就是这里报的假 FAIL）。
    """
    data = open(path, "rb").read()
    pool = parse_pool(path)
    n = struct.unpack_from(">H", data, 8)[0]
    i, idx = 10, 1
    while idx < n:
        tag = data[i]
        i += 1
        if tag == 0:
            # CONSTANT_End：javac 会把池里的 #0 / #1 留成占位空槽，
            # 不认它 ⇒ 从这里开始整池解错（double 1.0 就是这么丢的）
            pool[idx] = ("end", None)
        elif tag == 1:
            ln = struct.unpack_from(">H", data, i)[0]
            i += 2 + ln
        elif tag in (7, 8, 16, 19, 20):
            i += 2
        elif tag == 15:
            i += 3
        elif tag == 3:
            i += 4
        elif tag == 4:
            i += 4
        elif tag == 6:
            i += 8
            idx += 1
        elif tag in (9, 10, 11, 12, 17, 18):
            i += 4
        elif tag in (5,):
            i += 8
            idx += 1
        else:
            raise ValueError("pool tag %d" % tag)
        idx += 1
    i += 6  # access_flags, this_class, super_class
    ifc = struct.unpack_from(">H", data, i)[0]
    i += 2 + 2 * ifc
    fields = struct.unpack_from(">H", data, i)[0]
    i += 2
    for _ in range(fields):
        i += 6
        attrs = struct.unpack_from(">H", data, i)[0]
        i += 2
        for _a in range(attrs):
            ln = struct.unpack_from(">I", data, i + 2)[0]
            i += 6 + ln
    methods = struct.unpack_from(">H", data, i)[0]
    i += 2
    out = set()
    for _ in range(methods):
        name_i, desc_i = struct.unpack_from(">HH", data, i)
        i += 6
        attrs = struct.unpack_from(">H", data, i)[0]
        i += 2
        for _a in range(attrs):
            ln = struct.unpack_from(">I", data, i + 2)[0]
            i += 6 + ln
        nm, ds = pool.get(name_i), pool.get(desc_i)
        if nm and ds and nm[0] == "utf8" and ds[0] == "utf8":
            out.add((nm[1], ds[1]))
    return out


def cls(name):
    p = os.path.join(CLASSES, "com", "potatost", "mod", name + ".class")
    if not os.path.isfile(p):
        raise SystemExit(u"找不到 class：%s（先跑 compileJava）" % p)
    pool = Pool(p)
    pool.methods = read_class_methods(p)
    pool.bc_ints = bytecode_ints(p)
    pool.bc_floats = bytecode_floats(p, None)
    return pool


def read_json(path):
    return json.loads(open(path, encoding="utf-8").read())


def decode_png(path):
    u"""只解 8 位 RGBA / RGB / 灰度的 PNG，返回 (w, h, [alpha...])。"""
    b = open(path, "rb").read()
    if b[:8] != b"\x89PNG\r\n\x1a\n":
        return None
    pos, idat, dims, colortype = 8, b"", None, None
    while pos < len(b):
        ln = struct.unpack_from(">I", b, pos)[0]
        ctype = b[pos + 4:pos + 8]
        chunk = b[pos + 8:pos + 8 + ln]
        if ctype == b"IHDR":
            w, h, depth, colortype = struct.unpack_from(">IIBB", chunk, 0)
            if depth != 8 or colortype not in (2, 4, 6):
                return None
            dims = (w, h)
        elif ctype == b"IDAT":
            idat += chunk
        pos += 12 + ln
    ch = {2: 3, 4: 2, 6: 4}[colortype]
    stride = dims[0] * ch
    raw = zlib.decompress(idat)
    p, prev, alphas = 0, bytearray(stride), []
    for _y in range(dims[1]):
        f = raw[p]
        p += 1
        line = bytearray(raw[p:p + stride])
        p += stride
        if f == 1:
            for i in range(ch, stride):
                line[i] = (line[i] + line[i - ch]) & 0xFF
        elif f == 2:
            for i in range(stride):
                line[i] = (line[i] + prev[i]) & 0xFF
        elif f == 3:
            for i in range(stride):
                a = line[i - ch] if i >= ch else 0
                line[i] = (line[i] + ((a + prev[i]) >> 1)) & 0xFF
        elif f == 4:
            for i in range(stride):
                a = line[i - ch] if i >= ch else 0
                bq = prev[i]
                c = prev[i - ch] if i >= ch else 0
                pa, pb, pc = abs(bq - c), abs(a - c), abs(a + bq - 2 * c)
                pr = a if (pa <= pb and pa <= pc) else (bq if pb <= pc else c)
                line[i] = (line[i] + pr) & 0xFF
        for x in range(dims[0]):
            alphas.append(255 if ch in (2, 3) else line[x * ch + ch - 1])
        prev = line
    return dims[0], dims[1], alphas


def javap_disasm(class_name):
    u"""用 javap 反汇编一个 class，返回 `-p -c -constants` 的文本。

    为什么非它不可：**JVM 有一批内建常量根本不进常量池** ——
    `0.0` 是 `dconst_0`、`1.0` 是 `dconst_1`、`-1..5` 是 `iconst_*`。
    所以"星璨钢胸甲的韧性 = 1.0"这条**在常量池里永远查不到**（首跑因此漏检，
    被 K4 那一刀逮住）。javap 把指令流打出来，才能证明"那一行真的压了 1.0"。
    """
    exe = os.path.join(os.environ.get("JAVA_HOME", ""), "bin", "javap.exe")
    if not os.path.isfile(exe):
        exe = "javap"
    p = subprocess.run([exe, "-p", "-c", "-constants", "-classpath", CLASSES,
                        "com.potatost.mod." + class_name],
                       stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    return p.stdout.decode("utf-8", "replace")


CONST_INSTR = re.compile(
    u"^\\s*\\d+:\\s+(dconst_0|dconst_1|dconst_2|fconst_0|fconst_1|fconst_2"
    u"|ldc2_w\\s+#\\d+\\s+//\\s+double\\s+([0-9.eE+-]+)d?"
    u"|ldc\\s+#\\d+\\s+//\\s+float\\s+([0-9.eE+-]+)f?"
    u"|sipush\\s+(-?\\d+)"
    u"|bipush\\s+(-?\\d+)"
    u"|iconst_m1|iconst_([0-5]))")
FIELD_INIT = re.compile(u"^\\s*\\d+:\\s+putstatic\\s+#\\d+\\s+//\\s+Field\\s+(\\S+):")


# javap -constants 会把"编译期常量"直接打在字段声明行上：`private static final int X = 40;`
FIELD_CONST = re.compile(u"^\\s*(?:private|public|protected)?\\s*static\\s+final\\s+\\S+\\s+(\\w+)\\s*=\\s*(\\S+);")


def field_constants(disasm):
    u"""从 javap -constants 的字段声明行里读"名字 → 字面值"。

    为什么需要它：`ABSORPTION_REFRESH = 0` 这种**零值**在字节码里是 `iconst_0`，
    常量池里什么都没有（§4.71 那三类漏网字面量的近亲）。
    但 `javap -constants` 会把它作为**字段声明**打出来 ⇒ 这是唯一稳的取证口。
    """
    out = {}
    for line in disasm.split(u"\n"):
        m = FIELD_CONST.match(line)
        if m:
            out[m.group(1)] = m.group(2)
    return out


CALL_SEQ = re.compile(u"^\\s*\\d+:\\s+(.+?)\\s+//\\s+(?:Method|InterfaceMethod)\\s+(\\S+)")


def call_arg_sequences(disasm, method_name):
    u"""找每次 `invoke*(..., ..., method_name, ...)` 之前压进去的**数字参数序列**。

    用途：证明"伤害吸收那次调用传的是 0（必须等效果结束）、其他效果传的是 40（提前 2 s 续）"。
    这是"调用点取证"，比"名字在不在"强一级（§4.71 / §4.76）。
    """
    seqs = []
    cur = []
    for line in disasm.split(u"\n"):
        m = CALL_SEQ.match(line)
        if not m:
            # 收集这一行里出现的数字/常量（javap 把压栈指令和数字写在同一个操作数区）
            nums = re.findall(u"(?:iconst_([0-5])|bipush\\s+(-?\\d+)|sipush\\s+(-?\\d+)|"
                              u"ldc\\s+#\\d+\\s+//\\s+int\\s+(-?\\d+)|"
                              u"getstatic\\s+#\\d+\\s+//\\s+Field\\s+\\S+\\.(\\w+):)", line)
            for g in nums:
                for v in g:
                    if v:
                        cur.append(v)
            continue
        ops, target = m.group(1), m.group(2)
        nums = re.findall(u"(?:iconst_([0-5])|bipush\\s+(-?\\d+)|sipush\\s+(-?\\d+)|"
                          u"ldc\\s+#\\d+\\s+//\\s+int\\s+(-?\\d+)|"
                          u"getstatic\\s+#\\d+\\s+//\\s+Field\\s+\\S+\\.(\\w+):)", ops)
        for g in nums:
            for v in g:
                if v:
                    cur.append(v)
        if target.endswith(u"." + method_name) or target.split(u".")[-1].startswith(method_name + u":"):
            seqs.append(list(cur))
        cur = []
    return seqs


def static_init_constants(disasm, field_prefix):
    u"""从 `static {}` 里抠出"每个静态字段初始化时压进去的那几个常量"。

    形状（本项目实测，javac 21）：
        ldc  #119  // String star_steel_chestplate
        ...
        ldc2_w #121 // double 9.5d
        dconst_1                       <- 韧性 1.0
        invokestatic register(...)
        putstatic #123 // Field STAR_STEEL_CHESTPLATE
    ⇒ 找 `putstatic <前缀>` 那一行，**往前**收集最近的一串常量指令即可。
    """
    out = {}
    cur = []
    for line in disasm.split(u"\n"):
        m = CONST_INSTR.match(line)
        if m:
            g = m.groups()
            if g[0] == "dconst_0":
                cur.append(0.0)
            elif g[0] == "dconst_1":
                cur.append(1.0)
            elif g[0] == "dconst_2":
                cur.append(2.0)
            elif g[1] is not None:
                cur.append(float(g[1]))
            elif g[2] is not None:
                cur.append(float(g[2]))
            elif g[3] is not None:
                cur.append(int(g[3]))
            elif g[4] is not None:
                cur.append(int(g[4]))
            elif g[0] == "iconst_m1":
                cur.append(-1)
            elif g[5] is not None:
                cur.append(int(g[5]))
            continue
        f = FIELD_INIT.match(line)
        if f and f.group(1).startswith(field_prefix):
            out[f.group(1)] = list(cur)
            cur = []
            continue
        if u"putstatic" in line or u"putfield" in line:
            cur = []
    return out


def read_source(name):
    return open(os.path.join(SRC_DIR, name + ".java"), encoding="utf-8").read()


# (注册名, 耐久, 护甲值, 韧性)   ← 全部照**用户原话**抄，不是从源码抄
EXPECT = [
    ("titanium_alloy_helmet", 2801, 2.5, 0.0),
    ("titanium_alloy_chestplate", 4096, 8.0, 0.0),
    ("titanium_alloy_leggings", 3412, 6.0, 0.0),
    ("titanium_alloy_boots", 2048, 4.5, 0.0),
    ("star_steel_helmet", 2012, 5.5, 0.5),
    ("star_steel_chestplate", 3876, 9.5, 1.0),
    ("star_steel_leggings", 2790, 7.5, 0.5),
    ("star_steel_boots", 1754, 5.5, 0.5),
]

LANG_KEYS = ["item.potato_s_t.star_steel_ingot"]
for _set in ("titanium_alloy", "star_steel"):
    for _piece in ("helmet", "chestplate", "leggings", "boots"):
        LANG_KEYS.append("item.potato_s_t.%s_%s" % (_set, _piece))
LANG_KEYS += ["tooltip.potato_s_t.titanium_alloy_set",
              "tooltip.potato_s_t.star_steel_set",
              "message.potato_s_t.star_steel_void_block",
              "message.potato_s_t.star_steel_void_swap",
              "message.potato_s_t.star_steel_void_failed"]


def main():
    print(u"================ ① 数值：常量池取证 ================")
    items = cls("ModArmorItems")
    for name, dur, armor, tough in EXPECT:
        check(name in items.strings, u"%s 注册名在 ModArmorItems 常量池" % name)
        check(items.num(dur), u"%s 耐久 %d 编进了 class（sipush，常量池里没有）" % (name, dur),
              u"字节码立即数：%s" % sorted(items.bc_ints))
        check(items.num(armor), u"%s 护甲值 %s 编进了 class" % (name, armor),
              u"float/double：%s" % sorted(items.bc_floats | items.floats | items.doubles))
        if tough > 0.0:
            check(items.num(tough), u"%s 韧性 %s 编进了 class" % (name, tough))
    check(items.num(0.5), u"韧性 0.5（头/腿/靴共用）编进了 class")
    check(items.num(8.0) and items.num(6.0), u"护甲值 8.0 / 6.0 在（double 常量，不是 int）")
    check(items.num(9.5) and items.num(5.5) and items.num(7.5) and items.num(4.5),
          u"四件 .5 结尾的护甲值 9.5 / 5.5 / 7.5 / 4.5 都在（小数语义没被丢掉）")

    # ---------------------------------------------------------------
    #  ①b javap 反汇编：连 dconst_0 / dconst_1 这种"不进常量池"的值一起取证
    #      （K4 那一刀 —— 胸甲韧性 1.0 → 0.0 —— 常量池查不出来，只有这里能抓）
    # ---------------------------------------------------------------
    print(u"")
    print(u"---------------- ①b 静态初始化里的三元组（javap 指令流）----------------")
    disasm = javap_disasm("ModArmorItems")
    inits = static_init_constants(disasm, "STAR_STEEL_")
    inits.update(static_init_constants(disasm, "TITANIUM_ALLOY_"))
    inits.pop("STAR_STEEL_INGOT", None)   # 那是普通锭（没有三元组），前缀恰好撞上
    check(len(inits) == 8, u"javap 里找到 8 个盔甲字段的初始化常量串", u"实际 %d：%s"
          % (len(inits), sorted(inits)))
    for name, dur, armor, tough in EXPECT:
        field = name.upper()
        got = inits.get(field)
        if got is None:
            check(False, u"%s 的静态初始化常量串" % field, u"javap 没找到（改名了？）")
            continue
        # 期望形状：[..., 耐久(int), 护甲值(double), 韧性(double), ...]
        check(dur in got, u"%s：javap 指令流里有耐久 %d" % (field, dur), u"实际 %s" % got)
        check(armor in got, u"%s：javap 指令流里有护甲值 %s" % (field, armor), u"实际 %s" % got)
        check(tough in got, u"%s：javap 指令流里有韧性 %s（0.0/1.0 走 dconst_*，常量池查不到）"
              % (field, tough), u"实际 %s" % got)

    print(u"")
    print(u"================ ② 附魔权重：钛 > 金(22) ================")
    mats = cls("ModArmorMaterials")
    for holder, value in (("TITANIUM_ALLOY", 25), ("STAR_STEEL", 20)):
        check(holder in mats.names, u"%s 材料 holder 名在常量池" % holder)
        check(value in mats.ints, u"%s 附魔权重 %d 编进了常量池" % (holder, value),
              u"int 池：%s" % sorted(mats.ints))
    check(25 > 22, u"钛合金 25 > 原版金 22（用户要求比金高一些）")
    check(15 < 20 < 22, u"星璨钢 20 落在下界合金 15 与金 22 之间（本轮拍板值）")

    print(u"================ ③ 盔甲材料：图层贴图 + 修理材料 ================")
    # 【ZF106 改锚点】原来这两张是"借原版铁"（Layer 资源名 = iron）；
    #   用户给了自己的两张套装原图 ⇒ 现在 Layer 指向**本模组自己**的
    #   textures/models/armor/<材料名>_layer_1|2.png（由 _zf106_armor.py 从用户素材生成）。
    #   判据跟着换，**不是放宽**：从"必须出现 iron"变成"必须出现 potato_s_t 且四张图都在"。
    check(u"potato_s_t" in mats.strings,
          u"Layer 的 assetName 用自己的命名空间（⇒ potato_s_t:textures/models/armor/*.png）")
    # ⚠ 只查"potato_s_t 这个字符串在不在"是不够的：本类里 ARMOR_MATERIAL 的 ResourceKey
    #   也用了同一个 MODID 常量 ⇒ 把 Layer 改成原版命名空间，字符串照样在（K6 那一刀漏了）。
    #   真正的判据是**调用形状**：必须出现 `fromNamespaceAndPath(String, String)` 这一次调用，
    #   而且**不许**出现 `withDefaultNamespace(...)`（那是"借原版贴图"的写法）。
    check(any(n == "fromNamespaceAndPath"
              and d == u"(Ljava/lang/String;Ljava/lang/String;)Lnet/minecraft/resources/ResourceLocation;"
              for n, d in mats.refs),
          u"Layer 走 ResourceLocation.fromNamespaceAndPath(MODID, name)（调用形状取证）",
          u"常量池里没有这个签名的方法引用")
    check(not any(n == "withDefaultNamespace" for n, _d in mats.refs),
          u"**不再**借用原版命名空间（withDefaultNamespace 一次都没被调）")
    for _set_name in (u"titanium_alloy", u"star_steel"):
        for _layer in (1, 2):
            _p = os.path.join(ASSETS, u"textures", u"models", u"armor",
                              u"%s_layer_%d.png" % (_set_name, _layer))
            check(os.path.isfile(_p), u"盔甲图层贴图 %s_layer_%d.png 存在" % (_set_name, _layer))
            if os.path.isfile(_p):
                _got = decode_png(_p)
                check(_got is not None and _got[0] == 64 and _got[1] == 32,
                      u"%s_layer_%d.png 是 64×32（盔甲层的标准尺寸）" % (_set_name, _layer),
                      # ⚠ 这里必须**包一层单元素 tuple**：`% ((a, b) if got else u"…")`
                      #   会把 `(64, 32, [...])` 整个当成参数表 ⇒ "not all arguments converted"。
                      u"实际 %s" % (((_got[0], _got[1]),) if _got else (u"解不开",)))
    check("ARMOR_EQUIP_IRON" in mats.names, u"装备音效用原版铁的音效")
    check("LIGHT_TITANIUM_ALLOY" in mats.names, u"钛合金套修理材料 = 轻质钛合金")
    check("STAR_STEEL_INGOT" in mats.names, u"星璨钢套修理材料 = 星璨钢锭")
    check("unwrapKey" in mats.names, u"按材料 ResourceKey 判材料（不是逐个比 item 实例）")
    # 【ZF106 改锚点】`isMaterial` 与两个"判套装"的辅助已从 ModArmorSet **搬去** ModArmorMaterials
    #   （因为 ModArmorPiece 也要判满套 —— 末地永久不掉耐久那条，而它不该认识"套装效果"那个类）。
    #   判据跟着搬到被调用方：ModArmorSet 里现在出现的是 hasFullStarSteelSet / hasAnyStarSteelPiece。
    check("hasFullStarSteelSet" in cls("ModArmorSet").names,
          u"ModArmorSet 复用 ModArmorMaterials.hasFullStarSteelSet(...)")
    check("hasFullStarSteelSet" in cls("ModArmorMaterials").names
          or "hasFullStarSteelSet" in cls("ModArmorMaterials").strings,
          u"ModArmorMaterials 自己声明了 hasFullStarSteelSet（两处共用的唯一实现）")

    print(u"")
    print(u"================ ④ 单件：属性修饰符 / 夜晚耐久 ================")
    piece = cls("ModArmorPiece")
    # 修饰符 id = fromNamespaceAndPath(PotatoST.MODID, "armor." + getType().getName())
    # ⚠ javac 把字符串拼接编成 `"armor.\x01"` 这种带占位符的形状
    #   （StringConcatFactory），所以**不能用 == 比**，要用 startswith
    #   （本探针首跑就是这条报的假 FAIL）。
    check(any(s.startswith(u"armor.") for s in piece.strings),
          u"属性修饰符 id 前缀 armor. 在常量池",
          u"候选：%s" % [s for s in sorted(piece.strings) if u"armor" in s][:5])
    check(u"potato_s_t" in piece.strings,
          u"修饰符 id 的命名空间是 potato_s_t（不借用 minecraft:armor.<部位>，免得撞 id）")
    check(any(u"ArmorItem" in s for s in piece.strings) or u"ArmorItem" in piece.names,
          u"ModArmorPiece 引用原版 ArmorItem（继承它）")
    for target, owner in (("getDefaultAttributeModifiers", "ModArmorPiece"),
                          ("appendHoverText", "ModArmorPiece"),
                          ("damageItem", "ModArmorPiece"),
                          ("onPlayerTick", "ModArmorSet"),
                          ("onLivingDamaged", "ModArmorSet")):
        check(target in cls(owner).strings,
              u"%s 里有 %s（方法名会以 Utf8 进常量池）" % (owner, target))
    check("ADD_VALUE" in piece.names, u"修饰符用 ADD_VALUE（工具提示因此显示原值，不会乘成百分号）")
    check("isNight" in piece.names, u"夜晚判定走 Level.isNight()")
    # 【ZF106 追加】末地 + 满套星璨钢 ⇒ 永久不掉耐久（用户原话「星璨钢末地并不是不消耗耐久」）
    check(u"hasFullStarSteelSet" in piece.names,
          u"damageItem 里判了满套星璨钢（末地永久不消耗耐久那条）")
    check(u"END" in piece.names or u"LEVEL" in piece.names,
          u"damageItem 里判了维度（Level.END）")
    check(u"tooltip.potato_s_t.hold_shift" in piece.strings,
          u"不按 Shift 时提示 hold_shift（与海盐同一口径）")
    check("hurtAndBreak" not in piece.names, u"没有绕过 hurtAndBreak 直接扣耐久（否则夜晚那条会失效）")
    # ---------------------------------------------------------------
    #  ④b 源码级结构断言：**覆写本身**是否还在
    #     常量池只能证明"这个名字被引用过" —— 把整个覆写删掉，它就查不到了
    #     （K5 那一刀：删掉 damageItem 覆写，常量池断言全部照过，是漏检）。
    # ---------------------------------------------------------------
    print(u"")
    print(u"---------------- ④b 覆写的结构（源码 + @Override）----------------")
    src = read_source("ModArmorPiece")
    for sig, label in (
            (u"int damageItem(ItemStack stack", u"damageItem 覆写本身还在"),
            (u"ItemAttributeModifiers getDefaultAttributeModifiers()", u"getDefaultAttributeModifiers 覆写还在"),
            (u"void appendHoverText(ItemStack stack", u"appendHoverText 覆写还在")):
        check(sig in src, label, u"源码里找不到 %r" % sig)
    check(src.count(u"@Override") >= 3, u"三个覆写都带 @Override",
          u"实际 %d 个" % src.count(u"@Override"))
    # 夜晚不掉耐久的**语义**（不是只留个空壳）：isNight 必须在 damageItem 体内
    body = src.split(u"int damageItem(ItemStack stack", 1)[-1]
    body = body.split(u"\n    }", 1)[0]
    check(u"isNight()" in body, u"damageItem 体内真的判了 isNight()", u"体内：%s" % body.strip()[:120])
    check(u"return 0;" in body, u"夜晚那条 return 0（NeoForge 语义：返回 ≤ 0 ⇒ 一点耐久都不扣）")
    check(u"super.damageItem" in body, u"白天走 super.damageItem（不是把耐久关掉）")
    set_src = read_source("ModArmorSet")
    for sig, label in ((u"void onPlayerTick(PlayerTickEvent.Post", u"onPlayerTick 挂在 PlayerTickEvent.Post"),
                       (u"void onLivingDamaged(LivingDamageEvent.Post", u"onLivingDamaged 挂在 LivingDamageEvent.Post"),
                       (u"@EventBusSubscriber(modid = PotatoST.MODID)", u"ModArmorSet 挂在游戏总线上")):
        check(sig in set_src, label, u"源码里找不到 %r" % sig)
    print(u"================ ⑤ 套装：效果 / 虚空救援 ================")
    st = cls("ModArmorSet")
    for needle, label in [
        ("FELL_OUT_OF_WORLD", u"虚空判定 = DamageTypes.FELL_OUT_OF_WORLD"),
        ("DAMAGE_RESISTANCE", u"抗性提升 = MobEffects.DAMAGE_RESISTANCE"),
        ("DAMAGE_BOOST", u"力量 = MobEffects.DAMAGE_BOOST（不是 STRENGTH，1.21.1 没这个名字）"),
        ("REGENERATION", u"生命恢复 = MobEffects.REGENERATION"),
        ("ABSORPTION", u"伤害吸收 = MobEffects.ABSORPTION"),
        ("randomTeleport", u"换位走 LivingEntity.randomTeleport"),
        ("teleportTo", u"传送走 ServerPlayer.teleportTo(ServerLevel,...)"),
        ("isLoaded", u"找落点前先问 chunk 是否加载"),
        ("immutable", u"候选坐标 immutable()（防可变 BlockPos 复用）"),
        ("isFaceSturdy", u"实心方块判定"),
        ("getCollisionShape", u"净空判定"),
        ("addEffect", u"上效果"),
        ("getEffect", u"查身上现有的效果（不可叠加/不覆盖高级别的判据）"),
        ("displayClientMessage", u"救援结果用物品栏上方提示回报玩家"),
        # 【ZF106 追加】传送前免除摔落伤害（用户原话："传送之前加个缓降…要不然就摔死了"）
        ("resetFallDistance", u"传送前清空已累积的坠落距离"),
        ("SLOW_FALLING", u"传送前给缓降（落地时 checkFallDamage 不再结算）"),
        # ⚠ 上面两条只证明"方法**存在**" —— 把 preventFallDamage 的**调用**删掉它们照样过
        #   （K11 那一刀就是这么漏的）。所以必须再单独断言"这个辅助真的被调了"：
        #   (名字, 描述符) 出现在常量池的 Methodref 里 = 有一次真实调用。
    ]:
        check(needle in st.names or needle in st.strings, label)
    check(any(n == "preventFallDamage" for n, _d in st.refs),
          u"preventFallDamage(...) 真的被**调用**了（不只是定义了）",
          u"常量池方法引用里没有它")
    for value, label in [(940, u"缓降时长 940 tick = 47 s（够从世界顶落到世界底）")]:
        check(value in st.ints, label, u"int 池：%s" % sorted(st.ints))

    # ---------------------------------------------------------------
    #  ⑤b 伤害吸收**不许提前续**（用户原话：「护盾不要立马就恢复」）
    # ---------------------------------------------------------------
    print(u"")
    print(u"---------------- ⑤b 效果补充节奏（javap：常量声明 + 调用点实参）----------------")
    st_dis = javap_disasm("ModArmorSet")
    consts = field_constants(st_dis)
    check(consts.get(u"ABSORPTION_REFRESH") == u"0",
          u"ABSORPTION_REFRESH = 0（必须等效果彻底结束才给下一次）",
          u"javap 读到 %r" % consts.get(u"ABSORPTION_REFRESH"))
    check(consts.get(u"KNOCKBACK_MARGIN") == u"40",
          u"KNOCKBACK_MARGIN = 40（持续型效果提前 2 s 续，不断档）",
          u"javap 读到 %r" % consts.get(u"KNOCKBACK_MARGIN"))
    check(consts.get(u"END_ABSORPTION_TICKS") == u"240" and consts.get(u"OVERWORLD_ABSORPTION_TICKS") == u"200",
          u"吸收时长仍是末地 240 tick(12 s) / 主世界 200 tick(10 s)",
          u"读到 %r / %r" % (consts.get(u"END_ABSORPTION_TICKS"),
                             consts.get(u"OVERWORLD_ABSORPTION_TICKS")))
    # 调用点：吸收那条必须是「时长, 0」，持续型那些必须是「时长, 40」
    #   javap 把实参按压栈顺序列出来，形如 `..., 240, 0, invokestatic ensure`
    ensure_calls = [s for s in call_arg_sequences(st_dis, u"ensure") if s]
    check(len(ensure_calls) >= 7, u"抓到 ensure(...) 的调用点 %d 处（应为 7）" % len(ensure_calls),
          u"实际 %r" % ensure_calls)
    # 吸收：只有 ABSORPTION 那两次的实参序列里带 `ABSORPTION` 字段名 + `0`
    abs_calls = [s for s in ensure_calls if any(u"ABSORPTION" in x for x in s)]
    check(len(abs_calls) == 2, u"伤害吸收的调用点 2 处（末地 / 主世界各一）", u"实际 %r" % abs_calls)
    for seq in abs_calls:
        check(seq[-1] == u"0",
              u"吸收调用点最后一个实参 = 0（不提前续）",
              u"实参序列 %r" % seq)
    other_calls = [s for s in ensure_calls if not any(u"ABSORPTION" in x for x in s)]
    for seq in other_calls:
        check(seq and seq[-1] == u"40",
              u"持续型效果调用点最后一个实参 = 40（提前 2 s 续）",
              u"实参序列 %r" % seq)
    for target in ("onPlayerTick", "onLivingDamaged"):
        check(target in st.strings,
              u"ModArmorSet 里有 %s（方法名以 Utf8 进常量池）" % target)
    for value, label in [(200, u"主世界吸收 10 s = 200 tick"), (240, u"末地吸收 12 s = 240 tick"),
                         (40, u"补效果余量 40 tick"), (10, u"虚空搜索半径 ±10 格（20×20）"),
                         (2, u"落点净空 2 格"), (320, u"夜晚持续效果补充时长 320 tick"),
                         (16, u"换位搜索半径 16 格")]:
        check(value in st.ints, label, u"int 池：%s" % sorted(st.ints))
    for amp, label in [(1, u"抗性 II / 力量 II 的 amplifier = 1"),
                       (2, u"抗性 III / 吸收 III 的 amplifier = 2"),
                       (5, u"吸收 VI 的 amplifier = 5")]:
        check(amp in st.ints, label)

    print(u"")
    print(u"================ ⑥ 四语言 × 14 键 ================")
    check(len(LANG_KEYS) == 14, u"本轮新增键正好 14 个", u"实际 %d" % len(LANG_KEYS))
    check(len(set(LANG_KEYS)) == 14, u"14 个键没有重复")
    for locale in ("zh_cn", "en_us", "ja_jp", "ru_ru"):
        table = read_json(os.path.join(LANG, locale + ".json"))
        missing = [k for k in LANG_KEYS if k not in table]
        empty = [k for k in LANG_KEYS if k in table and not table[k].strip()]
        check(not missing and not empty, u"%s：14 个键齐全且非空" % locale,
              u"缺 %s / 空 %s" % (missing, empty))
        check(len(table) == 492, u"%s：总键数 492（… + ZF112 锂电池构造间 9 + ZF125 柴油发电机 11）" % locale,
              u"实际 %d" % len(table))
        check(bool(table.get("tooltip.potato_s_t.hold_shift")),
              u"%s：既有的 hold_shift 没被覆盖掉" % locale)

    print(u"")
    print(u"================ ⑦ 物品模型 / 贴图 ================")
    for name in [n for n, _d, _a, _t in EXPECT] + ["star_steel_ingot"]:
        model = os.path.join(ASSETS, "models", "item", name + ".json")
        if not os.path.isfile(model):
            check(False, u"models/item/%s.json 存在" % name)
            continue
        layer0 = read_json(model).get("textures", {}).get("layer0", "")
        check(bool(layer0), u"models/item/%s.json 有 layer0" % name, u"得到 %r" % layer0)
        if name == "star_steel_ingot":
            check(layer0 == "potato_s_t:item/star_steel_ingot",
                  u"星璨钢锭指向自己的贴图（不是借原版）", u"得到 %r" % layer0)
        elif name.startswith("star_steel_"):
            # 【ZF120 改锚点】ZF110/ZF116 之后，星璨钢四件拿到了用户自己的背包图标
            #   （`build/用户素材/星璨钢*.png`）⇒ 这一支从"借原版铁套"改成"指向自己的贴图"。
            #   判据跟着**新真相**走，不是放宽：钛合金那四件仍然必须借原版铁（下面那一支一字未动），
            #   振金四件（ZF120 新加）也借原版铁 —— 它们由 `_zf120_verify.py` 的 ⑤ 组盯。
            #   ⚠ 这 4 条从 ZF110/ZF116 起就是红的（ZF119 的 gatesnap 记着"失败项 = 4"）；
            #   本轮把 `_zf103_verify.py` 从 git 里救回来时顺手跟平，`ZF104 falsify` 的 13 把刀
            #   也因此从"基线不绿、拒绝开跑"恢复成真跑。
            check(layer0 == "potato_s_t:item/" + name,
                  u"%s 背包贴图指向自己的图（ZF110/ZF116 起用户给了素材）" % name,
                  u"得到 %r" % layer0)
        else:
            check(layer0.startswith("minecraft:item/iron_"),
                  u"%s 背包贴图借原版铁套（用户指定先用铁套的）" % name, u"得到 %r" % layer0)

    tex = os.path.join(ASSETS, "textures", "item", "star_steel_ingot.png")
    check(os.path.isfile(tex), u"textures/item/star_steel_ingot.png 已生成")
    if os.path.isfile(tex):
        head = open(tex, "rb").read(8)
        check(head == b"\x89PNG\r\n\x1a\n", u"星璨钢贴图是真 PNG（不是 webp 改名，§4.23）")
        got = decode_png(tex)
        if got is None:
            check(False, u"星璨钢贴图可解（8 位 RGBA/RGB）")
        else:
            w, h, alphas = got
            check((w, h) == (16, 16), u"星璨钢贴图 16×16（TextureCheck 口径）", u"实际 %dx%d" % (w, h))
            transparent = sum(1 for a in alphas if a == 0)
            opaque = sum(1 for a in alphas if a == 255)
            check(transparent > 0, u"有透明像素（物品贴图必须去底）", u"透明 %d / %d" % (transparent, w * h))
            check(opaque > 0, u"有实体像素", u"不透明 %d / %d" % (opaque, w * h))
            semi = w * h - transparent - opaque
            check(semi == 0, u"没有半透明脏边（面积平均只落在形状内部）", u"半透明 %d" % semi)

    print(u"")
    print(u"================ ⑧ c: 通用标签（星璨钢锭）================")
    for rel in ("item/ingots/star_steel.json", "item/star_steel_ingots.json"):
        p = os.path.join(DATA, "c", "tags", rel.replace("/", os.sep))
        ok = os.path.isfile(p) and "potato_s_t:star_steel_ingot" in open(p, encoding="utf-8").read()
        check(ok, u"data/c/tags/%s 含 star_steel_ingot" % rel)
    p = os.path.join(DATA, "c", "tags", "item", "ingots.json")
    check("potato_s_t:star_steel_ingot" in open(p, encoding="utf-8").read(),
          u"c:ingots 父标签也收了它（合金炉输入槽会认，与轻质钛合金同口径）")

    print(u"")
    print(u"================ ⑨ 创造页 / 注册入口 ================")
    mod_items = cls("ModItems")
    armor_fields = [n for n, _d, _a, _t in EXPECT] + ["STAR_STEEL_INGOT"]
    # 创造页那几行是 `output.accept(ModArmorItems.X.get())` ⇒ ModItems 常量池里出现的是
    # ModArmorItems 的**字段符号**（9 个），不是物品注册名字符串。首跑查错了集合，报了 8 条假 FAIL。
    for field in [f.upper() for f in armor_fields]:
        check(field in mod_items.names,
              u"ModItems 引用了 ModArmorItems.%s（创造页 accept）" % field)
    main_cls = cls("PotatoST")
    check("ARMOR_MATERIALS" in main_cls.names, u"PotatoST 构造器登记了 ModArmorMaterials.ARMOR_MATERIALS")
    check("ARMOR_MATERIAL" in mats.names or "ARMOR_MATERIAL" in mats.strings,
          u"盔甲材料注册表用的是 Registries.ARMOR_MATERIAL")

    print(u"")
    print(u"==============================")
    print(u"断言数 = %d   失败项 = %d" % (count, len(fails)))
    for f in fails:
        print(u"  !! " + f)
    print(u"结论: %s" % (u"通过" if not fails else u"有失败项"))
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())
