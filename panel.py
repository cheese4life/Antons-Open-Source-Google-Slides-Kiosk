# Kiosk Control Panel
# Web UI on port 8080 for managing the kiosk display.
# Talks to kiosk.py's API on localhost:8081.


import json
import urllib.request
import urllib.error
from http.server import HTTPServer, BaseHTTPRequestHandler
from datetime import datetime

PANEL_PORT = 8080
KIOSK_API = "http://localhost:8081"

def log(msg):
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"[panel {ts}] {msg}", flush=True)


def kiosk_request(method, path, data=None):
    """Send a request to the kiosk API. Returns (success, response_dict)."""
    url = KIOSK_API + path
    try:
        body = json.dumps(data).encode() if data else None
        req = urllib.request.Request(url, data=body, method=method)
        if body:
            req.add_header("Content-Type", "application/json")
        with urllib.request.urlopen(req, timeout=5) as resp:
            return True, json.loads(resp.read().decode())
    except Exception as e:
        return False, {"error": str(e)}


# ── HTML ──────────Section Generated w/ Claude Code ────────────────────────────────────
PAGE_HTML = r"""<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Kiosk Control Panel</title>
<style>
*{margin:0;padding:0;box-sizing:border-box}
body{background:#000;color:#fff;font-family:'Segoe UI',Arial,sans-serif;
     padding:40px 20px;max-width:600px;margin:0 auto}
h1{font-size:1.6em;font-weight:400;margin-bottom:30px}

.status-row{display:flex;align-items:center;gap:10px;margin-bottom:30px;
            font-size:1.1em}
.dot{width:14px;height:14px;border-radius:50%;flex-shrink:0}
.dot.green{background:#22c55e;box-shadow:0 0 8px #22c55e}
.dot.red{background:#ef4444;box-shadow:0 0 8px #ef4444}
.dot.gray{background:#666}

.mode-label{font-size:0.9em;opacity:0.5;margin-left:auto}

.section{margin-bottom:25px}
label{display:block;font-size:0.85em;opacity:0.6;margin-bottom:6px}
input[type=text]{width:100%;padding:10px 12px;background:#111;border:1px solid #333;
     color:#fff;font-size:1em;border-radius:4px;outline:none}
input[type=text]:focus{border-color:#555}

.buttons{display:flex;gap:10px;flex-wrap:wrap;margin-top:15px}
button{padding:10px 20px;border:1px solid #333;background:#111;color:#fff;
       font-size:0.95em;border-radius:4px;cursor:pointer;transition:background 0.2s}
button:hover{background:#222}
button:active{background:#333}

.msg{margin-top:15px;padding:10px 14px;border-radius:4px;font-size:0.9em;
     display:none}
.msg.ok{display:block;background:#052e16;border:1px solid #22c55e;color:#22c55e}
.msg.err{display:block;background:#2a0a0a;border:1px solid #ef4444;color:#ef4444}

.current-url{font-size:0.8em;opacity:0.4;margin-top:8px;word-break:break-all}
</style>
</head>
<body>

<h1>Kiosk Control Panel</h1>

<div class="status-row">
  <div class="dot gray" id="statusDot"></div>
  <span id="statusText">Checking...</span>
  <span class="mode-label" id="modeLabel"></span>
</div>

<div class="section">
  <label>Display URL</label>
  <input type="text" id="urlInput" placeholder="https://...">
  <div class="current-url" id="currentUrl"></div>
</div>

<div class="buttons">
  <button onclick="setUrl()">Set URL</button>
  <button onclick="refresh()">Force Refresh</button>
  <button onclick="toggleClock()">Toggle Clock</button>
</div>

<div class="msg" id="msg"></div>

<script>
var msg=document.getElementById('msg');
var dot=document.getElementById('statusDot');
var stxt=document.getElementById('statusText');
var mode=document.getElementById('modeLabel');
var curUrl=document.getElementById('currentUrl');

function showMsg(text,ok){
  msg.textContent=text;
  msg.className='msg '+(ok?'ok':'err');
  setTimeout(function(){msg.className='msg';},4000);
}

function checkStatus(){
  fetch('/api/status').then(function(r){return r.json()}).then(function(d){
    if(d.alive){
      dot.className='dot green';
      stxt.textContent='Kiosk is running';
    }else{
      dot.className='dot red';
      stxt.textContent='Kiosk is down';
    }
    mode.textContent=d.showing_clock?'Clock mode':'Slides mode';
    curUrl.textContent='Current: '+d.url;
  }).catch(function(){
    dot.className='dot red';
    stxt.textContent='Cannot reach kiosk service';
    mode.textContent='';
    curUrl.textContent='';
  });
}

function setUrl(){
  var url=document.getElementById('urlInput').value.trim();
  if(!url){showMsg('Enter a URL first',false);return;}
  fetch('/api/set-url',{method:'POST',headers:{'Content-Type':'application/json'},
    body:JSON.stringify({url:url})})
    .then(function(r){return r.json()})
    .then(function(d){
      if(d.ok){showMsg('URL updated — kiosk refreshing',true);document.getElementById('urlInput').value='';}
      else showMsg('Error: '+(d.error||'unknown'),false);
      checkStatus();
    }).catch(function(e){showMsg('Failed: '+e,false);});
}

function refresh(){
  fetch('/api/refresh',{method:'POST'})
    .then(function(r){return r.json()})
    .then(function(d){
      if(d.ok) showMsg('Refresh sent — kiosk reloading',true);
      else showMsg('Error: '+(d.error||'unknown'),false);
      checkStatus();
    }).catch(function(e){showMsg('Failed: '+e,false);});
}

function toggleClock(){
  fetch('/api/toggle-clock',{method:'POST'})
    .then(function(r){return r.json()})
    .then(function(d){
      if(d.ok) showMsg(d.showing_clock?'Clock mode ON':'Slides mode ON',true);
      else showMsg('Error: '+(d.error||'unknown'),false);
      checkStatus();
    }).catch(function(e){showMsg('Failed: '+e,false);});
}

checkStatus();setInterval(checkStatus,5000);
</script>
</body>
</html>"""


