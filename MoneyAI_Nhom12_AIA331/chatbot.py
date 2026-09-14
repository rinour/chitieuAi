"""
AI Chatbot - Trợ lý tài chính cá nhân (UC011)
Đồ án Nhóm 12 - AIA331
Đây là bản DEMO mô phỏng LLM dùng rule-based NLU + dữ liệu thật của user.
Trong production sẽ thay bằng Gemini/OpenAI API + RAG.
"""

from datetime import datetime
from collections import defaultdict
import re

from data import (
    DEFAULT_CATEGORIES, CATEGORIES_BY_ID,
    SAMPLE_TRANSACTIONS, SAMPLE_BUDGETS, SAMPLE_GOALS,
)

# ===================== TIỆN ÍCH TÍNH TOÁN =====================

def _now_month():
    return datetime.now().strftime("%Y-%m")


def _this_month_tx():
    month = _now_month()
    return [t for t in SAMPLE_TRANSACTIONS if t["date"].startswith(month)]


def _total_by_type(tx_list, t_type):
    return sum(t["amount"] for t in tx_list if t["type"] == t_type)


def _spending_by_category(tx_list):
    by_cat = defaultdict(int)
    for t in tx_list:
        if t["type"] == "expense":
            by_cat[t["category_id"]] += t["amount"]
    return by_cat


def _format_vnd(amount):
    """Format tiền VND: 1500000 -> '1.500.000 đ'."""
    return f"{amount:,.0f}".replace(",", ".") + " đ"


def _category_name(cat_id):
    cat = CATEGORIES_BY_ID.get(cat_id)
    return cat["name"] if cat else cat_id


# ===================== INTENT CLASSIFICATION (NLU) =====================

INTENT_PATTERNS = [
    # (intent, regex, score_weight)
    ("greeting",          r"\b(xin chào|chào|hi|hello|hey|chào bạn)\b", 1),
    ("thanks",            r"\b(cảm ơn|cám ơn|thanks|thank you|tuyệt vời|hay quá)\b", 1),

    ("top_spending",      r"(chi nhiều nhất|tiêu nhiều nhất|top chi|khoản chi lớn nhất|chi vào đâu nhiều|chi chủ yếu)", 2),
    ("top_spending",      r"(tháng này.*(chi|tiêu).*(gì|nhiều))", 2),

    ("total_expense",     r"(tổng chi|tổng tiền chi|đã chi|chi bao nhiêu|bao nhiêu tiền)", 2),
    ("total_income",      r"(tổng thu|thu nhập|được bao nhiêu|kiếm được)", 2),
    ("balance",           r"(số dư|còn lại|tiết kiệm được|tháng này còn)", 2),

    ("forecast",          r"(dự báo|forecast|cuối tháng|nếu tiếp tục|hết tháng)", 2),
    ("budget_check",      r"(ngân sách|budget|vượt ngân sách|còn ngân sách|vượt hạn mức)", 2),
    ("budget_suggest",    r"(gợi ý ngân sách|đề xuất ngân sách|ngân sách tham khảo|nên đặt.*ngân sách)", 2),

    ("save_tips",         r"(làm sao.*tiết kiệm|cách tiết kiệm|làm thế nào.*tiết kiệm|mẹo tiết kiệm)", 2),
    ("save_tips",         r"(tiết kiệm.*\d+\s*(triệu|tr|nghìn|k))", 2),
    ("reduce_tips",      r"(nên cắt|cắt khoản nào|giảm chi|bớt chi|chi không cần thiết)", 2),

    ("category_spending", r"(ăn uống|nhà ở|tiền trọ|di chuyển|học tập|giải trí|mua sắm|sức khỏe|hóa đơn)", 1),

    ("report_generate",   r"(tạo báo cáo|viết báo cáo|lập báo cáo|báo cáo tháng|báo cáo tổng hợp)", 2),

    ("analyze",           r"(phân tích|đánh giá|nhận xét|tổng quan|review|tóm tắt)", 1),

    ("goal_check",        r"(mục tiêu|tiết kiệm cho|mua laptop|du lịch|quỹ dự phòng|đạt được)", 1),

    ("compare",           r"(so với|so sánh|tháng trước|tăng hay giảm|khác gì)", 1),

    ("ocr_help",          r"(ocr|quét hóa đơn|hóa đơn|hình ảnh|chụp ảnh)", 1),

    ("help",              r"(bạn làm được gì|giúp được gì|chức năng|tính năng|hướng dẫn)", 1),
]


