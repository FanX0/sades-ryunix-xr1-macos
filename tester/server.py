#!/usr/bin/env python3
"""
Sades Ryunix XR1 - Diagnostic Studio & Preset Hub Server
Serves the web diagnostic interface and provides REST API endpoints for:
- Listing curated and community presets (/api/presets)
- Applying presets directly to ETS2 controls.sii (/api/presets/apply)
- Saving and uploading custom community presets (/api/presets/save, /api/presets/upload)
- Detecting ETS2 profile directories (/api/profiles)
"""

import http.server
import json
import os
import re
import socketserver
import subprocess
import sys
from pathlib import Path
from urllib.parse import urlparse

PORT = 8080
SERVER_DIR = Path(__file__).resolve().parent
REPO_ROOT = SERVER_DIR.parent
PRESETS_DIR = REPO_ROOT / "config/presets"


def get_presets():
    PRESETS_DIR.mkdir(parents=True, exist_ok=True)
    presets = []
    for f in sorted(PRESETS_DIR.glob("*.json")):
        try:
            data = json.loads(f.read_text(encoding="utf-8"))
            if not data.get("id"):
                data["id"] = f.stem
            presets.append(data)
        except Exception as e:
            print(f"[!] Error reading preset {f.name}: {e}", file=sys.stderr)
    return presets


def detect_profiles():
    doc_dir = Path.home() / "Documents/Euro Truck Simulator 2"
    if not doc_dir.is_dir():
        return []
    profiles = []
    for p in list(doc_dir.glob("profiles/*")) + list(doc_dir.glob("steam_profiles/*")):
        if (p / "controls.sii").is_file():
            profiles.append({
                "id": p.name,
                "type": "steam" if "steam_profiles" in str(p) else "local",
                "path": str(p),
            })
    return profiles


class StudioHandler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(SERVER_DIR), **kwargs)

    def end_headers(self):
        self.send_header("Cache-Control", "no-store, no-cache, must-revalidate, max-age=0")
        self.send_header("Pragma", "no-cache")
        self.send_header("Expires", "0")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        super().end_headers()

    def do_OPTIONS(self):
        self.send_response(200)
        self.end_headers()

    def send_json(self, data, status=200):
        body = json.dumps(data, indent=2).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def read_json_body(self):
        content_len = int(self.headers.get("Content-Length", 0))
        if content_len == 0:
            return {}
        raw = self.rfile.read(content_len).decode("utf-8", errors="ignore")
        return json.loads(raw)

    def do_GET(self):
        parsed = urlparse(self.path)

        if parsed.path == "/api/presets":
            presets = get_presets()
            self.send_json({"success": True, "presets": presets, "count": len(presets)})
            return

        if parsed.path == "/api/profiles":
            profiles = detect_profiles()
            self.send_json({"success": True, "profiles": profiles, "count": len(profiles)})
            return

        super().do_GET()

    def do_POST(self):
        parsed = urlparse(self.path)

        if parsed.path == "/api/presets/apply":
            try:
                body = self.read_json_body()
                preset_id = body.get("preset_id", "")
                preset_data = body.get("preset_data")
                shifter_layout = body.get("shifter_layout", "6plusR")

                config_script = REPO_ROOT / "bin/configure_ets2.py"
                cmd = [sys.executable, str(config_script), "--json", "--shifter-layout", shifter_layout]

                if preset_data and isinstance(preset_data, dict):
                    cmd.extend(["--preset", json.dumps(preset_data)])
                elif preset_id:
                    cmd.extend(["--preset", preset_id])
                else:
                    cmd.extend(["--preset", "default"])

                res = subprocess.run(cmd, capture_output=True, text=True, check=True)
                stdout_lines = [l.strip() for l in res.stdout.strip().splitlines() if l.strip().startswith("{") and l.strip().endswith("}")]
                if stdout_lines:
                    out_json = json.loads(stdout_lines[-1])
                else:
                    out_json = {"success": True, "output": res.stdout}
                self.send_json(out_json)
            except Exception as e:
                self.send_json({"success": False, "error": str(e)}, status=500)
            return

        if parsed.path in ("/api/presets/save", "/api/presets/upload"):
            try:
                data = self.read_json_body()
                if not isinstance(data, dict):
                    self.send_json({"success": False, "error": "Preset payload must be a JSON object."}, status=400)
                    return

                # Validate or assign ID
                raw_id = data.get("id") or data.get("name") or "custom_preset"
                safe_id = re.sub(r"[^a-zA-Z0-9_-]", "_", raw_id).strip("_").lower()
                data["id"] = safe_id
                data.setdefault("schema", "xr1-preset.v1")

                out_file = PRESETS_DIR / f"{safe_id}.json"
                out_file.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")

                self.send_json({
                    "success": True,
                    "preset_id": safe_id,
                    "preset": data,
                    "message": f"Preset '{data.get('name', safe_id)}' saved successfully.",
                })
            except Exception as e:
                self.send_json({"success": False, "error": str(e)}, status=500)
            return

        self.send_json({"success": False, "error": f"Endpoint not found: {self.path}"}, status=404)


if __name__ == "__main__":
    socketserver.TCPServer.allow_reuse_address = True
    with socketserver.TCPServer(("", PORT), StudioHandler) as httpd:
        print(f"🏎️  Sades Ryunix XR1 Studio & API running at http://0.0.0.0:{PORT} ...")
        httpd.serve_forever()
