#!/usr/bin/env python3
"""
Install SCS Telemetry SDK & Popup Bypass plugins into Euro Truck Simulator 2
Wine bottle on macOS.
"""

import os
import shutil
import sys
from pathlib import Path

SOURCE_PLUGINS_DIRS = [
    Path("/Volumes/vgen storage/Applications/TruckersMP for macOS.app/Contents/Resources/plugins"),
]

TARGET_ETS2_DIRS = [
    Path("/Volumes/vgen storage/GameData/Support/TruckersMP-Launcher/TruckersmpBottle/drive_c/Program Files (x86)/Steam/steamapps/common/Euro Truck Simulator 2/bin/win_x64"),
    Path.home() / "Library/Application Support/Steam/steamapps/common/Euro Truck Simulator 2/bin/win_x64",
    Path.home() / "Library/Application Support/CrossOver/Bottles/TruckersMP/drive_c/Program Files (x86)/Steam/steamapps/common/Euro Truck Simulator 2/bin/win_x64",
]

PLUGIN_FILES = [
    "ets2-telemetry-server.dll",
    "ScsSDKPopupBypass.dll",
]


def install_plugins() -> bool:
    # 1. Locate source plugins
    source_dir = None
    for s in SOURCE_PLUGINS_DIRS:
        if s.exists() and (s / "ets2-telemetry-server.dll").exists():
            source_dir = s
            break

    if not source_dir:
        print("[!] Error: Could not locate source telemetry plugins directory.")
        return False

    print(f"[*] Found source plugins at: {source_dir}")

    # 2. Locate target win_x64 directory
    target_win64 = None
    for t in TARGET_ETS2_DIRS:
        if t.exists() and (t / "eurotrucks2.exe").exists():
            target_win64 = t
            break

    if not target_win64:
        print("[!] Error: Could not locate ETS2 bin/win_x64 installation directory.")
        return False

    print(f"[*] Found ETS2 installation at: {target_win64}")

    plugins_dest = target_win64 / "plugins"
    plugins_dest.mkdir(parents=True, exist_ok=True)

    installed_count = 0
    for p in PLUGIN_FILES:
        src_file = source_dir / p
        dst_file = plugins_dest / p
        if src_file.exists():
            shutil.copy2(src_file, dst_file)
            os.chmod(dst_file, 0o755)
            print(f"  ✓ Installed: {p} -> {dst_file}")
            installed_count += 1
        else:
            print(f"  [!] Missing source plugin: {p}")

    print(f"[*] Successfully installed {installed_count} telemetry plugins to Wine ETS2.")
    return installed_count > 0


if __name__ == "__main__":
    success = install_plugins()
    sys.exit(0 if success else 1)
