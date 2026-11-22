# Sades Ryunix XR1 Driver & Compatibility Suite for macOS

Custom driver integration and direct input bridge for the Sades Ryunix XR1 racing wheel on Apple Silicon and Intel macOS systems running Wine, CrossOver, and Euro Truck Simulator 2.

## Key Capabilities

- **Automatic DirectInput Enumeration**: Resolves HID enumeration issues where macOS MFi GameController hides raw USB steering wheels from Wine.
- **Steam Overlay Hook Prevention**: Prevents GameOverlayRenderer from intercepting DirectInput calls in 64-bit Wine environments.
- **Automatic ETS2 Profile Configuration**: Detects existing game profiles and maps steering, pedals, H-shifter gears (1-6 + Reverse), Handbrake (B15), and Lo/Hi Range selector (B23).
- **Web Calibration Studio**: Built-in browser-based diagnostic utility (`./test.sh`) for real-time visualization of steering angles, pedal depression percentages, and shifter positions.
- **Safe Stock Restore**: Automated backups of all modified binary libraries allowing instant uninstallation.

---

## Technical Overview

On macOS, modern versions of `libSDL2` enable Apple's GameController framework by default. Because USB racing wheels report as generic desktop HID devices rather than MFi controllers, the framework filters them out unless raw IOKit mode is forced.

Furthermore, dynamic environment variable injection (`SDL_JOYSTICK_IOKIT=1`) is often dropped when wrapper executables spawn subprocesses directly. This suite resolves the problem at the core:

1. **SDL2 Binary Patch**: Patches `libSDL2` default initialization flags to disable MFi prioritization and prioritize raw IOKit HID enumeration.
2. **Wine Bus Architecture**: Ensures `winebus.sys` properly bridges host IOKit gamepads into Windows DirectInput 8 GUIDs.
3. **DLL Overrides**: Directs Wine to disable overlay hooks on DirectInput8 entry points.

---

## Quick Start

### 1. Installation

Run the automated installer from the repository root:

```bash
./install.sh
```

The script will:
1. Locate your Wine / CrossOver / TruckersMP installation.
2. Create safety backups of original dynamic libraries (`.bak`).
3. Apply binary and environment patches.
4. Scan and configure your Euro Truck Simulator 2 profiles.

### 2. Testing Your Hardware

Launch the interactive diagnostic studio in your browser:

```bash
./test.sh
```

Navigate to `http://localhost:8080` to verify steering angle (900 degrees), throttle, brake, clutch, and shifter buttons in real time.

---

## Controls Mapping in Euro Truck Simulator 2

| Control | Input Device / Axis | Button ID |
| :--- | :--- | :--- |
| **Steering** | LITE STAR Ryunix XR1 | `joy.x` |
| **Throttle** | Linear Y Axis | `joy.y` |
| **Brake** | Linear Z Axis | `joy.z` |
| **Clutch** | Linear RZ Axis | `joy.rz` |
| **H-Shifter Gears 1-6** | Shifter Gate Switches | Buttons 16 to 21 |
| **Reverse Gear** | Shifter Gate Switch | Button 22 |
| **Handbrake** | Shifter Toggle Switch | Button 15 |
| **Splitter / Range (Lo-Hi)** | Shifter Range Switch | Button 23 |

---

## Uninstallation

To restore original system and Wine libraries:

```bash
./uninstall.sh
```

All `.bak` files are restored to their original state and Wine configuration overrides are removed.

---

## License

This project is licensed under the terms described in the `LICENSE` file.