def classify_intent(text: str):
    """Trả về intent có score cao nhất và confidence."""
    text = (text or "").lower().strip()
    scores = defaultdict(int)
    for intent, pat, weight in INTENT_PATTERNS:
        if re.search(pat, text):
            scores[intent] += weight
    if not scores:
        return "unknown", 0.0
    intent = max(scores, key=scores.get)
    confidence = min(1.0, scores[intent] / 3.0)
    return intent, confidence


def extract_amount(text: str):
    """Tìm số tiền user đề cập: 'tiết kiệm 2 triệu' -> 2000000."""
    text = text.lower().replace(",", ".")
    # dạng "2 triệu", "2tr", "2tr5", "2.5 triệu"
    m = re.search(r"(\d+(?:[.,]\d+)?)\s*(triệu|tr|tr đồng)\b", text)
    if m:
        v = float(m.group(1).replace(",", "."))
        return int(v * 1_000_000)
    m = re.search(r"(\d+(?:[.,]\d+)?)\s*(nghìn|k|ngàn)\b", text)
    if m:
        v = float(m.group(1).replace(",", "."))
        return int(v * 1_000)
    # dạng số thuần > 1000 -> có thể là VND
    m = re.search(r"\b(\d{4,})\b", text)
    if m:
        return int(m.group(1))
    return None


# ===================== RESPONSE GENERATORS =====================

def _resp_top_spending():
    tx = _this_month_tx()
    if not tx:
        return "Tháng này bạn chưa có giao dịch nào. Hãy thử thêm một khoản chi để mình phân tích nhé! 💡"
    by_cat = _spending_by_category(tx)
    if not by_cat:
        return "Tháng này bạn chưa có khoản chi nào. 📊"
    top_cat, top_amt = max(by_cat.items(), key=lambda x: x[1])
    total_exp = sum(by_cat.values())
    pct = round(top_amt / total_exp * 100, 1) if total_exp else 0
    emoji = CATEGORIES_BY_ID.get(top_cat, {}).get("icon", "💰")
    return (
        f"📊 **{emoji} {_category_name(top_cat)}** là khoản bạn chi nhiều nhất tháng này: "
        f"**{_format_vnd(top_amt)}** ({pct}% tổng chi).\n\n"
        f"_Tổng quan top 3:_\n"
        + "\n".join(
            f"  {i+1}. {emoji} {CATEGORIES_BY_ID.get(c,{}).get('icon','•')} {_category_name(c)}: "
            f"**{_format_vnd(a)}**"
            for i, (c, a) in enumerate(sorted(by_cat.items(), key=lambda x: -x[1])[:3])
        )
        + "\n\n_Muốn mình gợi ý cách cắt giảm khoản này không? Thử hỏi: \"nên cắt khoản nào?\"_"
    )


def _resp_total_expense():
    tx = _this_month_tx()
    total = _total_by_type(tx, "expense")
    if not tx:
        return "Chưa có dữ liệu chi tiêu tháng này. 🤔"
    return (
        f"💸 Tổng chi tháng này của bạn: **{_format_vnd(total)}** "
        f"với **{sum(1 for t in tx if t['type']=='expense')}** giao dịch.\n"
        f"👉 Trung bình mỗi ngày: **{_format_vnd(int(total/30))}**."
    )


