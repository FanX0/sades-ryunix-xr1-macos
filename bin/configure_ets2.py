#!/usr/bin/env python3
"""
Euro Truck Simulator 2 - Profile, Controls & Force Feedback Calibrator
Applies curated or custom presets (FFB parameters and button/shifter bindings)
to all Euro Truck Simulator 2 player profiles in controls.sii.
Dynamically detects the active DirectInput 8 GUID for Ryunix XR1 and un-blacklists devices.
"""

import argparse
import json
import os
import re
import shutil
import sys
from pathlib import Path

FALLBACK_DEVICE_JOY_STR = "di8.'{9E573ED3-7734-11D2-8D4A-23903FB6BDF7}|{236411FF-0000-0000-0000-504944564944}'"

DEFAULT_BINDINGS = {
    "parkingbrake": "keyboard.space?0 | joy.b15?0",
    "gearboxhshifter": "1",
    "gearbox": "2",
    "hshifter_toggle1": "joy.b23?0",
    "hshifter_gear1": "joy.b16?0",
    "hshifter_gear2": "joy.b17?0",
    "hshifter_gear3": "joy.b18?0",
    "hshifter_gear4": "joy.b19?0",
    "hshifter_gear5": "joy.b20?0",
    "hshifter_gear6": "joy.b21?0",
    "hshifter_gear_r": "joy.b22?0",
}

DEFAULT_FFB = {
    "c_ff_enabled": 1.0,
    "c_ff_gain": 1.6,
    "c_ff_hi_spd": 0.35,
    "c_ff_lo_spd": 0.15,
    "c_ff_fricton": 0.06,
    "c_ff_engine": 0.25,
    "c_ff_surface": 0.20,
    "c_ff_bumps": 0.65,
    "c_ff_collis": 0.75,
    "c_ff_gearbox": 0.25,
    "c_ff_undrstr": 0.45,
    "c_ff_assist": 0.88,
}


def log(msg: str, quiet: bool = False):
    if not quiet:
        print(msg, file=sys.stderr)


def detect_active_di8_guid(doc_dir: Path, quiet: bool = False) -> str:
    """
    Detects the active DirectInput8 GUID assigned to Ryunix XR1 (VID 0x11FF, PID 0x2364)
    from game.log.txt or global_controls.sii.
    """
    # 1. Try reading recent entries in game.log.txt
    log_file = doc_dir / "game.log.txt"
    if log_file.is_file():
        try:
            content = log_file.read_text(encoding="utf-8", errors="ignore")
            # Look for lines like: [di8] Initializing device 'LITE STAR Ryunix XR1' as '{...}|{236411FF-...}'
            matches = re.findall(
                r"\[di8\] Initializing device '.*Ryunix XR1.*' as '(\{[0-9A-Fa-f\-]+\}\|(?:\{236411FF-[0-9A-Fa-f\-]+\}))'",
                content,
            )
            if matches:
                guid = matches[-1]
                log(f"[+] Detected active DirectInput8 GUID from game.log.txt: {guid}", quiet)
                return f"di8.'{guid}'"
        except Exception as e:
            log(f"[-] Warning: Failed reading game.log.txt: {e}", quiet)

    # 2. Try reading global_controls.sii
    global_ctrl = doc_dir / "global_controls.sii"
    if global_ctrl.is_file():
        try:
            content = global_ctrl.read_text(encoding="utf-8", errors="ignore")
            matches = re.findall(
                r"di8\.'(\{[0-9A-Fa-f\-]+\}\|(?:\{236411FF-[0-9A-Fa-f\-]+\}))'",
                content,
            )
            if matches:
                guid = matches[-1]
                log(f"[+] Detected active DirectInput8 GUID from global_controls.sii: {guid}", quiet)
                return f"di8.'{guid}'"
        except Exception as e:
            log(f"[-] Warning: Failed reading global_controls.sii: {e}", quiet)

    log(f"[*] Falling back to default DirectInput8 GUID: {FALLBACK_DEVICE_JOY_STR}", quiet)
    return FALLBACK_DEVICE_JOY_STR


