# -*- coding: utf-8 -*-
u"""_zf140_mapping.py —— 把 `SkyboxRenderer` 里的**盖片算式真读出来**，再拿它去验

为什么要读源码、而不是在校验器里再抄一份公式（档案 §4.126 的教训：源码字符串判据能防"删掉"，
防不住"改坏"）：如果校验器自带一份公式，那我在 Java 里把 `Math.atan(g*tmax)` 改成 `g*tmax`，
校验器**照样通过** —— 判据与被判物脱钩了。这里反过来：

  ① 从 Java 源码里解析出 `HOLE_DEGREES / HOLE_GRID / HOLE_RADIUS`、
     `buildCaps` 里的 `tmax`、`putCap` 里的 `g/theta/phi/sin/cos` 与 5 个 `out[n++] = …`；
  ② 用一个**受限表达式求值器**把这些算式翻成 numpy（只认四则、括号、`Math.sqrt/atan/atan2/sin/cos/`
     `toRadians/PI`）；出现读不懂的写法直接**报错退出**（不许静默放过）；
  ③ 于是"盖片顶点摆在哪、UV 怎么给"完全由 Java 决定，校验器只负责量它对不对。

两条硬判据：
  · **恒等**：把顶点方向换算成 gnomonic 坐标 `s = (x,z)/|y|`，必须**恰好等于** `(2u-1, 2v-1)·tanθmax`。
    这一条就是"正对极点看过去不变形"的数学形式 —— 位置算式与 UV 算式只要有一边被改坏，它立刻不成立。
  · **分格误差**：盖片是**平板四边形**（GPU 只画三角形），球面被它切成一格一格，
    格心的真实方向与"按 UV 线性插值该有的方向"之间的偏差，换算到 400 px 半径的屏幕上必须 ≤1 px。
"""
import math
import os
import re

import numpy as np

JAVA = os.path.join(r"E:\PotatoST", "src", "main", "java", "com", "potatost", "mod",
                    "client", "SkyboxRenderer.java")

FUNCS = {
    "Math.sqrt": np.sqrt, "Math.atan": np.arctan, "Math.atan2": np.arctan2,
    "Math.sin": np.sin, "Math.cos": np.cos, "Math.tan": np.tan,
    "Math.toRadians": np.radians, "Math.abs": np.abs,
}
CONSTS = {"Math.PI": math.pi}

TOKEN = re.compile(r"\s*([A-Za-z_][A-Za-z0-9_.]*|\d+\.?\d*(?:[eE][-+]?\d+)?|[+\-*/(),])")


class Bad(Exception):
    pass


def tokenize(src):
    src = src.strip()
    src = re.sub(r"\((?:float|double|int|long)\)", " ", src)     # 去掉强制类型转换
    src = re.sub(r"(\d)[fFdD]\b", r"\1", src)                     # 去掉 1.0F / 0.5D 后缀
    out, i = [], 0
    while i < len(src):
        m = TOKEN.match(src, i)
        if not m:
            raise Bad(u"读不懂的 Java 算式片段：%r" % src[i:i + 30])
        out.append(m.group(1))
        i = m.end()
    return out


class Parser(object):
    u"""递归下降，只认这个小子集；越界就 Bad（宁可报错，也不静默算错）"""

    def __init__(self, toks):
        self.t = toks
        self.i = 0

    def peek(self):
        return self.t[self.i] if self.i < len(self.t) else None

    def eat(self, tok):
        if self.peek() != tok:
            raise Bad(u"期望 %r，实际 %r" % (tok, self.peek()))
        self.i += 1

    def expr(self):
        node = self.term()
        while self.peek() in ("+", "-"):
            op = self.peek()
            self.i += 1
            node = (op, node, self.term())
        return node

    def term(self):
        node = self.unary()
        while self.peek() in ("*", "/"):
            op = self.peek()
            self.i += 1
            node = (op, node, self.unary())
        return node

    def unary(self):
        if self.peek() == "-":
            self.i += 1
            return ("neg", self.unary(), None)
        return self.primary()

    def primary(self):
        tok = self.peek()
        if tok == "(":
            self.i += 1
            node = self.expr()
            self.eat(")")
            return node
        if tok is None:
            raise Bad(u"算式提前结束")
        self.i += 1
        if re.match(r"^\d", tok):
            return ("num", float(tok), None)
        if self.peek() == "(":
            self.i += 1
            args = [self.expr()]
            while self.peek() == ",":
                self.i += 1
                args.append(self.expr())
            self.eat(")")
            if tok not in FUNCS:
                raise Bad(u"不认识的函数 %r" % tok)
            return ("call", tok, args)
        if tok in CONSTS:
            return ("num", CONSTS[tok], None)
        return ("var", tok, None)

    def run(self, src):
        toks = tokenize(src)
        node = self.expr()
        if self.i != len(toks):
            raise Bad(u"算式没读完：剩下 %r" % toks[self.i:])
        return node


