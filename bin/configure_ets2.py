#!/usr/bin/env python3
"""
Euro Truck Simulator 2 - Profile & Controls Calibrator
Automatically detects ETS2 user profiles and binds the Sades Ryunix XR1
with calibrated steering, pedal axes, handbrake (B15), Lo-Hi splitter (B23),
and 6-speed H-shifter gears (B16-22).
"""

import json
import os
import shutil
import sys
from pathlib import Path

DEVICE_JOY_STR = "di8.'{9E573EDF-7734-11D2-8D4A-23903FB6BDF7}|{236411FF-0000-0000-0000-504944564944}'"

CALIBRATED_BINDINGS = {
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


def patch_controls_sii(controls_path: Path):
    print(f"[*] Inspecting controls: {controls_path.parent.name}/controls.sii")
    bak_path = controls_path.with_suffix(".sii.bak")
    if not bak_path.exists():
        shutil.copy2(controls_path, bak_path)

    lines = controls_path.read_text(encoding="utf-8", errors="ignore").splitlines()
    updated = False

    for i, line in enumerate(lines):
        # 1. Bind device joy
        if 'device joy `' in line and 'config_lines[2]' in line:
            new_line = f' config_lines[2]: "device joy `{DEVICE_JOY_STR}`"'
            if lines[i] != new_line:
                lines[i] = new_line
                updated = True

        # 2. Bind calibrated buttons
        for key, val in CALIBRATED_BINDINGS.items():
            prefix = f'config_lines['
            if f' mix {key} `' in line:
                idx = line.split(":")[0].strip()
                new_line = f' {idx}: "mix {key} `{val}`"'
                if lines[i] != new_line:
                    lines[i] = new_line
                    updated = True

    if updated:
        controls_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
        print(f"[+] Successfully calibrated profile: {controls_path.parent.name}")
        return True
    else:
        print(f"[*] Profile is already calibrated: {controls_path.parent.name}")
        return True


def scan_and_configure_ets2(doc_dir: Path):
    if not doc_dir.is_dir():
        print(f"[-] ETS2 Documents directory not found at: {doc_dir}")
        return False

    profile_dirs = list(doc_dir.glob("profiles/*")) + list(doc_dir.glob("steam_profiles/*"))
    if not profile_dirs:
        print(f"[-] No ETS2 profiles found in: {doc_dir}")
        return False

    success = False
    for p in profile_dirs:
        ctrl = p / "controls.sii"
        if ctrl.is_file():
            if patch_controls_sii(ctrl):
                success = True

    return success


def main():
    default_ets2 = Path.home() / "Documents/Euro Truck Simulator 2"
    doc_dir = Path(sys.argv[1]).resolve() if len(sys.argv) > 1 else default_ets2

    if not doc_dir.is_dir():
        print(f"[-] Directory not found: {doc_dir}")
        sys.exit(1)

    scan_and_configure_ets2(doc_dir)


if __name__ == "__main__":
    main()
