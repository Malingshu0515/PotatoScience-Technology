# -*- coding: utf-8 -*-
u"""_zf85_fix.py —— 清掉 ModFluids.java 的 25 条 IDE 问题（用户："这个警告和报错很烦人 你看看能不能优化掉"）

逐条对账（截图里的 25 条）：

| IDE 报的 | 条数 | 处置 |
|---|---|---|
| 重写 `FluidType.initializeClient`（弃用并标记为移除） | 5 | **搬走**：改用 `RegisterClientExtensionsEvent`（NeoForge 21.1 的正路），5 个匿名覆盖全部删除 |
| 未注解的形参/方法重写（`@ParametersAreNonnullByDefault` / `@MethodsReturnNonnullByDefault`） | 16 | 随匿名类一起搬走；新落点 `PotatoSTClient` 类上补这两个注解（IDE 按名字识别） |
| 形参 `temperature` 的值始终为 300 | 1 | `liquidType(...)` **去掉这个形参**，内部固定 300 |
| 空行行将被忽略 | 1 | 重排 `gases()` 的 javadoc |
| 方法 `idOf` / `byId` 从未使用 | 2 | **删除**（ZF73 起界面改用注册表 id，这两个早已没人调；`GAS_COUNT` 只被它俩用，一并删） |
| American English uses '-iz-' | 1 | `initialiser` → `initializer` |
"""
import io
import os
import sys

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

ROOT = r"E:\PotatoST"
MODFLUIDS = os.path.join(ROOT, r"src\main\java\com\potatost\mod\ModFluids.java")
fails = []


def patch(text, old, new, label, expect=1):
    n = text.count(old)
    if n != expect:
        fails.append(u"%s：锚点命中 %d 次（期望 %d）" % (label, n, expect))
        return text
    print(u"  [OK]   %s" % label)
    return text.replace(old, new, expect)


