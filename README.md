# Sades Ryunix XR1 Driver & Compatibility Suite for macOS

Custom driver integration, DirectInput 8 bridge, Force Feedback (FFB) tuning studio, and community preset hub for the Sades Ryunix XR1 racing wheel on Apple Silicon and Intel macOS systems running Wine, CrossOver, and Euro Truck Simulator 2.

## Key Capabilities

- **Automatic DirectInput Enumeration**: Resolves HID enumeration issues where macOS MFi GameController hides raw USB steering wheels from Wine.
- **Steam Overlay Hook Prevention**: Prevents GameOverlayRenderer from intercepting DirectInput calls in 64-bit Wine environments.
- **Automatic ETS2 Profile Configuration**: Detects existing game profiles and maps steering, pedals, H-shifter gears (1-6 + Reverse), Handbrake (B15), and Lo/Hi Range selector (B23).
- **Web Force Feedback Studio**: Interactive tuning dashboard (`./test.sh`) with an official-wheel-app **Easy Mode** (4 macro sliders + driving style cards) and an **Advanced Mode** (10 granular DirectInput telemetry channels).
- **WebHID Direct Hardware Motor Actuator**: Transmits raw USB PID reports (`0x0C`, `0x0D`, `0x05`, `0x04`) directly to the wheel via Chromium WebHID, delivering real physical torque, dynamic centering pull, and engine vibration right in your hands without legacy Apple framework limitations.
- **Dynamic DirectInput8 GUID Auto-Sync**: Automatically detects live Wine instance GUIDs from `game.log.txt` and `global_controls.sii`, un-blacklists the wheel, and keeps profile bindings permanently synchronized.
- **Community Preset Hub**: Browse curated presets, 1-click apply to game profiles, export portable `.json` files, and upload community presets.
- **Safe Stock Restore**: Automated backups of all modified binary libraries allowing instant uninstallation.

---

## Technical Overview

On macOS, modern versions of `libSDL2` enable Apple's GameController framework by default. Because USB racing wheels report as generic desktop HID devices rather than MFi controllers, the framework filters them out unless raw IOKit mode is forced.

Furthermore, dynamic environment variable injection (`SDL_JOYSTICK_IOKIT=1`) is often dropped when wrapper executables spawn subprocesses directly. This suite resolves the problem at the core:

1. **SDL2 Binary Patch**: Patches `libSDL2` default initialization flags to disable MFi prioritization and prioritize raw IOKit HID enumeration.
2. **Wine Bus Architecture**: Ensures `winebus.sys` properly bridges host IOKit gamepads into Windows DirectInput 8 GUIDs.
3. **DLL Overrides**: Directs Wine to disable overlay hooks on DirectInput8 entry points.
4. **Preset Calibration Engine**: Injects `c_ff_*` constants and custom button mixes into `controls.sii` across all player profiles.

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

### 2. Interactive Web Studio & FFB Controller

Launch the interactive diagnostic studio and preset manager:

```bash
./test.sh
```

Navigate to `http://localhost:8080` to access:
- **Diagnostics**: 900-degree wheel angle tracker, triple pedal bars, H-shifter gate, and button matrix.
- **Force Feedback**: 10 live sliders with physical motor test buttons (Centering, Engine, Surface, Curb, Crash).
- **Preset Hub**: Curated profiles, 1-click apply to ETS2, export, and community upload.

---

## Curated Game Presets

| Preset | Description | Key Characteristics |
| :--- | :--- | :--- |
| **Balanced Simulation (Default)** | Authentic everyday trucking calibration. | Centering 1.45/0.85, Friction 0.75, Gain 8.0 |
| **Realistic Heavy Haulage** | Heavy resistance for 50t+ specialized cargo. | Centering 1.60/0.95, Friction 0.90, Gain 8.8, Engine 0.40 |
| **Smooth Highway Cruiser** | Relaxed steering for long-distance highway hauls. | Centering 1.15/0.65, Friction 0.40, Gain 6.8, Light assist 0.75 |
| **Arcade & Fast Return** | Agile, snappy wheel recovery and high collision punch. | Centering 1.85/1.10, Friction 0.20, Gain 7.6 |
| **Sequential & City Transit** | Paddle shifters (B1/B2) and automatic assist for tight city traffic. | Centering 1.25/0.70, High assist 0.80, Gain 6.8 |

---

## Force Feedback & Easy Mode Control

The Web Diagnostic Studio (`http://localhost:8080`) provides an official-app-style control center inspired by Logitech G HUB, Fanatec FanaLab, and the Ryunix Windows utility.

### 🟢 Easy Mode (Recommended)
Designed for effortless, intuitive tuning with 4 master sliders:
1. **Master FFB Strength (0–100%)**: Scales overall motor torque and peak physical steering resistance.
2. **Wheel Centering Speed (Soft $\leftrightarrow$ Fast)**: Controls how firmly and rapidly the wheel returns to 0° when you release it.
3. **Wheel Weight & Resistance (Light $\leftrightarrow$ Heavy)**: Simulates heavy hydraulic power steering fluid and tire patch friction.
4. **Road & Engine Vibration (Gentle $\leftrightarrow$ Intense)**: Adjusts tactile vibrations for diesel engine RPM resonance, cobblestones, rumble strips, and gear shifts.

