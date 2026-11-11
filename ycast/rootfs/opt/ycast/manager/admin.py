#!/usr/bin/env python3

import argparse
import logging
import os
import tempfile

import requests
import yaml
from flask import Flask, jsonify, request, send_from_directory

RADIOBROWSER_API = "http://all.api.radio-browser.info"
SEARCH_LIMIT = 30
ALLOWED_HOSTS = {"172.30.32.2", "127.0.0.1"}

app = Flask(__name__)
app.json.sort_keys = False
app.config['MAX_CONTENT_LENGTH'] = 1_000_000
stations_file = "/data/stations.yml"


@app.before_request
def check_ingress():
    if request.remote_addr not in ALLOWED_HOSTS:
        logging.warning("Rejected request from non-ingress host %s", request.remote_addr)
        return jsonify({"error": "forbidden"}), 403


def load_stations():
    try:
        with open(stations_file, "r") as f:
            data = yaml.safe_load(f)
    except FileNotFoundError:
        return {}
    except yaml.YAMLError as err:
        logging.error("Station configuration format error: %s", err)
        return None
    if data is None:
        return {}
    if not isinstance(data, dict):
        return None
    return data


def save_stations(data):
    directory = os.path.dirname(stations_file) or "."
    fd, tmp_path = tempfile.mkstemp(dir=directory, suffix=".tmp")
    try:
        with os.fdopen(fd, "w") as f:
            yaml.safe_dump(data, f, default_flow_style=False, sort_keys=False,
                           allow_unicode=True)
        os.replace(tmp_path, stations_file)
    except BaseException:
        if os.path.exists(tmp_path):
            os.unlink(tmp_path)
        raise


def validate_stations(data):
    if not isinstance(data, dict):
        return "stations must be an object"
    for category, stations in data.items():
        if not isinstance(category, str) or not category.strip():
            return "invalid category name"
        if not isinstance(stations, dict):
            return "invalid station list for category '%s'" % category
        for name, url in stations.items():
            if not isinstance(name, str) or not name.strip():
                return "invalid station name in category '%s'" % category
            if not isinstance(url, str) or not url.strip():
                return "invalid stream URL for station '%s'" % name
    return None


@app.route("/")
def index():
    return send_from_directory(os.path.dirname(os.path.abspath(__file__)), "index.html")


@app.route("/api/stations")
def api_get_stations():
    data = load_stations()
    if data is None:
        return jsonify({"error": "stations.yml is not valid YAML"}), 500
    return jsonify(data)


@app.route("/api/stations", methods=["POST"])
def api_save_stations():
    data = request.get_json(silent=True)
    error = validate_stations(data)
    if error:
        return jsonify({"error": error}), 400
    save_stations(data)
    logging.info("Saved %d categories to %s", len(data), stations_file)
    return jsonify({"ok": True})


@app.route("/api/search")
def api_search():
    query = request.args.get("q", "").strip()
    if len(query) < 2:
        return jsonify({"error": "search query too short"}), 400
    url = RADIOBROWSER_API + "/json/stations/search"
    params = {
        "name": query,
        "hidebroken": "true",
        "limit": SEARCH_LIMIT,
        "order": "votes",
        "reverse": "true",
    }
    headers = {"User-Agent": "ycast-addon/1.1"}
    try:
        response = requests.get(url, params=params, headers=headers, timeout=15)
        response.raise_for_status()
        results_json = response.json()
    except (requests.RequestException, ValueError) as err:
        logging.error("Radiobrowser search failed: %s", err)
        return jsonify({"error": "radiobrowser search failed"}), 502
    if not isinstance(results_json, list):
        logging.error("Radiobrowser search returned unexpected data type: %s",
                      type(results_json).__name__)
        return jsonify({"error": "radiobrowser search failed"}), 502
    results = []
    for station in results_json:
        name = station.get("name")
        stream_url = station.get("url_resolved") or station.get("url")
        if not name or not stream_url:
            continue
        results.append({
            "name": name,
            "url": stream_url,
            "tags": station.get("tags") or "",
            "country": station.get("country") or "",
            "bitrate": station.get("bitrate") or 0,
            "favicon": station.get("favicon") or "",
        })
    return jsonify(results)


def main():
    parser = argparse.ArgumentParser(description="YCast station manager")
    parser.add_argument("--port", type=int, default=8099)
    parser.add_argument("--stations", default="/data/stations.yml")
    args = parser.parse_args()
    global stations_file
    stations_file = args.stations
    logging.basicConfig(format="%(asctime)s %(levelname)s: %(message)s",
                        level=logging.INFO)
    logging.info("YCast station manager starting (stations: %s)", stations_file)
    app.run(host="0.0.0.0", port=args.port)


if __name__ == "__main__":
    main()
