"""
Analytics Module - Các hàm phân tích tài chính nâng cao
Nhóm 12 - AIA331 - Nâng cấp dự án (Prompt_nang_cap_du_an_tai_chinh.docx)

Nguyên tắc:
- KHÔNG bịa dữ liệu: trả về None/empty khi không đủ dữ liệu.
- Tận dụng dữ liệu thật từ SAMPLE_TRANSACTIONS / SAMPLE_BUDGETS / SAMPLE_GOALS.
- Tất cả kết quả đều giải thích được (explainable) - đi kèm con số tính toán.
- Simulation tách biệt với dữ liệu thật.
"""
from datetime import datetime, timedelta
from collections import defaultdict
from statistics import mean, median, stdev
import re

from data import (
    DEFAULT_CATEGORIES, CATEGORIES_BY_ID,
    SAMPLE_TRANSACTIONS, SAMPLE_BUDGETS, SAMPLE_GOALS,
)


# ===================== TIỆN ÍCH CHUNG =====================

def _format_vnd(amount):
    if amount is None:
        return "—"
    return f"{amount:,.0f}".replace(",", ".") + " đ"


def _category_name(cat_id):
    cat = CATEGORIES_BY_ID.get(cat_id)
    return cat["name"] if cat else cat_id


def _category_icon(cat_id):
    return CATEGORIES_BY_ID.get(cat_id, {}).get("icon", "•")


def _this_month_tx():
    month = datetime.now().strftime("%Y-%m")
    return [t for t in SAMPLE_TRANSACTIONS if t["date"].startswith(month)]


def _expenses(tx_list=None):
    return [t for t in (tx_list or SAMPLE_TRANSACTIONS) if t["type"] == "expense"]


def _incomes(tx_list=None):
    return [t for t in (tx_list or SAMPLE_TRANSACTIONS) if t["type"] == "income"]


# Các danh mục thiết yếu (để tính "chi phí thiết yếu" cho survival days)
ESSENTIAL_CATEGORIES = {
    "cat_food", "cat_rent", "cat_bill", "cat_trans", "cat_health",
}


# ===================== A1. DỰ BÁO CHI TIÊU CUỐI THÁNG (NÂNG CẤP) =====================

def forecast_spending(month=None):
    """Dự báo tổng chi tiêu cuối tháng.

    Logic nâng cấp:
    - Tính tốc độ chi 7 ngày gần nhất.
    - Kết hợp tốc độ tháng hiện tại (đến hiện tại).
    - So sánh với ngân sách tháng (nếu có).
    - Ước tính ngày vượt ngân sách (nếu chi vượt).

    Trả về dict với đầy đủ thông tin; nếu dữ liệu chưa đủ -> None cho các field không tính được.
    """
    if month is None:
        month = datetime.now().strftime("%Y-%m")

    tx_this = [t for t in SAMPLE_TRANSACTIONS
               if t["date"].startswith(month) and t["type"] == "expense"]

    if not tx_this:
        return {
            "month": month, "has_data": False,
            "message": f"Chưa có giao dịch chi tiêu nào trong tháng {month}.",
            "spent_so_far": 0, "days_elapsed": 0,
            "forecast_total": None, "speed_7day": None,
            "budget_total": None, "diff_vs_budget": None,
            "overshoot_date": None, "warning_level": "none",
        }

    today = datetime.now()
    days_elapsed = max(today.day, 1)
    days_in_month = 30  # đơn giản hóa
    days_remaining = max(days_in_month - days_elapsed, 0)

    spent_so_far = sum(t["amount"] for t in tx_this)
    avg_per_day = spent_so_far / days_elapsed

    # Tốc độ 7 ngày gần nhất
    last7_start = today - timedelta(days=7)
    last7_tx = [t for t in tx_this
                if datetime.strptime(t["date"], "%Y-%m-%d").date() >= last7_start.date()]
    speed_7day = (sum(t["amount"] for t in last7_tx) / 7) if last7_tx else avg_per_day

    # Forecast: kết hợp tốc độ 7 ngày (ưu tiên hơn) + tốc độ tháng
    # Trọng số: 70% tốc độ 7 ngày, 30% tốc độ từ đầu tháng
    combined_speed = 0.7 * speed_7day + 0.3 * avg_per_day
    forecast_total = int(spent_so_far + combined_speed * days_remaining)

    # So sánh với ngân sách tháng (chỉ tính budget tổng = tổng limit)
    budget_total = sum(b["limit"] for b in SAMPLE_BUDGETS)
    diff_vs_budget = forecast_total - budget_total if budget_total else None

    # Ước tính ngày vượt budget (nếu combined_speed > 0)
    overshoot_date = None
    warning_level = "ok"
    if budget_total and combined_speed > 0:
        # số ngày nữa sẽ chạm/vượt budget
        remaining_to_budget = budget_total - spent_so_far
        if remaining_to_budget > 0:
            days_to_budget = remaining_to_budget / combined_speed
            if days_to_budget <= days_remaining:
                overshoot_date = (today + timedelta(days=int(days_to_budget))).strftime("%d/%m")
                warning_level = "warning" if days_to_budget <= 7 else "watch"
        else:
            overshoot_date = "Đã vượt"
            warning_level = "danger"

    return {
        "month": month,
        "has_data": True,
        "spent_so_far": spent_so_far,
        "days_elapsed": days_elapsed,
        "days_remaining": days_remaining,
        "avg_per_day": int(avg_per_day),
        "speed_7day": int(speed_7day),
        "combined_speed": int(combined_speed),
        "forecast_total": forecast_total,
        "budget_total": budget_total,
        "diff_vs_budget": diff_vs_budget,
        "overshoot_date": overshoot_date,
        "warning_level": warning_level,
    }


