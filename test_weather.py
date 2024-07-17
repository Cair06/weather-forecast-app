import pytest
import os
from weather import app, save_search, get_searches
from init_db import init_db


@pytest.fixture
def client():
    test_db = "test_weather.db"
    app.config["DATABASE"] = test_db
    app.config["TESTING"] = True

    with app.test_client() as client:
        with app.app_context():
            init_db(app.config["DATABASE"])
        yield client

    os.remove(test_db)


def test_index_page(client):
    rv = client.get("/")
    assert b"Weather Forecast" in rv.data


def test_weather_search(client):
    rv = client.post("/", data={"city": "Moscow"})
    assert b"Temperature" in rv.data
    assert b"Wind Speed" in rv.data


def test_search_history(client):
    with app.app_context():
        save_search("Moscow")
        save_search("Moscow")
        save_search("London")
        searches = get_searches()
        assert searches[0][0] == "Moscow"
        assert searches[0][1] == 2
        assert searches[1][0] == "London"
        assert searches[1][1] == 1
