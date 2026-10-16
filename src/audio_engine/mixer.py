from pathlib import Path
from typing import List, Optional
from pydub import AudioSegment

from .spatial_panning import SpatialAudioEngine
from .jumpscare import JumpScareController
from .voice_effects import VoiceEffectsProcessor
from .vocal_mastering import VocalMasteringChain
from .bgm_synth import ProceduralHorrorBGM
from ..director.script_analyzer import ScriptSegment
from ..config import MOODS, SETTINGS


class HorrorAudioMixer:
    """
    Multi-Track Audio Mixer:
    - Lắp ráp giọng đọc từng câu kèm hiệu ứng không gian (Spatial Panning).
    - Áp dụng Mastering Vocal Warmth (khử chất giọng AI thô).
    - Tự động tạo BGM kinh dị Dark Ambient và Auto-Ducking.
    - Lồng ghép SFX và Jump scare đúng thời điểm.
    """

    def __init__(self, mood: str = "tam_linh_dan_gian"):
        self.mood = mood
        self.mood_cfg = MOODS.get(mood, {})
        self.jumpscare_ctrl = JumpScareController()

    def build_story_track(
        self,
        segments: List[ScriptSegment],
        audio_files: List[Path]
    ) -> AudioSegment:
        """Ghép các câu thoại thành track chính hoàn chỉnh kèm khoảng lặng và panning."""
        master_voice = AudioSegment.empty()

        for seg, file_path in zip(segments, audio_files):
            if not file_path.exists():
                continue

            sentence_audio = AudioSegment.from_file(str(file_path))

            # 1. Áp dụng Voice Preset (ma_nu, quy_du, vong_hon) nếu có
            if seg.voice_preset:
                sentence_audio = VoiceEffectsProcessor.apply_preset(sentence_audio, seg.voice_preset)
            else:
                # Áp dụng Mastering làm ấm giọng kể chuyện ma cho người dẫn
                sentence_audio = VocalMasteringChain.apply_horror_mastering(sentence_audio)

            # 2. Áp dụng Spatial Panning (Binaural 3D)
            sentence_audio = SpatialAudioEngine.apply_panning(sentence_audio, seg.spatial_position)

            # 3. Nối câu vào track chính
            master_voice += sentence_audio

            # 4. Chèn Jump scare hoặc SFX nếu có cue
            if seg.is_jumpscare:
                sfx = AudioSegment.silent(duration=800)
                js_segment = self.jumpscare_ctrl.create_jumpscare_segment(sfx)
                master_voice += js_segment

            # 5. Khoảng nghỉ (Pause ma mị)
            pause_ms = int(seg.pause_after * 1000)
            master_voice += AudioSegment.silent(duration=pause_ms)

        # 6. Tự động lót BGM kinh dị u ám (Dark Ambient Drone)
        total_duration_sec = len(master_voice) / 1000.0
        bgm_track = ProceduralHorrorBGM.generate_dark_ambient(total_duration_sec)

        # Trộn nhạc nền với giọng đọc (giọng đọc lấn át -14dB BGM)
        return self.mix_with_bgm(master_voice, bgm_track=bgm_track, ducking_db=-14.0)

    def mix_with_bgm(
        self,
        voice_track: AudioSegment,
        bgm_track: Optional[AudioSegment] = None,
        ducking_db: float = -14.0
    ) -> AudioSegment:
        """Trộn nhạc nền với Auto-Ducking khi có giọng đọc."""
        if bgm_track is None:
            return voice_track

        if len(bgm_track) < len(voice_track):
            loop_count = (len(voice_track) // len(bgm_track)) + 1
            bgm_track = bgm_track * loop_count

        bgm_track = bgm_track[:len(voice_track)]
        ducked_bgm = bgm_track.apply_gain(ducking_db)

        return ducked_bgm.overlay(voice_track)
