import os
from pathlib import Path
from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from ..config import OUTPUT_DIR, SETTINGS
from ..director.script_analyzer import HorrorScriptAnalyzer
from ..tts.voice_manager import VoiceManager
from ..director.story_generator import StoryGenerator
from ..storage.db import DatabaseManager
from ..main import run_pipeline

app = FastAPI(title="VODIE AI Horror Studio", version="1.0.0")


class ProduceRequest(BaseModel):
    title: str
    script: str
    mood: str = "kinh_di_nang"
    speaker: str = "auto"


class StoryGenRequest(BaseModel):
    prompt: str
    mood: str = "kinh_di_nang"


@app.get("/api/projects")
def get_projects():
    db = DatabaseManager()
    return db.list_projects()


@app.get("/api/outputs")
def get_outputs():
    files = []
    if OUTPUT_DIR.exists():
        for f in OUTPUT_DIR.iterdir():
            if f.is_file():
                files.append({
                    "name": f.name,
                    "size_mb": round(f.stat().st_size / (1024 * 1024), 2),
                    "modified": f.stat().st_mtime
                })
    return sorted(files, key=lambda x: x["modified"], reverse=True)


@app.get("/output/{filename}")
def download_output(filename: str):
    file_path = OUTPUT_DIR / filename
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="Không tìm thấy tệp")
    return FileResponse(file_path)


@app.post("/api/generate-story")
def generate_story(req: StoryGenRequest):
    gen = StoryGenerator()
    story = gen.generate_story(req.prompt, mood=req.mood)
    return {"story": story}


@app.post("/api/analyze")
def analyze_script(req: ProduceRequest):
    director = HorrorScriptAnalyzer(mood=req.mood)
    segments = director.analyze_text(req.script)
    return {
        "segments": [
            {
                "id": s.segment_id,
                "text": s.text,
                "tension": s.tension,
                "position": s.spatial_position,
                "speaker": s.speaker,
                "is_jumpscare": s.is_jumpscare,
                "emotion": s.emotion,
            }
            for s in segments
        ]
    }


@app.post("/api/produce")
def produce_project(req: ProduceRequest):
    clean_title = "".join(c if c.isalnum() or c in "_-" else "_" for c in req.title)
    run_pipeline(req.script, project_title=clean_title, mood=req.mood, speaker_style=req.speaker)
    return {
        "status": "success",
        "audio_url": f"/output/{clean_title}_master.mp3",
        "video_url": f"/output/{clean_title}_video.mp4",
        "subtitles_url": f"/output/{clean_title}_subtitles.srt"
    }


