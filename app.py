from flask import Flask, render_template, request
import requests
import datetime

app = Flask(__name__)

# Map beach names to NOAA tide station IDs and custom low tide thresholds
BEACHES = {
    "Fitzgerald Marine Reserve, CA": {"station_id": "9414131", "low_tide_threshold": 0.0},
    "Pillar Point, CA": {"station_id": "9414131", "low_tide_threshold": -0.1},
    "Fort Ross, CA": {"station_id": "9416024", "low_tide_threshold": -0.3}
}

def get_tide_data(date, station_id, low_tide_threshold):
    base_url = "https://api.tidesandcurrents.noaa.gov/api/prod/datagetter"

    params = {
        "product": "predictions",
        "datum": "MLLW",
        "station": station_id,
        "time_zone": "lst_ldt",
        "units": "english",
        "format": "json",
        "interval": "hilo",
        "begin_date": date,
        "end_date": date
    }

    response = requests.get(base_url, params=params)
    data = response.json()

    if "predictions" not in data:
        return [], False

    tides = []
    meets_criteria = False

    for tide in data["predictions"]:
        tide_time = datetime.datetime.strptime(tide["t"], "%Y-%m-%d %H:%M")
        tide_type = "Low" if tide["type"] == "L" else "High"
        tide_height = float(tide["v"])

        if tide_type == "Low" and tide_height <= low_tide_threshold:
            meets_criteria = True

        tides.append({"type": tide_type, "time": tide_time.strftime("%I:%M %p"), "height": tide_height})

    return tides, meets_criteria

@app.route("/", methods=["GET", "POST"])
def home():
    selected_date = datetime.datetime.today().strftime("%Y%m%d")
    display_date = datetime.datetime.today().strftime("%Y-%m-%d")
    selected_beach = "Fitzgerald Marine Reserve, CA"
    beach_data = BEACHES[selected_beach]
    tides, meets_criteria = get_tide_data(selected_date, beach_data["station_id"], beach_data["low_tide_threshold"])

    if request.method == "POST":
        user_date = request.form.get("date")
        user_beach = request.form.get("beach")

        if user_date:
            selected_date = user_date.replace("-", "")
            display_date = user_date

        if user_beach and user_beach in BEACHES:
            selected_beach = user_beach
            beach_data = BEACHES[selected_beach]

        tides, meets_criteria = get_tide_data(selected_date, beach_data["station_id"], beach_data["low_tide_threshold"])

    return render_template("index.html", tides=tides, meets_criteria=meets_criteria,
                           display_date=display_date, selected_beach=selected_beach,
                           beaches=BEACHES.keys())

if __name__ == "__main__":
    app.run(debug=True)
