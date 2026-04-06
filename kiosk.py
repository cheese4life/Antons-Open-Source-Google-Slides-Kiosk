#!/usr/bin/env python3
"""
Kiosk Display Driver
Launches Chromium in kiosk mode to display a URL (Google Slides, clock, etc).
Auto-refreshes every night at midnight.
Exposes a small HTTP API on port 8081 for the control panel.
"""

import subprocess
import signal
import sys
import time
import threading
import json
import urllib.request
from datetime import datetime, timedelta
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs

# ── Configuration ────────────────────────────────────────────────────────────
DEFAULT_URL = (
    "https://docs.google.com/presentation/d/e/"
    "2PACX-1vSo3wAX6ugrGWbUBr06BL4EviQUwZlNWVx2oYSMXb12sH3QcGxPp4XCWhfQFrYpFebP_q-s0mZdU3xT"
    "/pub?start=true&loop=true&delayms=5000"
)

CLOCK_URL = "http://localhost:8081/clock"
API_PORT = 8081

REFRESH_HOUR = 0
REFRESH_MINUTE = 0

CHROMIUM_CMD = "chromium-browser"
CHROMIUM_FLAGS = [
    "--kiosk",
    "--noerrdialogs",
    "--disable-infobars",
    "--disable-session-crashed-bubble",
    "--disable-translate",
    "--disable-features=TranslateUI",
    "--disable-component-update",
    "--disable-background-networking",
    "--disable-sync",
    "--disable-default-apps",
    "--disable-extensions",
    "--disable-hang-monitor",
    "--disable-prompt-on-repost",
    "--no-first-run",
    "--no-default-browser-check",
    "--autoplay-policy=no-user-gesture-required",
    "--start-fullscreen",
    "--incognito",
]
# ─────────────────────────────────────────────────────────────────────────────

# ── State ────────────────────────────────────────────────────────────────────
current_url = DEFAULT_URL
showing_clock = False
browser_proc = None
shutdown_event = threading.Event()
lock = threading.Lock()


def log(msg):
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"[kiosk {ts}] {msg}", flush=True)


def is_alive():
    with lock:
        return browser_proc is not None and browser_proc.poll() is None


def wait_for_network(timeout=120):
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        try:
            urllib.request.urlopen("https://docs.google.com", timeout=5)
            log("Network is up.")
            return True
        except Exception:
            log("Waiting for network...")
            time.sleep(3)
    log("Network timeout — launching browser anyway.")
    return False


def launch_browser(url=None):
    global browser_proc
    if url is None:
        url = CLOCK_URL if showing_clock else current_url
    with lock:
        cmd = [CHROMIUM_CMD] + CHROMIUM_FLAGS + [url]
        log(f"Launching browser → {url[:80]}...")
        browser_proc = subprocess.Popen(
            cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
        )
        log(f"Browser PID: {browser_proc.pid}")


def kill_browser():
    global browser_proc
    with lock:
        if browser_proc and browser_proc.poll() is None:
            log("Stopping browser...")
            browser_proc.terminate()
            try:
                browser_proc.wait(timeout=5)
            except subprocess.TimeoutExpired:
                browser_proc.kill()
                browser_proc.wait()
        browser_proc = None


def restart_browser(url=None):
    kill_browser()
    time.sleep(1)
    launch_browser(url)


def seconds_until(hour, minute):
    now = datetime.now()
    target = now.replace(hour=hour, minute=minute, second=0, microsecond=0)
    if target <= now:
        target += timedelta(days=1)
    return (target - now).total_seconds()


def midnight_refresh_loop():
    while not shutdown_event.is_set():
        wait_secs = seconds_until(REFRESH_HOUR, REFRESH_MINUTE)
        log(f"Next refresh in {wait_secs/3600:.1f} hours.")
        shutdown_event.wait(timeout=wait_secs)
        if shutdown_event.is_set():
            break
        log("Midnight refresh.")
        restart_browser()