# ===================== A2. PHÁT HIỆN KHOẢN CHI BẤT THƯỜNG =====================

def detect_anomalies(month=None, z_threshold=2.0, use_current_as_baseline=True):
    """Phát hiện giao dịch chi tiêu bất thường theo từng danh mục.

    Phương pháp: Modified Z-score sử dụng MAD (Median Absolute Deviation) -
    robust hơn z-score truyền thống với outliers.
    - Mỗi giao dịch mới được so sánh với median lịch sử cùng danh mục.
    - Nếu |amount - median| / MAD > threshold → bất thường.

    Cần tối thiểu 5 giao dịch trong danh mục để có ý nghĩa thống kê.
    Nếu use_current_as_baseline=True (mặc định), dùng giao dịch tháng hiện tại
    làm baseline (trừ chính giao dịch đang xét) - áp dụng cho trường hợp demo
    chỉ có data tháng này.
    """
    if month is None:
        month = datetime.now().strftime("%Y-%m")

    baseline_tx = [t for t in _expenses() if not t["date"].startswith(month)]
    current_tx = [t for t in _expenses() if t["date"].startswith(month)]

    anomalies = []
    for t in current_tx:
        # Lấy baseline: ưu tiên lịch sử trước, fallback về các tx khác trong tháng
        if baseline_tx:
            amounts = [tt["amount"] for tt in baseline_tx if tt["category_id"] == t["category_id"]]
        elif use_current_as_baseline:
            amounts = [tt["amount"] for tt in current_tx
                       if tt["category_id"] == t["category_id"] and tt["id"] != t["id"]]
        else:
            amounts = []

        if len(amounts) < 5:
            continue
        med = median(amounts)
        mad = median([abs(a - med) for a in amounts]) or 1
        modified_z = 0.6745 * (t["amount"] - med) / mad
        if abs(modified_z) >= z_threshold:
            anomalies.append({
                "tx_id": t["id"],
                "description": t["description"],
                "amount": t["amount"],
                "date": t["date"],
                "category_id": t["category_id"],
                "category_name": _category_name(t["category_id"]),
                "category_icon": _category_icon(t["category_id"]),
                "median_amount": int(med),
                "z_score": round(modified_z, 2),
                "ratio": round(t["amount"] / med, 2) if med else None,
                "severity": "high" if abs(modified_z) >= 3 else "medium",
            })

    anomalies.sort(key=lambda a: -abs(a["z_score"]))
    return anomalies


# ===================== B. THEO DÕI HÓA ĐƠN ĐỊNH KỲ =====================