#### 1-Click Driving Style Profiles
- 🚛 **Heavy Truck (ETS2 / ATS)**: Authentic heavy steering, high rack damping, and deep diesel engine rumble.
- 🏎️ **Track & GT Racing**: Stiff centering return force, rapid slip reaction, and maximum curb texture.
- 💨 **Drift & Agile**: Featherlight wheel, instant counter-steering recovery, zero mechanical drag.
- 🛋️ **Smooth Cruiser**: Long-distance highway comfort with 80% power steering assist.

### ⚙️ Advanced Telemetry Mode (10 Channels)
For telemetry enthusiasts, switch to Advanced Mode to fine-tune individual `controls.sii` parameters:
- `c_ff_gain`: Master DirectInput motor multiplier (tuned to `8.0` for Wine).
- `c_ff_hi_spd` / `c_ff_lo_spd`: Speed-dependent return spring tension.
- `c_ff_fricton` / `c_ff_undrstr` / `c_ff_assist`: Tire friction, slip lightening, and power steering curves.
- `c_ff_engine` / `c_ff_surface` / `c_ff_bumps` / `c_ff_gearbox` / `c_ff_collis`: Granular environmental vibrations.

All slider adjustments synchronize bidirectionally between Easy and Advanced modes in real time.

---

## ⚡ WebHID Direct Hardware Motor Actuator

### Why WebHID is Required on macOS
On macOS, Chromium browsers route standard Gamepad API rumble through Apple's legacy `ForceFeedback.framework`. Apple deprecated this framework and does not provide an in-kernel or user-space PID driver for generic USB racing wheels (VID `0x11FF`, PID `0x2364`), causing standard gamepad vibration calls to fail silently.

### How WebHID Works
WebHID (`navigator.hid`) communicates directly with macOS `IOHIDKit` USB endpoints, bypassing Apple's legacy framework completely:
1. Open the Web Studio in **Google Chrome**, **Microsoft Edge**, or **Brave**.
2. Click **`🔌 Connect WebHID`** in the top navigation bar.
3. Select **Ryunix XR1** from the browser USB permission prompt.
4. Once connected, click **`🎯 Feel Wheel in Hand`** or any effect in the **Live Physical Haptics Test Suite**:
   - **Report 12 (`0x0C`)**: Enables physical motor coils.
   - **Report 13 (`0x0D`)**: Sets master gain to 100%.
   - **Report 5 (`0x05`)**: Sends directional constant torque and centering spring forces.
   - **Report 10 (`0x0A`)**: Controls effect playback.

Your steering wheel will physically pull, center, and vibrate in your hands!

---

## Euro Truck Simulator 2 In-Game Recommendations

For optimal force feedback and steering accuracy in ETS2:
1. Open **Options $\rightarrow$ Controls** in ETS2.
2. Set **Controller Subtype** to **Wheel**.
3. Set **Steering Sensitivity** to 100% (middle position, linear 1:1 rotation).
4. Set **Steering Non-Linearity** to 0% (slider all the way to the left).
5. Ensure **Force Feedback** is **Checked / Enabled**.
6. Whenever you adjust presets in the Web Studio, click **`🚀 1-Click Sync to ETS2`** to automatically calibrate all profiles and refresh the active DirectInput8 GUID.

---

## Community Preset Sharing & Upload

### Exporting a Preset
In the Web Studio under **Preset Hub**, click **📥 Export** on any card. This downloads a portable JSON preset file (`sades-xr1-<preset_id>.json`) ready to share with friends, Discord, or GitHub.

### Uploading a Community Preset
Click **⬆ Upload / Import Preset**, then drag-and-drop any `.json` preset. The studio validates the schema, previews the parameters, saves it to your local library, and applies it to your game with one click.

### Preset JSON Specification (`xr1-preset.v1`)

```json
{
  "schema": "xr1-preset.v1",
  "id": "my_custom_preset",
  "name": "My Custom Setup",
  "author": "CommunityDriver",
  "game": "Euro Truck Simulator 2",
  "description": "Tuned for mountain roads and heavy timber transport.",
  "tags": ["Simulation", "HeavyHaul", "H-Shifter"],
  "ffb": {
    "c_ff_enabled": 1.0,
    "c_ff_gain": 6.0,
    "c_ff_hi_spd": 1.2,
    "c_ff_lo_spd": 0.8,
    "c_ff_fricton": 0.6,
    "c_ff_engine": 0.3,
    "c_ff_surface": 0.4,
    "c_ff_bumps": 0.85,
    "c_ff_collis": 1.0,
    "c_ff_gearbox": 0.4,
    "c_ff_undrstr": 0.5,
    "c_ff_assist": 0.4
  },
  "buttons": {
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
    "hshifter_gear_r": "joy.b22?0"
  }
}
```

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

## Local REST API Reference

When `tester/server.py` or `./test.sh` is active, the following endpoints are available:

- `GET /api/presets`: Returns list of all curated and community presets.
- `POST /api/presets/apply`: Injects selected preset (`preset_id` or `preset_data`) into `controls.sii`.
- `POST /api/presets/save`: Saves custom user preset to `config/presets/`.
- `POST /api/presets/upload`: Validates and saves an uploaded community preset.
- `GET /api/profiles`: Lists detected ETS2 profile directories.

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
