#!/usr/bin/env python3
"""
Sades Ryunix XR1 - Driver & Binary Patcher for macOS Wine / CrossOver
Patches:
  1. winebus.so: Fixes dlopen path for libSDL2 using @rpath/sdl.dylib
  2. libSDL2-2.0.0.dylib: Disables MFi (GCController) default to enforce raw IOKit USB HID
"""

import os
import shutil
import struct
import subprocess
import sys
from pathlib import Path


def log(msg, prefix="[*]"):
    print(f"{prefix} {msg}")


def codesign_file(filepath: Path):
    """Re-sign Mach-O binary with ad-hoc signature."""
    log(f"Codesigning: {filepath.name}...")
    try:
        subprocess.run(
            ["/usr/bin/codesign", "--force", "--sign", "-", str(filepath)],
            check=True,
            capture_output=True,
        )
        log(f"Successfully signed {filepath.name}", prefix="[+]")
        return True
    except subprocess.CalledProcessError as e:
        log(f"Codesign failed for {filepath}: {e.stderr.decode()}", prefix="[-]")
        return False


def patch_winebus(winebus_path: Path):
    """Patch winebus.so to use @rpath/sdl.dylib instead of bare libSDL2-2.0.0.dylib."""
    if not winebus_path.is_file():
        log(f"winebus.so not found at: {winebus_path}", prefix="[-]")
        return False

    bak_path = winebus_path.with_suffix(".so.bak")
    if not bak_path.exists():
        log(f"Creating backup: {bak_path}")
        shutil.copy2(winebus_path, bak_path)

    data = bytearray(winebus_path.read_bytes())
    target = b"libSDL2-2.0.0.dylib\x00"
    replacement = b"@rpath/sdl.dylib\x00\x00\x00\x00"

    if replacement in data:
        log(f"winebus.so is already patched.", prefix="[+]")
    elif target in data:
        data = data.replace(target, replacement)
        winebus_path.write_bytes(data)
        log(f"Patched winebus.so to use @rpath/sdl.dylib", prefix="[+]")
    else:
        log(f"Pattern for libSDL2 not found in winebus.so", prefix="[-]")
        return False

    # Ensure symlink sdl.dylib exists in wine/lib
    wine_lib = winebus_path.parent.parent.parent
    sdl_symlink = wine_lib / "sdl.dylib"
    sdl_target = wine_lib / "libSDL2-2.0.0.dylib"
    if sdl_target.exists() and not sdl_symlink.exists():
        try:
            sdl_symlink.symlink_to("libSDL2-2.0.0.dylib")
            log(f"Created symlink: {sdl_symlink} -> libSDL2-2.0.0.dylib", prefix="[+]")
        except OSError as e:
            log(f"Symlink creation note: {e}", prefix="[-]")

    return codesign_file(winebus_path)


def patch_libsdl2(sdl_path: Path):
    """Patch libSDL2 to disable MFi default, ensuring raw IOKit USB HID detection."""
    if not sdl_path.is_file():
        log(f"libSDL2 not found at: {sdl_path}", prefix="[-]")
        return False

    bak_path = sdl_path.with_suffix(".dylib.bak")
    if not bak_path.exists():
        log(f"Creating backup: {bak_path}")
        shutil.copy2(sdl_path, bak_path)

    data = bytearray(sdl_path.read_bytes())

    # Find references to SDL_JOYSTICK_MFI string
    mfi_str = b"SDL_JOYSTICK_MFI\x00"
    mfi_pos = data.find(mfi_str)
    if mfi_pos == -1:
        log("SDL_JOYSTICK_MFI string not found in libSDL2", prefix="[-]")
        return False

    patched_count = 0
    # Search for RIP-relative leaq instructions loading mfi_pos
    for i in range(len(data) - 15):
        if data[i] in (0x48, 0x4c) and data[i + 1] == 0x8D:
            disp = struct.unpack("<i", data[i + 3 : i + 7])[0]
            rip = i + 7
            if rip + disp == mfi_pos:
                # Check instruction following: movl $1, %esi (be 01 00 00 00)
                next_ins = i + 7
                if data[next_ins : next_ins + 5] == bytes.fromhex("be01000000"):
                    data[next_ins : next_ins + 5] = bytes.fromhex("be00000000")
                    patched_count += 1
                elif data[next_ins : next_ins + 5] == bytes.fromhex("be00000000"):
                    patched_count += 1

    if patched_count > 0:
        sdl_path.write_bytes(data)
        log(f"Patched {patched_count} MFi check(s) in libSDL2 to default 0 (disabled)", prefix="[+]")
        return codesign_file(sdl_path)
    else:
        log("No MFi default instructions matched in libSDL2", prefix="[-]")
        return False


def restore_backups(wine_dir: Path):
    """Restore original .bak files."""
    for bak in wine_dir.glob("**/*.bak"):
        orig = bak.with_suffix("")
        shutil.copy2(bak, orig)
        codesign_file(orig)
        bak.unlink()
        log(f"Restored: {orig.name}", prefix="[+]")


def main():
    if len(sys.argv) < 2:
        print("Usage: patch_driver.py <wine_root_directory> [--restore]")
        sys.exit(1)

    wine_root = Path(sys.argv[1]).resolve()
    if not wine_root.is_dir():
        log(f"Invalid directory: {wine_root}", prefix="[-]")
        sys.exit(1)

    if "--restore" in sys.argv:
        log("Restoring backups...")
        restore_backups(wine_root)
        sys.exit(0)

    # Locate winebus.so
    winebus = next(wine_root.glob("**/winebus.so"), None)
    sdl = next(wine_root.glob("**/libSDL2-2.0.0.dylib"), None)

    if not winebus or not sdl:
        log(f"Could not find winebus.so or libSDL2 inside {wine_root}", prefix="[-]")
        sys.exit(1)

    success_wb = patch_winebus(winebus)
    success_sdl = patch_libsdl2(sdl)

    if success_wb and success_sdl:
        log("Driver and library patching completed successfully!", prefix="[+]")
    else:
        log("Driver patching completed with warnings.", prefix="[!] ")


if __name__ == "__main__":
    main()
