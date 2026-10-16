import pytest

# Import config đầu tiên để inject FFmpeg path vào môi trường
import src.config  # noqa: F401
from pydub import AudioSegment

from src.director.script_analyzer import Character, HorrorScriptAnalyzer, detect_region
from src.tts.text_normalizer import TextNormalizer
from src.tts.voice_manager import VoiceManager
from src.audio_engine.dynamic_pacing import DynamicPacingController
from src.audio_engine.spatial_panning import SpatialAudioEngine
from src.audio_engine.jumpscare import JumpScareController
from src.storage.db import DatabaseManager
from src.storage.queue_manager import QueueManager
from src.safety.compliance import SafetyCompliance


# ---------------------------------------------------------------- chuẩn hóa tiếng Việt
@pytest.fixture
def norm():
    return TextNormalizer(custom_dict={})


@pytest.mark.parametrize("raw,expected", [
    ("1975", "một nghìn chín trăm bảy mươi lăm"),
    ("21", "hai mươi mốt"),
    ("15", "mười lăm"),
    ("24", "hai mươi tư"),
    ("105", "một trăm linh năm"),
    ("1005", "một nghìn không trăm linh năm"),
    ("1.000.000", "một triệu"),
    ("3,5", "ba phẩy năm"),
])
def test_number_reading(norm, raw, expected):
    assert norm.normalize(raw) == expected


def test_southern_dialect_numbers():
    n = TextNormalizer(custom_dict={}, dialect="nam")
    assert n.normalize("105") == "một trăm lẻ năm"
    assert n.normalize("2000") == "hai ngàn"


def test_dates_times_units(norm):
    out = norm.normalize("Đêm 15/8/1990 lúc 23h15, trời 18°C, đi 60km/h.")
    assert "mười lăm tháng tám năm một nghìn chín trăm chín mươi" in out
    assert "hai mươi ba giờ mười lăm phút" in out
    assert "mười tám độ xê" in out
    assert "sáu mươi ki lô mét trên giờ" in out
    assert norm.normalize("rằm tháng 4") == "rằm tháng tư"


def test_money_percent_abbrev_teencode(norm):
    out = norm.normalize("Ở TP.HCM giá 500k, 50% ng ko tin.")
    assert "thành phố Hồ Chí Minh" in out
    assert "năm trăm nghìn" in out
    assert "năm mươi phần trăm" in out
    assert "người không tin" in out


def test_roman_ordinal_phone(norm):
    assert norm.normalize("thế kỷ XIX") == "thế kỷ mười chín"
    assert norm.normalize("lần thứ 1") == "lần thứ nhất"
    assert norm.normalize("gọi 0912345678") == "gọi không chín một hai ba bốn năm sáu bảy tám"


def test_dialogue_marks_not_spoken(norm):
    assert norm.normalize("- Ai đó?") == "Ai đó?"
    assert norm.normalize('"Xuống đây..." - nó cười.') == "Xuống đây..., nó cười."


def test_pronunciation_dict():
    n = TextNormalizer(custom_dict={"exact_replacements": {"creepypasta": "cờ ri pi pát ta"},
                                    "acronyms": {"AI": "ây ai"}})
    assert n.normalize("Nghe creepypasta về AI") == "Nghe cờ ri pi pát ta về ây ai"
    assert n.normalize("TRAIN") == "TRAIN"  # không thay giữa từ


def test_project_pronunciation_dict_loads():
    out = TextNormalizer().normalize("Xem jumpscare trên YouTube")
    assert "dầm sờ ke" in out and "du túp" in out


# ---------------------------------------------------------------- đạo diễn theo luật
STORY = (
    "Đêm rằm tháng 7, tôi về quê ngoại ở Nam Định.\n"
    "- Ai đó? - bà ngoại thều thào.\n"
    "Có tiếng thì thầm bên tai lướt qua. Ai đó đang đứng sau lưng tôi.\n"
    "\"Xuống đây với ta...\" - con ma da cười khanh khách.\n"
    "Đột ngột một bóng đen kinh hoàng vồ lấy khiến tôi hét lên!"
)


def test_director_splits_dialogue_and_casts_roles():
    d = HorrorScriptAnalyzer().direct(STORY)
    texts = [s.text for s in d.segments]
    assert "Ai đó?" in texts and "bà ngoại thều thào." in texts
    ai_do = d.segments[texts.index("Ai đó?")]
    tag = d.segments[texts.index("bà ngoại thều thào.")]
    assert ai_do.speaker == "bà_ngoại" and d.characters["bà_ngoại"].gender == "nu"
    assert ai_do.emotion == "thi_tham"  # cảm xúc lấy từ lời dẫn "thều thào"
    assert tag.speaker == "narrator"

    ghost = d.segments[texts.index("Xuống đây với ta...")]
    assert ghost.speaker == "ma_nu" and ghost.voice_preset == "ma_nu"