def parse(src):
    u"""源码片段 -> 表达式树（读不懂就 Bad）"""
    return Parser(tokenize(src)).run(src)


def ev(node, env):
    kind = node[0]
    if kind == "num":
        return node[1]
    if kind == "var":
        if node[1] not in env:
            raise Bad(u"算式里出现了环境里没有的名字 %r" % node[1])
        return env[node[1]]
    if kind == "neg":
        return -ev(node[1], env)
    if kind == "call":
        return FUNCS[node[1]](*[ev(x, env) for x in node[2]])
    a, b = ev(node[1], env), ev(node[2], env)
    # ⚠ 不能写成 {"+": a+b, "-": a-b, "*": a*b, "/": a/b}[kind]：字典字面量会把**四个**都算一遍，
    #   于是 `-1.0 + 2.0 * r / HOLE_GRID` 里那个 `a/b`（b=0）先炸了。第一版就是这么炸的。
    if kind == "+":
        return a + b
    if kind == "-":
        return a - b
    if kind == "*":
        return a * b
    if kind == "/":
        return a / b
    raise Bad(u"不认识的运算符 %r" % kind)


def _method_body(text, header):
    u"""从 `header` 那一行开始，按大括号配平切出方法体"""
    i = text.index(header)
    j = text.index("{", i)
    depth = 0
    for k in range(j, len(text)):
        if text[k] == "{":
            depth += 1
        elif text[k] == "}":
            depth -= 1
            if depth == 0:
                return text[j:k + 1]
    raise Bad(u"找不到 %s 的结尾" % header)


