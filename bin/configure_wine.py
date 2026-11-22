#!/usr/bin/env python3
"""
Wine Registry & DirectInput Bridge Configurator
Sets up:
  1. Wine Session Environment: SDL_JOYSTICK_IOKIT=1, SDL_JOYSTICK_MFI=0
  2. Wine DllOverrides: Disables Steam GameOverlayRenderer hooks for DirectInput 8
"""

import subprocess
import sys
from pathlib import Path


def run_reg(wine_bin: Path, wine_prefix: Path, args: list):
    cmd = [
        str(wine_bin),
        "reg",
    ] + args
    env = {
        "WINEPREFIX": str(wine_prefix),
        "WINEMSYNC": "1",
        "PATH": "/usr/bin:/bin:/usr/sbin:/sbin",
    }
    res = subprocess.run(cmd, env=env, capture_output=True, text=True)
    return res.returncode == 0


def configure_wine_bottle(wine_bin: Path, wine_prefix: Path):
    print(f"[*] Configuring Wine bottle: {wine_prefix}")

    # 1. Add Environment Variables
    env_key = r"HKEY_LOCAL_MACHINE\System\CurrentControlSet\Control\Session Manager\Environment"
    ok1 = run_reg(
        wine_bin, wine_prefix, ["add", env_key, "/v", "SDL_JOYSTICK_IOKIT", "/t", "REG_SZ", "/d", "1", "/f"]
    )
    ok2 = run_reg(
        wine_bin, wine_prefix, ["add", env_key, "/v", "SDL_JOYSTICK_MFI", "/t", "REG_SZ", "/d", "0", "/f"]
    )
    if ok1 and ok2:
        print("[+] Registered SDL_JOYSTICK environment variables in Wine registry.")
    else:
        print("[-] Warning: Failed to write environment variables to registry.")

    # 2. Add DllOverrides for Steam GameOverlayRenderer
    dll_key = r"HKEY_CURRENT_USER\Software\Wine\DllOverrides"
    ok3 = run_reg(wine_bin, wine_prefix, ["add", dll_key, "/v", "gameoverlayrenderer64", "/t", "REG_SZ", "/d", "", "/f"])
    ok4 = run_reg(wine_bin, wine_prefix, ["add", dll_key, "/v", "gameoverlayrenderer", "/t", "REG_SZ", "/d", "", "/f"])
    if ok3 and ok4:
        print("[+] Disabled Steam Overlay DirectInput hooks via Wine DllOverrides.")
    else:
        print("[-] Warning: Failed to register DllOverrides.")

    return ok1 and ok2 and ok3 and ok4


def main():
    if len(sys.argv) < 3:
        print("Usage: configure_wine.py <wine_binary_path> <wine_prefix_path>")
        sys.exit(1)

    wine_bin = Path(sys.argv[1]).resolve()
    wine_prefix = Path(sys.argv[2]).resolve()

    if not wine_bin.is_file() or not wine_prefix.is_dir():
        print(f"[-] Invalid wine binary or bottle path: {wine_bin}, {wine_prefix}")
        sys.exit(1)

    success = configure_wine_bottle(wine_bin, wine_prefix)
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
