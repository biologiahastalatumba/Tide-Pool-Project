from flask import Flask, render_template, request
import requests
import datetime

app = Flask(__name__)

# Map beach names to NOAA tide station IDs and custom low tide thresholds
BEACHES = {
    "Fitzgerald Marine Reserve, CA": {"station_id": "9414131", "low_tide_threshold": -0.1},
    "Pillar Point, CA": {"station_id": "9414131", "low_tide_threshold": -0.0},
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


def find_next_best_tide(start_date, station_id, low_tide_threshold, max_days=21):
    for day_offset in range(1, max_days + 1):
        next_date = (datetime.datetime.strptime(start_date, "%Y%m%d") + datetime.timedelta(days=day_offset)).strftime(
            "%Y%m%d")
        tides, meets_criteria = get_tide_data(next_date, station_id, low_tide_threshold)

        if meets_criteria:
            return next_date, tides  # Found a good tide, return it immediately

    return None, None  # No good tide found in 21 days


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

    # Find the next best tide within 21 days
    next_best_date, next_best_tides = find_next_best_tide(selected_date, beach_data["station_id"],
                                                          beach_data["low_tide_threshold"], max_days=21)

    return render_template("index.html", tides=tides, meets_criteria=meets_criteria,
                           display_date=display_date, selected_beach=selected_beach,
                           beaches=BEACHES.keys(), next_best_date=next_best_date,
                           next_best_tides=next_best_tides)


if __name__ == "__main__":
    app.run(debug=True)

