package com.potatost.mod.sound;

import net.minecraft.core.registries.BuiltInRegistries;
import net.minecraft.resources.ResourceLocation;
import net.minecraft.sounds.SoundEvent;
import net.neoforged.neoforge.registries.DeferredHolder;
import net.neoforged.neoforge.registries.DeferredRegister;

public final class ModSounds {
    private ModSounds() {
    }

    public static final DeferredRegister<SoundEvent> SOUND_EVENTS =
            DeferredRegister.create(BuiltInRegistries.SOUND_EVENT, "potato_s_t");

    public static final DeferredHolder<SoundEvent, SoundEvent> GENERATOR_RUNNING =
            SOUND_EVENTS.register("generator_running",
                    () -> SoundEvent.createVariableRangeEvent(
                            ResourceLocation.fromNamespaceAndPath("potato_s_t", "generator_running")));

    public static final DeferredHolder<SoundEvent, SoundEvent> ELECTROLYZER_RUNNING =
            SOUND_EVENTS.register("electrolyzer_running",
                    () -> SoundEvent.createVariableRangeEvent(
                            ResourceLocation.fromNamespaceAndPath("potato_s_t", "electrolyzer_running")));

    /** 音乐唱片《共和之砧》。曲目数据（时长/比较器输出/唱片机曲目）见 data/potato_s_t/jukebox_song/anvil_of_the_republic.json */
    public static final DeferredHolder<SoundEvent, SoundEvent> MUSIC_DISC_ANVIL_OF_THE_REPUBLIC =
            SOUND_EVENTS.register("music_disc_anvil_of_the_republic",
                    () -> SoundEvent.createVariableRangeEvent(
                            ResourceLocation.fromNamespaceAndPath("potato_s_t", "music_disc_anvil_of_the_republic")));

    /** 音乐唱片《茉莉花（管弦乐）》（0.11 ZF93）。曲目数据见 data/potato_s_t/jukebox_song/jasmine_flower.json；
     *  音频实测 147.102132 s / 单声道 44100 Hz（build/zftools/_zf93_ogg.py 两条算法互核）。 */
    public static final DeferredHolder<SoundEvent, SoundEvent> MUSIC_DISC_JASMINE_FLOWER =
            SOUND_EVENTS.register("music_disc_jasmine_flower",
                    () -> SoundEvent.createVariableRangeEvent(
                            ResourceLocation.fromNamespaceAndPath("potato_s_t", "music_disc_jasmine_flower")));

    /**
     * 灌装机完成一次罐装的泄压声（0.10）。
     *
     * <p>素材是 freesound 的 short gas leak（#98286），转换流程见 {@code build/zftools/MakeSfx.py}：
     * 掐掉开头 0.708s 静音与结尾 0.414s 死气 → 48000 重采样到 44100 → 单声道 Vorbis，成品 1.35s。</p>
     */
    public static final DeferredHolder<SoundEvent, SoundEvent> FILLING_MACHINE_COMPLETE =
            SOUND_EVENTS.register("filling_machine_complete",
                    () -> SoundEvent.createVariableRangeEvent(
                            ResourceLocation.fromNamespaceAndPath("potato_s_t", "filling_machine_complete")));

    /**
     * 微型粉碎机运行中的循环嗡嗡声（0.10）。
     *
     * <p>素材是 freesound 的 coffee machine（#40834）。**循环音不能带淡入淡出**，
     * 否则每绕一圈都听得见一次音量塌陷；用 {@code MakeSfx.py --loop} 切出 6.45s 稳态段并做接缝交叉淡化，
     * 响度对齐到 0.10 RMS（和电解器循环一致——循环音的 volume 在代码里固定 1.0，只能靠文件本身对齐）。</p>
     */
    public static final DeferredHolder<SoundEvent, SoundEvent> MICRO_CRUSHER_RUNNING =
            SOUND_EVENTS.register("micro_crusher_running",
                    () -> SoundEvent.createVariableRangeEvent(
                            ResourceLocation.fromNamespaceAndPath("potato_s_t", "micro_crusher_running")));

    /**
     * 液压机运行中的循环液压声（0.10 ZF36）。
     *
     * <p>素材是用户给的 freesound hydraulic door（#107449，3.77s / 44100 Hz / 单声道）。它是
     * "开门…停顿…关门"一整段，<b>没有稳态段可切</b>，所以整段拿去循环 —— 好在首尾本来就安静，
     * 接缝天然干净。用 {@code MakeSfx.py --loop} 切 0.00~3.76s、末尾 200ms 与开头交叉淡化，
     * 成品 **3.56s**，工具回读的**接缝首尾差 = 0.0017**（越接近 0 越好）。</p>
     *
     * <p>响度本想对齐到 0.10 RMS（和电解器 / 微型粉碎机一致），但按那个增益会削波
     * ⇒ 工具自动改用**峰值保护**（增益 4.848），实落 **0.0794 RMS / 峰值 0.995**。
     * <b>循环音的 volume 在代码里固定 1.0，只能靠文件本身对齐</b>，所以这个数就是最终音量。</p>
     */
    public static final DeferredHolder<SoundEvent, SoundEvent> HYDRAULIC_PRESS_RUNNING =
            SOUND_EVENTS.register("hydraulic_press_running",
                    () -> SoundEvent.createVariableRangeEvent(
                            ResourceLocation.fromNamespaceAndPath("potato_s_t", "hydraulic_press_running")));

    /**
     * 合金冶炼炉运行中的循环电机声（0.10 ZF64）。
     *
     * <p>素材是<b>用户直接给的</b> {@code eaglaxle-background-motor-sound-453361}（freesound #453361）：
     * 原文件 <b>立体声</b> 44100 Hz 8.75s / RMS 0.0428 —— 立体声在 MC 里不吃距离衰减，
     * 所以按用户要求「如果不是单声道调为单声道」用 {@code MakeSfx.py} 降成单声道。</p>
     *
     * <p>转换配方：{@code --loop --crossfade 400 --target-rms 0.10} ⇒
     * 成品 <b>单声道 8.27s</b>、RMS 0.1003、峰值 0.304、<b>接缝首尾差 0.0008</b>
     * （素材首尾本来就淡到接近 0，交叉淡化只是把接缝抹平；响度对齐到 0.10 与本项目其它机器循环一致）。</p>
     */
    public static final DeferredHolder<SoundEvent, SoundEvent> ALLOY_SMELTER_RUNNING =
            SOUND_EVENTS.register("alloy_smelter_running",
                    () -> SoundEvent.createVariableRangeEvent(
                            ResourceLocation.fromNamespaceAndPath("potato_s_t", "alloy_smelter_running")));
}
