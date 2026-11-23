# Sades Ryunix XR1 Driver & Compatibility Suite for macOS

Custom driver integration, DirectInput 8 bridge, Force Feedback (FFB) tuning studio, and community preset hub for the Sades Ryunix XR1 racing wheel on Apple Silicon and Intel macOS systems running Wine, CrossOver, and Euro Truck Simulator 2.

## Key Capabilities

- **Automatic DirectInput Enumeration**: Resolves HID enumeration issues where macOS MFi GameController hides raw USB steering wheels from Wine.
- **Steam Overlay Hook Prevention**: Prevents GameOverlayRenderer from intercepting DirectInput calls in 64-bit Wine environments.
- **Automatic ETS2 Profile Configuration**: Detects existing game profiles and maps steering, pedals, H-shifter gears (1-6 + Reverse), Handbrake (B15), and Lo/Hi Range selector (B23).
- **Web Force Feedback Studio**: Interactive tuning dashboard (`./test.sh`) with 10 granular FFB sliders for gain, friction, assist, centering springs, understeer, and environmental vibrations.
- **Live Physical Haptics Testing**: Real-time physical wheel motor vibration tests (Centering, Engine Rumble, Road Surface, Curb Bumps, Collision Shock) using Web Gamepad Haptics and WebHID.
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
| **Balanced Simulation (Default)** | Authentic everyday trucking calibration. | Centering 1.0/0.5, Friction 0.5, Gain 5.0 |
| **Realistic Heavy Haulage** | Heavy resistance for 50t+ specialized cargo. | Centering 1.4/1.6, Friction 0.75, Gain 6.5, Engine 0.45 |
| **Smooth Highway Cruiser** | Relaxed steering for long-distance highway hauls. | Centering 0.8/0.4, Friction 0.35, Light assist 0.65 |
| **Arcade & Fast Return** | Agile, snappy wheel recovery and high collision punch. | Centering 1.6/0.3, Friction 0.10, Gain 5.5 |
| **Sequential & City Transit** | Paddle shifters (B1/B2) and automatic assist for tight city traffic. | Centering 0.9/0.35, High assist 0.70 |

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
