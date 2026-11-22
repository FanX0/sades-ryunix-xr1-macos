#!/usr/bin/env python3
"""
Steam Input Configurator
Disables Steam Input (UseSteamControllerConfig = "0") for ETS2 (AppID 227300)
across all detected userdata directories in the Wine Steam bottle.
"""

import re
import sys
from pathlib import Path


def disable_steam_input_for_app(vdf_path: Path, app_id: str = "227300"):
    if not vdf_path.is_file():
        return False

    content = vdf_path.read_text(encoding="utf-8", errors="ignore")
    # Match under "apps" block
    pattern = rf'("{app_id}"\s*\{{[^}}]*"UseSteamControllerConfig"\s*)"1"'
    if re.search(pattern, content):
        new_content = re.sub(pattern, r'\g<1>"0"', content)
        vdf_path.write_text(new_content, encoding="utf-8")
        print(f"[+] Disabled Steam Input for App {app_id} in: {vdf_path.name}")
        return True
    elif f'"{app_id}"' in content and '"UseSteamControllerConfig"' in content:
        print(f"[*] Steam Input is already disabled for App {app_id} in: {vdf_path.name}")
        return True
    else:
        print(f"[*] App {app_id} entry not found in: {vdf_path.name}")
        return False


def scan_and_configure_steam(steam_dir: Path, app_id: str = "227300"):
    print(f"[*] Scanning Steam userdata directory: {steam_dir}")
    userdata = steam_dir / "userdata"
    if not userdata.is_dir():
        print(f"[-] Userdata not found in {steam_dir}")
        return False

    vdf_files = list(userdata.glob("*/config/localconfig.vdf"))
    if not vdf_files:
        print(f"[-] No localconfig.vdf found in {userdata}")
        return False

    success = False
    for vdf in vdf_files:
        if disable_steam_input_for_app(vdf, app_id):
            success = True

    return success


def main():
    if len(sys.argv) < 2:
        print("Usage: configure_steam.py <steam_root_directory> [app_id]")
        sys.exit(1)

    steam_root = Path(sys.argv[1]).resolve()
    app_id = sys.argv[2] if len(sys.argv) > 2 else "227300"

    if not steam_root.is_dir():
        print(f"[-] Invalid Steam directory: {steam_root}")
        sys.exit(1)

    scan_and_configure_steam(steam_root, app_id)


if __name__ == "__main__":
    main()
