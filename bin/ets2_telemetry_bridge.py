#!/usr/bin/env python3
"""
Euro Truck Simulator 2 — Physics Force Feedback Telemetry Bridge for macOS
Translates ETS2 chassis kinematics and tire telemetry into authentic physical
motor torque for the Sades Ryunix XR1 steering wheel.

Supports:
1. Direct UDP broadcast on port 23640 (SCS Telemetry SDK UDP forwarder).
2. Funbit / ETS2 Telemetry Server HTTP REST endpoint at http://127.0.0.1:25555/api/ets2/telemetry.
3. Interactive Kinematic Mode when game telemetry is idle (accelerates on pedal input,
   simulates truck inertia, and provides speed-sensitive aligning torque).
"""

import json
import math
import os
import socket
import sys
import threading
import time
import urllib.request
from pathlib import Path


class ETS2TelemetryBridge:
    def __init__(self, port: int = 23640, http_port: int = 25555):
        self.port = port
        self.http_port = http_port
        self.running = False
        self._thread = None
        self._http_thread = None
        self._sock = None

        # Telemetry State
        self.state = {
            "connected": False,
            "source": "Standby",
            "speed_kmh": 0.0,
            "rpm": 650.0,
            "max_rpm": 2500.0,
            "gear": 0,
            "steer_angle": 0.0,
            "lateral_g": 0.0,
            "surface_roughness": 0.0,
            "engine_running": True,
            "ffb_torque": 0.0,  # -1.0 to 1.0 normalized
            "hw_force": 0,       # -10000 to 10000 PID range
            "packets_count": 0,
            "last_packet_time": 0.0,
        }

        # Live Hardware Inputs (from Studio / WebHID)
        self.inputs = {
            "steer_deg": 0.0,
            "throttle": 0.0,
            "brake": 0.0,
        }

        # Physics Tuning Parameters
        self.config = {
            "master_gain": 1.0,
            "centering_strength": 0.75,
            "rack_weight": 0.55,
            "engine_vibration": 0.40,
            "road_texture": 0.35,
            "steer_deadzone": 2.0,
        }

    def start(self):
        if self.running:
            return
        self.running = True
        self._thread = threading.Thread(target=self._run_loop, daemon=True)
        self._thread.start()
        self._http_thread = threading.Thread(target=self._run_http_poll, daemon=True)
        self._http_thread.start()

    def stop(self):
        self.running = False
        if self._sock:
            try:
                self._sock.close()
            except Exception:
                pass
            self._sock = None
        if self._thread and self._thread.is_alive():
            self._thread.join(timeout=0.5)
        self.state["connected"] = False
        self.state["source"] = "Stopped"
        self.state["ffb_torque"] = 0.0
        self.state["hw_force"] = 0

    def _run_http_poll(self):
        """Polls Funbit ETS2 Telemetry Server HTTP endpoint (port 25555) at 10Hz."""
        url = f"http://127.0.0.1:{self.http_port}/api/ets2/telemetry"
        while self.running:
            try:
                req = urllib.request.Request(url, headers={"User-Agent": "XR1-Bridge"})
                with urllib.request.urlopen(req, timeout=0.08) as resp:
                    if resp.status == 200:
                        raw = resp.read()
                        data = json.loads(raw.decode("utf-8", errors="ignore"))
                        if self._parse_funbit_telemetry(data):
                            self.state["last_packet_time"] = time.time()
                            self.state["packets_count"] += 1
                            self.state["connected"] = True
                            self.state["source"] = "ETS2 Telemetry Server (:25555)"
            except Exception:
                pass
            time.sleep(0.1)

    def _parse_funbit_telemetry(self, data: dict) -> bool:
        try:
            game = data.get("game", {})
            truck = data.get("truck", {})
            if not game.get("connected", False) or game.get("paused", False):
                return False

            self.state["speed_kmh"] = float(truck.get("speed", 0.0))
            self.state["rpm"] = float(truck.get("engineRpm", 650.0))
            self.state["max_rpm"] = float(truck.get("engineRpmMax", 2500.0))
            self.state["gear"] = int(truck.get("displayedGear", truck.get("gear", 0)))
            self.state["engine_running"] = bool(truck.get("engineOn", True))

            # Steering (-1 to +1 -> degrees)
            self.state["steer_angle"] = float(truck.get("gameSteer", truck.get("userSteer", 0.0))) * 450.0

            acc = truck.get("acceleration", {})
            self.state["lateral_g"] = float(acc.get("x", 0.0))
            self.state["surface_roughness"] = abs(float(acc.get("y", 0.0)))
            return True
        except Exception:
            return False

    def _run_loop(self):
        # Bind UDP socket for incoming SCS Telemetry broadcasts
        try:
            self._sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            self._sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            self._sock.settimeout(0.04)
            self._sock.bind(("127.0.0.1", self.port))
            self.state["source"] = f"Listening on UDP :{self.port}"
        except Exception as e:
            self.state["source"] = f"Socket Error: {e}"
            self._sock = None

        last_time = time.time()

        while self.running:
            now = time.time()
            dt = max(0.001, min(0.1, now - last_time))
            last_time = now

            packet_received = False
            if self._sock:
                try:
                    data, _ = self._sock.recvfrom(4096)
                    self._parse_telemetry(data)
                    packet_received = True
                    self.state["packets_count"] += 1
                    self.state["last_packet_time"] = now
                    self.state["connected"] = True
                    self.state["source"] = "SCS Telemetry Stream (Live)"
                except socket.timeout:
                    pass
                except Exception:
                    pass

            # If no telemetry packets received in > 1.2s, simulate kinematics
            if (now - self.state["last_packet_time"]) > 1.2:
                self.state["connected"] = False
                self.state["source"] = "Kinematic Resistance Active"
                self._simulate_kinematics(dt)

            # Compute physical force feedback
            self._compute_ffb(dt)
            time.sleep(0.01)  # 100 Hz physics update loop

    def _simulate_kinematics(self, dt: float):
        """Simulate realistic truck acceleration, RPM and gear progression when ETS2 telemetry is idle."""
        throttle = self.inputs["throttle"]
        brake = self.inputs["brake"]
        steer_deg = self.inputs["steer_deg"]

        self.state["steer_angle"] = steer_deg

        speed = self.state["speed_kmh"]
        if throttle > 0.05:
            accel = throttle * 24.0  # km/h per second
            speed += accel * dt
        else:
            speed -= (2.5 + speed * 0.04) * dt

        if brake > 0.05:
            decel = brake * 45.0  # heavy truck braking
            speed -= decel * dt

        speed = max(0.0, min(105.0, speed))
        self.state["speed_kmh"] = speed

        # RPM & Gear calculation
        if speed < 1.0:
            if throttle > 0.05:
                self.state["rpm"] = 650.0 + throttle * 1100.0
                self.state["gear"] = 1
            else:
                self.state["rpm"] = 650.0
                self.state["gear"] = 0
        else:
            gear = max(1, min(12, int(speed / 8.0) + 1))
            self.state["gear"] = gear
            gear_ratio_speed = (speed % 8.0) / 8.0
            self.state["rpm"] = 750.0 + gear_ratio_speed * 850.0 + (throttle * 300.0)

        self.state["lateral_g"] = (speed / 90.0) * (steer_deg / 450.0) * 0.5

    def _parse_telemetry(self, raw_bytes: bytes):
        try:
            text = raw_bytes.decode("utf-8", errors="ignore").strip()
            if text.startswith("{") and text.endswith("}"):
                data = json.loads(text)
                self.state["speed_kmh"] = float(data.get("speed", data.get("speed_kmh", 0.0)))
                self.state["rpm"] = float(data.get("rpm", data.get("engine_rpm", 750.0)))
                self.state["gear"] = int(data.get("gear", 0))
                self.state["steer_angle"] = float(data.get("steering", data.get("steer", 0.0)))
                self.state["lateral_g"] = float(data.get("lateral_g", data.get("acc_x", 0.0)))
                self.state["surface_roughness"] = float(data.get("surface", data.get("suspension_deflection", 0.0)))
                self.state["engine_running"] = bool(data.get("engine_running", True))
        except Exception:
            pass

    def _compute_ffb(self, dt: float):
        """
        Calculates authentic steering torque using vehicle dynamics:
        1. Aligning Torque (Pacejka pneumatic trail from tire lateral force)
        2. Speed-sensitive centering force
        3. Hydraulic steering rack damping / friction
        4. Diesel engine harmonic resonance
        5. Road surface texture
        """
        steer_deg = self.state["steer_angle"]
        speed = max(0.0, self.state["speed_kmh"])
        gain = self.config["master_gain"]
        centering = self.config["centering_strength"]
        weight = self.config["rack_weight"]
        vib_setting = self.config["engine_vibration"]
        road_setting = self.config["road_texture"]

        # Deadzone filter
        if abs(steer_deg) < self.config["steer_deadzone"]:
            effective_steer = 0.0
        else:
            effective_steer = steer_deg

        # Normalized steer (-1.0 to 1.0)
        norm_steer = max(-1.0, min(1.0, effective_steer / 450.0))

        # 1. Aligning Torque (Self-Centering)
        speed_factor = min(1.0, speed / 80.0)
        parking_factor = max(0.0, 1.0 - speed / 15.0)

        # Non-linear tire aligning torque curve (simulating tire slip saturation)
        sat_curve = math.sin(norm_steer * (math.pi / 2.0))
        align_torque = -sat_curve * (0.35 + 0.65 * speed_factor) * centering

        # 2. Hydraulic Rack Weight / Damping
        rack_resistance = -math.copysign(1.0, norm_steer) * (0.15 * parking_factor + 0.35 * weight) if abs(norm_steer) > 0.05 else 0.0

        # 3. Lateral G Weight Transfer
        lat_force = -self.state["lateral_g"] * 0.45

        # 4. Engine Vibration (Resonance with diesel RPM, only applied when active)
        engine_vib = 0.0
        if self.state["engine_running"] and abs(norm_steer) > 0.02:
            rpm = max(500.0, min(2600.0, self.state["rpm"]))
            freq = (rpm / 60.0) * 0.5  # 2-cylinder fire rate harmonic
            engine_vib = math.sin(time.time() * freq * 2.0 * math.pi) * 0.05 * vib_setting

        # 5. Road Surface / Gravel Bump
        road_vib = 0.0
        if speed > 5.0 and road_setting > 0.05:
            roughness = max(0.1, min(1.0, self.state["surface_roughness"] + 0.08))
            road_vib = (math.sin(time.time() * 45.0) * 0.5 + math.sin(time.time() * 85.0) * 0.5) * roughness * 0.12 * road_setting

        # Combine all forces
        total_torque = (align_torque + rack_resistance + lat_force + engine_vib + road_vib) * gain

        # Zero-clamp strictly within deadzone to eliminate floating point oscillation
        if effective_steer == 0.0 and abs(self.state["lateral_g"]) < 0.01:
            total_torque = 0.0

        clamped_torque = max(-1.0, min(1.0, total_torque))

        self.state["ffb_torque"] = round(clamped_torque, 4)
        self.state["hw_force"] = int(round(clamped_torque * 10000))

    def update_steer_input(self, steer_deg: float, throttle: float = 0.0, brake: float = 0.0, speed_hint: float = None):
        """Allows external UI loop to feed live wheel rotation and pedal inputs."""
        self.inputs["steer_deg"] = steer_deg
        self.inputs["throttle"] = max(0.0, min(1.0, throttle))
        self.inputs["brake"] = max(0.0, min(1.0, brake))
        if not self.state["connected"]:
            self.state["steer_angle"] = steer_deg
            if speed_hint is not None:
                self.state["speed_kmh"] = speed_hint


# Global singleton instance
bridge_instance = ETS2TelemetryBridge()


def get_bridge() -> ETS2TelemetryBridge:
    return bridge_instance


if __name__ == "__main__":
    b = get_bridge()
    b.start()
    print(f"[*] ETS2 Telemetry Bridge active on UDP :{b.port} and HTTP :{b.http_port}")
    try:
        while True:
            time.sleep(1)
            s = b.state
            print(f"[{s['source']}] Speed: {s['speed_kmh']:.1f} km/h | Steer: {s['steer_angle']:.1f}° | Torque: {s['ffb_torque']:.3f} (HW: {s['hw_force']})")
    except KeyboardInterrupt:
        b.stop()
        print("\n[*] Bridge stopped.")