def detect_recurring_bills(min_occurrences=2):
    """Phát hiện các khoản chi lặp lại (hóa đơn định kỳ).

    Thuật toán:
    - Gom các giao dịch có description tương tự nhau (so khớp keyword).
    - Tính khoảng cách ngày giữa các lần xuất hiện.
    - Nếu có ≥ min_occurrences lần xuất hiện trong vòng 90 ngày gần nhất
      và khoảng cách trung bình ổn định → coi là recurring.
    - Ước tính chu kỳ, ngày thanh toán tiếp theo, số tiền dự kiến.
    """
    keywords_bills = [
        "trọ", "thuê phòng", "tiền nhà", "điện", "nước",
        "internet", "wifi", "net", "điện thoại", "3g", "4g", "5g",
        "vinaphone", "viettel", "mobifone",
        "netflix", "spotify", "youtube premium", "steam",
        "bảo hiểm", "phí", "học phí",
    ]

    today = datetime.now().date()
    last_90 = today - timedelta(days=90)
    last_60 = today - timedelta(days=60)

    bills = []
    seen_keys = set()  # tránh trùng lặp description tương tự

    for t in _expenses():
        desc_lower = t["description"].lower()
        # Kiểm tra keyword
        matched_keyword = None
        for kw in keywords_bills:
            if (" " + kw + " ") in (" " + desc_lower + " ") or \
               desc_lower.startswith(kw) or desc_lower.endswith(kw) or \
               (" " + kw) in (" " + desc_lower):
                matched_keyword = kw
                break

        if not matched_keyword:
            continue

        # Gom tất cả giao dịch cùng keyword
        same_kind = [
            tt for tt in _expenses()
            if matched_keyword in tt["description"].lower()
            and datetime.strptime(tt["date"], "%Y-%m-%d").date() >= last_90
        ]

        if len(same_kind) < min_occurrences:
            continue

        # Tránh trùng trong output
        key = matched_keyword + "_" + (same_kind[0]["category_id"])
        if key in seen_keys:
            continue
        seen_keys.add(key)

        # Sắp xếp theo ngày
        same_kind.sort(key=lambda x: x["date"])
        amounts = [tt["amount"] for tt in same_kind]
        dates = [datetime.strptime(tt["date"], "%Y-%m-%d").date() for tt in same_kind]

        # Ước tính chu kỳ
        if len(dates) >= 2:
            intervals = [(dates[i] - dates[i-1]).days for i in range(1, len(dates))]
            avg_interval = int(mean(intervals))
            cycle_days = _round_to_cycle(avg_interval)
        else:
            avg_interval = 30
            cycle_days = "tháng"

        # Ước tính ngày thanh toán tiếp theo
        if dates:
            last_date = dates[-1]
            if isinstance(cycle_days, int):
                next_date = last_date + timedelta(days=cycle_days)
            else:
                next_date = last_date + timedelta(days=30)
            days_until = (next_date - today).days
        else:
            next_date = None
            days_until = None

        avg_amount = int(mean(amounts)) if amounts else 0

        bills.append({
            "keyword": matched_keyword,
            "label": matched_keyword.title(),
            "category_id": same_kind[0]["category_id"],
            "category_name": _category_name(same_kind[0]["category_id"]),
            "category_icon": _category_icon(same_kind[0]["category_id"]),
            "occurrences": len(same_kind),
            "avg_amount": avg_amount,
            "last_amount": amounts[-1] if amounts else 0,
            "last_date": dates[-1].strftime("%Y-%m-%d") if dates else None,
            "next_date": next_date.strftime("%Y-%m-%d") if next_date else None,
            "next_date_str": next_date.strftime("%d/%m") if next_date else None,
            "days_until": days_until,
            "cycle_text": _cycle_to_text(cycle_days),
            "history": [{"date": tt["date"], "amount": tt["amount"]} for tt in same_kind],
            "is_upcoming": days_until is not None and 0 <= days_until <= 7,
            "is_imminent": days_until is not None and 0 <= days_until <= 3,
        })

    # Sắp xếp: sắp đến hạn trước
    bills.sort(key=lambda b: b["days_until"] if b["days_until"] is not None else 999)
    return bills


def _round_to_cycle(days):
    """Làm tròn khoảng cách ngày về chu kỳ tiêu chuẩn."""
    if 6 <= days <= 9: return 7
    if 13 <= days <= 17: return 14
    if 27 <= days <= 33: return 30
    if 85 <= days <= 95: return 90
    if 175 <= days <= 190: return 180
    if 355 <= days <= 375: return 365
    return days


def _cycle_to_text(cycle):
    if cycle == 7: return "tuần"
    if cycle == 14: return "2 tuần"
    if cycle == 30: return "tháng"
    if cycle == 90: return "quý"
    if cycle == 180: return "6 tháng"
    if cycle == 365: return "năm"
    return f"{cycle} ngày"


# ===================== C. MÔ PHỎNG KỊCH BẢN TÀI CHÍNH "NẾU - THÌ" =====================

