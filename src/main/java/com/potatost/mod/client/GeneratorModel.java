
package com.potatost.mod.client;

import com.mojang.blaze3d.vertex.PoseStack;
import com.mojang.blaze3d.vertex.VertexConsumer;
import net.minecraft.client.model.geom.ModelPart;
import net.minecraft.client.model.geom.PartPose;
import net.minecraft.client.model.geom.builders.CubeListBuilder;
import net.minecraft.client.model.geom.builders.LayerDefinition;
import net.minecraft.client.model.geom.builders.MeshDefinition;
import net.minecraft.client.model.geom.builders.PartDefinition;

/**
 * 发电机模型（Blockbench 5.1.6 导出 -> 1.21.1 Mojmap）。
 * 三个组：stop（导出里的空 bone 组）、run（旋转涡轮，导出里的第二个 bone 组）、bb_main（外圈支架）。
 *
 * ★ 贴图 256×256：texOffs 直接采用导出的原始坐标，与 256 图集一一对应。
 *   （早期那份"128 坐标 ×2"的写法与本布局不符，已废弃。）
 * ★ pivot 由 24 改为 16，模型落地方块内；渲染器保持 translate(0.5, 0.0, 0.5) 即可。
 */
public class GeneratorModel {

    private final ModelPart root;
    private final ModelPart stop;
    private final ModelPart run;
    private final ModelPart bbMain;

    public GeneratorModel(ModelPart root) {
        this.root = root;
        this.stop = root.getChild("stop");
        this.run = root.getChild("run");
        this.bbMain = root.getChild("bb_main");
    }

