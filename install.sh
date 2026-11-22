#!/usr/bin/env bash
#
# Sades Ryunix XR1 macOS Compatibility Suite - 1-Click Installer
# Universal driver fix for Euro Truck Simulator 2 under CrossOver / Wine
#

set -e

# Terminal formatting
BOLD="\033[1m"
GREEN="\033[32m"
BLUE="\033[34m"
YELLOW="\033[33m"
RED="\033[31m"
NC="\033[0m"

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BIN_DIR="${SCRIPT_DIR}/bin"

echo -e "${BOLD}${BLUE}======================================================${NC}"
echo -e "${BOLD}${BLUE}   Sades Ryunix XR1 - macOS & ETS2 Compatibility Suite${NC}"
echo -e "${BOLD}${BLUE}======================================================${NC}"
echo ""

# 1. Auto-Detect Wine Installation
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

if [ -z "${DETECTED_WINE}" ]; then
    echo -e "${YELLOW}[?] Wine not found in default locations. Enter your Wine root path:${NC}"
    read -r DETECTED_WINE
fi

if [ ! -d "${DETECTED_WINE}" ]; then
    echo -e "${RED}[-] Invalid Wine directory: ${DETECTED_WINE}${NC}"
    exit 1
fi
echo -e "${GREEN}[+] Wine root:${NC} ${DETECTED_WINE}"

# 2. Auto-Detect Bottle / Prefix
BOTTLE_CANDIDATES=(
    "/Volumes/vgen storage/GameData/Support/TruckersMP-Launcher/TruckersmpBottle"
    "${HOME}/Library/Application Support/TruckersMP-Launcher/TruckersmpBottle"
    "${HOME}/Library/Application Support/CrossOver/Bottles/TruckersmpBottle"
)

DETECTED_BOTTLE=""
for b in "${BOTTLE_CANDIDATES[@]}"; do
    if [ -d "${b}" ]; then
        DETECTED_BOTTLE="${b}"
        break
    fi
done

if [ -z "${DETECTED_BOTTLE}" ]; then
    echo -e "${YELLOW}[?] Bottle not found in default locations. Enter your Bottle path:${NC}"
    read -r DETECTED_BOTTLE
fi

if [ ! -d "${DETECTED_BOTTLE}" ]; then
    echo -e "${RED}[-] Invalid Bottle directory: ${DETECTED_BOTTLE}${NC}"
    exit 1
fi
echo -e "${GREEN}[+] Bottle prefix:${NC} ${DETECTED_BOTTLE}"

# 3. Auto-Detect Steam Directory inside Bottle
STEAM_DIR="${DETECTED_BOTTLE}/drive_c/Program Files (x86)/Steam"
if [ ! -d "${STEAM_DIR}" ]; then
    STEAM_DIR="${DETECTED_BOTTLE}/drive_c/Program Files/Steam"
fi
if [ -d "${STEAM_DIR}" ]; then
    echo -e "${GREEN}[+] Steam directory:${NC} ${STEAM_DIR}"
fi

echo ""
echo -e "${YELLOW}[*] Shutting down active Wine and Steam processes...${NC}"
WINESERVER_BIN="${DETECTED_WINE}/bin/wineserver"
if [ -f "${WINESERVER_BIN}" ]; then
    WINEPREFIX="${DETECTED_BOTTLE}" WINEMSYNC=1 "${WINESERVER_BIN}" -k 2>/dev/null || true
fi
killall eurotrucks2.exe steam.exe winedevice.exe 2>/dev/null || true
sleep 1

# 4. Patch Driver & Libraries
echo ""
echo -e "${BOLD}[Step 1/3] Patching Wine Driver & SDL2 Libraries...${NC}"
python3 "${BIN_DIR}/patch_driver.py" "${DETECTED_WINE}"

# 5. Configure Wine Registry
echo ""
echo -e "${BOLD}[Step 2/3] Configuring Wine DirectInput Subsystem...${NC}"
python3 "${BIN_DIR}/configure_wine.py" "${DETECTED_WINE}/bin/wine" "${DETECTED_BOTTLE}"

# 6. Configure Steam Input
echo ""
echo -e "${BOLD}[Step 3/4] Disabling Steam Input Overlay Hook...${NC}"
if [ -d "${STEAM_DIR}" ]; then
    python3 "${BIN_DIR}/configure_steam.py" "${STEAM_DIR}" 227300
else
    echo -e "${YELLOW}[!] Steam directory not found. Skipping Steam Input bypass.${NC}"
fi

# 7. Configure ETS2 Profile
echo ""
echo -e "${BOLD}[Step 4/4] Calibrating ETS2 Profiles & Controls...${NC}"
ETS2_DOCS="${HOME}/Documents/Euro Truck Simulator 2"
if [ -d "${ETS2_DOCS}" ]; then
    python3 "${BIN_DIR}/configure_ets2.py" "${ETS2_DOCS}"
else
    echo -e "${YELLOW}[!] ETS2 documents not found at ${ETS2_DOCS}. Skipping profile patch.${NC}"
fi

echo ""
echo -e "${BOLD}${GREEN}======================================================${NC}"
echo -e "${BOLD}${GREEN}   Installation Successful! Wheel is now compatible.  ${NC}"
echo -e "${BOLD}${GREEN}======================================================${NC}"
echo ""
echo -e "Next steps:"
echo -e "  1. Connect your Sades Ryunix XR1 steering wheel."
echo -e "  2. Start Euro Truck Simulator 2 / TruckersMP."
echo -e "  3. Go to Options -> Controls."
echo -e "  4. Select 'LITE STAR Ryunix XR1' from the controller list."
echo ""