def _resp_total_income():
    tx = _this_month_tx()
    total = _total_by_type(tx, "income")
    return (
        f"💰 Tổng thu nhập tháng này: **{_format_vnd(total)}** "
        f"từ **{sum(1 for t in tx if t['type']=='income')}** nguồn thu.\n"
        f"Chi tiết: " + ", ".join(
            f"{CATEGORIES_BY_ID.get(t['category_id'],{}).get('icon','•')} {_format_vnd(t['amount'])}"
            for t in tx if t["type"] == "income"
        )
    )


def _resp_balance():
    tx = _this_month_tx()
    inc = _total_by_type(tx, "income")
    exp = _total_by_type(tx, "expense")
    balance = inc - exp
    status = "✅ Bạn đang **tiết kiệm** tốt!" if balance >= 0 else "⚠️ Bạn đang **thâm hụt** tháng này."
    return (
        f"📊 **Tình hình tháng này:**\n"
        f"  • Thu nhập: **{_format_vnd(inc)}**\n"
        f"  • Chi tiêu: **{_format_vnd(exp)}**\n"
        f"  • Còn lại: **{_format_vnd(balance)}**\n\n"
        f"{status}"
    )


def _resp_forecast():
    tx = _this_month_tx()
    exp_now = _total_by_type(tx, "expense")
    today = datetime.now()
    day = today.day
    days_in_month = 30
    avg_per_day = exp_now / day if day else 0
    forecast = int(avg_per_day * days_in_month)
    diff = forecast - exp_now
    return (
        f"🔮 **Dự báo chi tiêu cuối tháng:**\n"
        f"  • Đã chi {_day_count(day)} ngày: **{_format_vnd(exp_now)}**\n"
        f"  • Trung bình/ngày: **{_format_vnd(int(avg_per_day))}**\n"
        f"  • Ước tính cuối tháng: **{_format_vnd(forecast)}**\n"
        f"  • Có thể chi thêm: **{_format_vnd(diff)}**\n\n"
        f"_Dựa trên thuật toán Time-series Moving Average đơn giản._"
    )


def _resp_budget_check():
    tx = _this_month_tx()
    by_cat = _spending_by_category(tx)
    lines = ["📋 **Tình hình ngân sách tháng này:**\n"]
    over = []
    for b in SAMPLE_BUDGETS:
        cid = b["category_id"]
        spent = by_cat.get(cid, 0)
        limit = b["limit"]
        pct = round(spent / limit * 100, 1) if limit else 0
        name = _category_name(cid)
        icon = CATEGORIES_BY_ID.get(cid, {}).get("icon", "•")
        flag = "✅" if pct < 70 else "⚠️" if pct < 100 else "🚨"
        if pct >= 100:
            over.append(name)
        lines.append(f"  {flag} {icon} {name}: **{_format_vnd(spent)}** / {_format_vnd(limit)} ({pct}%)")
    if over:
        lines.append(f"\n🚨 **Vượt ngân sách:** {', '.join(over)}")
    else:
        lines.append("\n✨ Bạn đang kiểm soát chi tiêu rất tốt!")
    return "\n".join(lines)


def _resp_budget_suggest():
    tx = _this_month_tx()
    by_cat = _spending_by_category(tx)
    lines = ["💡 **Gợi ý ngân sách tháng tới (theo mô hình 50/30/20):**\n"]
    total = max(sum(by_cat.values()), 5_000_000)
    # Gợi ý theo % chi tiêu lịch sử
    for cat_id in ["cat_food", "cat_rent", "cat_trans", "cat_school", "cat_fun", "cat_shop", "cat_bill", "cat_health"]:
        spent = by_cat.get(cat_id, 0)
        # Buffer ngân sách = max(lịch sử + 10%, mặc định tối thiểu)
        suggested = int(spent * 1.1)
        suggested = max(suggested, {
            "cat_food": 1_500_000, "cat_rent": 2_500_000, "cat_trans": 500_000,
            "cat_school": 700_000, "cat_fun": 400_000, "cat_shop": 300_000,
            "cat_bill": 600_000, "cat_health": 300_000,
        }.get(cat_id, 200_000))
        icon = CATEGORIES_BY_ID.get(cat_id, {}).get("icon", "•")
        lines.append(f"  {icon} **{_category_name(cat_id)}**: {_format_vnd(suggested)}")
    lines.append(f"\n_Tổng ngân sách gợi ý: **{_format_vnd(5_500_000)}** (gồm cả quỹ tiết kiệm)_")
    return "\n".join(lines)


