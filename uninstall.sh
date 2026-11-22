#!/usr/bin/env bash
#
# Sades Ryunix XR1 macOS Compatibility Suite - Uninstaller & Restore
# Reverts patched binaries and restores factory stock libraries
#

set -e

BOLD="\033[1m"
GREEN="\033[32m"
YELLOW="\033[33m"
NC="\033[0m"

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BIN_DIR="${SCRIPT_DIR}/bin"

echo -e "${BOLD}Reverting Sades Ryunix XR1 Driver Patches...${NC}"

WINE_CANDIDATES=(
    "/Volumes/vgen storage/GameData/Support/TruckersMP-Launcher/wines/crossover wine 11 0/wine"
    "${HOME}/Library/Application Support/TruckersMP-Launcher/wines/crossover wine 11 0/wine"
    "/Applications/CrossOver.app/Contents/SharedSupport/CrossOver"
)

DETECTED_WINE=""
for dir in "${WINE_CANDIDATES[@]}"; do
    if [ -d "${dir}" ] && [ -f "${dir}/bin/wine" ]; then
        DETECTED_WINE="${dir}"
        break
    fi
done

if [ -n "${DETECTED_WINE}" ]; then
    python3 "${BIN_DIR}/patch_driver.py" "${DETECTED_WINE}" --restore
    echo -e "${GREEN}[+] Restored stock Wine libraries and driver binaries.${NC}"
else
    echo -e "${YELLOW}[!] Wine directory not found. Please provide path manually.${NC}"
fi