class JavaCap(object):
    u"""SkyboxRenderer 里那段盖片几何的**可求值副本**（数值全部来自源码）"""

    def __init__(self, path=JAVA):
        text = open(path, "r", encoding="utf-8").read()
        self.text = text
        self.degrees = self._const(text, "HOLE_DEGREES")
        self.grid = int(self._const(text, "HOLE_GRID"))
        self.radius = self._const(text, "RADIUS")
        self.radius_factor = self._const_factor(text)
        self.hole_radius = self.radius * self.radius_factor
        self.tex = re.search(r'"textures/skybox/([a-z0-9_]+\.png)"', text)
        if not self.tex:
            raise Bad(u"源码里找不到盖片贴图路径")
        self.tex = self.tex.group(1)

        body = _method_body(text, "private static float[][] buildCaps()")
        if "poleY = (p == 0) ? 1.0F : -1.0F" not in body:
            raise Bad(u"buildCaps 里没有 '北极 y=+1 / 南极 y=-1' 那条三元式")
        env = {"HOLE_DEGREES": self.degrees, "HOLE_GRID": float(self.grid),
               "RADIUS": self.radius, "HOLE_RADIUS": self.hole_radius}
        for name, rhs in re.findall(r"(?:double|float|int)\s+([A-Za-z_]\w*)\s*=\s*([^;]+);", body):
            if "?" in rhs:
                continue        # poleY 的那条三元式：北极 +1 / 南极 -1 由调用方传，见上面的断言
            env[name] = ev(parse(rhs), env)
        self.tmax = env["tmax"]

        cap = _method_body(text, "private static int putCap(")
        self.uv_src = re.findall(r"out\[n\+\+\]\s*=\s*([^;]+);", cap)
        if len(self.uv_src) != 5:
            raise Bad(u"putCap 里 out[n++] 有 %d 条（应为 5：x,y,z,u,v）" % len(self.uv_src))
        self.assign = re.findall(r"double\s+([A-Za-z_]\w*)\s*=\s*([^;]+);", cap)
        self.assign = [(n, parse(r)) for n, r in self.assign]
        self.out_nodes = [parse(s) for s in self.uv_src]
        for need in ("g", "theta", "phi"):
            if need not in [n for n, _ in self.assign]:
                raise Bad(u"putCap 里缺少 %s 的赋值" % need)

    @staticmethod
    def _const(text, name):
        m = re.search(r"%s\s*=\s*(-?\d+\.?\d*)[fFdD]?\s*;" % name, text)
        if not m:
            raise Bad(u"源码里找不到常量 %s" % name)
        return float(m.group(1))

    @staticmethod
    def _const_factor(text):
        m = re.search(r"HOLE_RADIUS\s*=\s*RADIUS\s*\*\s*(\d+\.?\d*)[fFdD]?\s*;", text)
        if not m:
            raise Bad(u"HOLE_RADIUS 不是 'RADIUS * 系数' 的形状")
        return float(m.group(1))

    # -------------------------------------------------- 对外的两个算式
    def theta_of(self, a, b, pole_y=1.0):
        u"""顶点方向：由 (a,b) 算出 θ（弧度）—— 走 putCap 自己的算式"""
        env = {"a": np.asarray(a, dtype=float), "b": np.asarray(b, dtype=float),
               "tmax": np.float64(self.tmax), "poleY": np.float64(pole_y),
               "HOLE_RADIUS": np.float64(self.hole_radius), "RADIUS": np.float64(self.radius)}
        for name, node in self.assign:
            env[name] = ev(node, env)
        return env["theta"]

    def uv_of(self, a, b, pole_y=1.0):
        u"""由 (a,b) 算出 UV（走 putCap 的 5 个赋值；同时返回位置向量供恒等检查用）"""
        env = {"a": np.asarray(a, dtype=float), "b": np.asarray(b, dtype=float),
               "tmax": np.float64(self.tmax), "poleY": np.float64(pole_y),
               "HOLE_RADIUS": np.float64(self.hole_radius), "RADIUS": np.float64(self.radius)}
        for name, node in self.assign:
            env[name] = ev(node, env)
        vals = [ev(node, env) for node in self.out_nodes]
        pos = np.stack([np.broadcast_to(np.asarray(v, dtype=float), env["a"].shape) for v in vals[:3]], axis=-1)
        uv = np.stack([np.broadcast_to(np.asarray(v, dtype=float), env["a"].shape) for v in vals[3:]], axis=-1)
        return pos, uv

    def inverse_g(self, theta, lo=0.0, hi=64.0):
        u"""给定 θ，反解 putCap 算式里的 g（二分；**不是**在校验器里另写一份公式）"""
        theta = np.asarray(theta, dtype=float)
        for _ in range(200):
            mid = 0.5 * (lo + hi)
            t = np.asarray(self.theta_of(mid, np.zeros_like(np.atleast_1d(mid))), dtype=float)
            t = np.broadcast_to(t, theta.shape)
            too_small = t < theta
            lo = np.where(too_small, mid, lo)
            hi = np.where(too_small, hi, mid)
            if np.all(np.abs(hi - lo) < 1e-12):
                break
        return 0.5 * (lo + hi)

    def sample(self, a, b, pole_y=1.0):
        u"""(a,b) -> (位置, UV)，给软件模拟器用"""
        return self.uv_of(a, b, pole_y)


def identity_error(cap, pole_y=1.0, grid=None):
    u"""恒等判据：每个顶点的 gnomonic 坐标必须恰好等于 (2u-1, 2v-1)·tanθmax"""
    n = grid or cap.grid
    a = np.linspace(-1.0, 1.0, n + 1)
    aa, bb = np.meshgrid(a, a)
    pos, uv = cap.sample(aa.ravel(), bb.ravel(), pole_y)
    norm = np.linalg.norm(pos, axis=1, keepdims=True)
    d = pos / norm
    s = np.stack([d[:, 0], d[:, 2]], axis=1) / np.abs(d[:, 1])[:, None]
    want = (2.0 * uv - 1.0) * cap.tmax
    return float(np.abs(s - want).max()), s, uv


