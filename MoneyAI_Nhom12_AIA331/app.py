"""
Flask Backend - Hệ thống quản lý chi tiêu cá nhân tích hợp AI
Nhóm 12 - ĐH CNTT&TT Thái Nguyên - AIA331
"""
from datetime import datetime
from collections import defaultdict
from flask import (Flask, render_template, request, jsonify,
                   session, redirect, url_for, flash)

from data import (
    DEFAULT_CATEGORIES, CATEGORIES_BY_ID,
    SAMPLE_TRANSACTIONS, SAMPLE_BUDGETS, SAMPLE_GOALS,
    DEMO_USER, ai_auto_categorize,
)
from chatbot import chat as chatbot_reply

app = Flask(__name__)
app.secret_key = "nhom12-aia331-secret-key-demo"


# ===================== AUTH =====================

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        u = request.form.get("username", "").strip()
        p = request.form.get("password", "")
        if u == DEMO_USER["username"] and p == DEMO_USER["password"]:
            session["user"] = DEMO_USER
            return redirect(url_for("dashboard"))
        flash("Tài khoản hoặc mật khẩu không đúng!", "error")
        return render_template("login.html")
    if session.get("user"):
        return redirect(url_for("dashboard"))
    return render_template("login.html")


@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))


def _login_required():
    return bool(session.get("user"))


# ===================== PAGES =====================

@app.route("/")
def index():
    if not _login_required():
        return redirect(url_for("login"))
    return redirect(url_for("dashboard"))


@app.route("/dashboard")
def dashboard():
    if not _login_required():
        return redirect(url_for("login"))
    return render_template("dashboard.html",
                           user=session["user"],
                           categories=DEFAULT_CATEGORIES)


@app.route("/transactions")
def transactions_page():
    if not _login_required():
        return redirect(url_for("login"))
    return render_template("transactions.html",
                           user=session["user"],
                           categories=DEFAULT_CATEGORIES)


@app.route("/budgets")
def budgets_page():
    if not _login_required():
        return redirect(url_for("login"))
    return render_template("budgets.html",
                           user=session["user"],
                           categories=DEFAULT_CATEGORIES)


@app.route("/goals")
def goals_page():
    if not _login_required():
        return redirect(url_for("login"))
    return render_template("goals.html",
                           user=session["user"])


@app.route("/reports")
def reports_page():
    if not _login_required():
        return redirect(url_for("login"))
    return render_template("reports.html",
                           user=session["user"],
                           categories=DEFAULT_CATEGORIES)


@app.route("/chat")
def chat_page():
    if not _login_required():
        return redirect(url_for("login"))
    return render_template("chat.html",
                           user=session["user"])


# ===================== API: TRANSACTIONS =====================

@app.route("/api/transactions", methods=["GET"])
def api_list_tx():
    if not _login_required():
        return jsonify({"error": "unauthorized"}), 401
    month = request.args.get("month")  # YYYY-MM
    items = SAMPLE_TRANSACTIONS
    if month:
        items = [t for t in items if t["date"].startswith(month)]
    items = sorted(items, key=lambda t: t["date"], reverse=True)
    return jsonify({"transactions": items, "total": len(items)})


@app.route("/api/transactions", methods=["POST"])
def api_create_tx():
    if not _login_required():
        return jsonify({"error": "unauthorized"}), 401
    data = request.get_json() or {}
    desc = data.get("description", "").strip()
    amount = int(data.get("amount", 0))
    t_type = data.get("type", "expense")
    cat_id = data.get("category_id") or ai_auto_categorize(desc)
    date = data.get("date") or datetime.now().strftime("%Y-%m-%d")
    wallet = data.get("wallet", "Tiền mặt")

    new_id = f"tx_{len(SAMPLE_TRANSACTIONS)+1:03d}"
    new_tx = {
        "id": new_id, "description": desc, "amount": amount,
        "type": t_type, "category_id": cat_id, "date": date, "wallet": wallet,
    }
    SAMPLE_TRANSACTIONS.append(new_tx)
    return jsonify({"ok": True, "transaction": new_tx,
                    "auto_category": CATEGORIES_BY_ID.get(cat_id, {}).get("name")})