    public static LayerDefinition createBodyLayer() {
        MeshDefinition mesh = new MeshDefinition();
        PartDefinition root = mesh.getRoot();

        // 空组（导出里的第一个 "bone"，无立方体）
        root.addOrReplaceChild("stop", CubeListBuilder.create(),
                PartPose.offset(0.0F, 16.0F, 0.0F));

        // 旋转涡轮组（导出里的第二个 "bone"）
        root.addOrReplaceChild("run", CubeListBuilder.create()
                        .texOffs(84, 96).addBox(3.0F, -16.0F, -3.0F, 2.0F, 16.0F, 6.0F)
                        .texOffs(102, 22).addBox(-1.0F, -16.0F, -5.0F, 4.0F, 16.0F, 4.0F)
                        .texOffs(70, 102).addBox(1.0F, -16.0F, -1.0F, 2.0F, 16.0F, 2.0F)
                        .texOffs(100, 96).addBox(-3.0F, -16.0F, -5.0F, 2.0F, 16.0F, 6.0F)
                        .texOffs(102, 42).addBox(-3.0F, -16.0F, 1.0F, 6.0F, 16.0F, 2.0F)
                        .texOffs(54, 102).addBox(-3.0F, -16.0F, 3.0F, 6.0F, 16.0F, 2.0F)
                        .texOffs(102, 0).addBox(-5.0F, -16.0F, -3.0F, 2.0F, 16.0F, 6.0F)
                        .texOffs(102, 60).addBox(-1.0F, -16.0F, -1.0F, 2.0F, 20.0F, 2.0F),
                PartPose.offset(0.0F, 16.0F, 0.0F));

        // 外圈支架
        PartDefinition bbMain = root.addOrReplaceChild("bb_main", CubeListBuilder.create()
                        .texOffs(66, 78).addBox(-8.0F, -16.0F, -4.0F, 1.0F, 16.0F, 8.0F)
                        .texOffs(84, 0).addBox(7.0F, -16.0F, -4.0F, 1.0F, 16.0F, 8.0F)
                        .texOffs(78, 102).addBox(1.0F, -16.0F, 6.0F, 2.0F, 16.0F, 1.0F)
                        .texOffs(110, 60).addBox(-4.0F, -16.0F, -7.0F, 2.0F, 16.0F, 1.0F)
                        .texOffs(110, 77).addBox(-3.0F, -16.0F, 6.0F, 2.0F, 16.0F, 1.0F)
                        .texOffs(36, 111).addBox(0.0F, -16.0F, -7.0F, 2.0F, 16.0F, 1.0F),
                PartPose.offset(0.0F, 16.0F, 0.0F));

        // 斜向支撑柱（bb_main 子部件）
        bbMain.addOrReplaceChild("cube_r1", CubeListBuilder.create()
                        .texOffs(116, 60).addBox(-1.0F, -16.0F, 0.0F, 2.0F, 16.0F, 1.0F),
                PartPose.offsetAndRotation(-6.0F, 0.0F, -1.0F, 0.0F, -1.5708F, 0.0F));
        bbMain.addOrReplaceChild("cube_r2", CubeListBuilder.create()
                        .texOffs(30, 113).addBox(-1.0F, -16.0F, 0.0F, 2.0F, 16.0F, 1.0F),
                PartPose.offsetAndRotation(7.0F, 0.0F, -3.0F, 0.0F, -1.1345F, 0.0F));
        bbMain.addOrReplaceChild("cube_r3", CubeListBuilder.create()
                        .texOffs(24, 113).addBox(-1.0F, -16.0F, 0.0F, 2.0F, 16.0F, 1.0F),
                PartPose.offsetAndRotation(4.0F, 0.0F, 5.0F, 0.0F, 0.7854F, 0.0F));
        bbMain.addOrReplaceChild("cube_r4", CubeListBuilder.create()
                        .texOffs(18, 113).addBox(-1.0F, -16.0F, 0.0F, 2.0F, 16.0F, 1.0F),
                PartPose.offsetAndRotation(6.0F, 0.0F, 3.0F, 0.0F, 1.0908F, 0.0F));
        bbMain.addOrReplaceChild("cube_r5", CubeListBuilder.create()
                        .texOffs(12, 113).addBox(-1.0F, -16.0F, 0.0F, 2.0F, 16.0F, 1.0F),
                PartPose.offsetAndRotation(-6.0F, 0.0F, 2.0F, 0.0F, -1.5708F, 0.0F));
        bbMain.addOrReplaceChild("cube_r6", CubeListBuilder.create()
                        .texOffs(6, 113).addBox(-1.0F, -16.0F, 0.0F, 2.0F, 16.0F, 1.0F),
                PartPose.offsetAndRotation(-7.0F, 0.0F, -4.0F, 0.0F, 1.0908F, 0.0F));
        bbMain.addOrReplaceChild("cube_r7", CubeListBuilder.create()
                        .texOffs(0, 113).addBox(-1.0F, -16.0F, 0.0F, 2.0F, 16.0F, 1.0F),
                PartPose.offsetAndRotation(7.0F, 0.0F, 0.0F, 0.0F, -1.5708F, 0.0F));
        bbMain.addOrReplaceChild("cube_r8", CubeListBuilder.create()
                        .texOffs(18, 89).addBox(-1.4142F, -16.0F, -4.0F, 1.0F, 16.0F, 8.0F),
                PartPose.offsetAndRotation(-5.0F, 0.0F, 5.0F, 0.0F, 0.7854F, 0.0F));
        bbMain.addOrReplaceChild("cube_r9", CubeListBuilder.create()
                        .texOffs(48, 111).addBox(-1.0F, -16.0F, 0.0F, 2.0F, 16.0F, 1.0F),
                PartPose.offsetAndRotation(-5.0F, 0.0F, 5.0F, 0.0F, -0.7854F, 0.0F));
        bbMain.addOrReplaceChild("cube_r10", CubeListBuilder.create()
                        .texOffs(42, 111).addBox(-1.0F, -16.0F, 0.0F, 2.0F, 16.0F, 1.0F),
                PartPose.offsetAndRotation(5.0F, 0.0F, -5.0F, 0.0F, -0.7854F, 0.0F));
        bbMain.addOrReplaceChild("cube_r11", CubeListBuilder.create()
                        .texOffs(0, 89).addBox(0.0F, -16.0F, -4.0F, 1.0F, 16.0F, 8.0F),
                PartPose.offsetAndRotation(5.0F, 0.0F, -5.0F, 0.0F, 0.7854F, 0.0F));
        bbMain.addOrReplaceChild("cube_r12", CubeListBuilder.create()
                        .texOffs(36, 87).addBox(0.0F, -16.0F, -4.0F, 1.0F, 16.0F, 8.0F),
                PartPose.offsetAndRotation(-6.0F, 0.0F, -6.0F, 0.0F, -0.7854F, 0.0F));
        bbMain.addOrReplaceChild("cube_r13", CubeListBuilder.create()
                        .texOffs(84, 72).addBox(0.0F, -16.0F, -4.0F, 1.0F, 16.0F, 8.0F),
                PartPose.offsetAndRotation(0.0F, 0.0F, 7.0F, 0.0F, -1.5708F, 0.0F));
        bbMain.addOrReplaceChild("cube_r14", CubeListBuilder.create()
                        .texOffs(84, 48).addBox(0.0F, -16.0F, -4.0F, 1.0F, 16.0F, 8.0F),
                PartPose.offsetAndRotation(0.0F, 0.0F, -8.0F, 0.0F, -1.5708F, 0.0F));
        bbMain.addOrReplaceChild("cube_r15", CubeListBuilder.create()
                        .texOffs(84, 24).addBox(0.0F, -16.0F, -4.0F, 1.0F, 16.0F, 8.0F),
                PartPose.offsetAndRotation(5.0F, 0.0F, 5.0F, 0.0F, -0.7854F, 0.0F));

        return LayerDefinition.create(mesh, 256, 256);   // ← 256×256 贴图
    }

    /** rotorAngle 只作用于 run（涡轮）组，stop / bb_main 静止 */
    public void render(PoseStack poseStack, VertexConsumer consumer,
                       int packedLight, int packedOverlay, float rotorAngle) {
        this.run.yRot = rotorAngle;
        this.stop.render(poseStack, consumer, packedLight, packedOverlay, 0xFFFFFFFF);
        this.run.render(poseStack, consumer, packedLight, packedOverlay, 0xFFFFFFFF);
        this.bbMain.render(poseStack, consumer, packedLight, packedOverlay, 0xFFFFFFFF);
    }
}