package com.potatost.mod.menu;

// 还原说明：原文 2026-09-13 被外部删除；由当日编译产物反编译还原（逻辑与原版一致）。

import net.minecraft.world.entity.player.Inventory;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.inventory.AbstractContainerMenu;
import net.minecraft.world.inventory.ContainerLevelAccess;
import net.minecraft.world.inventory.MenuType;
import net.minecraft.world.inventory.Slot;
import net.minecraft.world.item.ItemStack;

public abstract class MachineMenu extends AbstractContainerMenu {
   private final int machineSlots;
   protected final ContainerLevelAccess access;

   protected MachineMenu(MenuType<?> type, int containerId, int machineSlots, ContainerLevelAccess access) {
      super(type, containerId);
      this.machineSlots = machineSlots;
      this.access = access;
   }

   protected void addPlayerInventory(Inventory playerInventory) {
      this.addPlayerInventory(playerInventory, 102);
   }

   protected void addPlayerInventory(Inventory playerInventory, int startY) {
      for (int row = 0; row < 3; row++) {
         for (int col = 0; col < 9; col++) {
            this.addSlot(new Slot(playerInventory, col + row * 9 + 9, 8 + col * 18, startY + row * 18));
         }
      }

      for (int col = 0; col < 9; col++) {
         this.addSlot(new Slot(playerInventory, col, 8 + col * 18, startY + 58));
      }
   }

   public int getMachineSlots() {
      return this.machineSlots;
   }

   protected int getMachineSlotFor(ItemStack stack) {
      return -1;
   }

   public ItemStack quickMoveStack(Player player, int index) {
      Slot slot = (Slot)this.slots.get(index);
      if (slot != null && slot.hasItem()) {
         ItemStack stack = slot.getItem();
         ItemStack copy = stack.copy();
         if (index < this.machineSlots) {
            if (!this.moveItemStackTo(stack, this.machineSlots, this.slots.size(), true)) {
               return ItemStack.EMPTY;
            }
         } else {
            int target = this.getMachineSlotFor(stack);
            if (target < 0 || !this.moveItemStackTo(stack, target, target + 1, false)) {
               if (index >= this.machineSlots + 27) {
                  if (!this.moveItemStackTo(stack, this.machineSlots, this.machineSlots + 27, false)) {
                     return ItemStack.EMPTY;
                  }
               } else if (!this.moveItemStackTo(stack, this.machineSlots + 27, this.slots.size(), false)) {
                  return ItemStack.EMPTY;
               }
            }
         }

         if (stack.isEmpty()) {
            slot.set(ItemStack.EMPTY);
         } else {
            slot.setChanged();
         }

         return copy;
      } else {
         return ItemStack.EMPTY;
      }
   }
}