@app.route("/api/transactions/<tx_id>", methods=["DELETE"])
def api_delete_tx(tx_id):
    if not _login_required():
        return jsonify({"error": "unauthorized"}), 401
    for i, t in enumerate(SAMPLE_TRANSACTIONS):
        if t["id"] == tx_id:
            SAMPLE_TRANSACTIONS.pop(i)
            return jsonify({"ok": True})
    return jsonify({"error": "not found"}), 404


@app.route("/api/categorize", methods=["POST"])
def api_categorize():
    """AI auto-categorize demo."""
    if not _login_required():
        return jsonify({"error": "unauthorized"}), 401
    text = (request.get_json() or {}).get("text", "")
    cat_id = ai_auto_categorize(text)
    cat = CATEGORIES_BY_ID.get(cat_id, {})
    return jsonify({
        "category_id": cat_id,
        "category_name": cat.get("name"),
        "icon": cat.get("icon"),
        "color": cat.get("color"),
    })


# ===================== API: BUDGETS =====================

@app.route("/api/budgets", methods=["GET"])
def api_list_budgets():
    if not _login_required():
        return jsonify({"error": "unauthorized"}), 401
    month = datetime.now().strftime("%Y-%m")
    spent_by_cat = defaultdict(int)
    for t in SAMPLE_TRANSACTIONS:
        if t["date"].startswith(month) and t["type"] == "expense":
            spent_by_cat[t["category_id"]] += t["amount"]

    result = []
    for b in SAMPLE_BUDGETS:
        spent = spent_by_cat.get(b["category_id"], 0)
        pct = round(spent / b["limit"] * 100, 1) if b["limit"] else 0
        cat = CATEGORIES_BY_ID.get(b["category_id"], {})
        result.append({
            **b,
            "category_name": cat.get("name"),
            "icon": cat.get("icon"),
            "color": cat.get("color"),
            "spent": spent,
            "percent": pct,
            "status": "over" if pct >= 100 else "warning" if pct >= 70 else "ok",
        })
    return jsonify({"budgets": result})


@app.route("/api/budgets", methods=["POST"])
def api_create_budget():
    if not _login_required():
        return jsonify({"error": "unauthorized"}), 401
    data = request.get_json() or {}
    new_id = f"bud_{len(SAMPLE_BUDGETS)+1:03d}"
    b = {
        "id": new_id,
        "category_id": data["category_id"],
        "limit": int(data["limit"]),
        "period": data.get("period", "monthly"),
    }
    SAMPLE_BUDGETS.append(b)
    return jsonify({"ok": True, "budget": b})


@app.route("/api/budgets/<bud_id>", methods=["DELETE"])
def api_delete_budget(bud_id):
    if not _login_required():
        return jsonify({"error": "unauthorized"}), 401
    for i, b in enumerate(SAMPLE_BUDGETS):
        if b["id"] == bud_id:
            SAMPLE_BUDGETS.pop(i)
            return jsonify({"ok": True})
    return jsonify({"error": "not found"}), 404


# ===================== API: GOALS =====================

@app.route("/api/goals", methods=["GET"])
def api_list_goals():
    if not _login_required():
        return jsonify({"error": "unauthorized"}), 401
    out = []
    for g in SAMPLE_GOALS:
        pct = round(g["saved"] / g["target"] * 100, 1) if g["target"] else 0
        out.append({**g, "percent": pct,
                    "remaining": g["target"] - g["saved"]})
    return jsonify({"goals": out})


@app.route("/api/goals", methods=["POST"])
def api_create_goal():
    if not _login_required():
        return jsonify({"error": "unauthorized"}), 401
    data = request.get_json() or {}
    new_id = f"goal_{len(SAMPLE_GOALS)+1:03d}"
    g = {
        "id": new_id,
        "name": data["name"],
        "target": int(data["target"]),
        "saved": int(data.get("saved", 0)),
    }
    SAMPLE_GOALS.append(g)
    return jsonify({"ok": True, "goal": g})


@app.route("/api/goals/<goal_id>/deposit", methods=["POST"])
def api_deposit_goal(goal_id):
    if not _login_required():
        return jsonify({"error": "unauthorized"}), 401
    amount = int((request.get_json() or {}).get("amount", 0))
    for g in SAMPLE_GOALS:
        if g["id"] == goal_id:
            g["saved"] += amount
            pct = round(g["saved"] / g["target"] * 100, 1) if g["target"] else 0
            return jsonify({"ok": True, "goal": g, "percent": pct})
    return jsonify({"error": "not found"}), 404


