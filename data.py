"""
Module dữ liệu mẫu - Hệ thống quản lý chi tiêu cá nhân tích hợp AI
Nhóm 12 - ĐH CNTT&TT Thái Nguyên
Dữ liệu demo sinh viên điển hình (in-memory, reset khi restart server).
"""

from datetime import datetime, timedelta
import random

# ---------- DANH MỤC THU/CHI MẶC ĐỊNH ----------
DEFAULT_CATEGORIES = [
    # Chi phí
    {"id": "cat_food",   "name": "Ăn uống",        "type": "expense", "icon": "🍜", "color": "#f97316"},
    {"id": "cat_rent",   "name": "Nhà ở / Tiền trọ","type": "expense", "icon": "🏠", "color": "#3b82f6"},
    {"id": "cat_trans",  "name": "Di chuyển",       "type": "expense", "icon": "🚌", "color": "#06b6d4"},
    {"id": "cat_school", "name": "Học tập",         "type": "expense", "icon": "📚", "color": "#8b5cf6"},
    {"id": "cat_fun",    "name": "Giải trí",        "type": "expense", "icon": "🎮", "color": "#ec4899"},
    {"id": "cat_shop",   "name": "Mua sắm",         "type": "expense", "icon": "🛍️", "color": "#f59e0b"},
    {"id": "cat_health", "name": "Sức khỏe",        "type": "expense", "icon": "💊", "color": "#10b981"},
    {"id": "cat_bill",   "name": "Hóa đơn (điện,nước,net)", "type": "expense", "icon": "🧾", "color": "#64748b"},
    {"id": "cat_other_e","name": "Chi khác",        "type": "expense", "icon": "💸", "color": "#94a3b8"},
    # Thu nhập
    {"id": "cat_salary", "name": "Lương / Part-time","type": "income",  "icon": "💼", "color": "#22c55e"},
    {"id": "cat_gift",   "name": "Tiền được cho / Thưởng", "type": "income", "icon": "🎁", "color": "#eab308"},
    {"id": "cat_other_i","name": "Thu khác",        "type": "income",  "icon": "💰", "color": "#14b8a6"},
]

CATEGORIES_BY_ID = {c["id"]: c for c in DEFAULT_CATEGORIES}


# ---------- RULE PHÂN LOẠI TỰ ĐỘNG BẰNG AI (MÔ PHỎNG) ----------
AUTO_CATEGORY_RULES = [
    # (từ khóa, danh mục)
    (["cơm", "phở", "bún", "trà sữa", "cafe", "cà phê", "gong cha", "highland",
      "ăn", "lẩu", "nướng", "kfc", "lotteria", "pizza", "burger", "starbucks",
      "quán", "buffet", "snack", "chè", "bánh"], "cat_food"),
    (["trọ", "nhà", "phòng", "thuê phòng", "tiền phòng"], "cat_rent"),
    (["xe", "grab", "be", "xăng", "bus", "xe buýt", "taxi", "vé tàu", "vé xe",
      "đổ xăng", "gửi xe"], "cat_trans"),
    (["sách", "vở", "học phí", "bút", "in ấn", "photo", "đồ án", "luận văn",
      "khoản học", "trường"], "cat_school"),
    (["netflix", "spotify", "youtube premium", "steam", "game", "rạp", "phim",
      "karaoke", "bar", "club"], "cat_fun"),
    (["shopee", "lazada", "tiki", "mua", "quần áo", "giày", "thời trang",
      "đồ dùng"], "cat_shop"),
    (["thuốc", "bệnh viện", "phòng khám", "khám", "bác sĩ", "paracetamol"],
     "cat_health"),
    (["điện", "nước", "internet", "wifi", "net", "3g", "4g", "5g", "vinaphone",
      "viettel", "mobifone"], "cat_bill"),
    (["lương", "part time", "part-time", "công việc", "trợ cấp"], "cat_salary"),
    (["thưởng", "được cho", "mừng tuổi", "lì xì"], "cat_gift"),
]


def ai_auto_categorize(text: str) -> str:
    """Mô phỏng AI Text Classification - phân loại giao dịch từ mô tả tiếng Việt.

    Dùng padded matching để tránh false positive (VD: 'ăn' trong 'xăng').
    """
    import re
    t = (text or "").lower().strip()
    # Pad với khoảng trắng để khớp biên an toàn
    padded = " " + re.sub(r"[^\w\s]", " ", t) + " "
    for keywords, cat_id in AUTO_CATEGORY_RULES:
        for kw in keywords:
            kw_norm = kw.lower().strip()
            # Yêu cầu keyword đứng rời (có khoảng trắng bao quanh)
            if (" " + kw_norm + " ") in padded:
                return cat_id
            # Hoặc đứng đầu/cuối
            if padded.startswith(kw_norm + " ") or padded.endswith(" " + kw_norm) or padded.strip() == kw_norm:
                return cat_id
    return "cat_other_e"