def facet_error_px(cap, pole_y=1.0, screen_radius_px=400.0, samples=5, grid=None):
    u"""分格误差 —— **按 GPU 的真做法**量：盖片是平板三角形，不是曲面。

    第一版这里按"参数域双线性"插值，量出来网格 1×1 居然是 0.000 px —— 因为参数域里
    位置与 UV 的关系本来就是线性的，等于什么都没量（**判据与被判物脱钩**，正是 §4.126 那类坑）。
    这里改成：格内撒一批**射线**，拿射线去撞三角形所在的平面，
    按重心坐标线性插值出 UV，再和射线真实的 gnomonic 坐标比 —— 这才是屏幕上真正发生的事。
    """
    n = grid or cap.grid
    pts = np.linspace(0.02, 0.98, samples)
    worst = 0.0
    for r in range(n):
        b0 = -1.0 + 2.0 * r / n
        b1 = -1.0 + 2.0 * (r + 1) / n
        for c in range(n):
            a0 = -1.0 + 2.0 * c / n
            a1 = -1.0 + 2.0 * (c + 1) / n
            ab = np.array([[a0, b0], [a0, b1], [a1, b1], [a1, b0]])
            pos, uv = cap.sample(ab[:, 0], ab[:, 1], pole_y)
            for tri in ((0, 1, 2), (0, 2, 3)):
                P = pos[list(tri)]
                U = uv[list(tri)]
                # ⚠ axis=1：三列分别是 P1-P0、P2-P0、-u。第一版漏了 axis（默认 axis=0 按行堆），
                #   矩阵被转置 ⇒ 量出来的"误差"随网格数按 1/n 衰减、数值大 20 倍，一看就是假的。
                M = np.stack([P[1] - P[0], P[2] - P[0], np.zeros(3)], axis=1)
                for p in pts:
                    for q in pts:
                        # ⚠ 采样射线必须是**该参数下真实的方向**（由 gnomonic 坐标反推），
                        #   不能拿"四角位置的线性插值"当方向：那个点在三角形平面之外，
                        #   它的方向对应的是另一个参数 ⇒ 量出来是 O(1/n) 的假误差（第二版就是这样）。
                        ap = a0 + (a1 - a0) * p
                        bq = b0 + (b1 - b0) * q
                        u = np.array([ap * cap.tmax, pole_y, bq * cap.tmax])
                        u = u / np.linalg.norm(u)
                        M[:, 2] = -u
                        # 几何式：t·u = P0 + α(P1-P0) + β(P2-P0)
                        #   ⇒ α(P1-P0) + β(P2-P0) - t·u = **-P0**（右端是负号！
                        #     第一版写成 +P0，解出来的 t 全是负的 ⇒ 每个采样都被当成"射到背面"跳过，
                        #     误差于是恒等于 0.000 —— 一条永远通过的假判据，比没有还坏）
                        try:
                            sol = np.linalg.solve(M, -P[0])
                        except np.linalg.LinAlgError:
                            continue
                        # ⚠ 解出来的顺序是 [α, β, t]（M 的三列依次是 P1-P0、P2-P0、-u），
                        #   第一版按 [t, α, β] 拆的 ⇒ 量出来误差随网格数 1/n 衰减，一眼假
                        al, be, t = sol
                        if t <= 0 or al < -1e-9 or be < -1e-9 or al + be > 1 + 1e-9:
                            continue
                        uv_i = U[0] + al * (U[1] - U[0]) + be * (U[2] - U[0])
                        real = np.array([u[0], u[2]]) / abs(u[1])
                        want = (2.0 * uv_i - 1.0) * cap.tmax
                        worst = max(worst, float(np.abs(real - want).max()))
    return worst * screen_radius_px


if __name__ == "__main__":
    import sys
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass
    cap = JavaCap()
    print(u"从源码读出：θmax=%.1f° 网格=%d×%d 半径=%.3f×%.1f=%.2f 贴图=%s tmax=%.6f"
          % (cap.degrees, cap.grid, cap.grid, cap.radius_factor, cap.radius,
             cap.hole_radius, cap.tex, cap.tmax))
    err, _, _ = identity_error(cap)
    print(u"恒等误差（应 ~0）= %.3e" % err)
    for g in (1, 2, 4, 8, 16, 32):
        print(u"  网格 %2d×%2d 分格误差 = %.3f px（400 px 半径屏）"
              % (g, g, facet_error_px(cap, grid=g)))