def test_director_tension_spatial_jumpscare():
    segs = HorrorScriptAnalyzer().analyze_text(STORY)
    by_text = {s.text: s for s in segs}
    assert by_text["Có tiếng thì thầm bên tai lướt qua."].spatial_position in ("left_to_right", "right")
    assert by_text["Ai đó đang đứng sau lưng tôi."].spatial_position == "rear"
    last = segs[-1]
    assert last.tension >= 7.0 and last.is_jumpscare


def test_narration_mentioning_ghost_keeps_narrator_voice():
    segs = HorrorScriptAnalyzer().analyze_text("Người làng đồn dưới giếng có ma da.")
    assert segs[0].speaker == "narrator" and segs[0].voice_preset is None


def test_detect_region():
    assert detect_region("Chuyện xảy ra ở miền Tây, má tôi kể lại.") == "nam"
    assert detect_region("Ở Huế, mệ hỏi: răng rứa?") == "trung"
    assert detect_region("Làng tôi ở Thái Bình.") == "bac"


# ---------------------------------------------------------------- đạo diễn AI (LLM giả lập)
def test_llm_director_maps_output(monkeypatch):
    from src.director import llm_director as ld

    def line(text, speaker, **kw):
        base = dict(emotion="binh_thuong", tension=2, pause_after_ms=900, speed=1.0, spatial="center",
                    nonverbal="none", sfx="none", is_jumpscare=False)
        base.update(kw)
        return ld.LineDirection(text=text, speaker=speaker, **base)

    fake = ld.ChunkScript(
        story_region="nam",
        characters=[ld.CharacterSheet(key="ma_da", display_name="Ma da", gender="nu",
                                      age_group="thanh_nien", ghost_preset="ma_nu")],
        lines=[
            line("Đêm đó trời mưa.", "narrator", sfx="rain_storm", speed=0.95),
            line("Xuống đây...", "ma_da", emotion="thi_tham", tension=8, pause_after_ms=99999,
                 speed=2.0, spatial="left_to_right", nonverbal="cười"),
            line("Ai vậy?", "khong_ton_tai", emotion="so_hai"),
        ],
    )
    director = ld.LLMDirector.__new__(ld.LLMDirector)
    director.model, director.mood = "test", "kinh_di_nang"
    monkeypatch.setattr(director, "_direct_chunk", lambda *a, **k: fake)

    d = director.direct("Đêm đó trời mưa. Xuống đây... Ai vậy?")
    assert d.story_region == "nam"
    assert [s.speaker for s in d.segments] == ["narrator", "ma_da", "narrator"]  # key lạ -> narrator
    ghost = d.segments[1]
    assert ghost.voice_preset == "ma_nu" and ghost.nonverbal == "cười"
    assert ghost.pause_after == 3.0 and ghost.speed == 1.15  # bị kẹp về khoảng an toàn
    assert d.segments[0].sfx_cue == "rain_storm"


def test_direct_story_falls_back_when_llm_fails(monkeypatch):
    from src.director import llm_director as ld

    def boom(*a, **k):
        raise RuntimeError("API lỗi")

    monkeypatch.setattr(ld.LLMDirector, "__init__", boom)
    d = ld.direct_story("Đêm khuya. Có tiếng gõ cửa.", use_llm=True)
    assert len(d.segments) == 2


# ---------------------------------------------------------------- giọng & phân vai
def test_voice_manager_casting_and_consent(tmp_path):
    vm = VoiceManager()
    assert vm.get_voice("nguyen_ngoc_ngan").id == "narrator_bac_nam_tram"  # tên cũ vẫn chạy
    assert vm.get_voice("khong_co").id == "narrator_bac_nam"

    chars = {"ba_cu": Character("ba_cu", "Bà cụ", gender="nu", age_group="gia"),
             "thang_teo": Character("thang_teo", "Thằng Tèo", gender="nam", age_group="tre_em")}
    cast = vm.cast("narrator_nam_nam", chars, region="nam")
    assert cast["ba_cu"].gender == "nu" and cast["thang_teo"].gender == "nam"
    assert cast["ba_cu"].region == "nam"
    assert len({v.id for v in cast.values()}) == 3  # mỗi vai một giọng

    with pytest.raises(PermissionError):
        vm.register_cloned_voice("x", "X", "sample.wav", consent_confirmed=False)
    wav = tmp_path / "me.wav"
    AudioSegment.silent(duration=3000).export(str(wav), format="wav")
    v = vm.register_cloned_voice("me", "Tôi", str(wav), consent_confirmed=True)
    assert v.is_cloned and v.ref_audio == str(wav)


