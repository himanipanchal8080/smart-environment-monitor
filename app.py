from flask import Flask, render_template, request, redirect, url_for
import requests
import os

app = Flask(__name__)

# ---------------- TEMP STORAGE ---------------- #
data_storage = []
record_id = 1

# ---------------- API ---------------- #
API_KEY = "31df7b8e7bc1c3fec4edad8efaeecba8"

def fetch_city_data(city):
    try:
        geo = requests.get(
            f"http://api.openweathermap.org/geo/1.0/direct?q={city}&limit=1&appid={API_KEY}"
        ).json()

        if not geo or len(geo) == 0:
            return None

        lat = geo[0].get("lat")
        lon = geo[0].get("lon")

        if lat is None or lon is None:
            return None

        weather = requests.get(
            f"https://api.openweathermap.org/data/2.5/weather?lat={lat}&lon={lon}&appid={API_KEY}&units=metric"
        ).json()

        air = requests.get(
            f"http://api.openweathermap.org/data/2.5/air_pollution?lat={lat}&lon={lon}&appid={API_KEY}"
        ).json()

        # SAFE CHECKS (IMPORTANT)
        if "main" not in weather:
            print("Weather API error:", weather)
            return None

        if "list" not in air or len(air["list"]) == 0:
            print("Air API error:", air)
            return None

        return {
            "temperature": weather["main"].get("temp", 0),
            "humidity": weather["main"].get("humidity", 0),
            "aqi": air["list"][0]["main"].get("aqi", 1) * 50
        }

    except Exception as e:
        print("ERROR:", e)
        return None


# ---------------- RISK ENGINE ---------------- #
def predict_risk(aqi, temp, humidity):

    risks = []

    # AQI Risk
    if aqi <= 100:
        risks.append({
            "parameter": "Air Quality (AQI)",
            "level": "🟢 Low Risk (0–100)",
            "justification": "Air quality satisfactory.",
            "solutions": ["Normal outdoor routine."]
        })
    elif aqi <= 200:
        risks.append({
            "parameter": "Air Quality (AQI)",
            "level": "🟠 Medium Risk (101–200)",
            "justification": "Unhealthy for sensitive groups.",
            "solutions": [
                "Avoid outdoor exercise",
                "Drink plenty of water",
                "Keep windows closed"
            ]
        })
    else:
        risks.append({
            "parameter": "Air Quality (AQI)",
            "level": "🔴 High Risk (201+)",
            "justification": "Health alert condition.",
            "solutions": [
                "Avoid going outside",
                "Wear mask",
                "Stay indoors"
            ]
        })

    # Temperature Risk
    if temp >= 39:
        risks.append({
            "parameter": "Temperature",
            "level": "🔴 Heatstroke Risk",
            "justification": "Very high temperature.",
            "solutions": [
                "Drink fluids",
                "Avoid sun",
                "Wear light clothes"
            ]
        })
    elif temp <= 5:
        risks.append({
            "parameter": "Temperature",
            "level": "🔵 Cold Risk",
            "justification": "Very low temperature.",
            "solutions": [
                "Wear warm clothes",
                "Avoid cold exposure"
            ]
        })

    # Humidity Risk
    if humidity < 30:
        risks.append({
            "parameter": "Humidity",
            "level": "🟡 Low Humidity",
            "justification": "Dry air.",
            "solutions": ["Use moisturizer", "Drink water"]
        })
    elif humidity > 60:
        risks.append({
            "parameter": "Humidity",
            "level": "🔴 High Humidity",
            "justification": "High humidity discomfort.",
            "solutions": ["Use ventilation"]
        })

    return risks


# ---------------- ROUTES ---------------- #

@app.route("/")
def index():
    return render_template("index.html", data=data_storage)


@app.route("/add", methods=["POST"])
def add():
    global record_id

    city = request.form.get("city")

    if not city:
        return "Please enter a city!"

    data = fetch_city_data(city)

    if not data:
        return "City not found or API error!"

    data_storage.append({
        "id": record_id,
        "area": city,
        "air_quality_index": data["aqi"],
        "temperature": data["temperature"],
        "humidity": data["humidity"],
        "created_at": "Now"
    })

    record_id += 1
    return redirect(url_for("index"))


@app.route("/delete/<int:id>")
def delete(id):
    global data_storage
    data_storage = [d for d in data_storage if d["id"] != id]
    return redirect(url_for("index"))


@app.route("/edit/<int:id>", methods=["GET", "POST"])
def edit(id):
    record = next((d for d in data_storage if d["id"] == id), None)

    if not record:
        return "Record not found!"

    if request.method == "POST":
        record["area"] = request.form.get("city")
        record["air_quality_index"] = int(request.form.get("aqi", 0))
        record["temperature"] = float(request.form.get("temp", 0))
        record["humidity"] = float(request.form.get("humidity", 0))
        return redirect(url_for("index"))

    return render_template("edit.html", record=record)


@app.route("/dashboard")
def dashboard():
    data = data_storage

    total_records = len(data)

    if total_records > 0:
        avg_aqi = round(sum(d["air_quality_index"] for d in data) / total_records, 2)
        avg_temp = round(sum(d["temperature"] for d in data) / total_records, 2)
        avg_humidity = round(sum(d["humidity"] for d in data) / total_records, 2)
    else:
        avg_aqi = avg_temp = avg_humidity = 0

    return render_template(
        "dashboard.html",
        data=data,
        avg_aqi=avg_aqi,
        avg_temp=avg_temp,
        avg_humidity=avg_humidity,
        total_records=total_records
    )


@app.route("/prediction")
def prediction():
    all_data = []

    for r in data_storage:
        all_data.append({
            "city": r["area"],
            "aqi": r["air_quality_index"],
            "temp": r["temperature"],
            "humidity": r["humidity"],
            "risks": predict_risk(
                r["air_quality_index"],
                r["temperature"],
                r["humidity"]
            )
        })

    return render_template("prediction.html", all_data=all_data)


# ---------------- RUN ---------------- #

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)