def _resp_save_tips(text):
    amount = extract_amount(text) or 2_000_000
    tx = _this_month_tx()
    by_cat = _spending_by_category(tx)
    if not by_cat:
        return "Bạn chưa có dữ liệu để mình gợi ý. Hãy thử thêm vài giao dịch trước nhé! 📝"
    # Sắp xếp các khoản chi nhiều nhất để gợi ý cắt
    sorted_cats = sorted(by_cat.items(), key=lambda x: -x[1])[:4]
    lines = [f"🎯 **Kế hoạch tiết kiệm {_format_vnd(amount)}:**\n"]
    cuts = {
        "cat_food":   ("🍜 Ăn uống", "  • Nấu ăn tại nhà 3-4 bữa/tuần (-300k-500k)\n  • Hạn chế trà sữa/cà phê mua ngoài (-200k)"),
        "cat_fun":    ("🎮 Giải trí", "  • Cắt gói Netflix/Spotify không cần thiết (-100k)\n  • Hạn chế karaoke/rạp phim (-300k)"),
        "cat_shop":   ("🛍️ Mua sắm", "  • Áp dụng quy tắc 24h chờ trước khi mua\n  • Tránh mua đồ sale không cần thiết (-500k)"),
        "cat_trans":  ("🚌 Di chuyển", "  • Đi xe buýt/đi bộ khi gần\n  • Gom chuyến Grab để tiết kiệm (-150k)"),
        "cat_shop":   ("🛍️ Mua sắm", "  • Tránh mua sắm vặt"),
        "cat_health": ("💊 Sức khỏe", "  • Mua thuốc generic thay vì biệt dược"),
        "cat_bill":   ("🧾 Hóa đơn", "  • Kiểm tra gói internet/combo tiết kiệm hơn"),
    }
    saved = 0
    tips_added = 0
    for cat_id, amt in sorted_cats:
        if cat_id in cuts and tips_added < 3:
            title, body = cuts[cat_id]
            lines.append(f"\n{title} (đang chi {_format_vnd(amt)}):")
            lines.append(body)
            tips_added += 1
            saved += 500_000
    lines.append(f"\n✅ **Tổng có thể tiết kiệm: ~{_format_vnd(min(saved, amount))}**")
    lines.append(f"\n📌 Mẹo thêm: đặt mục tiêu tiết kiệm cụ thể trong app để theo dõi tiến độ!")
    return "\n".join(lines)


def _resp_reduce_tips():
    tx = _this_month_tx()
    by_cat = _spending_by_category(tx)
    if not by_cat:
        return "Chưa có dữ liệu để phân tích. ✍️"
    # Top 3 khoản chi lớn nhất
    top3 = sorted(by_cat.items(), key=lambda x: -x[1])[:3]
    lines = ["✂️ **Top 3 khoản nên xem xét cắt giảm:**\n"]
    reasons = {
        "cat_food":   "Cân nhắc nấu ăn tại nhà hoặc đặt món theo tuần.",
        "cat_rent":   "Nếu ở ghép, có thể tìm phòng rẻ hơn hoặc ở cùng bạn.",
        "cat_trans":  "Sử dụng xe buýt/đi chung xe khi có thể.",
        "cat_school": "Đầu tư vào tài liệu dùng lại/second-hand.",
        "cat_fun":    "Tạm dừng các gói subscription không dùng thường xuyên.",
        "cat_shop":   "Áp dụng quy tắc 24h và danh sách mua sắm.",
        "cat_health": "Khám định kỳ tại phòng khám công để tiết kiệm.",
        "cat_bill":   "Kiểm tra gói combo internet+điện thoại.",
    }
    for cat_id, amt in top3:
        name = _category_name(cat_id)
        icon = CATEGORIES_BY_ID.get(cat_id, {}).get("icon", "•")
        lines.append(f"  {icon} **{name}**: {_format_vnd(amt)}")
        lines.append(f"     → {reasons.get(cat_id, 'Xem xét nhu cầu thực tế.')}\n")
    return "\n".join(lines)