# ---------- DATA MẪU CHO USER DEMO ----------
def _make_sample_transactions():
    """Sinh ~30 giao dịch mẫu trong 30 ngày gần nhất."""
    today = datetime.now()
    samples = [
        ("Ăn cơm trưa canteen trường",      35000,  "expense", 1),
        ("Mua trà sữa Gong Cha",            55000,  "expense", 1),
        ("Đổ xăng xe máy",                 80000,  "expense", 2),
        ("Grab đi học",                     45000,  "expense", 2),
        ("Tiền trọ tháng này",            2500000,  "expense", 5),
        ("Mua sách giáo trình",            180000,  "expense", 4),
        ("Học phí học kỳ",               3200000,  "expense", 7),
        ("Netflix Premium",                 260000,  "expense", 6),
        ("Mua đồ Shopee quần áo",          420000,  "expense", 8),
        ("Cà phê Highland với nhóm",        75000,  "expense", 3),
        ("Ăn lẩu Thái cuối tuần",         350000,  "expense", 3),
        ("Tiền điện tháng này",           250000,  "expense", 10),
        ("Internet VNPT",                  220000,  "expense", 11),
        ("Khám sức khỏe định kỳ",         500000,  "expense", 12),
        ("Mua bút vở photo bài",           35000,  "expense", 4),
        ("Xem phim CGV",                  180000,  "expense", 9),
        ("Tiền xe buýt đi học",             60000,  "expense", 1),
        ("Lương part-time gia sư",        2500000,  "income", 3),
        ("Ba mẹ cho tiền ăn",            1500000,  "income", 8),
        ("Thưởng đồ án tốt nghiệp",      1000000,  "income", 12),
        ("Mua giày thể thao mới",         650000,  "expense", 14),
        ("Buffet King BBQ sinh nhật bạn",  450000,  "expense", 18),
        ("Đăng ký Spotify Premium",        59000,  "expense", 17),
        ("Ăn sáng bánh mì",                20000,  "expense", 1),
        ("Ăn tối cùng gia đình",          200000,  "expense", 22),
        ("Đổ xăng đầy bình",             150000,  "expense", 19),
        ("Mua dầu gội đầu",               110000,  "expense", 21),
        ("Nạp tiền điện thoại Viettel",    50000,  "expense", 23),
        ("Tiền gửi xe máy cả tháng",       90000,  "expense", 6),
        ("In đồ án + photo",               45000,  "expense", 27),
    ]

    transactions = []
    for i, (desc, amount, t_type, days_ago) in enumerate(samples):
        date = today - timedelta(days=days_ago)
        cat_id = ai_auto_categorize(desc)
        if t_type == "income" and cat_id in ("cat_other_e",):
            cat_id = "cat_salary"
        transactions.append({
            "id": f"tx_{i+1:03d}",
            "description": desc,
            "amount": amount,
            "type": t_type,
            "category_id": cat_id,
            "date": date.strftime("%Y-%m-%d"),
            "wallet": "Tiền mặt" if i % 2 == 0 else "Techcombank",
        })
    return transactions


SAMPLE_TRANSACTIONS = _make_sample_transactions()

# ---------- NGÂN SÁCH THÁNG HIỆN TẠI ----------
SAMPLE_BUDGETS = [
    {"id": "bud_food",  "category_id": "cat_food",   "limit": 1500000, "period": "monthly"},
    {"id": "bud_rent",  "category_id": "cat_rent",   "limit": 2500000, "period": "monthly"},
    {"id": "bud_trans", "category_id": "cat_trans",  "limit":  500000, "period": "monthly"},
    {"id": "bud_school","category_id": "cat_school", "limit":  800000, "period": "monthly"},
    {"id": "bud_fun",   "category_id": "cat_fun",    "limit":  600000, "period": "monthly"},
    {"id": "bud_shop",  "category_id": "cat_shop",   "limit":  500000, "period": "monthly"},
    {"id": "bud_bill",  "category_id": "cat_bill",   "limit":  600000, "period": "monthly"},
]

# ---------- MỤC TIÊU TIẾT KIỆM ----------
SAMPLE_GOALS = [
    {"id": "goal_laptop",  "name": "Mua Laptop mới",   "target": 20000000, "saved": 8500000},
    {"id": "goal_travel",  "name": "Du lịch Đà Lạt",   "target":  5000000, "saved": 3200000},
    {"id": "goal_emergency","name": "Quỹ dự phòng",    "target": 10000000, "saved": 4500000},
]

# ---------- USER DEMO ----------
DEMO_USER = {
    "username": "demo",
    "password": "123456",
    "fullname": "Nguyễn Xuân Phong",
    "email": "phong.nx@ictu.edu.vn",
}
