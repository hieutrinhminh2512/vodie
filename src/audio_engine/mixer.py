from pathlib import Path
from typing import List, Optional
from pydub import AudioSegment

from .spatial_panning import SpatialAudioEngine
from .jumpscare import JumpScareController
from .voice_effects import VoiceEffectsProcessor
from ..director.script_analyzer import ScriptSegment
from ..config import MOODS, SETTINGS


class HorrorAudioMixer:
    """
    Multi-Track Audio Mixer:
    - Lắp ráp giọng đọc từng câu kèm hiệu ứng không gian (Spatial Panning).
    - Lồng ghép SFX và Jump scare đúng thời điểm.
    - Nhạc nền BGM theo Mood kèm Auto-Ducking khi có giọng nói.
    """

    def __init__(self, mood: str = "kinh_di_nang"):
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

            # 2. Áp dụng Spatial Panning (Binaural 3D)
            sentence_audio = SpatialAudioEngine.apply_panning(sentence_audio, seg.spatial_position)

            # 3. Nối câu vào track chính
            master_voice += sentence_audio

            # 4. Chèn Jump scare hoặc SFX nếu có cue
            if seg.is_jumpscare:
                # Tạo tiếng giật mình rợn tóc gáy
                sfx = AudioSegment.silent(duration=800)  # placeholder SFX
                js_segment = self.jumpscare_ctrl.create_jumpscare_segment(sfx)
                master_voice += js_segment

            # 5. Khoảng nghỉ (Pause)
            pause_ms = int(seg.pause_after * 1000)
            master_voice += AudioSegment.silent(duration=pause_ms)

        return master_voice

    def mix_with_bgm(
        self,
        voice_track: AudioSegment,
        bgm_track: Optional[AudioSegment] = None,
        ducking_db: float = -14.0
    ) -> AudioSegment:
        """Trộn nhạc nền với Auto-Ducking khi có giọng đọc."""
        if bgm_track is None:
            return voice_track

        # Loop BGM cho đủ độ dài
        if len(bgm_track) < len(voice_track):
            loop_count = (len(voice_track) // len(bgm_track)) + 1
            bgm_track = bgm_track * loop_count

        bgm_track = bgm_track[:len(voice_track)]
        # Hạ âm lượng BGM để tôn giọng đọc (Ducking)
        ducked_bgm = bgm_track.apply_gain(ducking_db)

        # Trộn 2 track
        return ducked_bgm.overlay(voice_track)