def _resp_category_spending(text):
    for cat_id, cat in CATEGORIES_BY_ID.items():
        if cat["name"].lower() in text.lower() or any(
            kw in text.lower() for kw in {
                "ăn uống": "cat_food", "tiền trọ": "cat_rent", "trọ": "cat_rent",
                "xe": "cat_trans", "học": "cat_school", "sách": "cat_school",
                "game": "cat_fun", "phim": "cat_fun", "netflix": "cat_fun",
                "shopee": "cat_shop", "mua": "cat_shop",
                "thuốc": "cat_health", "khám": "cat_health",
                "điện": "cat_bill", "nước": "cat_bill", "net": "cat_bill",
            }.items() if kw in text.lower()
        ):
            tx = _this_month_tx()
            spent = sum(t["amount"] for t in tx if t["type"] == "expense" and t["category_id"] == cat_id)
            count = sum(1 for t in tx if t["type"] == "expense" and t["category_id"] == cat_id)
            if spent == 0:
                return f"{cat['icon']} Bạn chưa chi cho **{cat['name']}** tháng này. ✅"
            return (
                f"{cat['icon']} Bạn đã chi cho **{cat['name']}** tháng này: "
                f"**{_format_vnd(spent)}** ({count} giao dịch)."
            )
    return "Mình không xác định được danh mục bạn hỏi. Thử hỏi 'ăn uống', 'học tập', 'giải trí' nhé."


def _resp_report():
    tx = _this_month_tx()
    inc = _total_by_type(tx, "income")
    exp = _total_by_type(tx, "expense")
    by_cat = _spending_by_category(tx)
    top_cat = max(by_cat.items(), key=lambda x: x[1]) if by_cat else (None, 0)
    today = datetime.now().strftime("%d/%m/%Y")
    body = f"""📑 **BÁO CÁO TÀI CHÍNH THÁNG {_now_month()}**
_(Sinh tự động bởi AI - cập nhật {today})_

═══════════════════════════════
1️⃣ **TỔNG QUAN**
  • Tổng thu: **{_format_vnd(inc)}**
  • Tổng chi: **{_format_vnd(exp)}**
  • Chênh lệch: **{_format_vnd(inc - exp)}** {"✅" if inc >= exp else "⚠️"}
  • Số giao dịch: **{len(tx)}**

2️⃣ **CƠ CẤU CHI TIÊU**
"""
    for cat_id, amt in sorted(by_cat.items(), key=lambda x: -x[1])[:5]:
        cat = CATEGORIES_BY_ID.get(cat_id, {})
        pct = round(amt / exp * 100, 1) if exp else 0
        body += f"  • {cat.get('icon','•')} {cat.get('name', cat_id)}: {_format_vnd(amt)} ({pct}%)\n"

    body += f"""
3️⃣ **NHẬN XÉT AI**
  • Khoản chi lớn nhất: **{_category_name(top_cat[0])}** ({_format_vnd(top_cat[1])})
  • Điểm tích cực: {"Tỷ lệ tiết kiệm tốt" if inc > exp else "Cần điều chỉnh chi tiêu"}
  • Gợi ý: Giảm 10% chi {_category_name(top_cat[0])} sẽ tiết kiệm ~{_format_vnd(int(top_cat[1]*0.1))}

═══════════════════════════════
_Báo cáo này có thể xuất ra PDF/Excel trong bản production._"""
    return body