def test_cloned_voice_requires_consent_in_config(tmp_path):
    wav = tmp_path / "a.wav"
    AudioSegment.silent(duration=3000).export(str(wav), format="wav")
    vm = VoiceManager(config={"voices": {}, "cloned_voices": {
        "ok": {"file": str(wav), "consent": True}, "no": {"file": str(wav)}}})
    ids = [v.id for v in vm.list_voices()]
    assert "ok" in ids and "no" not in ids


# ---------------------------------------------------------------- TTS engine + cache
def test_tts_engine_normalizes_and_caches(monkeypatch, tmp_path):
    from src.tts import backends, engine as eng
    from pydub.generators import Sine

    calls = []

    class FakeBackend(backends.TTSBackend):
        name = "fake"

        def synthesize(self, text, voice, out_path, emotion="binh_thuong", nonverbal=None):
            calls.append(text)
            out = out_path.with_suffix(".wav")
            out.parent.mkdir(parents=True, exist_ok=True)
            tone = Sine(220).to_audio_segment(duration=1000).apply_gain(-10)
            (AudioSegment.silent(400) + tone + AudioSegment.silent(400)).export(str(out), format="wav")
            return out

    monkeypatch.setattr(eng, "create_backend", lambda *a, **k: FakeBackend())
    monkeypatch.setattr(eng, "CACHE_DIR", tmp_path)
    tts = eng.TTSEngine()
    p1 = tts.synthesize("Năm 1975", voice="narrator_bac_nam")
    p2 = tts.synthesize("Năm 1975", voice="narrator_bac_nam")
    assert p1 == p2 and p1.exists()
    assert calls == ["Năm một nghìn chín trăm bảy mươi lăm"]  # đọc 1 lần, lần 2 lấy cache
    assert len(AudioSegment.from_file(str(p1))) < 1400  # đã cắt bớt khoảng lặng thừa
    tts.synthesize("Năm 1975", voice="narrator_nam_nu")
    assert len(calls) == 2  # đổi giọng -> đọc lại


def test_create_backend_validation():
    from src.tts.backends import create_backend
    with pytest.raises(ValueError):
        create_backend("khong_co_engine")


# ---------------------------------------------------------------- hậu kỳ & lưu trữ
def test_dynamic_pacing():
    rate_open, pause_open = DynamicPacingController.calculate_rate_and_pause(2.0, is_opening=True)
    assert rate_open == "-8%"
    assert pause_open >= 1.0
    rate_climax, pause_climax = DynamicPacingController.calculate_rate_and_pause(9.0)
    assert rate_climax == "+18%"
    assert pause_climax <= 0.5
    # Hệ số tốc độ cho TTS: biên độ nhỏ để giọng không méo
    assert DynamicPacingController.speed_for(2.0, is_opening=True) < 1.0
    assert 1.0 < DynamicPacingController.speed_for(9.0) <= 1.1


def test_vocal_mastering_keeps_length_and_format():
    from pydub.generators import Sine
    from src.audio_engine.vocal_mastering import VocalMasteringChain

    voice = Sine(200).to_audio_segment(duration=500).set_frame_rate(48000)
    out = VocalMasteringChain.apply_horror_mastering(voice)
    assert len(out) == len(voice) and out.frame_rate == 48000 and out.max_dBFS < 0


def test_spatial_panning_stereo():
    test_audio = AudioSegment.silent(duration=500).set_channels(2)
    assert SpatialAudioEngine.apply_panning(test_audio, "left").channels == 2
    assert SpatialAudioEngine.apply_panning(test_audio, "rear").channels == 2


def test_jumpscare_safe_limiter():
    controller = JumpScareController(gentle_mode=False, peak_limit_db=-1.0)
    js = controller.create_jumpscare_segment(AudioSegment.silent(duration=300))
    assert len(js) >= 1500
    assert js.max_dBFS <= -1.0


def test_database_sqlite(tmp_path):
    db = DatabaseManager(db_path=tmp_path / "test_vodie.db")
    proj_id = db.create_project("Chuyện Ma Đêm Khuya", "Kịch bản mẫu...", mood="kinh_di_nang")
    assert proj_id > 0
    projects = db.list_projects()
    assert len(projects) == 1 and projects[0]["title"] == "Chuyện Ma Đêm Khuya"

    queue = QueueManager(db=db)
    task_id = queue.add_to_queue(proj_id, "Chuyện Ma Đêm Khuya")
    assert task_id > 0
    pending = queue.get_pending_tasks()
    assert len(pending) == 1 and pending[0]["status"] == "pending"
    queue.update_status(task_id, status="completed", progress=100)
    assert len(queue.get_pending_tasks()) == 0


def test_safety_compliance():
    assert SafetyCompliance.verify_voice_consent(True) is True
    with pytest.raises(PermissionError):
        SafetyCompliance.verify_voice_consent(False)