def simulate_scenario(scenario_type, **params):
    """Mô phỏng kịch bản tài chính. KHÔNG ghi vào dữ liệu thật.

    Supported scenarios:
    - "monthly_installment": Thêm khoản trả góp hàng tháng.
      params: amount (int), months (int)
    - "income_change": Thu nhập thay đổi %.
      params: percent (float, có thể âm)
    - "lump_sum_expense": Một khoản chi lớn 1 lần.
      params: amount (int)
    - "savings_target": Tiết kiệm để đạt mục tiêu X trong Y tháng.
      params: target (int), months (int)
    """
    month_tx = _this_month_tx()
    income_now = sum(t["amount"] for t in month_tx if t["type"] == "income")
    expense_now = sum(t["amount"] for t in month_tx if t["type"] == "expense")

    # Tính số dư giả định = tổng thu nhập - tổng chi tiêu hiện tại
    # (đơn giản hóa: không tính ví, mà tính trên cashflow tháng)
    current_balance = income_now - expense_now

    # Tổng budget hiện tại
    total_budget = sum(b["limit"] for b in SAMPLE_BUDGETS)

    result = {
        "scenario": scenario_type,
        "params": params,
        "current": {
            "income_month": income_now,
            "expense_month": expense_now,
            "balance_month": current_balance,
            "total_budget": total_budget,
        },
        "after": {},
        "impact": {},
    }

    if scenario_type == "monthly_installment":
        amount = int(params.get("amount", 0))
        months = int(params.get("months", 1))
        new_expense = expense_now + amount
        new_balance = income_now - new_expense
        is_negative = new_balance < 0
        result["after"] = {
            "new_monthly_expense": new_expense,
            "new_monthly_balance": new_balance,
            "total_extra_cost": amount * months,
        }
        result["impact"] = {
            "balance_change": -amount,
            "budget_overrun": new_expense - total_budget if total_budget else None,
            "risk_negative": is_negative,
            "warning": _installment_warning(amount, months, new_balance),
        }

    elif scenario_type == "income_change":
        percent = float(params.get("percent", 0))
        new_income = int(income_now * (1 + percent / 100))
        new_balance = new_income - expense_now
        result["after"] = {
            "new_income": new_income,
            "income_delta": new_income - income_now,
            "new_balance": new_balance,
        }
        result["impact"] = {
            "balance_change": new_balance - current_balance,
            "savings_rate_after": round((new_income - expense_now) / new_income * 100, 1) if new_income else 0,
        }

    elif scenario_type == "lump_sum_expense":
        amount = int(params.get("amount", 0))
        new_balance = current_balance - amount
        result["after"] = {
            "new_balance_after_one_time": new_balance,
            "months_to_recover": _months_to_recover(amount, current_balance),
        }
        result["impact"] = {
            "balance_change": -amount,
            "risk_negative": new_balance < 0,
            "survival_after": _survival_days_after(amount),
        }

    elif scenario_type == "savings_target":
        target = int(params.get("target", 0))
        months = int(params.get("months", 1))
        per_month = int(target / months) if months else target
        # Còn có thể tiết kiệm được bao nhiêu/tháng (sau chi phí)?
        max_saveable = max(current_balance, 0)
        result["after"] = {
            "required_per_month": per_month,
            "max_saveable_now": max_saveable,
            "feasible": max_saveable >= per_month,
        }
        result["impact"] = {
            "shortfall": max(per_month - max_saveable, 0),
            "months_to_target_at_current": (
                int(target / max_saveable) if max_saveable > 0 else None
            ),
        }

    return result


def _installment_warning(amount, months, new_balance):
    if new_balance < 0:
        return f"⚠️ CẢNH BÁO: Khoản trả góp này khiến bạn bị ÂM {abs(new_balance):,.0f} đ/tháng."
    if new_balance < amount * 2:
        return f"⚠️ Số dư sau chi chỉ còn {new_balance:,.0f} đ - rất rủi ro."
    return f"✅ Khả thi - số dư sau chi: {new_balance:,.0f} đ"


def _months_to_recover(amount, balance):
    if balance <= 0:
        return None
    return max(1, int(amount / balance))


def _survival_days_after(amount):
    """Số ngày sinh tồn nếu bỏ ra khoản amount."""
    res = survival_days()
    if res.get("balance_available") is None:
        return None
    new_bal = res["balance_available"] - amount
    if new_bal <= 0:
        return 0
    return int(new_bal / res["essential_per_day"])


