# ui/app.py
# -----------------------------------------------
# Flask web server for eBay Ali Hunter UI.
# Handles:
#   - Serving the main page
#   - Reading/saving keywords
#   - Starting the scraper pipeline
#   - Streaming live logs to browser
#   - Serving results for preview
# -----------------------------------------------

import asyncio
import json
import os
import sys
import threading
from flask import Flask, jsonify, render_template, request, Response

# Make sure project root is in path so imports work
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from config import KEYWORDS_FILE, OUTPUT_DIR
from scrapers.browser import BrowserManager
from pipeline.runner import run_pipeline
from output.deduplicator import deduplicate
from output.exporter import export_results

app = Flask(__name__)

# --- Global state ---
scraper_running  = False
scraper_logs     = []
scraper_results  = []
latest_excel     = None
selected_market  = "US"


# -----------------------------------------------
# ROUTES
# -----------------------------------------------

@app.route("/")
def index():
    return render_template("index.html")


@app.route("/api/keywords", methods=["GET"])
def get_keywords():
    """Return current keywords as JSON list."""
    keywords = _load_keywords()
    return jsonify({"keywords": keywords})


@app.route("/api/keywords", methods=["POST"])
def save_keywords():
    """Save updated keywords list to file."""
    data = request.get_json()
    keywords = data.get("keywords", [])
    _save_keywords(keywords)
    return jsonify({"status": "saved", "count": len(keywords)})


@app.route("/api/start", methods=["POST"])
def start_scraper():
    """Start the scraper in a background thread."""
    global scraper_running, scraper_logs, scraper_results, latest_excel, selected_market

    if scraper_running:
        return jsonify({"status": "already_running"})

    # Get market from request
    data           = request.get_json() or {}
    selected_market = data.get("market", "US")

    scraper_running = True
    scraper_logs    = []
    scraper_results = []
    latest_excel    = None

    thread = threading.Thread(target=_run_scraper_thread, daemon=True)
    thread.start()

    return jsonify({"status": "started", "market": selected_market})


@app.route("/api/stop", methods=["POST"])
def stop_scraper():
    """Signal the scraper to stop."""
    global scraper_running
    scraper_running = False
    scraper_logs.append("⚠️ Stop requested by user...")
    return jsonify({"status": "stopping"})


@app.route("/api/logs")
def stream_logs():
    """Stream logs to browser using Server-Sent Events."""
    def generate():
        sent = 0
        import time
        while True:
            if sent < len(scraper_logs):
                for line in scraper_logs[sent:]:
                    yield f"data: {json.dumps(line)}\n\n"
                sent = len(scraper_logs)
            if not scraper_running and sent >= len(scraper_logs):
                yield f"data: {json.dumps('__DONE__')}\n\n"
                break
            time.sleep(0.3)

    return Response(generate(), mimetype="text/event-stream")


@app.route("/api/results")
def get_results():
    """Return scraped results as JSON for table preview."""
    return jsonify({
        "results" : scraper_results,
        "excel"   : latest_excel,
        "count"   : len(scraper_results),
    })

@app.route("/api/open_excel")
def open_excel():
    import subprocess
    path = request.args.get("path", "")
    if path and os.path.exists(path):
        os.startfile(os.path.abspath(path))
    return jsonify({"status": "ok"})

@app.route("/api/status")
def get_status():
    """Return current scraper status."""
    return jsonify({"running": scraper_running})


# -----------------------------------------------
# HELPERS
# -----------------------------------------------

def _run_scraper_thread():
    """Runs the async pipeline inside a thread."""
    global scraper_running, scraper_results, latest_excel

    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

    try:
        loop.run_until_complete(_run_pipeline_async())
    except Exception as e:
        scraper_logs.append(f"❌ Fatal error: {e}")
    finally:
        scraper_running = False
        loop.close()


async def _run_pipeline_async():
    """Actual async pipeline — same as main.py but logs to UI."""
    global scraper_results, latest_excel, selected_market

    keywords = _load_keywords()
    if not keywords:
        scraper_logs.append("❌ No keywords found. Please add keywords first.")
        return

    scraper_logs.append(f"✅ Loaded {len(keywords)} keywords")
    scraper_logs.append("🚀 Starting browser...")

    browser = BrowserManager()
    await browser.start()
    scraper_logs.append("✅ Browser launched")

    try:
        results, ebay_top = await run_pipeline(browser, keywords, log_callback=scraper_logs.append, market=selected_market)
        results = deduplicate(results)

        scraper_logs.append(f"✅ Found {len(results)} profitable products")
        scraper_logs.append(f"✅ Collected {len(ebay_top)} eBay top sellers")

        path = export_results(results, ebay_top)
        if path:
            scraper_logs.append(f"✅ Excel saved: {path}")
            latest_excel = path

        scraper_results = results

    except Exception as e:
        scraper_logs.append(f"❌ Error: {e}")
    finally:
        await browser.close()
        scraper_logs.append("✅ Browser closed")
        scraper_logs.append("🏁 Pipeline finished!")


def _load_keywords() -> list[str]:
    try:
        with open(KEYWORDS_FILE, "r", encoding="utf-8") as f:
            return [
                line.strip() for line in f
                if line.strip() and not line.startswith("#")
            ]
    except FileNotFoundError:
        return []


def _save_keywords(keywords: list[str]):
    with open(KEYWORDS_FILE, "w", encoding="utf-8") as f:
        for kw in keywords:
            f.write(kw.strip() + "\n")


# -----------------------------------------------
# RUN
# -----------------------------------------------

if __name__ == "__main__":
    import webbrowser
    webbrowser.open("http://localhost:5000")
    import logging
    log = logging.getLogger('werkzeug')
    log.setLevel(logging.ERROR)
    app.run(debug=False, threaded=True, port=5000)