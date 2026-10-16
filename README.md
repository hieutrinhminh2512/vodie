# 🎙️ VODIE - AI Horror Audio & Video Production Studio

[![VODIE Studio CI Test Suite](https://github.com/hieutrinhminh2512/vodie/actions/workflows/ci.yml/badge.svg)](https://github.com/hieutrinhminh2512/vodie/actions/workflows/ci.yml)
[![Python 3.12](https://img.shields.io/badge/python-3.12-blue.svg)](https://www.python.org/downloads/)
[![License: CC0](https://img.shields.io/badge/License-CC0-lightgrey.svg)](assets/CREDITS.md)

> **VODIE** là Studio tự động hóa sản xuất truyện ma, podcast kinh dị và video rùng rợn ứng dụng trí tuệ nhân tạo (AI Director Engine), xử lý âm thanh không gian 3D (Binaural Spatial Panning), kiểm định phát âm Whisper và render video đa nền tảng (YouTube 16:9 & TikTok/Shorts 9:16).

---

## ✨ TÍNH NĂNG ĐẮT GIÁ ("ĂN TIỀN")

### 🎧 Trải Nghiệm Kinh Dị Đỉnh Cao
- **Âm thanh vòm cho tai nghe (Binaural 3D Panning):** Đạo diễn AI tự động gán vị trí di chuyển cho tiếng thì thầm (từ tai trái lướt sang tai phải), tiếng bước chân rón rén sau lưng.
- **Jump scare có tính toán an toàn:** Tạo khoảng lặng nín thở 1–2 giây trước khi bật tiếng động bất ngờ. Tích hợp bộ **True Peak Limiter (-1 dBTP)** bảo vệ tai người nghe, kèm tùy chọn *"Chế độ dịu tai"*.
- **Nhịp độ tự co giãn (Dynamic Pacing):** Tự động điều chỉnh tốc độ đọc (speed rate) và ngắt nghỉ theo thang điểm căng thẳng (`tension: 0–10`). Mở đầu chậm rãi u ám, đoạn cao trào dồn dập, câu chốt ngắt dài ám ảnh.
- **Preset giọng ma rợn người:**
  - `ma_nu`: Thì thầm, reverb lớn, tăng cao độ (pitch the thé).
  - `quy_du`: Giọng trầm đục, méo tiếng ghê rợn (distortion).
  - `vong_hon`: Vang vọng từ xa (echo xa, lowpass filter).
- **Hệ thống Mood:** Lựa chọn `nhe_nhang`, `kinh_di_nang`, `tam_linh_dan_gian`, `creepypasta` để tự động phối nhạc nền và mật độ SFX.

### 🔊 Giọng Đọc Người Việt Thật (VieNeu-TTS)
- **Engine mặc định: [VieNeu-TTS v3 Turbo](https://github.com/pnnbao97/VieNeu-TTS)** – model TTS tiếng Việt huấn luyện trên 10.000+ giờ giọng người Việt, 25 giọng dựng sẵn đủ **Bắc – Trung – Nam**, chạy được **trên CPU thường** (~2 lần thời gian thực), không cần GPU, miễn phí, giấy phép Apache 2.0.
- **Mỗi nhân vật một giọng:** đạo diễn tách lời thoại khỏi lời dẫn, đoán vai qua cách xưng hô (*bà cụ thều thào*, *thằng Tèo hét*…) rồi tự phân giọng nam/nữ phù hợp, cùng miền với bối cảnh truyện.
- **Người kể theo miền:** truyện ở miền Tây, Sài Gòn → giọng Nam; Huế, Quảng → giọng Trung; còn lại giọng Bắc. Số đếm cũng đọc theo miền (*nghìn/linh* – *ngàn/lẻ*).
- **Clone giọng của bạn** từ clip 3–8 giây (xem mục "Thêm giọng của bạn").
- Dự phòng: `edge-tts` (khi chưa cài được VieNeu), ElevenLabs `eleven_v3` (trả phí).

### 🎬 Đạo Diễn AI Hiểu Văn Hóa Việt (tùy chọn)
- Có `ANTHROPIC_API_KEY` trong `.env` → dùng Claude làm đạo diễn: hiểu xưng hô, ma da/ma lai/quỷ nhập tràng/vong, rằm tháng bảy, canh ba… để gán cảm xúc, nhịp kể, ngắt nghỉ, hiệu ứng như người kể chuyện ma thật. Giữ nguyên văn truyện, không viết lại.
- Không có key → đạo diễn theo luật (miễn phí, vẫn tách thoại và phân vai).

### 🇻🇳 Đọc Tiếng Việt Chuẩn Xác
- **Chuẩn hóa tự động:** số (*1975 → một nghìn chín trăm bảy mươi lăm*, *21 → hai mươi mốt*), ngày tháng (*15/8 → mười lăm tháng tám*, *tháng 4 → tháng tư*), giờ (*23h15*), tiền (*500k*, *1.250.000đ*), đơn vị (*km/h*, *°C*), phần trăm, số La Mã (*thế kỷ XIX*), số điện thoại, viết tắt (*TP.HCM*, *UBND*) và teencode (*ko, đc, ng*).
- **Từ điển phát âm tùy chỉnh (`config/pronunciation_dict.yaml`):** Sửa lỗi đọc tên riêng ("Út Lụa"), địa danh, từ tiếng Anh ("creepypasta", "jump scare"), cổ ngữ tâm linh.
- **Kiểm định giọng đọc bằng Whisper ASR:** Dùng Whisper nghe lại audio từng câu so với văn bản gốc. Tự động đọc lại (re-take tối đa 2 lần) nếu bị nuốt chữ hoặc ngọng.
- **Tùy chọn giọng Bắc / Nam:** Linh hoạt chọn giọng kể chuyện và giọng nhân vật vùng miền.

### 🎬 Sản Xuất Video Đa Nền Tảng
- **Xuất MP4 YouTube (16:9):** Nền ảnh tối u ám + Sóng âm động (Audio Waveform Visualizer) + Phụ đề cháy chữ theo nhịp đọc.
- **Tự cắt Shorts/TikTok/Reels (9:16):** Thuật toán tự động tìm đoạn có điểm Tension cao trào nhất và trích xuất thành video ngắn 30–60 giây.
- **Chia chương sách nói (M4B):** Tự động tạo Chapter Markers cho truyện dài.

### 💻 Giao Diện Web Studio Trực Quan
- Bảng điều khiển Web Dashboard tại `http://localhost:8000` với giao diện Dark Horror huyền bí.
- Xem trực tiếp biểu đồ Tension Timeline, nghe thử Audio Master và xem Video MP4 ngay trên trình duyệt.

### ⚡ Tiện Ích & An Toàn Bản Quyền
- **Hàng đợi chạy ngầm qua đêm (Batch Queue):** Thả 10+ truyện vào hàng đợi, tự resume nếu khởi động lại máy.
- **Lưu dự án SQLite:** Quản lý kịch bản, lưu nháp và theo dõi lịch sử phiên bản.
- **AI Sáng tác truyện:** Nhập ý tưởng ngắn (vd: *"ngôi nhà hoang ở Đà Lạt"*), AI tự sinh kịch bản 3 hồi hoàn chỉnh.
- **An toàn & Pháp lý:** Cam kết bản quyền khi nhái giọng, gắn metadata ID3 *"AI-generated"* vào file xuất ra và sử dụng thư viện âm thanh CC0 miễn phí bản quyền (`CREDITS.md`).

---

## 📁 CẤU TRÚC DỰ ÁN

```
vodie/
├── SPEC.md                      # Tài liệu kỹ thuật chi tiết toàn bộ dự án
├── README.md                    # Giới thiệu & Hướng dẫn sử dụng
├── requirements.txt             # Danh sách thư viện Python
├── .gitignore                   # Cấu hình bỏ qua tệp tạm & media
├── demo_sample.txt              # Kịch bản mẫu thử nghiệm
├── run_studio.bat               # Bấm đúp để mở Web Studio Dashboard
├── run_pipeline.bat             # Bấm đúp để chạy Pipeline sinh Audio/Video
├── run_tests.bat                # Bấm đúp để chạy toàn bộ Unit Tests
├── .github/workflows/ci.yml     # CI/CD tự động test trên GitHub
├── config/
│   ├── settings.yaml            # Cấu hình hệ thống toàn cục
│   ├── voice_presets.yaml       # Cấu hình hiệu ứng giọng ma mị
│   ├── pronunciation_dict.yaml  # Từ điển ngữ âm tiếng Việt
│   └── moods.yaml               # Thiết lập không khí truyện
├── src/
│   ├── main.py                  # Entrypoint điều phối Pipeline
│   ├── config.py                # Nạp cấu hình YAML & Auto-detect FFmpeg
│   ├── director/                # Giai đoạn 1: Đạo diễn AI & Sinh kịch bản
│   ├── tts/                     # Giai đoạn 2: Giọng đọc & Chuẩn hóa ngữ âm
│   ├── validator/               # Giai đoạn 3: Whisper ASR kiểm định phát âm
│   ├── audio_engine/            # Giai đoạn 4: Âm thanh 3D, FX & Mixer
│   ├── video_engine/            # Giai đoạn 5: Render Video 16:9 & Shorts 9:16
│   ├── storage/                 # Giai đoạn 6: SQLite & Batch Queue
│   ├── safety/                  # An toàn bản quyền & AI Metadata
│   └── studio/                  # Web Studio Dashboard (FastAPI + HTML5)
├── tests/
│   └── test_vodie.py            # Bộ Unit Test tự động (Pytest)
├── assets/
│   └── CREDITS.md               # Danh mục nguồn gốc bản quyền BGM & SFX
└── output/                      # Thư mục lưu sản phẩm audio/video hoàn thiện
```

---

## 🚀 HƯỚNG DẪN CÀI ĐẶT & CHẠY THỬ

### Bước 0: Cài đặt (chỉ 1 lần)
1. Cài [Python 3.11+](https://www.python.org/downloads/) (nhớ tick **Add Python to PATH**).
2. Bấm đúp [`cai_dat.bat`](cai_dat.bat). Script tạo môi trường riêng, cài thư viện, tải model giọng VieNeu (~600 MB, chỉ lần đầu) và đọc thử 1 câu.
3. (Tùy chọn) Mở file `.env`, dán `ANTHROPIC_API_KEY` để bật đạo diễn AI.

Không cần cài FFmpeg riêng – dự án dùng bản đóng gói sẵn của `imageio-ffmpeg`.

### Thêm giọng của bạn (clone giọng)
1. Thu một đoạn **3–8 giây**, nói rõ, phòng yên tĩnh, lưu thành `voices/giong_cua_toi.wav`.
2. Mở `config/voices.yaml`, thêm vào mục `cloned_voices`:
   ```yaml
   giong_cua_toi:
     name: "Giọng của tôi"
     file: voices/giong_cua_toi.wav
     gender: nam        # nam | nu
     region: bac        # bac | trung | nam
     consent: true      # xác nhận bạn có quyền dùng giọng này
   ```
3. Chọn giọng đó ở Web Studio hoặc chạy `--speaker giong_cua_toi`.

> ⚠️ Chỉ clone giọng của chính bạn hoặc người đã đồng ý. Không dùng để giả mạo người khác.

### Đổi engine giọng đọc
Sửa `tts.engine` trong `config/settings.yaml`: `auto` (mặc định, VieNeu) · `vieneu` · `elevenlabs` · `edge`.
`temperature` (0.5–0.9) chỉnh độ biểu cảm: thấp = đều, ổn định; cao = biểu cảm hơn.

### Chạy bằng GPU NVIDIA (nhanh hơn nhiều, không bắt buộc)
```bash
.venv\Scripts\pip install torch==2.8.0 torchaudio==2.8.0 --index-url https://download.pytorch.org/whl/cu128
.venv\Scripts\pip install "transformers==4.57.6"
```
Giữ `tts.device: auto` – VieNeu tự dùng GPU nếu có.

### Thêm nhạc nền / hiệu ứng (SFX)
Bỏ file vào `assets/sfx/` với đúng tên cue: `footsteps_creak`, `door_creak`, `wind_howl`, `rain_storm`, `dog_howl`, `owl`, `temple_bell`, `funeral_horn`, `water_drip`, `jumpscare_screech` (`.wav/.mp3/.ogg`). Không có file thì bỏ qua, không chèn tiếng giả. Nhớ ghi nguồn vào `assets/CREDITS.md`.

### Cách 1: Khởi động Web Studio trực quan (Khuyên dùng)
Bấm đúp chuột vào tệp [`run_studio.bat`](run_studio.bat) hoặc chạy:
```bash
python -m uvicorn src.studio.server:app --reload
```
Trình duyệt sẽ tự động mở tại `http://localhost:8000`.

### Cách 2: Chạy tự động qua dòng lệnh (CLI)
Bấm đúp chuột vào [`run_pipeline.bat`](run_pipeline.bat) hoặc chạy:
```bash
python -u -m src.main --title "Chuyen_Ma_Da_Lat" --mood "kinh_di_nang"
```

### Cách 3: Chạy bộ kiểm thử tự động (Unit Tests)
Bấm đúp chuột vào [`run_tests.bat`](run_tests.bat) hoặc chạy:
```bash
pytest tests/ -v
```

---

## 📜 GIẤY PHÉP & BẢN QUYỀN
Phát triển bởi **VODIE Team**. Tuân thủ chính sách minh bạch nội dung AI-Generated Content.