class PanelHandler(BaseHTTPRequestHandler):
    def log_message(self, fmt, *args):
        log(f"{fmt % args}")

    def _respond(self, code, content_type, body):
        self.send_response(code)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        if self.path == "/" or self.path == "/index.html":
            self._respond(200, "text/html", PAGE_HTML.encode())
        elif self.path == "/api/status":
            ok, data = kiosk_request("GET", "/status")
            self._respond(200 if ok else 502, "application/json", json.dumps(data).encode())
        else:
            self._respond(404, "text/plain", b"not found")

    def do_POST(self):
        if self.path == "/api/refresh":
            ok, data = kiosk_request("POST", "/refresh")
            self._respond(200 if ok else 502, "application/json", json.dumps(data).encode())

        elif self.path == "/api/set-url":
            length = int(self.headers.get("Content-Length", 0))
            body = self.rfile.read(length)
            try:
                payload = json.loads(body.decode())
                url = payload.get("url", "").strip()
            except (json.JSONDecodeError, AttributeError):
                self._respond(400, "application/json", json.dumps({"error": "bad json"}).encode())
                return
            if not url or not url.startswith(("http://", "https://")):
                self._respond(400, "application/json", json.dumps({"error": "invalid url"}).encode())
                return
            ok, data = kiosk_request("POST", "/set-url", {"url": url})
            self._respond(200 if ok else 502, "application/json", json.dumps(data).encode())

        elif self.path == "/api/toggle-clock":
            ok, data = kiosk_request("POST", "/toggle-clock")
            self._respond(200 if ok else 502, "application/json", json.dumps(data).encode())

        else:
            self._respond(404, "text/plain", b"not found")
            
# ────────────────────────────────────────────────────────────────────────────────────────────────────────────


def main():
    server = HTTPServer(("0.0.0.0", PANEL_PORT), PanelHandler)
    log(f"Control panel listening on http://0.0.0.0:{PANEL_PORT}")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        log("Shutting down.")
        server.server_close()


if __name__ == "__main__":
    main()
