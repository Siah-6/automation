# Arcane Legends Vision-Based Automation

A computer vision automation system for Arcane Legends that can farm dungeon/event maps automatically without relying on fixed coordinates.

## Features

- **Vision-based detection** of enemies, loot, portals, HP bar, and skill cooldowns
- **Adaptive movement** that works regardless of map orientation changes
- **Smart combat system** with automatic skill usage
- **Loot collection** and dungeon cycling
- **Health monitoring** with automatic healing
- **10-20 FPS detection loop** for fast-paced gameplay

## Installation

1. Install Python 3.8 or higher
2. Install required dependencies:
```bash
pip install -r requirements.txt
```

## Setup

### 1. Configure Game Window
- Run Arcane Legends in windowed mode
- Position the game window on your monitor
- Note which monitor the game is on (primary=0, secondary=1, etc.)

### 2. Adjust Configuration
Edit `config.py` to match your game setup:

```python
MONITOR_INDEX = 1  # Change to your monitor
TARGET_FPS = 15    # 10-20 recommended
```

### 3. Calibrate Colors (IMPORTANT)
The automation uses HSV color detection. You'll need to adjust the color values in `config.py`:

1. Take screenshots of the game elements
2. Use a color picker tool to get HSV values for:
   - Enemy colors (usually red/orange)
   - Loot colors (usually yellow/gold)
   - Portal colors (usually blue/purple)
   - HP bar color (usually red)

### 4. Test Detection Regions
Adjust the region coordinates in `config.py` to match your game window:
- `HP_BAR_REGION`: Where the health bar appears
- `SKILL_BAR_REGION`: Where skill icons are located
- `COMBAT_AREA_REGION`: Main gameplay area

## Usage

1. Start Arcane Legends and enter a dungeon area
2. Run the automation:
```bash
python arcane_legends_automation.py
```
3. Press `Ctrl+C` to stop the automation

## Controls

The automation uses these default keys (can be changed in `config.py`):
- **Movement**: WASD
- **Skills**: 1, 2, 3, 4
- **Loot**: Spacebar
- **Interact**: E (for portals)
- **Heal**: Q
- **Enter Dungeon**: Enter

## How It Works

### Detection System
1. **Screen Capture**: Uses MSS for fast screen capture
2. **Color Detection**: HSV color space for robust detection
3. **Contour Analysis**: Finds objects by shape and size
4. **Region-based Processing**: Only scans relevant screen areas

### State Machine
The automation follows this gameplay loop:
1. **OUTSIDE_DUNGEON** → Enter dungeon
2. **IN_DUNGEON** → Explore and detect enemies/loot
3. **COMBAT** → Fight enemies with skills
4. **LOOTING** → Collect dropped items
5. **MOVING_TO_EXIT** → Head to portal
6. **Repeat**

### Decision Logic
- Always prioritize combat when enemies are detected
- Use available skills based on cooldown status
- Collect loot when combat is clear
- Move to exit when no enemies remain
- Monitor HP and use healing when needed

## Performance Optimization

- **Region-based detection**: Only scans specific screen areas
- **FPS limiting**: Maintains 10-20 FPS for responsiveness
- **Efficient algorithms**: Uses OpenCV optimized functions
- **Minimal memory usage**: Processes frames without storage

## Troubleshooting

### Detection Not Working
1. Check color values in `config.py`
2. Verify region coordinates match your game window
3. Ensure game is in windowed mode (not fullscreen)
4. Adjust detection thresholds if objects are missed

### Movement Issues
1. Verify WASD keys work in the game
2. Check if game window is active
3. Adjust `MOVEMENT_THRESHOLD` if movement is too sensitive

### Performance Issues
1. Lower `TARGET_FPS` to 10 if CPU usage is high
2. Reduce detection region sizes
3. Close unnecessary background applications

## Safety Features

- **Fail-safe**: PyAutoGUI's built-in fail-safe (move mouse to corner)
- **Health monitoring**: Automatic healing at low HP
- **Graceful shutdown**: Clean stop on Ctrl+C
- **Non-invasive**: Only reads screen and sends keyboard inputs

## Customization

### Adding New Detection Types
You can extend the `VisualDetector` class to detect additional game elements:

```python
def detect_special_items(self, frame):
    # Add custom detection logic
    pass
```

### Modifying Combat Behavior
Edit the `handle_combat` method in `DecisionEngine` to implement different combat strategies.

### Adding New States
Extend the `GameState` enum and add corresponding logic to the state machine.

## Legal Notice

This automation tool is for educational purposes only. Use it responsibly and in accordance with the game's terms of service. The developers are not responsible for any consequences of using this software.

## Requirements

- Python 3.8+
- Windows OS (tested on Windows 10/11)
- Arcane Legends game client
- Windowed mode display

## Support

For issues and questions:
1. Check the troubleshooting section
2. Verify your configuration matches the game
3. Test with different color values if detection fails