def clean_global_controls(doc_dir: Path, quiet: bool = False):
    """
    Removes Ryunix XR1 from ui_blacklisted in global_controls.sii to prevent ETS2
    from ignoring or blocking the controller in the interface.
    """
    global_path = doc_dir / "global_controls.sii"
    if not global_path.is_file():
        return

    try:
        content = global_path.read_text(encoding="utf-8", errors="ignore")
        lines = content.splitlines()
        new_lines = []
        updated = False

        for line in lines:
            if "ui_blacklisted:" in line:
                new_lines.append(" ui_blacklisted: 0")
                if line.strip() != "ui_blacklisted: 0":
                    updated = True
            elif "ui_blacklisted[" in line and "236411FF" in line:
                updated = True
                continue  # drop the blacklisted device entry
            else:
                new_lines.append(line)

        if updated:
            global_path.write_text("\n".join(new_lines) + "\n", encoding="utf-8")
            log("[+] Un-blacklisted Ryunix XR1 in global_controls.sii", quiet)
    except Exception as e:
        log(f"[-] Warning: Failed to sanitize global_controls.sii: {e}", quiet)


def load_preset(preset_arg: str, root_dir: Path) -> dict:
    if not preset_arg:
        default_file = root_dir / "config/presets/default.json"
        if default_file.is_file():
            try:
                return json.loads(default_file.read_text(encoding="utf-8"))
            except Exception:
                pass
        return {"ffb": DEFAULT_FFB, "buttons": DEFAULT_BINDINGS, "name": "Default"}

    # Check if direct JSON string
    if preset_arg.strip().startswith("{") and preset_arg.strip().endswith("}"):
        try:
            return json.loads(preset_arg)
        except Exception as e:
            print(f"[-] Invalid JSON preset string: {e}", file=sys.stderr)

    # Check if direct file path
    p = Path(preset_arg)
    if not p.is_file():
        # Check inside config/presets/
        preset_candidate = root_dir / "config/presets" / (preset_arg if preset_arg.endswith(".json") else f"{preset_arg}.json")
        if preset_candidate.is_file():
            p = preset_candidate

    if p.is_file():
        try:
            return json.loads(p.read_text(encoding="utf-8"))
        except Exception as e:
            print(f"[-] Failed reading preset file {p}: {e}", file=sys.stderr)

    return {"ffb": DEFAULT_FFB, "buttons": DEFAULT_BINDINGS, "name": "Fallback"}


def patch_controls_sii(controls_path: Path, preset: dict, active_device_joy: str, quiet: bool = False) -> bool:
    preset_name = preset.get("name", "Custom")
    log(f"[*] Applying preset [{preset_name}] to: {controls_path.parent.name}/controls.sii", quiet)

    bak_path = controls_path.with_suffix(".sii.bak")
    if not bak_path.exists():
        try:
            shutil.copy2(controls_path, bak_path)
        except Exception as e:
            log(f"[-] Warning: Failed to create backup: {e}", quiet)

    content = controls_path.read_text(encoding="utf-8", errors="ignore")
    lines = content.splitlines()
    updated = False

    ffb_settings = preset.get("ffb", {})
    button_bindings = preset.get("buttons", {})

    # Normalize button_bindings aliases:
    # ETS2 controls.sii uses 'gear1', 'gearsel1tgl', 'parkingbrake', etc.
    normalized_buttons = {}
    alias_map = {
        "hshifter_gear1": "gear1",
        "hshifter_gear2": "gear2",
        "hshifter_gear3": "gear3",
        "hshifter_gear4": "gear4",
        "hshifter_gear5": "gear5",
        "hshifter_gear6": "gear6",
        "hshifter_gear_r": "gear7",
        "hshifter_toggle1": "gearsel1tgl",
        "hshifter_toggle2": "gearsel2tgl",
    }
    for k, v in button_bindings.items():
        normalized_buttons[k] = v
        if k in alias_map:
            normalized_buttons[alias_map[k]] = v

    # Also mirror gear7 to gearreverse for reverse gear compatibility
    if "gear7" in normalized_buttons and "gearreverse" not in normalized_buttons:
        normalized_buttons["gearreverse"] = normalized_buttons["gear7"]

    for i, line in enumerate(lines):
        # 1. Bind device joy to the active DirectInput8 GUID
        if 'device joy `' in line and 'config_lines[2]' in line:
            new_line = f' config_lines[2]: "device joy `{active_device_joy}`"'
            if lines[i] != new_line:
                lines[i] = new_line
                updated = True

        # 1b. Bind POV Hat Switch to interior camera look
        if 'input j_look_ud `' in line:
            idx = line.split(":")[0].strip()
            new_line = f' {idx}: "input j_look_ud `joy.pov1_y`"'
            if lines[i] != new_line:
                lines[i] = new_line
                updated = True
        if 'input j_look_lr `' in line:
            idx = line.split(":")[0].strip()
            new_line = f' {idx}: "input j_look_lr `joy.pov1_x`"'
            if lines[i] != new_line:
                lines[i] = new_line
                updated = True

        # 2. Patch FFB Constants: constant <c_ff_key> <float>
        for ffb_key, ffb_val in ffb_settings.items():
            pattern = f"constant {ffb_key} "
            if pattern in line:
                idx = line.split(":")[0].strip()
                val_float = float(ffb_val)
                new_line = f' {idx}: "constant {ffb_key} {val_float:.6f}"'
                if lines[i] != new_line:
                    lines[i] = new_line
                    updated = True

        # 3. Patch Button Mixes: mix <button_key> `<val>`
        for btn_key, btn_val in normalized_buttons.items():
            pattern = f'"mix {btn_key} `'
            if pattern in line:
                idx = line.split(":")[0].strip()
                new_line = f' {idx}: "mix {btn_key} `{btn_val}`"'
                if lines[i] != new_line:
                    lines[i] = new_line
                    updated = True

    if updated:
        controls_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
        log(f"[+] Successfully calibrated profile: {controls_path.parent.name}", quiet)
        return True
    else:
        log(f"[*] Profile is already in sync with preset: {controls_path.parent.name}", quiet)
        return True