@app.get("/", response_class=HTMLResponse)
def index():
    html_content = """
<!DOCTYPE html>
<html lang="vi">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>VODIE Studio - AI Horror Audio & Video Production</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <style>
        body { background-color: #0b090a; color: #f5f3f4; font-family: system-ui, sans-serif; }
        .glow-red { text-shadow: 0 0 15px rgba(229, 56, 59, 0.8); }
        .border-glow { border-color: #ba181b; box-shadow: 0 0 15px rgba(186, 24, 27, 0.3); }
    </style>
</head>
<body class="p-6">
    <div class="max-w-7xl mx-auto">
        <!-- Header -->
        <header class="flex justify-between items-center pb-6 border-b border-zinc-800">
            <div>
                <h1 class="text-3xl font-extrabold text-red-600 tracking-wider glow-red">🎙️ VODIE STUDIO</h1>
                <p class="text-zinc-400 text-sm mt-1">Phòng Thu Tự Động Hóa Audio 3D & Video Truyện Ma AI</p>
            </div>
            <div class="flex gap-3">
                <span class="px-3 py-1 bg-red-950/60 border border-red-800/80 rounded-full text-xs text-red-400 flex items-center gap-1.5">
                    ● True Peak Limiter -1dBTP Safe
                </span>
                <span class="px-3 py-1 bg-zinc-900 border border-zinc-700 rounded-full text-xs text-emerald-400">
                    ✓ AI-Generated Metadata Verified
                </span>
            </div>
        </header>

        <!-- Main Workspace Grid -->
        <div class="grid grid-cols-1 lg:grid-cols-12 gap-6 mt-6">
            <!-- Left Panel: Script & Controls (7 cols) -->
            <div class="lg:col-span-7 space-y-5">
                <div class="bg-zinc-900/90 border border-zinc-800 rounded-xl p-5 border-glow">
                    <div class="flex justify-between items-center mb-3">
                        <label class="font-semibold text-zinc-200">Kịch Bản Văn Bản Gốc</label>
                        <button onclick="aiGenerateStory()" class="text-xs bg-red-900/40 hover:bg-red-800/60 text-red-300 border border-red-700 px-3 py-1 rounded transition">
                            ✨ AI Sáng Tác Truyện
                        </button>
                    </div>
                    <input id="projectTitle" type="text" value="Dem_Kinh_Hoang_Da_Lat" placeholder="Tên dự án..." 
                           class="w-full bg-zinc-950 border border-zinc-800 rounded-lg p-2.5 text-sm text-zinc-100 mb-3 focus:outline-none focus:border-red-600">
                    <textarea id="scriptText" rows="9" 
                              class="w-full bg-zinc-950 border border-zinc-800 rounded-lg p-3 text-sm text-zinc-200 leading-relaxed focus:outline-none focus:border-red-600"
                              placeholder="Nhập truyện ma tại đây..."></textarea>
                    
                    <div class="grid grid-cols-2 gap-4 mt-4">
                        <div>
                            <label class="text-xs text-zinc-400 block mb-1">Giọng Người Kể</label>
                            <select id="speakerSelect" class="w-full bg-zinc-950 border border-zinc-800 rounded-lg p-2 text-sm text-zinc-200">
                                <option value="auto">🎙️ Tự chọn theo miền của truyện</option>
                                __NARRATOR_OPTIONS__
                            </select>
                        </div>
                        <div>
                            <label class="text-xs text-zinc-400 block mb-1">Không Khí (Mood)</label>
                            <select id="moodSelect" class="w-full bg-zinc-950 border border-zinc-800 rounded-lg p-2 text-sm text-zinc-200">
                                <option value="tam_linh_dan_gian">Tâm Linh Dân Gian Việt Nam</option>
                                <option value="kinh_di_nang">Kinh Dị Nặng (Suspense & Jump scare)</option>
                                <option value="creepypasta">Creepypasta Đô Thị Hiện Đại</option>
                                <option value="nhe_nhang">Rùng Rợn Nhẹ Nhàng / Huyền Bí</option>
                            </select>
                        </div>
                    </div>

                    <div class="grid grid-cols-2 gap-4 mt-3">
                        <div class="bg-zinc-950 border border-zinc-800 rounded-lg p-2 text-xs text-emerald-400 flex items-center gap-1.5">
                            ✓ Động Cơ Nhân Hóa: Lấy hơi & Ngắt vế câu
                        </div>
                        <div class="bg-zinc-950 border border-zinc-800 rounded-lg p-2 text-xs text-emerald-400 flex items-center gap-1.5">
                            ✓ Âm Thanh Không Gian (Binaural 3D Panning)
                        </div>
                    </div>

                    <button id="btnProduce" onclick="startProduction()" 
                            class="w-full mt-5 bg-gradient-to-r from-red-700 to-red-900 hover:from-red-600 hover:to-red-800 text-white font-bold py-3 rounded-lg shadow-lg shadow-red-950/50 transition">
                        ⚡ BẮT ĐẦU SẢN XUẤT AUDIO & VIDEO MP4
                    </button>
                </div>

                <!-- Tension Timeline -->
                <div class="bg-zinc-900/90 border border-zinc-800 rounded-xl p-5">
                    <h3 class="font-semibold text-zinc-200 mb-3 text-sm">📊 Phân Tích Căng Thẳng (Tension Curve 0–10)</h3>
                    <div id="timelineList" class="space-y-2 max-h-56 overflow-y-auto pr-1 text-xs text-zinc-400">
                        <p class="italic text-zinc-600">Bấm 'Phân tích' hoặc 'Sản xuất' để xem đạo diễn AI chấm điểm...</p>
                    </div>
                </div>
            </div>

            <!-- Right Panel: Studio Monitor & Player (5 cols) -->
            <div class="lg:col-span-5 space-y-5">
                <!-- Video Monitor -->
                <div class="bg-zinc-900/90 border border-zinc-800 rounded-xl p-5">
                    <h3 class="font-semibold text-zinc-200 mb-3 text-sm">📺 Màn Hình Giám Sát Video (16:9)</h3>
                    <div class="aspect-video bg-black rounded-lg overflow-hidden border border-zinc-800 flex items-center justify-center">
                        <video id="videoPlayer" controls class="w-full h-full hidden"></video>
                        <div id="videoPlaceholder" class="text-center p-4 text-zinc-600">
                            <span class="text-4xl block mb-2">🎬</span>
                            <span class="text-xs">Chưa có video. Hãy bấm Sản Xuất để render.</span>
                        </div>
                    </div>
                    <div class="mt-4">
                        <label class="text-xs text-zinc-400 block mb-1">Master Audio Player</label>
                        <audio id="audioPlayer" controls class="w-full hidden"></audio>
                    </div>
                </div>

                <!-- Exported Files -->
                <div class="bg-zinc-900/90 border border-zinc-800 rounded-xl p-5">
                    <h3 class="font-semibold text-zinc-200 mb-3 text-sm">📁 Tệp Xuất Bản Hoàn Thiện (output/)</h3>
                    <div id="outputList" class="space-y-2 text-xs">
                        <p class="text-zinc-500">Đang nạp danh sách tệp...</p>
                    </div>
                </div>
            </div>
        </div>
    </div>

    <script>
        const sampleScript = `Đêm Đà Lạt lạnh buốt, sương mù giăng kín các rặng thông quanh căn biệt thự hoang cổ kính.\\nTôi rón rén bước từng bước trên nền gỗ mục nát, xung quanh im lìm đến ghê người.\\nBỗng nhiên, từ trên tầng hai phát ra tiếng bước chân lê lết chậm rãi.\\nCó một tiếng con gái thì thầm ngay bên tai tôi một lời van xin ai oán.\\nTôi run rẩy quay đầu lại phía sau lưng nhưng chẳng thấy ai, chỉ có một luồng gió lạnh thấu xương.\\nĐột ngột, một bàn tay trắng bệch từ bóng tối vồ lấy vai tôi khiến tôi kinh hoàng hét lên!\\nVà rồi, mọi thứ chìm vào im lặng vĩnh hằng giữa màn đêm sương phủ.`;

        document.getElementById('scriptText').value = sampleScript;

        async function loadOutputs() {
            try {
                const res = await fetch('/api/outputs');
                const files = await res.json();
                const container = document.getElementById('outputList');
                if (files.length === 0) {
                    container.innerHTML = '<p class="text-zinc-600">Chưa có tệp nào được xuất.</p>';
                    return;
                }
                container.innerHTML = files.map(f => `
                    <div class="flex justify-between items-center p-2 bg-zinc-950 border border-zinc-800 rounded">
                        <span class="truncate max-w-[220px] text-zinc-300 font-mono">${f.name}</span>
                        <div class="flex items-center gap-2">
                            <span class="text-zinc-500">${f.size_mb} MB</span>
                            <a href="/output/${f.name}" download class="text-red-400 hover:underline">Tải về</a>
                        </div>
                    </div>
                `).join('');
            } catch (e) {
                console.error(e);
            }
        }

        async function aiGenerateStory() {
            const prompt = prompt("Nhập ý tưởng ngắn:", "ngôi nhà hoang ở Đà Lạt");
            if (!prompt) return;
            const res = await fetch('/api/generate-story', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({prompt, mood: document.getElementById('moodSelect').value})
            });
            const data = await res.json();
            document.getElementById('scriptText').value = data.story;
            analyzeScript();
        }

        async function analyzeScript() {
            const res = await fetch('/api/analyze', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({
                    title: document.getElementById('projectTitle').value,
                    script: document.getElementById('scriptText').value,
                    mood: document.getElementById('moodSelect').value
                })
            });
            const data = await res.json();
            const container = document.getElementById('timelineList');
            container.innerHTML = data.segments.map(s => `
                <div class="p-2 bg-zinc-950 border border-zinc-800 rounded flex justify-between items-center">
                    <span class="truncate max-w-[320px] text-zinc-300">#${s.id}: ${s.text}</span>
                    <div class="flex gap-2">
                        <span class="px-2 py-0.5 bg-red-950 text-red-400 rounded text-[10px]">Tension: ${s.tension}/10</span>
                        <span class="px-2 py-0.5 bg-zinc-800 text-zinc-300 rounded text-[10px]">${s.position}</span>
                    </div>
                </div>
            `).join('');
        }

        async function startProduction() {
            const btn = document.getElementById('btnProduce');
            btn.disabled = true;
            btn.innerText = '⏳ ĐANG SẢN XUẤT AUDIO 3D & VIDEO MP4... (Xin chờ)';

            try {
                await analyzeScript();
                const res = await fetch('/api/produce', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({
                        title: document.getElementById('projectTitle').value,
                        script: document.getElementById('scriptText').value,
                        mood: document.getElementById('moodSelect').value,
                        speaker: document.getElementById('speakerSelect').value
                    })
                });
                const data = await res.json();

                // Cập nhật Player
                const audioPlayer = document.getElementById('audioPlayer');
                audioPlayer.src = data.audio_url + '?t=' + Date.now();
                audioPlayer.classList.remove('hidden');

                const videoPlayer = document.getElementById('videoPlayer');
                videoPlayer.src = data.video_url + '?t=' + Date.now();
                videoPlayer.classList.remove('hidden');
                document.getElementById('videoPlaceholder').classList.add('hidden');

                alert('🎉 SẢN XUẤT HOÀN TẤT! Bạn có thể nghe thử và xem video ngay trên màn hình.');
                loadOutputs();
            } catch (err) {
                alert('Lỗi: ' + err);
            } finally {
                btn.disabled = false;
                btn.innerText = '⚡ BẮT ĐẦU SẢN XUẤT AUDIO & VIDEO MP4';
            }
        }

        loadOutputs();
        analyzeScript();
    </script>
</body>
</html>
    """
    narrator_options = "\n".join(
        f'<option value="{v.id}">🎙️ {v.name}</option>'
        for v in VoiceManager().list_voices() if "narrator" in v.tags or v.is_cloned
    )
    return HTMLResponse(content=html_content.replace("__NARRATOR_OPTIONS__", narrator_options))