# ===================== D. SỐ NGÀY SINH TỒN & QUỸ DỰ PHÒNG =====================

def survival_days():
    """Tính số ngày sinh tồn với chi phí thiết yếu.

    Công thức: Số dư khả dụng / Chi phí thiết yếu trung bình mỗi ngày.

    Số dư khả dụng = Tổng thu nhập tháng - Tổng chi tiêu tháng hiện tại
                     (đơn giản hóa, chưa tính ví/savings).

    Chi phí thiết yếu = Trung bình chi tiêu các danh mục thiết yếu (30 ngày gần nhất).
    """
    month_tx = _this_month_tx()

    if not month_tx:
        return {
            "has_data": False,
            "message": "Chưa có dữ liệu tháng này để tính quỹ dự phòng.",
        }

    income = sum(t["amount"] for t in month_tx if t["type"] == "income")
    expense = sum(t["amount"] for t in month_tx if t["type"] == "expense")
    balance = income - expense

    # Tính chi phí thiết yếu: lấy tất cả giao dịch chi trong danh mục thiết yếu
    # từ 30 ngày gần nhất
    today = datetime.now().date()
    last30 = today - timedelta(days=30)
    essential_tx = [
        t for t in _expenses()
        if t["category_id"] in ESSENTIAL_CATEGORIES
        and datetime.strptime(t["date"], "%Y-%m-%d").date() >= last30
    ]
    essential_total = sum(t["amount"] for t in essential_tx)
    essential_per_day = essential_total / 30 if essential_total else None

    if essential_per_day is None or essential_per_day <= 0:
        return {
            "has_data": False,
            "message": "Chưa có chi tiêu thiết yếu nào trong 30 ngày qua.",
        }

    # Tính số ngày sinh tồn (an toàn khi balance âm)
    if balance <= 0:
        days = 0
        level = "danger"
    else:
        days = balance / essential_per_day
        if days < 30:
            level = "warning"
        elif days < 60:
            level = "watch"
        else:
            level = "safe"

    return {
        "has_data": True,
        "balance_available": balance,
        "essential_per_day": int(essential_per_day),
        "essential_total_30d": essential_total,
        "survival_days": int(days),
        "level": level,
    }


# ===================== E. SMART MICRO-SAVINGS / ROUND-UP =====================

def round_up_savings(tx_amount=None):
    """Tính khoản tiết kiệm lẻ theo nguyên tắc làm tròn.

    Có thể áp dụng cho:
    - Một giao dịch cụ thể (tx_amount).
    - Toàn bộ chi tiêu tháng hiện tại (tx_amount=None).
    """
    if tx_amount is None:
        # Tính cho toàn bộ tháng
        month_tx = _this_month_tx()
        total_saved = 0
        total_rounded_sum = 0
        items = []
        for t in month_tx:
            if t["type"] != "expense":
                continue
            rounded = _round_up_amount(t["amount"])
            saved = rounded - t["amount"]
            total_rounded_sum += rounded  # tính trên TẤT CẢ giao dịch
            if saved > 0:
                total_saved += saved
                items.append({
                    "description": t["description"],
                    "amount": t["amount"],
                    "rounded": rounded,
                    "saved": saved,
                })
        return {
            "scope": "month",
            "total_original": sum(t["amount"] for t in month_tx if t["type"] == "expense"),
            "total_rounded": total_rounded_sum,
            "total_saved": total_saved,
            "items_count": len(items),
            "items": items[:20],  # giới hạn hiển thị
        }
    else:
        rounded = _round_up_amount(tx_amount)
        return {
            "scope": "single",
            "amount": tx_amount,
            "rounded": rounded,
            "saved": rounded - tx_amount,
        }