def scan_and_configure_ets2(doc_dir: Path, preset: dict, quiet: bool = False):
    if not doc_dir.is_dir():
        log(f"[-] ETS2 Documents directory not found at: {doc_dir}", quiet)
        return []

    # Clean blacklist in global_controls.sii
    clean_global_controls(doc_dir, quiet=quiet)

    # Dynamically detect active DirectInput8 GUID
    active_device_joy = detect_active_di8_guid(doc_dir, quiet=quiet)

    profile_dirs = list(doc_dir.glob("profiles/*")) + list(doc_dir.glob("steam_profiles/*"))
    if not profile_dirs:
        log(f"[-] No ETS2 profiles found in: {doc_dir}", quiet)
        return []

    configured = []
    for p in profile_dirs:
        ctrl = p / "controls.sii"
        if ctrl.is_file():
            if patch_controls_sii(ctrl, preset, active_device_joy, quiet):
                configured.append(p.name)

    return configured


def main():
    parser = argparse.ArgumentParser(description="Configure ETS2 controls and FFB presets for Sades Ryunix XR1.")
    parser.add_argument("doc_dir", nargs="?", default=str(Path.home() / "Documents/Euro Truck Simulator 2"), help="ETS2 Documents path")
    parser.add_argument("--preset", "-p", default="", help="Preset ID, file path, or JSON string")
    parser.add_argument(
        "--shifter-layout",
        choices=["6plusR", "5plusR"],
        default="6plusR",
        help="Shifter pattern layout (6plusR or 5plusR)",
    )
    parser.add_argument("--json", action="store_true", help="Output JSON result for API consumption")

    args = parser.parse_args()

    repo_root = Path(__file__).resolve().parent.parent
    doc_path = Path(args.doc_dir).resolve()
    preset_data = load_preset(args.preset, repo_root)

    if args.shifter_layout == "5plusR":
        preset_data.setdefault("buttons", {})
        preset_data["buttons"]["hshifter_gear6"] = ""
        preset_data["buttons"]["hshifter_gear_r"] = "joy.b21?0"

    configured_profiles = scan_and_configure_ets2(doc_path, preset_data, quiet=args.json)

    # Ensure SCS telemetry plugins are deployed to Wine ETS2
    try:
        from install_telemetry_plugin import install_plugins
        install_plugins()
    except Exception:
        pass

    result = {
        "success": len(configured_profiles) > 0,
        "preset": preset_data.get("name", "Custom"),
        "preset_id": preset_data.get("id", "custom"),
        "profiles": configured_profiles,
        "count": len(configured_profiles),
    }

    if args.json:
        print(json.dumps(result))
    else:
        if result["success"]:
            print(f"[+] Successfully applied preset '{result['preset']}' to {result['count']} profile(s).")
        else:
            print("[-] No profiles were updated.")


if __name__ == "__main__":
    main()
