# 🎙️ VODIE - AI Horror Audio & Video Production Studio

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

### 🇻🇳 Đọc Tiếng Việt Chuẩn Xác
- **Từ điển phát âm tùy chỉnh (`config/pronunciation_dict.yaml`):** Sửa lỗi đọc tên riêng ("Út Lụa"), địa danh, từ tiếng Anh ("creepypasta", "jump scare"), cổ ngữ tâm linh.
- **Kiểm định giọng đọc bằng Whisper ASR:** Dùng Whisper nghe lại audio từng câu so với văn bản gốc. Tự động đọc lại (re-take tối đa 2 lần) nếu bị nuốt chữ hoặc ngọng.
- **Tùy chọn giọng Bắc / Nam:** Linh hoạt chọn giọng kể chuyện và giọng nhân vật vùng miền.

### 🎬 Sản Xuất Video Đa Nền Tảng
- **Xuất MP4 YouTube (16:9):** Nền ảnh tối u ám + Sóng âm động (Audio Waveform Visualizer) + Phụ đề cháy chữ theo nhịp đọc.
- **Tự cắt Shorts/TikTok/Reels (9:16):** Thuật toán tự động tìm đoạn có điểm Tension cao trào nhất và trích xuất thành video ngắn 30–60 giây.
- **Chia chương sách nói (M4B):** Tự động tạo Chapter Markers cho truyện dài.

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
├── config/
│   ├── settings.yaml            # Cấu hình hệ thống toàn cục
│   ├── voice_presets.yaml       # Cấu hình hiệu ứng giọng ma mị
│   ├── pronunciation_dict.yaml  # Từ điển ngữ âm tiếng Việt
│   └── moods.yaml               # Thiết lập không khí truyện
├── src/
│   ├── main.py                  # Entrypoint điều phối Pipeline
│   ├── config.py                # Nạp cấu hình YAML
│   ├── director/                # Giai đoạn 1: Đạo diễn AI & Sinh kịch bản
│   ├── tts/                     # Giai đoạn 2: Giọng đọc & Chuẩn hóa ngữ âm
│   ├── validator/               # Giai đoạn 3: Whisper ASR kiểm định phát âm
│   ├── audio_engine/            # Giai đoạn 4: Âm thanh 3D, FX & Mixer
│   ├── video_engine/            # Giai đoạn 5: Render Video 16:9 & Shorts 9:16
│   ├── storage/                 # Giai đoạn 6: SQLite & Batch Queue
│   └── safety/                  # An toàn bản quyền & AI Metadata
├── assets/
│   └── CREDITS.md               # Danh mục nguồn gốc bản quyền BGM & SFX
└── output/                      # Thư mục lưu sản phẩm audio/video hoàn thiện
```

---

## 🚀 HƯỚNG DẪN CÀI ĐẶT & CHẠY THỬ

### 1. Cài đặt thư viện
```bash
pip install -r requirements.txt
```

### 2. Chạy thử nghiệm ngay với kịch bản mẫu
```bash
python -m src.main --title "Chuyen_Ma_Da_Lat" --mood "kinh_di_nang"
```

### 3. Đưa kịch bản tùy chỉnh của bạn vào
```bash
python -m src.main --script demo_sample.txt --title "Dem_Kinh_Hoang" --mood "tam_linh_dan_gian"
```

### 4. Dùng AI sáng tác truyện từ ý tưởng
```bash
python -m src.main --generate "ngôi nhà hoang ở Đà Lạt" --title "Biet_Thu_Co"
```

---

## 📜 GIẤY PHÉP & BẢN QUYỀN
Phát triển bởi **VODIE Team**. Tuân thủ chính sách minh bạch nội dung AI-Generated Content.
