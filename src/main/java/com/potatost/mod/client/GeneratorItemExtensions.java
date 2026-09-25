package com.potatost.mod.client;

import net.minecraft.client.renderer.BlockEntityWithoutLevelRenderer;
import net.neoforged.neoforge.client.extensions.common.IClientItemExtensions;

/**
 * 发电机物品的“自定义渲染”接线：把 图标/手持/掉落物 交给 GeneratorItemRenderer（BEWLR 单例）。
 * 生效前提：models/item/generator.json 的 parent 是 "builtin/entity"（现文件已是）。
 */
public class GeneratorItemExtensions implements IClientItemExtensions {

    @Override
    public BlockEntityWithoutLevelRenderer getCustomRenderer() {
        return GeneratorItemRenderer.getInstance();   // 懒加载单例：官方要求整个 mod 只 new 一次
    }
}