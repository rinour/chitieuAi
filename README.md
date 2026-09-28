# 💰 MoneyAI - Hệ thống Quản lý Chi tiêu Cá nhân tích hợp AI

> **Đồ án môn học AIA331 - Ứng dụng Trí tuệ Nhân tạo**
> **Nhóm 12** - ĐH CNTT&TT Thái Nguyên
> GVHD: Ts. Trần Quang Quý

Demo web app quản lý chi tiêu cá nhân với AI Financial Advisor Chatbot, xây dựng bằng **Python Flask** theo đúng SRS đồ án Nhóm 12.

**🆕 Phiên bản nâng cấp** (theo `Prompt_nang_cap_du_an_tai_chinh.docx`):
- Forecast nâng cấp (7-day speed + budget compare + overshoot date)
- Anomaly detection (Modified Z-score với MAD)
- Hóa đơn định kỳ & nhắc sắp đến hạn
- Mô phỏng kịch bản "Nếu - Thì"
- Số ngày sinh tồn / Quỹ dự phòng
- Smart Round-up (Micro-savings)
- AI Bill Optimizer
- Trang `/insights` tổng hợp 6 widget AI

---

## ✨ Tính năng chính

| # | Chức năng | Use Case | Phiên bản |
|---|-----------|----------|-----------|
| 1 | Đăng nhập / Quản lý tài khoản | UC001 | v1 |
| 2 | Quản lý danh mục thu/chi (12 danh mục) | UC002 | v1 |
| 3 | Ghi nhận giao dịch (CRUD + AI auto-categorize) | UC003 | v1 |
| 4 | Thiết lập & theo dõi ngân sách | UC004 | v1 |
| 5 | Quản lý mục tiêu tiết kiệm | UC005 | v1 |
| 6 | Tìm kiếm & lọc giao dịch | UC006 | v1 |
| 7 | Cảnh báo vượt ngân sách (70%/90%/100%) | UC007 | v1 |
| 8 | Thống kê & trực quan hóa (Pie/Bar/Line) | UC008 | v1 |
| 9 | AI sinh báo cáo tài chính tháng | UC009 | v1 |
| 10 | AI gợi ý ngân sách tham khảo | UC010 | v1 |
| 11 | **AI Chatbot tư vấn tài chính** (24 intent) | UC011 | v1 + v2 |
| 12 | Bảo vệ dữ liệu (PII Masking concept) | UC012 | v1 |
| **13** | **🔮 Forecast nâng cấp** (7-day speed + budget compare + overshoot date) | A1 | **v2 MỚI** |
| **14** | **⚠️ Anomaly Detection** (Modified Z-score với MAD) | A2 | **v2 MỚI** |
| **15** | **📋 Hóa đơn định kỳ** (auto-detect + nhắc trước 2-3 ngày) | B | **v2 MỚI** |
| **16** | **🧪 If-Then Simulation** (trả góp, lương, du lịch, mua 1 lần) | C | **v2 MỚI** |
| **17** | **🛡️ Số ngày sinh tồn / Quỹ dự phòng** | D | **v2 MỚI** |
| **18** | **💰 Smart Round-up / Micro-savings** | E | **v2 MỚI** |
| **19** | **💸 AI Bill Optimizer** (subscription analysis + đề xuất) | F | **v2 MỚI** |

---

## 🤖 AI Chatbot Demo - Tính năng nổi bật

Chatbot hiểu **tiếng Việt có dấu**, **24 intent** (18 cũ + 6 mới), có thể trả lời:

### 📊 Phân tích (v1)
- "Tháng này chi nhiều nhất vào đâu?"
- "Phân tích chi tiêu tháng này"
- "Tổng chi bao nhiêu?"
- "Tổng thu nhập tháng này"
- "Còn lại bao nhiêu?"

### 🆕 Tính năng nâng cấp (v2)
- **Forecast nâng cấp**: "Dự báo chi tiêu cuối tháng" — phân tích 7-day speed + ngân sách + ngày vượt
- **Anomaly**: "Có khoản chi nào bất thường/lạ không?" — Modified Z-score
- **Recurring**: "Hóa đơn định kỳ sắp đến hạn?" / "Tiền điện bao giờ đến hạn?"
- **Simulation**: "Nếu mua laptop trả góp 2 triệu/tháng thì sao?"
- **Simulation**: "Nếu thu nhập giảm 20% thì tình hình thế nào?"
- **Simulation**: "Nếu đi du lịch 5 triệu trong 3 tháng?"
- **Survival**: "Quỹ dự phòng của tôi" / "Số ngày sinh tồn"
- **Round-up**: "Làm tròn tiết kiệm"
- **Bill Optimizer**: "Tối ưu hóa đơn"

### 💡 Tư vấn tiết kiệm
- "Làm sao tiết kiệm 2 triệu?"
- "Làm sao tiết kiệm 500k?"
- "Nên cắt khoản nào?"
- "Gợi ý ngân sách tháng tới"

### 📈 Dự báo & Báo cáo
- "Dự báo chi tiêu cuối tháng"
- "Tạo báo cáo tài chính tháng này"
- "So sánh với tháng trước"

### 🎯 Ngân sách & Mục tiêu
- "Tình hình ngân sách"
- "Tiến độ mục tiêu tiết kiệm"

### 🆘 Khác
- "Giúp" - xem tất cả tính năng
- "Xin chào" / "Cảm ơn"

> **Lưu ý:** Đây là bản **DEMO** dùng rule-based NLU + dữ liệu thật. Trong production, sẽ tích hợp **Google Gemini API** hoặc **OpenAI GPT-4o-mini** kết hợp **RAG** (xem SRS mục 2.1).

---

## 🚀 Cài đặt & Chạy

