from flask import Flask, request, render_template, session, g
from init_db import init_db
import sqlite3
import requests

app = Flask(__name__)
app.secret_key = "your_secret_key"

DATABASE = "weather.db"
app.config["DATABASE"] = DATABASE

WEATHER_API_URL = "https://api.open-meteo.com/v1/forecast"
GEOCODING_API_URL = "https://geocoding-api.open-meteo.com/v1/search"


def get_db():
    if "db" not in g:
        g.db = sqlite3.connect(app.config["DATABASE"])
    return g.db


@app.teardown_appcontext
def close_db(error):
    if hasattr(g, "db"):
        g.db.close()


@app.route("/", methods=["GET", "POST"])
def index():
    weather = None
    error = None
    last_city = session.get("last_city")
    if request.method == "POST":
        city = request.form["city"]
        session["last_city"] = city
        weather, error = get_weather(city)
        if weather:
            save_search(city)
    elif last_city:
        weather, error = get_weather(last_city)
    searches = get_searches()
    return render_template(
        "index.html",
        weather=weather,
        error=error,
        searches=searches,
        last_city=session.get("last_city"),
    )


def get_coordinates(city):
    params = {"name": city}
    try:
        response = requests.get(GEOCODING_API_URL, params=params)
        response.raise_for_status()
        data = response.json()
        if "results" in data and len(data["results"]) > 0:
            return data["results"][0]["latitude"], data["results"][0]["longitude"]
        return None, None
    except requests.exceptions.RequestException as e:
        return None, None


def get_weather(city):
    lat, lon = get_coordinates(city)
    if lat is None or lon is None:
        return None, f"Could not find coordinates for {city}"

    params = {"latitude": lat, "longitude": lon, "current_weather": True}
    try:
        response = requests.get(WEATHER_API_URL, params=params)
        response.raise_for_status()
        data = response.json()
        return {
            "temperature": data["current_weather"]["temperature"],
            "windspeed": data["current_weather"]["windspeed"]
            * 3.6,  # Переводим из м/с в км/ч
        }, None
    except requests.exceptions.RequestException as e:
        return None, f"Request error: {e}, Response text: {response.text}"
    except ValueError as e:
        return None, f"JSON decode error: {e}, Response text: {response.text}"


def save_search(city):
    db = get_db()
    c = db.cursor()
    c.execute("SELECT id, search_count FROM searches WHERE city = ?", (city,))
    result = c.fetchone()
    if result:
        c.execute(
            "UPDATE searches SET search_count = search_count + 1 WHERE id = ?",
            (result[0],),
        )
    else:
        c.execute("INSERT INTO searches (city, search_count) VALUES (?, 1)", (city,))
    db.commit()


def get_searches():
    db = get_db()
    c = db.cursor()
    c.execute("SELECT city, search_count FROM searches ORDER BY search_count DESC")
    searches = c.fetchall()
    return searches


if __name__ == "__main__":
    init_db()
    app.run(debug=True)