# ── Clock HTML page ────── Section Generated using Claude Code ─────
CLOCK_HTML = r"""<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<title>Clock</title>
<style>
*{margin:0;padding:0;box-sizing:border-box}
body{background:#000;color:#fff;font-family:'Segoe UI',Arial,sans-serif;
     display:flex;flex-direction:column;align-items:center;justify-content:center;
     height:100vh;overflow:hidden}
#time{font-size:12vw;font-weight:200;letter-spacing:0.05em}
#date{font-size:3vw;font-weight:300;margin-top:1vh;opacity:0.7}
#weather{font-size:2.5vw;font-weight:300;margin-top:3vh;opacity:0.6}
</style>
</head>
<body>
<div id="time">--:--:--</div>
<div id="date">---</div>
<div id="weather">Loading weather...</div>
<script>
function tick(){
  var d=new Date();
  var h=d.getHours(),m=d.getMinutes(),s=d.getSeconds();
  var ampm=h>=12?'PM':'AM';
  h=h%12||12;
  document.getElementById('time').textContent=
    h+':'+(m<10?'0':'')+m+':'+(s<10?'0':'')+s+' '+ampm;
  var opts={weekday:'long',year:'numeric',month:'long',day:'numeric'};
  document.getElementById('date').textContent=d.toLocaleDateString('en-US',opts);
}
tick();setInterval(tick,1000);

function fetchWeather(){
  // Get location first, then weather from Open-Meteo (free, no key)
  fetch('https://ipapi.co/json/')
    .then(function(r){return r.json()})
    .then(function(loc){
      var lat=loc.latitude,lon=loc.longitude,city=loc.city||'';
      return fetch('https://api.open-meteo.com/v1/forecast?latitude='+lat+
        '&longitude='+lon+'&current_weather=true&temperature_unit=fahrenheit')
        .then(function(r){return r.json()})
        .then(function(w){
          var cw=w.current_weather;
          var desc=weatherCode(cw.weathercode);
          document.getElementById('weather').textContent=
            city+'  ·  '+Math.round(cw.temperature)+'°F  ·  '+desc;
        });
    })
    .catch(function(){
      document.getElementById('weather').textContent='Weather unavailable';
    });
}
function weatherCode(c){
  var m={0:'Clear',1:'Mostly Clear',2:'Partly Cloudy',3:'Overcast',
    45:'Foggy',48:'Fog',51:'Light Drizzle',53:'Drizzle',55:'Heavy Drizzle',
    61:'Light Rain',63:'Rain',65:'Heavy Rain',71:'Light Snow',73:'Snow',
    75:'Heavy Snow',80:'Light Showers',81:'Showers',82:'Heavy Showers',
    95:'Thunderstorm',96:'Thunderstorm w/ Hail',99:'Severe Thunderstorm'};
  return m[c]||'';
}
fetchWeather();setInterval(fetchWeather,600000);
</script>
</body>
</html>"""


# ── Internal API server (port 8081) ─────────────────────────────────────────
class KioskAPIHandler(BaseHTTPRequestHandler):
    def log_message(self, fmt, *args):
        log(f"API: {fmt % args}")

    def _respond(self, code, data):
        body = json.dumps(data).encode()
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _respond_html(self, html):
        body = html.encode()
        self.send_response(200)
        self.send_header("Content-Type", "text/html")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        path = urlparse(self.path).path

        if path == "/status":
            self._respond(200, {
                "alive": is_alive(),
                "url": current_url,
                "showing_clock": showing_clock,
            })

        elif path == "/clock":
            self._respond_html(CLOCK_HTML)

        else:
            self._respond(404, {"error": "not found"})

    def do_POST(self):
        global current_url, showing_clock
        path = urlparse(self.path).path

        if path == "/refresh":
            log("API: force refresh requested.")
            restart_browser()
            self._respond(200, {"ok": True, "action": "refresh"})

        elif path == "/set-url":
            length = int(self.headers.get("Content-Length", 0))
            body = self.rfile.read(length).decode()
            try:
                data = json.loads(body)
                new_url = data.get("url", "").strip()
            except (json.JSONDecodeError, AttributeError):
                self._respond(400, {"error": "invalid json"})
                return
            if not new_url or not new_url.startswith(("http://", "https://")):
                self._respond(400, {"error": "invalid url"})
                return
            current_url = new_url
            showing_clock = False
            log(f"API: URL set to {current_url[:80]}")
            restart_browser()
            self._respond(200, {"ok": True, "action": "set-url", "url": current_url})

        elif path == "/toggle-clock":
            showing_clock = not showing_clock
            log(f"API: clock {'ON' if showing_clock else 'OFF'}")
            restart_browser()
            self._respond(200, {"ok": True, "showing_clock": showing_clock})

        else:
            self._respond(404, {"error": "not found"})


def api_server_loop():
    server = HTTPServer(("0.0.0.0", API_PORT), KioskAPIHandler)
    log(f"API server listening on port {API_PORT}")
    server.serve_forever()


# ── Signal handling ──────────────────────────────────────────────────────────
def signal_handler(signum, frame):
    log(f"Received signal {signum}, shutting down.")
    shutdown_event.set()
    kill_browser()
    sys.exit(0)


def main():
    signal.signal(signal.SIGTERM, signal_handler)
    signal.signal(signal.SIGINT, signal_handler)

    log("Kiosk starting up.")

    # Start API server
    api_thread = threading.Thread(target=api_server_loop, daemon=True)
    api_thread.start()

    wait_for_network()
    launch_browser()

    # Start midnight refresh thread
    refresh_thread = threading.Thread(target=midnight_refresh_loop, daemon=True)
    refresh_thread.start()

    # Watchdog loop
    while not shutdown_event.is_set():
        if browser_proc and browser_proc.poll() is not None:
            exit_code = browser_proc.returncode
            log(f"Browser exited (code {exit_code}). Restarting in 3s...")
            time.sleep(3)
            if not shutdown_event.is_set():
                launch_browser()
        time.sleep(2)


if __name__ == "__main__":
    main()