def main():
    t = io.open(MODFLUIDS, encoding="utf-8").read()
    before_lines = t.count(u"\n") + 1

    print(u"== ① 三种气体：去掉 initializeClient 匿名覆盖 ==")
    for name in [u"oxygen", u"hydrogen", u"chlorine"]:
        old = (
            u"            FLUID_TYPES.register(\"%s\", () -> new FluidType(FluidType.Properties.create()\n"
            u"                    .density(%s)      // %s\n"
            u"                    .viscosity(200))\n"
            u"            {\n"
            u"                @Override\n"
            u"                public void initializeClient(Consumer<IClientFluidTypeExtensions> consumer) {\n"
            u"                    consumer.accept(new IClientFluidTypeExtensions() {\n"
            u"                        @Override\n"
            u"                        public ResourceLocation getStillTexture() {\n"
            u"                            return ResourceLocation.fromNamespaceAndPath(PotatoST.MODID, \"block/%s_still\");\n"
            u"                        }\n"
            u"\n"
            u"                        @Override\n"
            u"                        public ResourceLocation getFlowingTexture() {\n"
            u"                            return ResourceLocation.fromNamespaceAndPath(PotatoST.MODID, \"block/%s_flow\");\n"
            u"                        }\n"
            u"                    });\n"
            u"                }\n"
            u"            });\n")
        new = (
            u"            FLUID_TYPES.register(\"%s\", () -> new FluidType(FluidType.Properties.create()\n"
            u"                    .density(%s)      // %s\n"
            u"                    .viscosity(200)));\n")
        t = patch(t, old, new, u"%s：覆盖删除" % name)

    print(u"== ② 原油：同样去掉覆盖 ==")
    old_crude = (
        u"                    .supportsBoating(false))\n"
        u"            {\n"
        u"                @Override\n"
        u"                public void initializeClient(Consumer<IClientFluidTypeExtensions> consumer) {\n"
        u"                    consumer.accept(new IClientFluidTypeExtensions() {\n"
        u"                        @Override\n"
        u"                        public ResourceLocation getStillTexture() {\n"
        u"                            return ResourceLocation.fromNamespaceAndPath(PotatoST.MODID,\n"
        u"                                    \"block/crude_oil_still\");\n"
        u"                        }\n"
        u"\n"
        u"                        @Override\n"
        u"                        public ResourceLocation getFlowingTexture() {\n"
        u"                            return ResourceLocation.fromNamespaceAndPath(PotatoST.MODID,\n"
        u"                                    \"block/crude_oil_flow\");\n"
        u"                        }\n"
        u"                    });\n"
        u"                }\n"
        u"            });\n")
    new_crude = u"                    .supportsBoating(false)));\n"
    t = patch(t, old_crude, new_crude, u"crude_oil：覆盖删除")

    print(u"== ③ liquidType 工厂：去掉恒为 300 的形参 + 覆盖 ==")
    t = patch(t, u"""     * @param name        流体注册名（同时决定贴图 {@code block/<name>_still|_flow}）
     * @param density     密度（比水 1000 小 = 浮在水上）
     * @param viscosity   黏度
     * @param temperature 温度（开氏，风味属性）
     */
    private static FluidType liquidType(String name, int density, int viscosity, int temperature) {
        return new FluidType(FluidType.Properties.create()
                .density(density)
                .viscosity(viscosity)
                .temperature(temperature)""",
u"""     * @param name        流体注册名（同时决定贴图 {@code block/<name>_still|_flow}）
     * @param density     密度（比水 1000 小 = 浮在水上）
     * @param viscosity   黏度
     */
    private static FluidType liquidType(String name, int density, int viscosity) {
        return new FluidType(FluidType.Properties.create()
                .density(density)
                .viscosity(viscosity)
                // 温度固定 300（NeoForge 默认也是 300）：四种产物本来就一样，
                // 原先做成形参 ⇒ 四个调用点全传 300，IDE 直接报「形参的值始终为 300」（ZF85 去掉）
                .temperature(300)""", u"liquidType：形参收敛")

    t = patch(t, u"""                .supportsBoating(false))
        {
            @Override
            public void initializeClient(Consumer<IClientFluidTypeExtensions> consumer) {
                consumer.accept(new IClientFluidTypeExtensions() {
                    @Override
                    public ResourceLocation getStillTexture() {
                        return ResourceLocation.fromNamespaceAndPath(PotatoST.MODID,
                                "block/" + name + "_still");
                    }

                    @Override
                    public ResourceLocation getFlowingTexture() {
                        return ResourceLocation.fromNamespaceAndPath(PotatoST.MODID,
                                "block/" + name + "_flow");
                    }
                });
            }
        };
    }""",
u"""                .supportsBoating(false));
    }""", u"liquidType：覆盖删除")

    print(u"== ④ 删掉从未使用的 idOf / byId / GAS_COUNT ==")
    t = patch(t, u"""    /** Number of process gases registered here. */
    public static final int GAS_COUNT = 3;

""", u"", u"GAS_COUNT 删除")
    t = patch(t, u"""    /** 1-based gas index (matches the ids carried in container data); 0 = empty/unknown. */
    public static int idOf(Fluid fluid) {
        if (fluid == null || fluid == Fluids.EMPTY) {
            return 0;
        }
        for (int i = 0; i < GAS_COUNT; i++) {
            if (fluid == gases().get(i)) {
                return i + 1;
            }
        }
        return 0;
    }

    /** Reverse of idOf; anything out of range (including 0) means empty/unknown. */
    public static Fluid byId(int id) {
        if (id <= 0 || id > GAS_COUNT) {
            return Fluids.EMPTY;
        }
        return gases().get(id - 1);
    }

""", u"""    // ⚠ 0.11 ZF85 删掉了这里的 idOf(Fluid) / byId(int)：它们是 ZF72 时代"用 1..3 紧凑编号
    //   同步流体"的产物，ZF73 起**界面改用流体注册表 id**（BuiltInRegistries.FLUID.getId/byId），
    //   这两个方法再没有任何调用点 —— IDE 会报"方法从未使用"，删掉最干净。
    //   （档案 §4.44 那段历史记录保留：它记的是"当年为什么错"，不是"现在还有这个方法"。）

""", u"idOf/byId 删除")

    print(u"== ⑤ 注释：空行警告 + 美式拼写 ==")
    t = patch(t, u"""     * The three process gases, in fixed order (oxygen / hydrogen / chlorine).
     *
     * Deliberately a METHOD, not a static field: DeferredHolder.get() only works
     * after the registry event has bound the holders, and a static initialiser in
     * this class runs far earlier""",
u"""     * The three process gases, in fixed order (oxygen / hydrogen / chlorine).
     * Deliberately a METHOD, not a static field: DeferredHolder.get() only works
     * after the registry event has bound the holders, and a static initializer in
     * this class runs far earlier""", u"gases() 注释：空行 + initializer")

    print(u"== ⑥ 收尾：干净导入 ==")
    t = patch(t, u"import java.util.List;\nimport java.util.function.Consumer;\n",
              u"import java.util.List;\n", u"删 Consumer 导入")
    t = patch(t, u"import net.minecraft.resources.ResourceLocation;\n", u"", u"删 ResourceLocation 导入")
    t = patch(t, u"import net.neoforged.neoforge.client.extensions.common.IClientFluidTypeExtensions;\n",
              u"", u"删 IClientFluidTypeExtensions 导入")

    print(u"== ⑦ 类注释补一句：贴图注册搬去哪了 ==")
    t = patch(t, u" * <p>贴图路径：assets/potato_s_t/textures/block/chlorine_still.png 等（16x16）。</p>",
u""" * <p>贴图路径：assets/potato_s_t/textures/block/chlorine_still.png 等（16x16）。
 * <b>0.11 ZF85 起，贴图的"客户端注册"搬到了 {@code PotatoSTClient#onRegisterClientExtensions}</b>
 * （用 {@code RegisterClientExtensionsEvent}）—— 原先那 5 个 {@code initializeClient} 匿名覆盖
 * 在 NeoForge 21.1 里已经"弃用并标记为移除"，IDE 会当成报错。本文件从此**只做注册**，
 * 不引用任何客户端类。</p>""", u"类注释更新")

    io.open(MODFLUIDS, "w", encoding="utf-8", newline=u"\n").write(t)
    print(u"\n行数 %d → %d" % (before_lines, t.count(u"\n") + 1))
    print(u"失败项 = %d" % len(fails))
    for f in fails:
        print(u"  !! " + f)
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())
