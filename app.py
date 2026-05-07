from flask import Flask, render_template, request, redirect, url_for, session, jsonify
import joblib
import numpy as np
import json

app = Flask(__name__)
app.secret_key = "creditriskproject"

# ---------------- LOAD DATA ----------------
model = joblib.load("model.pkl")

with open("data/users.json") as f:
    users = json.load(f)

with open("data/history.json") as f:
    history = json.load(f)


# ---------------- LOGIN ----------------
@app.route("/", methods=["GET", "POST"])
def login():

    if request.method == "POST":
        email = request.form.get("username")
        password = request.form.get("password")

        for user in users:
            if user["email"] == email and user["password"] == password:
                session["user"] = user["name"]
                return redirect(url_for("dashboard"))

    return render_template("login.html")


# ---------------- DASHBOARD ----------------
@app.route("/dashboard")
def dashboard():

    if "user" not in session:
        return redirect(url_for("login"))

    total = len(history)
    critical = 0
    medium = 0
    low = 0

    alerts = []

    for c in history:

        util = (c["balance"] / c["limit"]) * 100
        c["percent"] = round(util, 1)

        delay = c.get("delay", 0)
        days_left = 30 - delay

        if util >= 90:
            c["risk"] = "critical"
            critical += 1
        elif util >= 60:
            c["risk"] = "medium"
            medium += 1
        else:
            c["risk"] = "low"
            low += 1

        if util >= 80:
            alerts.append({
                "name": c["name"],
                "percent": c["percent"],
                "days_left": days_left,
                "risk": c["risk"]
            })

    return render_template("dashboard.html",
        customers=history,
        alerts=alerts,
        total_customers=total,
        critical=critical,
        medium=medium,
        low=low
    )


# ---------------- DASHBOARD REALTIME ----------------
@app.route("/dashboard_data")
def dashboard_data():

    total = len(history)
    critical = 0
    medium = 0
    low = 0

    for c in history:
        util = (c["balance"] / c["limit"]) * 100

        if util >= 90:
            critical += 1
        elif util >= 60:
            medium += 1
        else:
            low += 1

    return jsonify({
        "total": total,
        "critical": critical,
        "medium": medium,
        "low": low
    })


# ---------------- PREDICT PAGE ----------------
@app.route("/predict")
def predict_page():

    if "user" not in session:
        return redirect(url_for("login"))

    return render_template("predict.html")


# ---------------- PREDICT API ----------------
@app.route("/predict_api", methods=["POST"])
def predict_api():

    data = request.json

    limit = float(data["limit"])
    balance = float(data["balance"])
    monthly = float(data["monthly"])
    tx = int(data["txCount"])
    delay = int(data["delay"])

    features = np.array([[limit, balance, monthly, tx, delay]])
    result = model.predict(features)[0]

    probability = int(np.random.randint(60, 95))

    prediction = "high" if result == 1 else "low"

    return jsonify({
        "prediction": prediction,
        "probability": probability,
        "recommendation": "Monitor customer closely"
    })


# ---------------- SAVE CUSTOMER ----------------
@app.route("/save_customer", methods=["POST"])
def save_customer():

    data = request.json

    new_entry = {
        "id": data["id"],
        "name": data["name"],
        "sector": data.get("sector", "General"),
        "limit": float(data["limit"]),
        "balance": float(data["balance"]),
        "delay": int(data.get("delay", 0)),
        "payHist": data.get("payHist", "Good"),
        "prediction": data["prediction"],
        "probability": data["probability"]
    }

    history.append(new_entry)

    with open("data/history.json", "w") as f:
        json.dump(history, f, indent=4)

    return jsonify({"status": "saved"})


# ---------------- CUSTOMERS PAGE ----------------
@app.route("/customers")
def customers():

    if "user" not in session:
        return redirect(url_for("login"))

    return render_template("customers.html", customers=history)


# ---------------- REALTIME CUSTOMERS ----------------
@app.route("/customers_data")
def customers_data():

    data = []

    for c in history:

        util = (c["balance"] / c["limit"]) * 100
        days_left = 30 - c.get("delay", 0)

        if util >= 90:
            risk = "high"
        elif util >= 60:
            risk = "medium"
        else:
            risk = "low"

        data.append({
            "id": c.get("id"),
            "name": c.get("name"),
            "sector": c.get("sector", "General"),
            "limit": c.get("limit"),
            "balance": c.get("balance"),
            "utilization": round(util, 1),
            "daysLeft": days_left,
            "payHist": c.get("payHist", "Good"),
            "risk": risk
        })

    return jsonify(data)


# ---------------- ANALYSIS PAGE ----------------
@app.route("/analysis")
def analysis():

    if "user" not in session:
        return redirect(url_for("login"))

    return render_template("analysis.html")


# ---------------- ANALYSIS REALTIME ----------------
@app.route("/analysis_data")
def analysis_data():

    total = len(history)

    customers_data = []

    no_delay = 0
    d1_5 = 0
    d6_14 = 0
    d15 = 0

    sector_data = {}

    for c in history:

        util = (c["balance"] / c["limit"]) * 100

        customers_data.append({
            "name": c["name"],
            "util": round(util, 1)
        })

        # delay buckets
        delay = c.get("delay", 0)

        if delay == 0:
            no_delay += 1
        elif delay <= 5:
            d1_5 += 1
        elif delay <= 14:
            d6_14 += 1
        else:
            d15 += 1

        # sector
        sector = c.get("sector", "General")
        sector_data[sector] = sector_data.get(sector, 0) + 1

    # convert to %
    def percent(x):
        return round((x / total) * 100, 1) if total > 0 else 0

    # sector %
    sector_percent = {}
    for k, v in sector_data.items():
        sector_percent[k] = percent(v)

    return jsonify({
        "customers": customers_data,
        "delay": {
            "no": percent(no_delay),
            "d1_5": percent(d1_5),
            "d6_14": percent(d6_14),
            "d15": percent(d15)
        },
        "sector": sector_percent
    })


# ---------------- OTHER PAGES ----------------
@app.route("/alerts")
def alerts():
    return render_template("alerts.html", customers=history)

@app.route("/dataset")
def dataset():
    return render_template("dataset.html")

@app.route("/model")
def model_page():
    return render_template("model.html")

@app.route("/settings")
def settings():
    return render_template("settings.html")


# ---------------- ADD USER ----------------
@app.route("/add_user", methods=["POST"])
def add_user():
    global users
    
    data = request.json
    name = data.get("name", "").strip()
    role = data.get("role", "Analyst").strip()
    password = data.get("password", "").strip()
    
    if not name or not password:
        return jsonify({"success": False, "message": "Name and password required"})
    
    # Check if user already exists
    for user in users:
        if user["name"].lower() == name.lower():
            return jsonify({"success": False, "message": "User already exists"})
    
    # Create new user
    new_user = {
        "id": len(users) + 1,
        "name": name,
        "email": name.lower().replace(" ", ".") + "@bank.com",
        "password": password,
        "role": role
    }
    
    users.append(new_user)
    
    # Save to file
    with open("data/users.json", "w") as f:
        json.dump(users, f, indent=2)
    
    return jsonify({"success": True, "message": "User created successfully"})


# ---------------- LOGOUT ----------------
@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))


# -------- RUN --------
if __name__ == "__main__":
    app.run(debug=True)