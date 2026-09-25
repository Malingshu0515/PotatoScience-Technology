package com.potatost.mod.client;

import com.potatost.mod.ElectrolyzerBlockEntity;
import com.potatost.mod.ElectrolyzerMenu;
import com.potatost.mod.ModFluids;
import com.potatost.mod.client.gui.MachineScreen;
import com.potatost.mod.client.gui.parts.EnergyBarPart;
import com.potatost.mod.client.gui.parts.FluidTankPart;

import net.minecraft.network.chat.Component;
import net.minecraft.world.entity.player.Inventory;
import net.minecraft.world.level.material.Fluids;

/**
 * 电解器界面：只负责"摆件"。
 * 面板 / 槽位 / 悬停提示全由 MachineScreen 处理。
 * 双配方版：四根罐柱 = 水（输入）+ 氧气 / 氯气 / 氢气（产物，名字自动取 lang）。
 */
public class ElectrolyzerScreen extends MachineScreen<ElectrolyzerMenu> {

    public ElectrolyzerScreen(ElectrolyzerMenu menu, Inventory playerInventory, Component title) {
        super(menu, playerInventory, title, 176, 184);

        // 水罐（名字用原版键 block.minecraft.water，最稳）
        parts.add(new FluidTankPart(26, 17, 18, 52, menu::getInputAmount,
                ElectrolyzerBlockEntity.INPUT_CAPACITY, Fluids.WATER,
                Component.translatable("block.minecraft.water")));

        // 三根产物罐：氧气（纯水配方）/ 氯气（盐水配方）/ 氢气（两配方共用）
        parts.add(new FluidTankPart(87, 17, 18, 52, menu::getOxygenAmount,
                ElectrolyzerBlockEntity.OXYGEN_CAPACITY, ModFluids.OXYGEN.get()));
        parts.add(new FluidTankPart(107, 17, 18, 52, menu::getChlorineAmount,
                ElectrolyzerBlockEntity.CHLORINE_CAPACITY, ModFluids.CHLORINE.get()));
        parts.add(new FluidTankPart(127, 17, 18, 52, menu::getHydrogenAmount,
                ElectrolyzerBlockEntity.HYDROGEN_CAPACITY, ModFluids.HYDROGEN.get()));

        // 能量条
        parts.add(new EnergyBarPart(67, 17, 10, 52, menu::getEnergy,
                ElectrolyzerBlockEntity.MAX_ENERGY));
    }
}