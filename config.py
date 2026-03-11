"""
Configuration file for Arcane Legends Automation
Adjust these values based on your game setup
"""

# Screen capture settings
MONITOR_INDEX = 1  # Change to 0 for primary monitor, 1 for secondary, etc.
TARGET_FPS = 15  # Detection loop FPS (10-20 recommended)

# Detection regions (adjust based on your game window)
HP_BAR_REGION = (10, 10, 200, 40)  # Top left HP bar
ENERGY_BAR_REGION = (300, 10, 150, 40)  # Top center energy icons
SKILL_BAR_REGION = (500, 520, 300, 80)  # Bottom right skills
HOTBAR_REGION = (520, 540, 200, 60)  # Bottom right hotbar items
COMBAT_AREA_REGION = (100, 100, 600, 400)  # Main game area
PORTAL_MENU_REGION = (250, 200, 300, 200)  # Center menu area
INTERACTION_BUTTON_REGION = (520, 540, 80, 80)  # Space button area

# Color detection values (HSV format)
# You'll need to adjust these based on the actual game colors
ENEMY_COLORS = {
    'lower': [0, 120, 70],    # Red/orange enemies
    'upper': [20, 255, 255]
}

LOOT_COLORS = {
    'lower': [20, 100, 100],  # Yellow/gold loot
    'upper': [30, 255, 255]
}

GREEN_PORTAL_COLORS = {
    'lower': [40, 150, 150],  # Bright green portal glow
    'upper': [80, 255, 255]
}

ENERGY_ICON_COLORS = {
    'lower': [40, 100, 100],  # Green energy icons
    'upper': [80, 255, 255]
}

INTERACTION_BUTTON_COLORS = {
    'lower': [100, 100, 100],  # Blue/purple interaction button
    'upper': [150, 255, 255]
}

MENU_BUTTON_COLORS = {
    'lower': [100, 50, 50],   # Blue/purple menu buttons
    'upper': [150, 255, 255]
}

ENERGY_KIT_COLORS = {
    'lower': [15, 100, 100],  # Yellow/orange energy kit
    'upper': [35, 255, 255]
}

PORTAL_COLORS = {
    'lower': [100, 50, 50],   # Blue/purple dungeon exit portal
    'upper': [150, 255, 255]
}

HP_BAR_COLORS = {
    'lower': [0, 120, 70],    # Red HP bar
    'upper': [10, 255, 255]
}

# Detection thresholds
MIN_ENEMY_AREA = 100  # Minimum pixel area for enemy detection
MIN_LOOT_AREA = 50    # Minimum pixel area for loot detection
MIN_PORTAL_AREA = 500  # Minimum pixel area for portal detection
MIN_GREEN_PORTAL_AREA = 500  # Minimum pixel area for green portal
MIN_ENERGY_ICON_AREA = 50  # Minimum pixel area for energy icons
MIN_MENU_BUTTON_AREA = 1000  # Minimum pixel area for menu buttons
MIN_HOTBAR_ITEM_AREA = 100  # Minimum pixel area for hotbar items

# Combat settings
COMBAT_TIMEOUT = 3.0  # Seconds to wait after combat before moving to exit
LOW_HP_THRESHOLD = 0.3  # Use healing at 30% HP or below
SKILL_USAGE_DELAY = 0.5  # Seconds between skill uses

# Movement settings
INTERACTION_DISTANCE = 50  # Pixels - distance to interact with objects
MOVEMENT_THRESHOLD = 0.3   # Minimum movement input threshold

# Input settings
MOVEMENT_KEYS = {
    'up': 'w',
    'down': 's', 
    'left': 'a',
    'right': 'd'
}

SKILL_KEYS = ['1', '2', '3', '4']
INTERACTION_KEY = 'e'  # For portals/objects
LOOT_KEY = 'space'     # For picking up loot
HEAL_KEY = 'q'         # For healing potions
DUNGEON_ENTER_KEY = 'enter'  # For entering dungeons

# Performance settings
ENABLE_DEBUG_DISPLAY = False  # Show detection visualization (slows performance)
SAVE_DEBUG_FRAMES = False     # Save frames for debugging
DEBUG_FRAME_INTERVAL = 30     # Save every N frames if enabled