### Yêu cầu
- Python 3.8 trở lên
- pip

### Bước 1: Cài đặt thư viện
```bash
pip install -r requirements.txt
```

### Bước 2: Chạy server
```bash
python app.py
```

### Bước 3: Mở trình duyệt
Truy cập: **http://localhost:5000**

**Tài khoản demo:**
- Username: `demo`
- Password: `123456`

---

## 📂 Cấu trúc dự án

```
expense_ai_app/
├── app.py                # Flask backend - routes + REST API
├── chatbot.py            # AI Chatbot engine (rule-based NLU)
├── data.py               # Sample data (transactions, budgets, goals)
├── requirements.txt      # Python dependencies
├── README.md             # File này
├── templates/
│   ├── base.html         # Base template (cho login)
│   ├── _layout.html      # Layout chung (sidebar + topbar)
│   ├── login.html        # Trang đăng nhập
│   ├── dashboard.html    # Dashboard tổng quan
│   ├── transactions.html # Quản lý giao dịch
│   ├── budgets.html      # Quản lý ngân sách
│   ├── goals.html        # Mục tiêu tiết kiệm
│   ├── reports.html      # Báo cáo & thống kê
│   └── chat.html         # AI Chatbot
└── static/
    └── css/
        └── style.css     # Custom CSS
```

---

## 🔌 REST API Endpoints

### Authentication
- `POST /login` - Đăng nhập
- `GET /logout` - Đăng xuất

### Transactions
- `GET /api/transactions?month=YYYY-MM` - Danh sách giao dịch
- `POST /api/transactions` - Tạo giao dịch mới (AI auto-categorize)
- `DELETE /api/transactions/<id>` - Xóa giao dịch
- `POST /api/categorize` - AI phân loại từ mô tả

### Budgets
- `GET /api/budgets` - Danh sách + tiến độ
- `POST /api/budgets` - Tạo ngân sách
- `DELETE /api/budgets/<id>` - Xóa

### Goals
- `GET /api/goals` - Danh sách mục tiêu
- `POST /api/goals` - Tạo mục tiêu
- `POST /api/goals/<id>/deposit` - Nạp tiền vào quỹ

### Stats
- `GET /api/stats/summary` - Tổng quan tháng
- `GET /api/stats/charts` - Data cho biểu đồ

### AI Chatbot
- `POST /api/chat` - Gửi câu hỏi, nhận phản hồi AI
- `GET /api/chat/suggestions` - Gợi ý câu hỏi

---

## 🛠 Công nghệ sử dụng

| Thành phần | Công nghệ |
|-----------|-----------|
| Backend | Python 3.x + Flask 3.0 |
| Frontend | HTML5 + TailwindCSS (CDN) |
| Charts | Chart.js 4.4 |
| Markdown | Marked.js |
| AI Engine | Rule-based NLU (mô phỏng LLM) |
| Data | In-memory (sẽ thay bằng PostgreSQL trong production) |

> Tham khảo tài liệu SRS mục **2.4 Các điều kiện phụ thuộc** để biết stack công nghệ đầy đủ dự kiến cho production.

---

## 📸 Screenshots (cấu trúc)

1. **Login** - Gradient background, đăng nhập 1 cú nhấp với tài khoản demo
2. **Dashboard** - 4 summary cards (thu/chi/số dư/mục tiêu) + AI insight banner + 3 charts
3. **Transactions** - Bảng CRUD với filter theo danh mục, loại, từ khóa
4. **Budgets** - Cards trực quan với progress bar + cảnh báo màu
5. **Goals** - Cards gradient đẹp mắt theo % tiến độ
6. **Reports** - Charts + AI tự sinh báo cáo
7. **AI Chat** - Chat UI với bubble messages, typing indicator, suggestion chips

---

## 🎯 Điểm nhấn AI trong demo

1. **AI Auto-Categorize**: Khi nhập mô tả giao dịch (VD: "Mua trà sữa Gong Cha"), AI tự động đề xuất danh mục "Ăn uống" với icon và màu sắc.

2. **AI Financial Advisor Chatbot**: Hiểu câu hỏi tự nhiên tiếng Việt, phân tích dữ liệu thật của user, đưa ra lời khuyên cá nhân hóa.

3. **AI Sinh báo cáo**: Tự động tổng hợp dữ liệu tháng → sinh báo cáo markdown có cấu trúc.

4. **AI Forecast**: Dự báo chi tiêu cuối tháng dựa trên Moving Average.

5. **AI Budget Suggestions**: Gợi ý ngân sách tháng tới theo mô hình 50/30/20.

---

## 🔒 Bảo mật (Demo)

- Session-based authentication với Flask secret key
- Khử định danh (PII Masking) trước khi gửi cho AI - đã implement trong chatbot (chỉ gửi aggregated stats)
- HTTPS/TLS sẽ được thêm khi deploy production

---

## 📝 License & Credit

Đồ án phục vụ mục đích học tập - Học phần AIA331 - Ứng dụng Trí tuệ Nhân tạo.

**Sinh viên thực hiện:**
- Nguyễn Xuân Phong (Trưởng nhóm)
- Đặng Quang Tuệ
- Dương Anh Hoan

---

## 🚧 Hướng phát triển (Roadmap)

- [ ] Tích hợp Gemini/OpenAI API thay rule-based
- [ ] Database thật (SQLite/PostgreSQL)
- [ ] OCR quét hóa đơn (PaddleOCR/Tesseract)
- [ ] Voice input (Speech-to-Text)
- [ ] Mobile app (Flutter)
- [ ] Xuất PDF/Excel cho báo cáo
- [ ] Đa tiền tệ + tỷ giá realtime
- [ ] Group expense / Split bill