def _resp_analyze():
    tx = _this_month_tx()
    if not tx:
        return "Chưa có giao dịch để phân tích. Hãy thêm vài khoản chi trước nhé! 📊"
    inc = _total_by_type(tx, "income")
    exp = _total_by_type(tx, "expense")
    savings_rate = (inc - exp) / inc * 100 if inc else 0
    by_cat = _spending_by_category(tx)
    top = sorted(by_cat.items(), key=lambda x: -x[1])[:1]
    top_name = _category_name(top[0][0]) if top else "N/A"
    return (
        f"🔍 **Phân tích chi tiêu tháng này:**\n\n"
        f"• **Tỷ lệ tiết kiệm**: {savings_rate:.1f}% "
        f"{'✅ tốt (>20%)' if savings_rate >= 20 else '⚠️ cần cải thiện'}\n"
        f"• **Khoản chi lớn nhất**: {top_name} ({_format_vnd(top[0][1]) if top else 'N/A'})\n"
        f"• **Số ngày đã chi**: {len(set(t['date'] for t in tx))} ngày\n"
        f"• **Trung bình/giao dịch**: {_format_vnd(int(exp / max(1,sum(1 for t in tx if t['type']=='expense'))))}\n\n"
        f"📈 Bạn đang trên hướng tiết kiệm tốt! Tiếp tục theo dõi nhé."
    )


def _resp_goal_check():
    lines = ["🎯 **Tiến độ mục tiêu tiết kiệm:**\n"]
    for g in SAMPLE_GOALS:
        pct = round(g["saved"] / g["target"] * 100, 1)
        flag = "🟢" if pct >= 70 else "🟡" if pct >= 30 else "🔴"
        remaining = g["target"] - g["saved"]
        lines.append(
            f"  {flag} **{g['name']}**: {_format_vnd(g['saved'])} / {_format_vnd(g['target'])} ({pct}%)\n"
            f"     → Còn thiếu: **{_format_vnd(remaining)}**"
        )
    lines.append("\n💪 Mỗi ngày tiết kiệm một chút, bạn sẽ đạt được mục tiêu thôi!")
    return "\n".join(lines)


def _resp_compare():
    return (
        "📊 **So sánh với tháng trước:**\n\n"
        "_(Tính năng đang phát triển - sẽ tích hợp trong bản chính thức)_\n\n"
        "Trong bản demo, bạn có thể xem biểu đồ xu hướng trong trang **Báo cáo**."
    )


def _resp_ocr():
    return (
        "📷 **Tính năng OCR hóa đơn** (UC003 - AI OCR):\n\n"
        "Trong bản production, bạn có thể:\n"
        "  1. Chụp ảnh hóa đơn/biên lai\n"
        "  2. AI (PaddleOCR/Google Vision) sẽ trích xuất: tên cửa hàng, ngày, tổng tiền\n"
        "  3. Tự động tạo giao dịch mới với danh mục AI đề xuất\n\n"
        "⏱️ Thời gian xử lý: < 3.0s"
    )


def _resp_greeting():
    hour = datetime.now().hour
    if hour < 12:  tod = "Chào buổi sáng"
    elif hour < 18: tod = "Chào buổi chiều"
    else: tod = "Chào buổi tối"
    return (
        f"👋 {tod}! Mình là **AI Financial Advisor** — trợ lý tài chính cá nhân của bạn.\n\n"
        f"Mình có thể giúp bạn:\n"
        f"  💸 Phân tích chi tiêu tháng này\n"
        f"  📊 Tạo báo cáo tài chính tự động\n"
        f"  💡 Gợi ý kế hoạch tiết kiệm\n"
        f"  🔮 Dự báo chi tiêu cuối tháng\n"
        f"  🎯 Đề xuất ngân sách theo mô hình 50/30/20\n\n"
        f"_Bạn muốn hỏi gì nào?_"
    )


