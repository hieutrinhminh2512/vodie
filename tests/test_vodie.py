import pytest
import os
from pathlib import Path

# Import config đầu tiên để inject FFmpeg path vào môi trường
import src.config
from pydub import AudioSegment

from src.director.script_analyzer import HorrorScriptAnalyzer, ScriptSegment
from src.tts.text_normalizer import TextNormalizer
from src.tts.voice_manager import VoiceManager
from src.audio_engine.dynamic_pacing import DynamicPacingController
from src.audio_engine.spatial_panning import SpatialAudioEngine
from src.audio_engine.jumpscare import JumpScareController
from src.audio_engine.voice_effects import VoiceEffectsProcessor
from src.storage.db import DatabaseManager
from src.storage.queue_manager import QueueManager
from src.safety.compliance import SafetyCompliance


def test_text_normalizer():
    """Kiểm tra chuẩn hóa từ ngữ tiếng Việt & thuật ngữ."""
    normalizer = TextNormalizer()
    sample = "Nghe creepypasta về bà Út Lụa và xem jumpscare trên YouTube bằng AI TTS."
    res = normalizer.normalize(sample)
    assert "cờ ri pi pát ta" in res
    assert "dầm sờ ke" in res
    assert "du túp" in res
    assert "tê tê ét" in res


def test_script_analyzer_tension_and_panning():
    """Kiểm tra AI Director phân tích kịch bản kinh dị."""
    director = HorrorScriptAnalyzer(mood="kinh_di_nang")
    text = (
        "Đêm Đà Lạt lạnh buốt sương mù.\n"
        "Có tiếng thì thầm bên tai lướt qua.\n"
        "Ai đó đang đứng sau lưng tôi.\n"
        "Đột ngột một bóng ma kinh hoàng vồ lấy khiến tôi hét lên!"
    )
    segments = director.analyze_text(text)
    assert len(segments) == 4

    # Câu có thì thầm -> Panning
    assert segments[1].spatial_position in ["left_to_right", "right"]

    # Câu có sau lưng -> rear
    assert segments[2].spatial_position == "rear"

    # Câu cao trào cuối cùng -> Jump scare & tension cao
    assert segments[3].tension >= 7.0
    assert segments[3].is_jumpscare is True


def test_voice_manager_consent():
    """Kiểm tra bắt buộc cam kết bản quyền khi nhái giọng."""
    vm = VoiceManager()
    voices = vm.list_voices()
    assert len(voices) >= 2  # Bắc & Nam

    # Chưa tích cam kết bản quyền -> Bắt buộc ném ngoại lệ PermissionError
    with pytest.raises(PermissionError):
        vm.register_cloned_voice(
            voice_id="fake_voice",
            name="Test Voice",
            source_audio_path="sample.wav",
            consent_confirmed=False
        )


def test_dynamic_pacing():
    """Kiểm tra co giãn nhịp độ theo tension."""
    # Mở đầu -> đọc chậm
    rate_open, pause_open = DynamicPacingController.calculate_rate_and_pause(2.0, is_opening=True)
    assert rate_open == "-8%"
    assert pause_open >= 1.0

    # Cao trào tension = 9.0 -> đọc nhanh dồn dập
    rate_climax, pause_climax = DynamicPacingController.calculate_rate_and_pause(9.0)
    assert rate_climax == "+18%"
    assert pause_climax <= 0.5


def test_spatial_panning_stereo():
    """Kiểm tra xử lý âm thanh không gian (Binaural 3D)."""
    # Tạo một đoạn âm thanh mẫu 500ms
    test_audio = AudioSegment.silent(duration=500).set_channels(2)

    panned_left = SpatialAudioEngine.apply_panning(test_audio, "left")
    assert panned_left.channels == 2

    panned_rear = SpatialAudioEngine.apply_panning(test_audio, "rear")
    assert panned_rear.channels == 2


def test_jumpscare_safe_limiter():
    """Kiểm tra bộ giới hạn âm lượng True Peak Limiter (-1 dBTP)."""
    controller = JumpScareController(gentle_mode=False, peak_limit_db=-1.0)
    # Tạo audio giả lập
    sfx = AudioSegment.silent(duration=300)
    js = controller.create_jumpscare_segment(sfx)
    assert len(js) >= 1500  # Bao gồm cả khoảng lặng nín thở 1.5s
    assert js.max_dBFS <= -1.0


def test_database_sqlite(tmp_path):
    """Kiểm tra cơ sở dữ liệu SQLite lưu trữ dự án và hàng đợi."""
    db_file = tmp_path / "test_vodie.db"
    db = DatabaseManager(db_path=db_file)

    # Tạo dự án
    proj_id = db.create_project("Chuyện Ma Đêm Khuya", "Kịch bản mẫu...", mood="kinh_di_nang")
    assert proj_id > 0

    projects = db.list_projects()
    assert len(projects) == 1
    assert projects[0]["title"] == "Chuyện Ma Đêm Khuya"

    # Kiểm tra hàng đợi batch queue
    queue = QueueManager(db=db)
    task_id = queue.add_to_queue(proj_id, "Chuyện Ma Đêm Khuya")
    assert task_id > 0

    pending = queue.get_pending_tasks()
    assert len(pending) == 1
    assert pending[0]["status"] == "pending"

    queue.update_status(task_id, status="completed", progress=100)
    updated_pending = queue.get_pending_tasks()
    assert len(updated_pending) == 0


def test_safety_compliance():
    """Kiểm tra tuân thủ an toàn & pháp lý."""
    assert SafetyCompliance.verify_voice_consent(True) is True
    with pytest.raises(PermissionError):
        SafetyCompliance.verify_voice_consent(False)