def _round_up_amount(amount):
    """Làm tròn lên bội số 10.000đ.

    VD: 32.000 → 40.000 (làm tròn 10k)
        156.000 → 160.000
        1.500.000 → 1.500.000 (không đổi)
    """
    if amount <= 0:
        return 0
    # Bội số: 10.000đ cho giao dịch < 1tr; 50.000đ cho < 5tr; 100.000đ cho >= 5tr
    if amount < 100_000:
        step = 10_000
    elif amount < 1_000_000:
        step = 50_000
    else:
        step = 100_000
    if amount % step == 0:
        return amount
    return ((amount // step) + 1) * step


# ===================== F. AI DEAL & BILL OPTIMIZER =====================

def bill_optimizer():
    """Phân tích các khoản chi định kỳ (subscription/dịch vụ) để tối ưu.

    - Tổng hợp tổng chi phí định kỳ / tháng.
    - Phát hiện subscription ít sử dụng (nếu data cho phép).
    - Đề xuất giảm chi phí.
    - KHÔNG bịa giá/khuyến mãi thực tế.
    """
    bills = detect_recurring_bills(min_occurrences=2)

    if not bills:
        return {
            "has_data": False,
            "message": "Chưa phát hiện khoản chi định kỳ nào.",
        }

    monthly_total = sum(b["avg_amount"] for b in bills)
    yearly_total = monthly_total * 12

    # Phát hiện subscription ít dùng (chỉ dựa vào dữ liệu có sẵn)
    # Heuristic: số lần xuất hiện ít + chu kỳ dài → có thể không cần thiết
    low_usage = []
    for b in bills:
        if b["occurrences"] <= 2 and b["cycle_text"] not in ("tháng", "2 tuần"):
            low_usage.append(b)

    suggestions = []
    for b in bills:
        if b["category_id"] == "cat_fun":
            suggestions.append({
                "type": "review",
                "title": f"Xem xét {b['label']}",
                "detail": f"Chi {b['avg_amount']:,.0f} đ/{b['cycle_text']}. Nếu không dùng thường xuyên, có thể tạm hủy.",
            })
        if b["keyword"] in ("netflix", "spotify", "youtube premium"):
            suggestions.append({
                "type": "consolidate",
                "title": f"Gói {b['label']}",
                "detail": f"Chi {b['avg_amount']:,.0f} đ/{b['cycle_text']}. Cân nhắc gói family/năm nếu phù hợp.",
            })

    return {
        "has_data": True,
        "monthly_total": monthly_total,
        "yearly_total": yearly_total,
        "bills_count": len(bills),
        "bills": bills,
        "low_usage_count": len(low_usage),
        "low_usage": low_usage,
        "suggestions": suggestions,
    }


# ===================== TEST =====================

if __name__ == "__main__":
    print("=" * 60)
    print("TEST: forecast_spending()")
    print("=" * 60)
    f = forecast_spending()
    for k, v in f.items():
        print(f"  {k}: {v}")

    print("\n" + "=" * 60)
    print("TEST: detect_anomalies()")
    print("=" * 60)
    a = detect_anomalies()
    print(f"  Found {len(a)} anomalies")
    for x in a[:3]:
        print(f"    - {x['description']}: {x['amount']:,.0f}đ (median {x['median_amount']:,.0f}, z={x['z_score']})")

    print("\n" + "=" * 60)
    print("TEST: detect_recurring_bills()")
    print("=" * 60)
    b = detect_recurring_bills()
    for x in b:
        print(f"    - {x['label']}: {x['avg_amount']:,.0f}đ/{x['cycle_text']}, next: {x['next_date_str']}")

    print("\n" + "=" * 60)
    print("TEST: simulate_scenario()")
    print("=" * 60)
    for s in [
        {"scenario_type": "monthly_installment", "amount": 2000000, "months": 12},
        {"scenario_type": "income_change", "percent": -20},
        {"scenario_type": "lump_sum_expense", "amount": 5000000},
        {"scenario_type": "savings_target", "target": 5000000, "months": 3},
    ]:
        r = simulate_scenario(**s)
        print(f"  {s['scenario_type']}:")
        for k, v in r["after"].items():
            print(f"    {k}: {v}")

    print("\n" + "=" * 60)
    print("TEST: survival_days()")
    print("=" * 60)
    sd = survival_days()
    print(f"  {sd}")

    print("\n" + "=" * 60)
    print("TEST: round_up_savings()")
    print("=" * 60)
    rs = round_up_savings(32000)
    print(f"  Single: {rs}")
    rs_m = round_up_savings()
    print(f"  Month total: saved {rs_m['total_saved']:,.0f}đ from {rs_m['items_count']} tx")

    print("\n" + "=" * 60)
    print("TEST: bill_optimizer()")
    print("=" * 60)
    bo = bill_optimizer()
    if bo.get("has_data"):
        print(f"  Monthly total: {bo['monthly_total']:,.0f}đ, yearly: {bo['yearly_total']:,.0f}đ")
        print(f"  Suggestions: {len(bo['suggestions'])}")
    else:
        print(f"  {bo}")