def _resp_thanks():
    return "😊 Không có gì! Mình luôn sẵn sàng giúp bạn quản lý tài chính thông minh hơn."


def _resp_help():
    return (
        "🤖 **Các chức năng mình hỗ trợ:**\n\n"
        "📊 **Phân tích:**\n"
        "  • \"Phân tích chi tiêu tháng này\"\n"
        "  • \"Chi nhiều nhất vào đâu?\"\n"
        "  • \"Tổng chi tháng này bao nhiêu?\"\n\n"
        "💡 **Tư vấn tiết kiệm:**\n"
        "  • \"Làm sao tiết kiệm 2 triệu?\"\n"
        "  • \"Nên cắt khoản nào?\"\n"
        "  • \"Gợi ý ngân sách tháng tới\"\n\n"
        "📈 **Dự báo & Báo cáo:**\n"
        "  • \"Dự báo chi tiêu cuối tháng\"\n"
        "  • \"Tạo báo cáo tài chính tháng 9\"\n\n"
        "🎯 **Mục tiêu & Ngân sách:**\n"
        "  • \"Tình hình ngân sách\"\n"
        "  • \"Tiến độ mục tiêu tiết kiệm\"\n\n"
        "_Thử hỏi bất kỳ câu nào nhé!_"
    )


def _resp_unknown(text):
    return (
        f"🤔 Mình chưa hiểu rõ câu: _\"{text[:80]}{'...' if len(text)>80 else ''}\"_\n\n"
        f"💬 Bạn có thể thử hỏi:\n"
        f"  • \"Phân tích chi tiêu tháng này\"\n"
        f"  • \"Làm sao tiết kiệm 2 triệu?\"\n"
        f"  • \"Tạo báo cáo tài chính\"\n\n"
        f"Hoặc gõ **\"giúp\"** để xem tất cả tính năng."
    )


# ===================== MAIN ENTRY =====================

RESPONSE_HANDLERS = {
    "greeting":         _resp_greeting,
    "thanks":           _resp_thanks,
    "help":             _resp_help,
    "top_spending":     _resp_top_spending,
    "total_expense":    _resp_total_expense,
    "total_income":     _resp_total_income,
    "balance":          _resp_balance,
    "forecast":         _resp_forecast,
    "budget_check":     _resp_budget_check,
    "budget_suggest":   _resp_budget_suggest,
    "save_tips":        _resp_save_tips,
    "reduce_tips":      _resp_reduce_tips,
    "category_spending":_resp_category_spending,
    "report_generate":  _resp_report,
    "analyze":          _resp_analyze,
    "goal_check":       _resp_goal_check,
    "compare":          _resp_compare,
    "ocr_help":         _resp_ocr,
}


def chat(message: str, history=None):
    """API chính: nhận message, trả về (reply, intent, confidence)."""
    intent, confidence = classify_intent(message)
    handler = RESPONSE_HANDLERS.get(intent, _resp_unknown)
    if handler is _resp_unknown:
        # unknown: truyền text vào để hiển thị trong phản hồi
        reply = _resp_unknown(message)
    else:
        # handler cần message: riêng _resp_save_tips & _resp_category_spending
        if intent in ("save_tips", "category_spending"):
            reply = handler(message)
        else:
            reply = handler()
    return {
        "reply": reply,
        "intent": intent,
        "confidence": round(confidence, 2),
    }


def _day_count(day):
    return day


# Sanity check
if __name__ == "__main__":
    for q in [
        "Xin chào",
        "Tháng này chi nhiều nhất vào đâu?",
        "Tổng chi bao nhiêu?",
        "Làm sao tiết kiệm 2 triệu?",
        "Dự báo cuối tháng",
        "Tạo báo cáo tháng này",
        "Tình hình ngân sách",
    ]:
        r = chat(q)
        print(f"\n>>> Q: {q}\nA ({r['intent']}): {r['reply'][:200]}...")