# ===================== API: STATS (cho Dashboard) =====================

@app.route("/api/stats/summary")
def api_stats_summary():
    if not _login_required():
        return jsonify({"error": "unauthorized"}), 401
    month = datetime.now().strftime("%Y-%m")
    tx = [t for t in SAMPLE_TRANSACTIONS if t["date"].startswith(month)]
    income = sum(t["amount"] for t in tx if t["type"] == "income")
    expense = sum(t["amount"] for t in tx if t["type"] == "expense")
    return jsonify({
        "month": month,
        "income": income,
        "expense": expense,
        "balance": income - expense,
        "savings_rate": round((income - expense) / income * 100, 1) if income else 0,
        "tx_count": len(tx),
        "active_budgets": len(SAMPLE_BUDGETS),
        "active_goals": len(SAMPLE_GOALS),
    })


@app.route("/api/stats/charts")
def api_stats_charts():
    if not _login_required():
        return jsonify({"error": "unauthorized"}), 401
    month = datetime.now().strftime("%Y-%m")
    tx = [t for t in SAMPLE_TRANSACTIONS if t["date"].startswith(month)]

    # Pie: cơ cấu chi tiêu theo danh mục
    by_cat = defaultdict(int)
    for t in tx:
        if t["type"] == "expense":
            by_cat[t["category_id"]] += t["amount"]
    pie = []
    for cid, amt in sorted(by_cat.items(), key=lambda x: -x[1]):
        cat = CATEGORIES_BY_ID.get(cid, {})
        pie.append({
            "label": cat.get("name", cid),
            "value": amt,
            "color": cat.get("color", "#94a3b8"),
        })

    # Line: xu hướng chi 7 ngày gần nhất
    today = datetime.now().date()
    line = []
    for d in range(6, -1, -1):
        day = (today - __import__("datetime").timedelta(days=d)).strftime("%Y-%m-%d")
        day_exp = sum(t["amount"] for t in tx if t["date"] == day and t["type"] == "expense")
        line.append({"date": day[5:], "value": day_exp})

    # Bar: thu vs chi 6 tháng gần nhất
    bar = []
    now = datetime.now()
    for m in range(5, -1, -1):
        ym = (now.replace(day=1) - __import__("datetime").timedelta(days=30*m)).strftime("%Y-%m")
        mtx = [t for t in SAMPLE_TRANSACTIONS if t["date"].startswith(ym)]
        inc = sum(t["amount"] for t in mtx if t["type"] == "income")
        exp = sum(t["amount"] for t in mtx if t["type"] == "expense")
        bar.append({"month": ym[5:], "income": inc, "expense": exp})

    return jsonify({"pie": pie, "line": line, "bar": bar})


# ===================== API: AI CHATBOT =====================

@app.route("/api/chat", methods=["POST"])
def api_chat():
    if not _login_required():
        return jsonify({"error": "unauthorized"}), 401
    data = request.get_json() or {}
    message = data.get("message", "").strip()
    if not message:
        return jsonify({"error": "empty message"}), 400
    result = chatbot_reply(message)
    return jsonify(result)


@app.route("/api/chat/suggestions")
def api_chat_suggestions():
    if not _login_required():
        return jsonify({"error": "unauthorized"}), 401
    return jsonify({
        "suggestions": [
            "📊 Phân tích chi tiêu tháng này",
            "💰 Tháng này chi nhiều nhất vào đâu?",
            "💸 Làm sao tiết kiệm 2 triệu?",
            "📋 Tình hình ngân sách hiện tại",
            "🔮 Dự báo chi tiêu cuối tháng",
            "🎯 Tiến độ mục tiêu tiết kiệm",
            "📑 Tạo báo cáo tài chính tháng này",
            "💡 Gợi ý ngân sách tháng tới",
        ]
    })


# ===================== ERROR HANDLERS =====================

@app.errorhandler(404)
def not_found(_e):
    return render_template("login.html"), 404


if __name__ == "__main__":
    print("=" * 60)
    print("🚀 Hệ thống Quản lý Chi tiêu Cá nhân tích hợp AI")
    print("=" * 60)
    print(f"📂 Mở trình duyệt: http://localhost:5000")
    print(f"🔐 Tài khoản demo:  user = demo,  pass = 123456")
    print("=" * 60)
    app.run(host="0.0.0.0", port=5000, debug=True)
