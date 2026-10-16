from pathlib import Path
from typing import List, Optional
from pydub import AudioSegment

from .spatial_panning import SpatialAudioEngine
from .jumpscare import JumpScareController
from .voice_effects import VoiceEffectsProcessor
from .vocal_mastering import VocalMasteringChain
from .bgm_synth import ProceduralHorrorBGM
from ..director.script_analyzer import ScriptSegment
from ..config import ASSETS_DIR, MOODS, SETTINGS


def load_sfx(cue: str) -> Optional[AudioSegment]:
    """Tìm assets/sfx/<cue>.wav|mp3|ogg. Không có file thì bỏ qua (không chèn tiếng giả)."""
    for ext in ("wav", "mp3", "ogg", "flac"):
        path = ASSETS_DIR / "sfx" / f"{cue}.{ext}"
        if path.exists():
            return AudioSegment.from_file(str(path))
    return None


class HorrorAudioMixer:
    """
    Multi-Track Audio Mixer:
    - Lắp ráp giọng đọc từng câu kèm hiệu ứng không gian (Spatial Panning).
    - Áp dụng Mastering Vocal Warmth (khử chất giọng AI thô ráp, tạo độ trầm ấm băng cối).
    - Tự động tạo BGM kinh dị Dark Ambient và Auto-Ducking.
    - Lồng ghép SFX và Jump scare đúng thời điểm.
    """

    def __init__(self, mood: str = "tam_linh_dan_gian", speaker_style: str = "nguyen_ngoc_ngan"):
        self.mood = mood
        self.speaker_style = speaker_style
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

            sentence_audio = (AudioSegment.from_file(str(file_path))
                              .set_frame_rate(44100).set_sample_width(2))

            # 1. Áp dụng Voice Preset (ma_nu, quy_du, vong_hon) nếu có
            if seg.voice_preset:
                sentence_audio = VoiceEffectsProcessor.apply_preset(sentence_audio, seg.voice_preset)
            else:
                # Áp dụng Mastering làm ấm giọng kể chuyện ma cho người dẫn theo phong cách
                sentence_audio = VocalMasteringChain.apply_horror_mastering(
                    sentence_audio, speaker_style=self.speaker_style
                )

            # 1b. Âm lượng theo cảm xúc (thì thầm nhỏ, hét to)
            gain = {"thi_tham": -4.0, "het": 2.0, "so_hai": -1.0}.get(getattr(seg, "emotion", ""), 0.0)
            if gain:
                sentence_audio = sentence_audio.apply_gain(gain)

            # 2. Áp dụng Spatial Panning (Binaural 3D)
            sentence_audio = SpatialAudioEngine.apply_panning(sentence_audio, seg.spatial_position)

            # 3. Nối câu vào track chính, SFX (nếu có file) lót nhỏ dưới câu
            sfx = load_sfx(seg.sfx_cue) if seg.sfx_cue and not seg.is_jumpscare else None
            if sfx is not None:
                sfx = sfx.set_frame_rate(44100).set_channels(2)[: len(sentence_audio) + 1500] - 12
                sentence_audio = sentence_audio.overlay(sfx.fade_out(400))
            master_voice += sentence_audio.set_channels(2)

            # 4. Jump scare: im lặng nín thở rồi bật SFX (đã giới hạn peak)
            if seg.is_jumpscare:
                js_sfx = load_sfx("jumpscare_screech") or AudioSegment.silent(duration=800)
                js_segment = self.jumpscare_ctrl.create_jumpscare_segment(js_sfx.set_frame_rate(44100))
                master_voice += js_segment.set_channels(2)

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
